"""WhatsApp delivery and webhook integration for the notifications module.

Uses the WhatsApp Business Cloud API (Meta) directly — no extra package
needed, it's a plain authenticated POST. Configuration keys in site_config.json:

    bench --site frappe.local set-config whatsapp_phone_number_id "<phone_number_id>"
    bench --site frappe.local set-config whatsapp_access_token "<access_token>"
    bench --site frappe.local set-config whatsapp_verify_token "<webhook_verify_token>"
    bench --site frappe.local set-config whatsapp_api_version "v20.0"   # optional, defaults to v20.0
    bench --site frappe.local set-config whatsapp_template_name "krushivikas_alert" # optional

Features:
1. Webhook Endpoint (/api/method/krushi_vikas.whatsapp.webhook):
   - GET: Meta webhook verification handshake (hub.mode, hub.challenge, hub.verify_token).
   - POST: Inbound WhatsApp events (message delivery statuses, incoming messages/replies).
2. Outbound Alerts (send_whatsapp):
   - Sends template alerts (default: "krushivikas_alert") or text alerts.
   - Falls back gracefully and logs detailed Meta Graph API error messages.
3. Status & Diagnostics (get_whatsapp_status, test_whatsapp_connection):
   - Whitelisted endpoints to test and verify configuration from Desk or API.
"""

import re
import json
import frappe
from werkzeug.wrappers import Response

DEFAULT_API_VERSION = "v20.0"
DEFAULT_TEMPLATE_NAME = "krushivikas_alert"
DEFAULT_VERIFY_TOKEN = "krushi_vikas_webhook_token"


def clean_phone_number(phone):
    """Normalizes phone number to E.164 digits-only format required by WhatsApp API (e.g. 919876543210)."""
    if not phone:
        return ""
    digits = re.sub(r"[^\d]", "", str(phone))
    # Remove leading trunk zero if present (e.g. 09876543210 -> 9876543210)
    if digits.startswith("0") and len(digits) > 10:
        digits = digits[1:]
    return digits


def is_configured():
    """Checks if WhatsApp Cloud API credentials are configured in site_config."""
    return bool(
        frappe.conf.get("whatsapp_phone_number_id")
        and frappe.conf.get("whatsapp_access_token")
    )


@frappe.whitelist(allow_guest=True)
def webhook():
    """Meta WhatsApp Cloud API Webhook Handler.

    Handles both GET verification handshake and POST incoming WhatsApp events.
    Meta docs: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/
    """
    request_method = frappe.request.method if hasattr(frappe, "request") and frappe.request else "GET"

    # 1. GET: Webhook Verification Handshake
    if request_method == "GET":
        mode = frappe.form_dict.get("hub.mode") or frappe.form_dict.get("hub_mode")
        challenge = frappe.form_dict.get("hub.challenge") or frappe.form_dict.get("hub_challenge")
        verify_token = frappe.form_dict.get("hub.verify_token") or frappe.form_dict.get("hub_verify_token")

        expected_token = frappe.conf.get("whatsapp_verify_token") or DEFAULT_VERIFY_TOKEN

        if mode == "subscribe" and verify_token == expected_token:
            frappe.logger("whatsapp").info("WhatsApp Webhook handshake verified successfully.")
            return Response(challenge, mimetype="text/plain", status=200)

        frappe.logger("whatsapp").warning(
            f"WhatsApp Webhook verification failed. Received mode={mode}, token={verify_token}"
        )
        return Response("Forbidden: Invalid verification token", mimetype="text/plain", status=403)

    # 2. POST: Inbound WhatsApp Events
    if request_method == "POST":
        try:
            data = frappe.request.get_json() if hasattr(frappe.request, "get_json") else None
            if not data:
                try:
                    data = json.loads(frappe.request.data.decode("utf-8"))
                except Exception:
                    data = frappe.form_dict

            return handle_whatsapp_event(data)
        except Exception as e:
            frappe.log_error(title="WhatsApp Webhook Processing Failed", message=frappe.get_traceback())
            return Response(f"Internal error: {str(e)}", mimetype="text/plain", status=500)


