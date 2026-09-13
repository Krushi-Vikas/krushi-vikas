import json
from unittest.mock import patch, MagicMock
import frappe
from krushi_vikas.whatsapp import (
    clean_phone_number,
    is_configured,
    get_whatsapp_status,
    webhook,
    send_whatsapp,
    DEFAULT_VERIFY_TOKEN,
)


def run():
    print("=== TESTING WHATSAPP INTEGRATION & WEBHOOK EVENTS ===")

    test_phone_number_cleaning()
    test_configuration_status()
    test_webhook_handshake()
    test_webhook_event_processing()
    test_send_whatsapp_unconfigured()
    test_send_whatsapp_mocked_success()
    test_send_whatsapp_error_handling()
    test_feedback_survey_submission_whatsapp_alert()

    print("\n=======================================================")
    print("🎉 ALL WHATSAPP INTEGRATION & EVENT TESTS PASSED! 🎉")
    print("=======================================================")


def test_phone_number_cleaning():
    assert clean_phone_number("+91 98765-43210") == "919876543210"
    assert clean_phone_number("09876543210") == "9876543210"
    assert clean_phone_number("+1 (555) 123-4567") == "15551234567"
    assert clean_phone_number(None) == ""
    print("  [PASS] Phone number normalization (E.164)")


def test_configuration_status():
    status = get_whatsapp_status()
    assert "is_configured" in status
    assert "webhook_url" in status
    assert status["webhook_url"].endswith("/api/method/krushi_vikas.whatsapp.webhook")
    assert "verify_token" in status
    print(f"  [PASS] WhatsApp status diagnostic endpoint (Webhook URL: {status['webhook_url']})")


def test_webhook_handshake():
    # 1. Valid handshake
    frappe.request = MagicMock()
    frappe.request.method = "GET"
    frappe.form_dict = {
        "hub.mode": "subscribe",
        "hub.challenge": "test_challenge_12345",
        "hub.verify_token": DEFAULT_VERIFY_TOKEN,
    }

    res = webhook()
    assert res.status_code == 200
    assert res.get_data(as_text=True) == "test_challenge_12345"
    assert res.mimetype == "text/plain"
    print("  [PASS] Webhook GET verification handshake succeeded with challenge token.")

    # 2. Invalid verify token
    frappe.form_dict["hub.verify_token"] = "wrong_token"
    res_bad = webhook()
    assert res_bad.status_code == 403
    print("  [PASS] Webhook GET rejected invalid verify token with HTTP 403.")


def test_webhook_event_processing():
    frappe.request = MagicMock()
    frappe.request.method = "POST"

    # Mock delivery status event
    status_event = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "1234567890",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"phone_number_id": "999999"},
                    "statuses": [{
                        "id": "wamid.HBgLMTIzNDU2",
                        "status": "delivered",
                        "timestamp": "1726230000",
                        "recipient_id": "919876543210"
                    }]
                }
            }]
        }]
    }

    frappe.request.get_json.return_value = status_event
    res_status = webhook()
    assert res_status.status_code == 200
    assert res_status.get_data(as_text=True) == "EVENT_RECEIVED"
    print("  [PASS] Webhook POST delivery status event processed successfully.")

    # Mock incoming user text message event
    msg_event = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "1234567890",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"phone_number_id": "999999"},
                    "contacts": [{"wa_id": "919876543210", "profile": {"name": "Ramesh Patel"}}],
                    "messages": [{
                        "from": "919876543210",
                        "id": "wamid.HBgLNTY3ODkw",
                        "timestamp": "1726230050",
                        "text": {"body": "Tree plantation survey completed today in village"},
                        "type": "text"
                    }]
                }
            }]
        }]
    }

    frappe.request.get_json.return_value = msg_event
    res_msg = webhook()
    assert res_msg.status_code == 200
    assert res_msg.get_data(as_text=True) == "EVENT_RECEIVED"
    print("  [PASS] Webhook POST incoming text message event received & parsed.")


