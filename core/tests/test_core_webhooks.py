"""Tests for core webhook endpoints and payment handlers."""

import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from core.views import (
    _get_rent_from_event,
    _process_referral,
    cashfree_payout_webhook,
    check_signature_or_return_http_response,
    create_rent_payment,
    razorpay_webhook,
)
from properties.models import Building, Renter, RentRecord, Unit

User = get_user_model()


class ProcessReferralTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="referral_user",
            email="referral@test.com",
            password="p",
            full_name="Referral User",
            phone="+919999999999",
        )
        self.otp = __import__("core.models", fromlist=["OTP"]).OTP.objects.create(
            phone_number="+919999999999",
            code="123456",
            referral_code="",
        )

    def test_invalid_referral_returns_error(self):
        self.otp.referral_code = "INVALID"
        self.otp.save()
        response = _process_referral(self.otp, self.user)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": "Invalid referral code"})


class CashfreePayoutWebhookTests(TestCase):
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

    def test_invalid_signature_returns_400(self):
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
        self.assertEqual(response.status_code, 400)

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
            with patch("core.views.send_payout_notification"):
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
            with patch("core.views.send_payout_notification"):
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
            with patch("core.views.send_payout_notification"):
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
            rent = RentRecord.objects.create(
                unit=self.unit,
                renter=self.renter,
                amount=10000,
                payment_method="upi",
                status="PAID",
                payout_reference="txn_exc",
                payout_status="PENDING",
                due_date="2025-01-05",
            )
            with patch(
                "core.views.send_payout_notification",
                side_effect=Exception("notification failed"),
            ):
                response = cashfree_payout_webhook(req)
        self.assertEqual(response.status_code, 200)
        rent.refresh_from_db()
        self.assertEqual(rent.payout_status, "SUCCESS")


class CreateRentPaymentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="pay_user",
            email="pay@test.com",
            password="p",
            full_name="Pay User",
            phone="+919999999999",
        )
        self.building = Building.objects.create(
            owner=self.user,
            name="PayB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="P1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Pay Renter",
            phone="+919876543210",
            email="pr@test.com",
            rent_amount=10000,
            start_date="2025-01-01",
        )

    def _make_request(self, payload):
        from django.test import RequestFactory

        factory = RequestFactory()
        req = factory.post(
            "/test",
            data=json.dumps(payload),
            content_type="application/json",
        )
        return req

    def test_invalid_method_returns_405(self):
        from django.test import RequestFactory

        factory = RequestFactory()
        req = factory.get("/test")
        response = create_rent_payment(req)
        self.assertEqual(response.status_code, 405)

    def test_rent_not_found_returns_404(self):
        response = create_rent_payment(self._make_request({"rent_id": "9999"}))
        self.assertEqual(response.status_code, 404)

    @patch("core.views.razorpay.Client")
    def test_success_returns_order(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.order.create.return_value = {"id": "order_123", "amount": 100000}

        rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=10000,
            payment_method="upi",
            status="PENDING",
            due_date="2025-01-05",
        )
        response = create_rent_payment(self._make_request({"rent_id": str(rent.id)}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["order_id"], "order_123")
        rent.refresh_from_db()
        self.assertEqual(rent.razorpay_order_id, "order_123")


class CheckSignatureTests(TestCase):
    def test_invalid_signature_returns_400(self):
        body = b"test body"
        signature = "bad_signature"
        response = check_signature_or_return_http_response("secret", signature, body)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 400)

    def test_missing_signature_returns_400(self):
        body = b"test body"
        response = check_signature_or_return_http_response("secret", None, body)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 400)

    def test_valid_signature_returns_none(self):
        body = b"test body"
        secret = "secret"
        signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        response = check_signature_or_return_http_response(secret, signature, body)
        self.assertIsNone(response)


class GetRentFromEventTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="event_user",
            email="event@test.com",
            password="p",
            full_name="Event User",
            phone="+919999999999",
        )
        self.building = Building.objects.create(
            owner=self.user,
            name="EvB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="EV1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="EvRenter",
            phone="+919876543210",
            email="evr@test.com",
            rent_amount=10000,
            start_date="2025-01-01",
        )

    def test_payment_link_paid_missing_reference_returns_none(self):
        data = {
            "event": "payment_link.paid",
            "payload": {
                "payment_link": {"entity": {}},
            },
        }
        result = _get_rent_from_event(data, data["event"])
        self.assertIsNone(result)

    def test_payment_link_paid_returns_rent(self):
        rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=10000,
            payment_method="upi",
            status="PENDING",
            due_date="2025-01-05",
        )
        data = {
            "event": "payment_link.paid",
            "payload": {
                "payment_link": {"entity": {"reference_id": str(rent.id)}},
            },
        }
        result = _get_rent_from_event(data, data["event"])
        self.assertEqual(result.id, rent.id)


class RazorpayWebhookTests(TestCase):
    def test_get_returns_405(self):
        from django.test import RequestFactory

        factory = RequestFactory()
        req = factory.get("/test")
        response = razorpay_webhook(req)
        self.assertEqual(response.status_code, 405)

    def test_invalid_json_returns_400(self):
        from django.test import RequestFactory

        factory = RequestFactory()
        req = factory.post(
            "/test",
            data="not json",
            content_type="application/json",
        )
        response = razorpay_webhook(req)
        self.assertEqual(response.status_code, 400)


class UpdateOwnerBankDetailsTests(TestCase):
    def test_missing_fields_returns_400(self):
        from rest_framework_simplejwt.tokens import RefreshToken

        from django.test import RequestFactory

        user = User.objects.create_user(
            username="bank_user",
            email="bank@test.com",
            password="p",
            full_name="Bank User",
            phone="+919999999999",
        )
        factory = RequestFactory()
        token = RefreshToken.for_user(user).access_token
        req = factory.post(
            "/test",
            data={},
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        req.user = user
        from core.views import update_owner_bank_details

        response = update_owner_bank_details(req)
        self.assertEqual(response.status_code, 400)
