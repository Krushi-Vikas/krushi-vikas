"""WhatsApp delivery for the notifications module.

Uses the WhatsApp Business Cloud API (Meta) directly — no extra package
needed, it's a plain authenticated POST. Three site_config keys drive it:

    bench --site krushivikas.local set-config whatsapp_phone_number_id "123456789"
    bench --site krushivikas.local set-config whatsapp_access_token "EAAG..."
    bench --site krushivikas.local set-config whatsapp_api_version "v20.0"   # optional, defaults below

Until those are set, send_whatsapp() is a documented no-op — every other
notification path (bell icon, ToDo) keeps working unaffected. Each User
needs a `whatsapp_number` (E.164, e.g. 919876543210 with no leading +)
for delivery to reach them; users without one are silently skipped.

Meta requires business-initiated messages to use a pre-approved template
(a free-form message only works inside a 24h customer-service window that
does not apply here), so this sends a template call. Create and get
"KrushiVikasAlert" approved in the WhatsApp Manager before going live —
until then, log delivery attempts are the useful thing this module gives
you to confirm wiring is correct.
"""

import frappe
import frappe.integrations.utils

DEFAULT_API_VERSION = "v20.0"
TEMPLATE_NAME = "krushivikas_alert"  # must match the approved template name exactly


def is_configured():
    return bool(
        frappe.conf.get("whatsapp_phone_number_id")
        and frappe.conf.get("whatsapp_access_token")
    )


def send_whatsapp(user, message):
    """Best-effort WhatsApp send to a User's registered number.

    Never raises into the caller — a notification run must not fail
    because one WhatsApp send failed or credentials aren't in yet.
    """
    if not is_configured():
        frappe.logger("whatsapp").info(
            f"WhatsApp not configured — skipped alert to {user}: {message}"
        )
        return False

    number = frappe.db.get_value("User", user, "whatsapp_number")
    if not number:
        return False

    phone_id = frappe.conf.get("whatsapp_phone_number_id")
    token = frappe.conf.get("whatsapp_access_token")
    version = frappe.conf.get("whatsapp_api_version") or DEFAULT_API_VERSION
    url = f"https://graph.facebook.com/{version}/{phone_id}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "template",
        "template": {
            "name": TEMPLATE_NAME,
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": message[:1024]}],
                }
            ],
        },
    }

    try:
        response = frappe.integrations.utils.make_post_request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            data=frappe.as_json(payload),
        )
        frappe.logger("whatsapp").info(f"WhatsApp sent to {user} ({number}): {response}")
        return True
    except Exception:
        frappe.log_error(title="WhatsApp send failed", message=frappe.get_traceback())
        return False