def test_send_whatsapp_unconfigured():
    # When unconfigured in site_config, send_whatsapp must gracefully no-op
    with patch.dict(frappe.conf, {"whatsapp_phone_number_id": None, "whatsapp_access_token": None}, clear=False):
        res = send_whatsapp("Administrator", "Unconfigured test message")
        assert res["success"] is False
        assert "not configured" in res["message"].lower()
    print("  [PASS] send_whatsapp safely no-ops without exception when unconfigured.")


def test_send_whatsapp_mocked_success():
    # When configured, verify payload and successful dispatch
    with patch.dict(frappe.conf, {
        "whatsapp_phone_number_id": "123456789",
        "whatsapp_access_token": "test_meta_token_abc"
    }, clear=False):
        with patch("requests.post") as mock_post:
            mock_res = MagicMock()
            mock_res.ok = True
            mock_res.status_code = 200
            mock_res.json.return_value = {
                "messaging_product": "whatsapp",
                "contacts": [{"input": "919876543210", "wa_id": "919876543210"}],
                "messages": [{"id": "wamid.HBgLMTIz"}]
            }
            mock_post.return_value = mock_res

            res = send_whatsapp("919876543210", "Task TASK-001 has been assigned to you")
            assert res["success"] is True
            assert mock_post.called

            # Check authorization header
            headers = mock_post.call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer test_meta_token_abc"
            print("  [PASS] send_whatsapp successfully dispatches message to Meta Cloud API.")


def test_send_whatsapp_error_handling():
    # Verify exact Meta API error extraction
    with patch.dict(frappe.conf, {
        "whatsapp_phone_number_id": "123456789",
        "whatsapp_access_token": "test_meta_token_abc"
    }, clear=False):
        with patch("requests.post") as mock_post:
            mock_res = MagicMock()
            mock_res.ok = False
            mock_res.status_code = 400
            mock_res.json.return_value = {
                "error": {
                    "message": "(#100) Parameter template['name'] is invalid",
                    "type": "OAuthException",
                    "code": 100
                }
            }
            mock_post.return_value = mock_res

            res = send_whatsapp("919876543210", "Invalid template test")
            assert res["success"] is False
            assert "100" in res["message"]
            assert "Parameter template['name'] is invalid" in res["message"]
            print("  [PASS] send_whatsapp accurately captures and reports Meta Graph API error codes.")


def test_feedback_survey_submission_whatsapp_alert():
    from krushi_vikas.notifications import notify_feedback_survey_submitted

    doc = MagicMock()
    doc.name = "FS-2026-00042"
    doc.project = "KV-PROJ-TEST"
    doc.village = "Ralegaon"
    doc.field_officer = "fo@krushivikas.org"
    doc.owner = "fo@krushivikas.org"
    doc.get = lambda k: getattr(doc, k, None)

    mock_project_data = {
        "name": "KV-PROJ-TEST",
        "project_manager": "pm@krushivikas.org",
        "project_coordinator": "pc@krushivikas.org",
        "project_director": "pd@krushivikas.org",
    }

    with patch("frappe.db.get_value", return_value=mock_project_data):
        with patch("krushi_vikas.notifications._push") as mock_push:
            notify_feedback_survey_submitted(doc)
            assert mock_push.call_count == 2
            called_users = {call[0][0] for call in mock_push.call_args_list}
            assert "pm@krushivikas.org" in called_users
            assert "pc@krushivikas.org" in called_users
            for call in mock_push.call_args_list:
                subject = call[0][1]
                assert "Feedback Survey Submitted" in subject
                assert "Ralegaon" in subject
                assert "FS-2026-00042" in subject
                assert "fo@krushivikas.org" in subject
                assert call[0][2] == "Feedback Survey"
                assert call[0][3] == "FS-2026-00042"
    print("  [PASS] notify_feedback_survey_submitted triggers alerts to assigned PM and Coordinator.")
