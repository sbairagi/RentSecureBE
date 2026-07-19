import hashlib
import hmac
import json
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase

from payments.views.webhooks import cashfree_payout_webhook, razorpay_webhook


class TestWebhookSecurity(TestCase):
    def _make_request(self, payload, headers=None):
        from django.test import RequestFactory

        factory = RequestFactory()
        body = json.dumps(payload).encode("utf-8")
        req = factory.post(
            "/test",
            data=body,
            content_type="application/json",
        )
        req._body = body
        if headers:
            for key, value in headers.items():
                req.META[f"HTTP_{key.upper().replace('-', '_')}"] = value
        return req

    def _sign_payload(self, payload, secret):
        body = json.dumps(payload).encode("utf-8")
        signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        return body, signature

    def test_cashfree_invalid_signature_rejected(self):
        payload = {"transferId": "txn1", "event": "TRANSFER_SUCCESS"}
        body, _ = self._sign_payload(payload, "secret")
        req = self._make_request(payload)
        req._body = body
        req.META["HTTP_X_CASHFREE_SIGNATURE"] = "invalid"
        with patch.object(settings, "CASHFREE_WEBHOOK_SECRET", "secret"):
            response = cashfree_payout_webhook(req)
        self.assertEqual(response.status_code, 401)

    def test_cashfree_tampered_payload_rejected(self):
        original_payload = {"transferId": "txn1", "event": "TRANSFER_SUCCESS"}
        tampered_payload = {"transferId": "txn1", "event": "TRANSFER_FAILED"}
        _, signature = self._sign_payload(original_payload, "secret")
        req = self._make_request(tampered_payload)
        req.META["HTTP_X_CASHFREE_SIGNATURE"] = signature
        with patch.object(settings, "CASHFREE_WEBHOOK_SECRET", "secret"):
            response = cashfree_payout_webhook(req)
        self.assertEqual(response.status_code, 401)

    def test_cashfree_missing_x_cashfree_signature(self):
        payload = {"transferId": "txn1", "event": "TRANSFER_SUCCESS"}
        req = self._make_request(payload)
        with patch.object(settings, "CASHFREE_WEBHOOK_SECRET", "secret"):
            response = cashfree_payout_webhook(req)
        self.assertEqual(response.status_code, 400)

    def test_cashfree_missing_transfer_id_returns_400(self):
        payload = {"event": "TRANSFER_SUCCESS"}
        body, signature = self._sign_payload(payload, "test-cashfree-secret")
        req = self._make_request(payload)
        req._body = body
        req.META["HTTP_X_CASHFREE_SIGNATURE"] = signature
        with patch.object(settings, "CASHFREE_WEBHOOK_SECRET", "test-cashfree-secret"):
            response = cashfree_payout_webhook(req)
        self.assertEqual(response.status_code, 400)

    def test_razorpay_invalid_signature_rejected(self):
        payload = {
            "event": "payment.captured",
            "payload": {"payment": {"entity": {"order_id": "order1"}}},
        }
        body, _ = self._sign_payload(payload, "secret")
        req = self._make_request(payload)
        req._body = body
        req.META["HTTP_X_RAZORPAY_SIGNATURE"] = "invalid"
        with patch.object(settings, "RAZORPAY_WEBHOOK_SECRET", "secret"):
            response = razorpay_webhook(req)
        self.assertEqual(response.status_code, 401)

    def test_razorpay_tampered_payload_rejected(self):
        original_payload = {
            "event": "payment.captured",
            "payload": {"payment": {"entity": {"order_id": "order1"}}},
        }
        tampered_payload = {
            "event": "payment.captured",
            "payload": {"payment": {"entity": {"order_id": "order2"}}},
        }
        _, signature = self._sign_payload(original_payload, "secret")
        req = self._make_request(tampered_payload)
        req.META["HTTP_X_RAZORPAY_SIGNATURE"] = signature
        with patch.object(settings, "RAZORPAY_WEBHOOK_SECRET", "secret"):
            response = razorpay_webhook(req)
        self.assertEqual(response.status_code, 401)

    def test_razorpay_missing_x_razorpay_signature(self):
        payload = {
            "event": "payment.captured",
            "payload": {"payment": {"entity": {"order_id": "order1"}}},
        }
        req = self._make_request(payload)
        with patch.object(settings, "RAZORPAY_WEBHOOK_SECRET", "secret"):
            response = razorpay_webhook(req)
        self.assertEqual(response.status_code, 400)

    def test_razorpay_malformed_json_returns_400(self):
        import hashlib
        import hmac

        from django.test import RequestFactory

        factory = RequestFactory()
        body = b"not json"
        signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
        req = factory.post(
            "/test",
            data=body,
            content_type="application/json",
        )
        req._body = body
        req.META["HTTP_X_RAZORPAY_SIGNATURE"] = signature
        with patch.object(settings, "RAZORPAY_WEBHOOK_SECRET", "secret"):
            response = razorpay_webhook(req)
        self.assertEqual(response.status_code, 400)

    def test_cashfree_missing_event_returns_200(self):
        payload = {"transferId": "txn1"}
        body, signature = self._sign_payload(payload, "test-cashfree-secret")
        req = self._make_request(payload)
        req._body = body
        req.META["HTTP_X_CASHFREE_SIGNATURE"] = signature
        with patch.object(settings, "CASHFREE_WEBHOOK_SECRET", "test-cashfree-secret"):
            response = cashfree_payout_webhook(req)
        self.assertEqual(response.status_code, 404)