def handle_whatsapp_event(payload):
    """Processes inbound Meta WhatsApp webhook event payload."""
    logger = frappe.logger("whatsapp")

    if not isinstance(payload, dict):
        logger.warning(f"WhatsApp webhook received invalid payload type: {type(payload)}")
        return Response("EVENT_RECEIVED", mimetype="text/plain", status=200)

    entry_list = payload.get("entry", [])
    for entry in entry_list:
        changes = entry.get("changes", [])
        for change in changes:
            field = change.get("field")
            value = change.get("value", {})

            # We care primarily about messages and status changes
            if field != "messages" and "messages" not in value and "statuses" not in value:
                continue

            # A. Process delivery status updates (sent, delivered, read, failed)
            statuses = value.get("statuses", [])
            for st in statuses:
                msg_id = st.get("id")
                status = st.get("status")
                recipient_id = st.get("recipient_id")
                errors = st.get("errors", [])
                logger.info(
                    f"WhatsApp message status update: id={msg_id}, status={status}, recipient={recipient_id}"
                )
                if errors:
                    logger.error(f"WhatsApp message delivery error: {errors}")

            # B. Process inbound messages from users / field workers
            messages = value.get("messages", [])
            contacts = {c.get("wa_id"): c.get("profile", {}).get("name") for c in value.get("contacts", [])}

            for msg in messages:
                from_number = msg.get("from")
                msg_type = msg.get("type")
                msg_id = msg.get("id")
                sender_name = contacts.get(from_number, from_number)

                body = ""
                if msg_type == "text":
                    body = msg.get("text", {}).get("body", "")
                elif msg_type == "button":
                    body = msg.get("button", {}).get("text", "")
                elif msg_type == "interactive":
                    body = msg.get("interactive", {}).get("button_reply", {}).get("title", "")
                else:
                    body = f"[{msg_type} message]"

                logger.info(
                    f"Inbound WhatsApp message received from {sender_name} ({from_number}): {body}"
                )

                # Attempt to link with existing User if registered
                linked_user = frappe.db.get_value("User", {"whatsapp_number": from_number}, "name")
                if not linked_user and from_number:
                    # Check without country code prefix if relevant
                    linked_user = frappe.db.get_value("User", {"whatsapp_number": ["like", f"%{from_number[-10:]}"]}, "name")

                if linked_user:
                    logger.info(f"Matched sender {from_number} to registered user '{linked_user}'.")

    return Response("EVENT_RECEIVED", mimetype="text/plain", status=200)


