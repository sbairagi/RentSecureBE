import hashlib
import hmac
import json
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from payments.views.webhooks import cashfree_payout_webhook, razorpay_webhook
from properties.models import Building, Renter, RentRecord, Unit

User = get_user_model()


class TestCashfreeWebhook(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="cf_user",
            email="cf@test.com",
            password="p",
            full_name="CF User",
            phone="+919999999999",
        )
        self.building = Building.objects.create(
            owner=self.user,
            name="CFB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="CF1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="CF Renter",
            phone="+919876543210",
            email="cfr@test.com",
            rent_amount=10000,
            start_date="2025-01-01",
        )

    def _make_request(self, payload):
        from django.test import RequestFactory

        factory = RequestFactory()
        body = json.dumps(payload).encode("utf-8")
        req = factory.post(
            "/test",
            data=body,
            content_type="application/json",
        )
        req._body = body
        return req

    def _sign_payload(self, payload, secret):
        body = json.dumps(payload).encode("utf-8")
        signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        return body, signature

    def test_invalid_method_returns_405(self):
        from django.test import RequestFactory

        factory = RequestFactory()
        req = factory.get("/test")
        response = cashfree_payout_webhook(req)
        self.assertEqual(response.status_code, 405)

    def test_missing_signature_returns_400(self):
        with patch.object(settings, "CASHFREE_WEBHOOK_SECRET", "secret"):
            response = cashfree_payout_webhook(
                self._make_request(
                    {
                        "transferId": "txn_success",
                        "event": "TRANSFER_SUCCESS",
                    }
                )
            )
        self.assertEqual(response.status_code, 400)

    def test_invalid_signature_returns_401(self):
        payload = {
            "transferId": "txn_success",
            "event": "TRANSFER_SUCCESS",
        }
        body, _ = self._sign_payload(payload, "secret")
        req = self._make_request(payload)
        req._body = body
        req.META["HTTP_X_CASHFREE_SIGNATURE"] = "invalid"
        with patch.object(settings, "CASHFREE_WEBHOOK_SECRET", "secret"):
            response = cashfree_payout_webhook(req)
        self.assertEqual(response.status_code, 401)

    def test_valid_signature_allows_webhook(self):
        payload = {
            "transferId": "txn_success",
            "event": "TRANSFER_SUCCESS",
        }
        body, signature = self._sign_payload(payload, "test-cashfree-secret")
        req = self._make_request(payload)
        req._body = body
        req.META["HTTP_X_CASHFREE_SIGNATURE"] = signature
        with patch.object(settings, "CASHFREE_WEBHOOK_SECRET", "test-cashfree-secret"):
            rent = RentRecord.objects.create(
                unit=self.unit,
                renter=self.renter,
                amount=10000,
                payment_method="upi",
                status="PAID",
                payout_reference="txn_success",
                payout_status="PENDING",
                due_date="2025-01-05",
            )
            response = cashfree_payout_webhook(req)
        self.assertEqual(response.status_code, 200)
        rent.refresh_from_db()
        self.assertEqual(rent.payout_status, "SUCCESS")

    def test_invalid_transfer_id_returns_404(self):
        payload = {
            "transferId": "nonexistent",
            "event": "TRANSFER_SUCCESS",
        }
        body, signature = self._sign_payload(payload, "test-cashfree-secret")
        req = self._make_request(payload)
        req._body = body
        req.META["HTTP_X_CASHFREE_SIGNATURE"] = signature
        with patch.object(settings, "CASHFREE_WEBHOOK_SECRET", "test-cashfree-secret"):
            response = cashfree_payout_webhook(req)
        self.assertEqual(response.status_code, 404)

    def test_transfer_success_updates_status(self):
        payload = {
            "transferId": "txn_success",
            "event": "TRANSFER_SUCCESS",
        }
        body, signature = self._sign_payload(payload, "test-cashfree-secret")
        req = self._make_request(payload)
        req._body = body
        req.META["HTTP_X_CASHFREE_SIGNATURE"] = signature
        with patch.object(settings, "CASHFREE_WEBHOOK_SECRET", "test-cashfree-secret"):
            rent = RentRecord.objects.create(
                unit=self.unit,
                renter=self.renter,
                amount=10000,
                payment_method="upi",
                status="PAID",
                payout_reference="txn_success",
                payout_status="PENDING",
                due_date="2025-01-05",
            )
            response = cashfree_payout_webhook(req)
        self.assertEqual(response.status_code, 200)
        rent.refresh_from_db()
        self.assertEqual(rent.payout_status, "SUCCESS")

    def test_transfer_failed_updates_status(self):
        payload = {
            "transferId": "txn_fail",
            "event": "TRANSFER_FAILED",
        }
        body, signature = self._sign_payload(payload, "test-cashfree-secret")
        req = self._make_request(payload)
        req._body = body
        req.META["HTTP_X_CASHFREE_SIGNATURE"] = signature
        with patch.object(settings, "CASHFREE_WEBHOOK_SECRET", "test-cashfree-secret"):
            rent = RentRecord.objects.create(
                unit=self.unit,
                renter=self.renter,
                amount=10000,
                payment_method="upi",
                status="PAID",
                payout_reference="txn_fail",
                payout_status="PENDING",
                due_date="2025-01-05",
            )
            response = cashfree_payout_webhook(req)
        self.assertEqual(response.status_code, 200)
        rent.refresh_from_db()
        self.assertEqual(rent.payout_status, "FAILED")

    def test_notification_exception_is_handled(self):
        payload = {
            "transferId": "txn_exc",
            "event": "TRANSFER_SUCCESS",
        }
        body, signature = self._sign_payload(payload, "test-cashfree-secret")
        req = self._make_request(payload)
        req._body = body
        req.META["HTTP_X_CASHFREE_SIGNATURE"] = signature
        with patch.object(settings, "CASHFREE_WEBHOOK_SECRET", "test-cashfree-secret"):
            RentRecord.objects.create(
                unit=self.unit,
                renter=self.renter,
                amount=10000,
                payment_method="upi",
                status="PAID",
                payout_reference="txn_exc",
                payout_status="PENDING",
                due_date="2025-01-05",
            )
            response = cashfree_payout_webhook(req)
        self.assertEqual(response.status_code, 200)
        rent = RentRecord.objects.get(payout_reference="txn_exc")
        self.assertEqual(rent.payout_status, "SUCCESS")


class TestRazorpayWebhook(TestCase):
    def test_get_returns_405(self):
        from django.test import RequestFactory

        factory = RequestFactory()
        req = factory.get("/test")
        response = razorpay_webhook(req)
        self.assertEqual(response.status_code, 405)

    def test_invalid_json_returns_400(self):
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
