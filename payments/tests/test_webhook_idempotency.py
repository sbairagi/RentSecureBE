import hashlib
import hmac
import json
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from payments.models import WebhookEvent
from payments.views.webhooks import cashfree_payout_webhook, razorpay_webhook
from properties.models import Building, Renter, RentRecord, Unit

User = get_user_model()


class TestWebhookIdempotency(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="idem_user",
            email="idem@test.com",
            password="p",
            full_name="Idem User",
            phone="+919999999999",
        )
        self.building = Building.objects.create(
            owner=self.user,
            name="IdemB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="ID1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Idem Renter",
            phone="+919876543210",
            email="idemr@test.com",
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

    def test_duplicate_cashfree_webhook_returns_200(self):
        payload = {
            "transferId": "txn_dup",
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
                payout_reference="txn_dup",
                payout_status="PENDING",
                due_date="2025-01-05",
            )
            response1 = cashfree_payout_webhook(req)
            response2 = cashfree_payout_webhook(req)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(WebhookEvent.objects.count(), 1)

    def test_duplicate_razorpay_webhook_returns_200(self):
        payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "order_id": "order_dup",
                    }
                }
            },
        }
        body, signature = self._sign_payload(payload, "test-razorpay-secret")
        req = self._make_request(payload)
        req._body = body
        req.META["HTTP_X_RAZORPAY_SIGNATURE"] = signature
        with patch.object(settings, "RAZORPAY_WEBHOOK_SECRET", "test-razorpay-secret"):
            RentRecord.objects.create(
                unit=self.unit,
                renter=self.renter,
                amount=10000,
                payment_method="upi",
                status="PENDING",
                razorpay_order_id="order_dup",
                due_date="2025-01-05",
            )
            response1 = razorpay_webhook(req)
            response2 = razorpay_webhook(req)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(WebhookEvent.objects.count(), 1)

    def test_webhook_event_created_on_first_processing(self):
        payload = {
            "transferId": "txn_created",
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
                payout_reference="txn_created",
                payout_status="PENDING",
                due_date="2025-01-05",
            )
            cashfree_payout_webhook(req)
        event = WebhookEvent.objects.get(event_id="txn_created")
        self.assertEqual(event.provider, WebhookEvent.Provider.CASHFREE)
        self.assertEqual(event.status, WebhookEvent.Status.PROCESSED)

    def test_webhook_event_with_different_event_id_processed(self):
        payload1 = {
            "transferId": "txn_a",
            "event": "TRANSFER_SUCCESS",
        }
        payload2 = {
            "transferId": "txn_b",
            "event": "TRANSFER_SUCCESS",
        }
        body1, sig1 = self._sign_payload(payload1, "test-cashfree-secret")
        body2, sig2 = self._sign_payload(payload2, "test-cashfree-secret")
        req1 = self._make_request(payload1)
        req1._body = body1
        req1.META["HTTP_X_CASHFREE_SIGNATURE"] = sig1
        req2 = self._make_request(payload2)
        req2._body = body2
        req2.META["HTTP_X_CASHFREE_SIGNATURE"] = sig2
        with patch.object(settings, "CASHFREE_WEBHOOK_SECRET", "test-cashfree-secret"):
            RentRecord.objects.create(
                unit=self.unit,
                renter=self.renter,
                amount=10000,
                payment_method="upi",
                status="PAID",
                payout_reference="txn_a",
                payout_status="PENDING",
                due_date="2025-01-05",
            )
            RentRecord.objects.create(
                unit=self.unit,
                renter=self.renter,
                amount=10000,
                payment_method="upi",
                status="PAID",
                payout_reference="txn_b",
                payout_status="PENDING",
                due_date="2025-01-06",
            )
            with patch(
                "notification.services.rent_notify_service.send_payout_notification"
            ):
                cashfree_payout_webhook(req1)
                cashfree_payout_webhook(req2)
        self.assertEqual(WebhookEvent.objects.count(), 2)