def send_whatsapp(user_or_number, message, template_name=None, use_template=True):
    """Best-effort WhatsApp send to a User's registered number or direct phone number.

    Never raises into the caller — a notification run must not fail
    because one WhatsApp send failed or credentials aren't configured.

    Args:
        user_or_number (str): User ID (email) or direct phone number (E.164).
        message (str): Alert message to send.
        template_name (str, optional): Custom template name. Defaults to site config or krushivikas_alert.
        use_template (bool): If True, sends Meta pre-approved template; if False, sends standard text.

    Returns:
        dict: {"success": bool, "message": str, "response": dict|None}
    """
    logger = frappe.logger("whatsapp")

    if not is_configured():
        logger.info(f"WhatsApp not configured — skipped alert to {user_or_number}: {message}")
        return {"success": False, "message": "WhatsApp not configured in site_config", "response": None}

    # Resolve phone number
    number = None
    user_label = str(user_or_number)

    # Check if user_or_number is an existing User email
    if frappe.db.exists("User", user_or_number):
        number = frappe.db.get_value("User", user_or_number, "whatsapp_number")
        if not number:
            logger.info(f"User {user_or_number} has no 'whatsapp_number' set — skipping.")
            return {"success": False, "message": f"User {user_or_number} has no WhatsApp number", "response": None}
    else:
        # Treat as direct phone number
        number = clean_phone_number(user_or_number)

    number = clean_phone_number(number)
    if not number or len(number) < 8:
        logger.warning(f"Invalid recipient phone number '{number}' for {user_label}.")
        return {"success": False, "message": f"Invalid phone number: {number}", "response": None}

    phone_id = frappe.conf.get("whatsapp_phone_number_id")
    token = frappe.conf.get("whatsapp_access_token")
    version = frappe.conf.get("whatsapp_api_version") or DEFAULT_API_VERSION
    active_template = template_name or frappe.conf.get("whatsapp_template_name") or DEFAULT_TEMPLATE_NAME

    url = f"https://graph.facebook.com/{version}/{phone_id}/messages"

    # Build payload
    if use_template:
        payload = {
            "messaging_product": "whatsapp",
            "to": number,
            "type": "template",
            "template": {
                "name": active_template,
                "language": {"code": "en"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": str(message)[:1024]}],
                    }
                ],
            },
        }
    else:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {"preview_url": False, "body": str(message)[:4096]},
        }

    try:
        import requests
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        res = requests.post(url, headers=headers, json=payload, timeout=15)

        if not res.ok:
            error_data = {}
            try:
                error_data = res.json().get("error", {})
            except Exception:
                error_data = {"message": res.text}

            error_msg = error_data.get("message", res.text)
            error_code = error_data.get("code", res.status_code)
            detailed_err = f"Meta Graph API Error {error_code}: {error_msg}"

            logger.error(f"WhatsApp send failed to {user_label} ({number}): {detailed_err}")
            frappe.log_error(title=f"WhatsApp send failed: {user_label}", message=f"{detailed_err}\nPayload: {frappe.as_json(payload)}")
            return {"success": False, "message": detailed_err, "response": error_data}

        res_json = res.json()
        logger.info(f"WhatsApp sent successfully to {user_label} ({number}): {res_json}")
        return {"success": True, "message": "Message dispatched successfully", "response": res_json}

    except Exception as exc:
        traceback_str = frappe.get_traceback()
        logger.error(f"WhatsApp request exception to {user_label}: {str(exc)}")
        frappe.log_error(title=f"WhatsApp exception: {user_label}", message=traceback_str)
        return {"success": False, "message": str(exc), "response": None}


@frappe.whitelist(allow_guest=True)
def get_whatsapp_status():
    """Returns current WhatsApp Cloud API configuration status and diagnostics."""
    phone_id = frappe.conf.get("whatsapp_phone_number_id")
    has_token = bool(frappe.conf.get("whatsapp_access_token"))
    verify_token = frappe.conf.get("whatsapp_verify_token") or DEFAULT_VERIFY_TOKEN
    version = frappe.conf.get("whatsapp_api_version") or DEFAULT_API_VERSION
    template_name = frappe.conf.get("whatsapp_template_name") or DEFAULT_TEMPLATE_NAME
    configured = is_configured()

    base_url = frappe.utils.get_url()
    webhook_url = f"{base_url}/api/method/krushi_vikas.whatsapp.webhook"

    return {
        "is_configured": configured,
        "phone_number_id": phone_id if phone_id else "Not configured",
        "has_access_token": has_token,
        "api_version": version,
        "template_name": template_name,
        "verify_token": verify_token,
        "webhook_url": webhook_url,
        "instructions": [
            f"1. Set Phone Number ID: bench --site {frappe.local.site or 'frappe.local'} set-config whatsapp_phone_number_id '<id>'",
            f"2. Set Access Token: bench --site {frappe.local.site or 'frappe.local'} set-config whatsapp_access_token '<EAAG...>'",
            f"3. Configure Webhook in Meta App Dashboard: URL: {webhook_url}, Verify Token: {verify_token}",
            "4. Ensure recipient Users have 'WhatsApp Number' populated in User Profile (e.g. 919876543210)."
        ]
    }


@frappe.whitelist()
def test_whatsapp_connection(phone_number=None, message="Test alert from Krushi Vikas"):
    """Whitelisted test utility to verify WhatsApp Cloud API setup."""
    if not is_configured():
        return {
            "success": False,
            "message": "WhatsApp is not configured. Please set whatsapp_phone_number_id and whatsapp_access_token in site_config.json.",
            "status": get_whatsapp_status()
        }

    target = phone_number or frappe.session.user
    res = send_whatsapp(target, message, use_template=False)
    if not res["success"]:
        # Also try template in case Meta rejects free-form text
        res = send_whatsapp(target, message, use_template=True)

    return res

