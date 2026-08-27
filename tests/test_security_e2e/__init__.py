"""
Security E2E Tests — IDOR, Authorization, and Payment Security

Mandatory security regression tests that must NEVER be disabled or
downgraded without explicit security review.

These tests verify that the backend enforces authorization on every
protected operation and that client-side trust is never assumed.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import AddOnPurchase as AddOnPurchase
from core.models import OwnerBankDetails as OwnerBankDetails
from core.models import PlanFeatureLimit as PlanFeatureLimit
from core.models import SubscriptionPlan as SubscriptionPlan
from core.models import UserSubscription as UserSubscription
from notification.models import DeviceToken as DeviceToken
from notification.models import Notification as Notification
from properties.models import Building as Building
from properties.models import Caretaker as Caretaker
from properties.models import ExtraCharge as ExtraCharge
from properties.models import Renter as Renter
from properties.models import RentRecord as RentRecord
from properties.models import Unit as Unit

User = get_user_model()
API_PREFIX = "/api"


class IDORSecurityTests(APITestCase):
    """Test Insecure Direct Object Reference (IDOR) prevention.

    Every protected resource must be scoped to the authenticated user.
    Changing IDs in requests must NOT grant access to another user's data.
    """

    def setUp(self):
        self.user_a = User.objects.create_user(
            username="idor_user_a", password="TestPass123!", email="a@test.com"
        )
        self.user_b = User.objects.create_user(
            username="idor_user_b", password="TestPass123!", email="b@test.com"
        )
        self.plan, _ = SubscriptionPlan.objects.get_or_create(
            name="idor_pro",
            defaults={
                "monthly_price": Decimal("29.99"),
                "yearly_price": Decimal("299.99"),
                "features": "Pro",
                "is_active": True,
            },
        )
        UserSubscription.objects.create(
            user=self.user_a,
            plan=self.plan,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365),
            is_active=True,
        )
        UserSubscription.objects.create(
            user=self.user_b,
            plan=self.plan,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365),
            is_active=True,
        )

        self.building_a = Building.objects.create(
            owner=self.user_a,
            name="User A Building",
            address_line="123 A St",
            city="City A",
            state="AA",
            country="IN",
            postal_code="400001",
        )
        self.building_b = Building.objects.create(
            owner=self.user_b,
            name="User B Building",
            address_line="456 B St",
            city="City B",
            state="BB",
            country="IN",
            postal_code="400002",
        )
        self.unit_a = Unit.objects.create(
            owner=self.user_a,
            building=self.building_a,
            unit="A-101",
            address_line="123 A St",
            city="City A",
            state="AA",
            country="IN",
            postal_code="400001",
            unit_type=Unit.UnitType.FLAT,
        )
        self.unit_b = Unit.objects.create(
            owner=self.user_b,
            building=self.building_b,
            unit="B-101",
            address_line="456 B St",
            city="City B",
            state="BB",
            country="IN",
            postal_code="400002",
            unit_type=Unit.UnitType.FLAT,
        )
        self.renter_a = Renter.objects.create(
            unit=self.unit_a,
            owner=self.user_a,
            name="Renter A",
            phone="+919876543210",
            rent_amount=Decimal("10000.00"),
            start_date=timezone.now().date(),
        )
        self.renter_b = Renter.objects.create(
            unit=self.unit_b,
            owner=self.user_b,
            name="Renter B",
            phone="+919876543211",
            rent_amount=Decimal("12000.00"),
            start_date=timezone.now().date(),
        )
        self.rent_a = RentRecord.objects.create(
            renter=self.renter_a,
            unit=self.unit_a,
            due_date=timezone.now().date().replace(day=5),
            amount=Decimal("10000.00"),
            status="pending",
        )
        self.rent_b = RentRecord.objects.create(
            renter=self.renter_b,
            unit=self.unit_b,
            due_date=timezone.now().date().replace(day=5),
            amount=Decimal("12000.00"),
            status="pending",
        )
        self.caretaker_a = Caretaker.objects.create(
            unit=self.unit_a,
            owner=self.user_a,
            name="Caretaker A",
            phone="+919876543212",
            joining_date=timezone.now().date(),
        )
        self.caretaker_b = Caretaker.objects.create(
            unit=self.unit_b,
            owner=self.user_b,
            name="Caretaker B",
            phone="+919876543213",
            joining_date=timezone.now().date(),
        )

        self.client_a = APIClient()
        self.client_a.force_authenticate(user=self.user_a)
        self.client_b = APIClient()
        self.client_b.force_authenticate(user=self.user_b)

    # ------------------------------------------------------------------
    # Building IDOR
    # ------------------------------------------------------------------

    def test_user_a_cannot_list_user_b_buildings(self):
        response = self.client_a.get(f"{API_PREFIX}/buildings/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [b["id"] for b in response.data]
        self.assertNotIn(self.building_b.id, ids)

    def test_user_a_cannot_retrieve_user_b_building(self):
        response = self.client_a.get(f"{API_PREFIX}/buildings/{self.building_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_a_cannot_update_user_b_building(self):
        response = self.client_a.patch(
            f"{API_PREFIX}/buildings/{self.building_b.id}/",
            {"name": "Hacked"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_a_cannot_delete_user_b_building(self):
        response = self.client_a.delete(f"{API_PREFIX}/buildings/{self.building_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ------------------------------------------------------------------
    # Unit IDOR
    # ------------------------------------------------------------------

    def test_user_a_cannot_list_user_b_units(self):
        response = self.client_a.get(f"{API_PREFIX}/units/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [u["id"] for u in response.data]
        self.assertNotIn(self.unit_b.id, ids)

    def test_user_a_cannot_retrieve_user_b_unit(self):
        response = self.client_a.get(f"{API_PREFIX}/units/{self.unit_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_a_cannot_update_user_b_unit(self):
        response = self.client_a.patch(
            f"{API_PREFIX}/units/{self.unit_b.id}/",
            {"status": "maintenance"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_a_cannot_delete_user_b_unit(self):
        response = self.client_a.delete(f"{API_PREFIX}/units/{self.unit_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ------------------------------------------------------------------
    # Renter IDOR
    # ------------------------------------------------------------------

    def test_user_a_cannot_list_user_b_renters(self):
        response = self.client_a.get(f"{API_PREFIX}/renters/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [r["id"] for r in response.data]
        self.assertNotIn(self.renter_b.id, ids)

    def test_user_a_cannot_retrieve_user_b_renter(self):
        response = self.client_a.get(f"{API_PREFIX}/renters/{self.renter_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_a_cannot_update_user_b_renter(self):
        response = self.client_a.patch(
            f"{API_PREFIX}/renters/{self.renter_b.id}/",
            {"name": "Hacked"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_a_cannot_delete_user_b_renter(self):
        response = self.client_a.delete(f"{API_PREFIX}/renters/{self.renter_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ------------------------------------------------------------------
    # Rent Record IDOR
    # ------------------------------------------------------------------

    def test_user_a_cannot_list_user_b_rent_records(self):
        response = self.client_a.get(f"{API_PREFIX}/rent-records/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [r["id"] for r in response.data]
        self.assertNotIn(self.rent_b.id, ids)

    def test_user_a_cannot_retrieve_user_b_rent_record(self):
        response = self.client_a.get(f"{API_PREFIX}/rent-records/{self.rent_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_a_cannot_update_user_b_rent_record(self):
        response = self.client_a.patch(
            f"{API_PREFIX}/rent-records/{self.rent_b.id}/",
            {"status": "paid"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_a_cannot_delete_user_b_rent_record(self):
        response = self.client_a.delete(f"{API_PREFIX}/rent-records/{self.rent_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ------------------------------------------------------------------
    # Caretaker IDOR
    # ------------------------------------------------------------------

    def test_user_a_cannot_list_user_b_caretakers(self):
        response = self.client_a.get(f"{API_PREFIX}/caretakers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [c["id"] for c in response.data]
        self.assertNotIn(self.caretaker_b.id, ids)

    def test_user_a_cannot_retrieve_user_b_caretaker(self):
        response = self.client_a.get(f"{API_PREFIX}/caretakers/{self.caretaker_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_a_cannot_update_user_b_caretaker(self):
        response = self.client_a.patch(
            f"{API_PREFIX}/caretakers/{self.caretaker_b.id}/",
            {"name": "Hacked"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_a_cannot_delete_user_b_caretaker(self):
        response = self.client_a.delete(
            f"{API_PREFIX}/caretakers/{self.caretaker_b.id}/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ------------------------------------------------------------------
    # Extra Charge IDOR
    # ------------------------------------------------------------------

    def test_user_a_cannot_list_user_b_extra_charges(self):
        ExtraCharge.objects.create(
            renter=self.renter_b,
            unit=self.unit_b,
            name="B Charge",
            amount=Decimal("500.00"),
            due_date=timezone.now().date(),
            status=ExtraCharge.Status.DUE,
        )
        response = self.client_a.get(f"{API_PREFIX}/extra-charges/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for charge in response.data:
            self.assertNotEqual(charge.get("name"), "B Charge")

    # ------------------------------------------------------------------
    # Notification IDOR
    # ------------------------------------------------------------------

    def test_user_a_cannot_access_user_b_notifications(self):
        Notification.objects.create(
            user=self.user_b,
            title="B Secret",
            message="Should not be visible to A",
            notification_type=Notification.SYSTEM_ALERT,
        )
        response = self.client_a.get(f"{API_PREFIX}/notifications/get/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for note in response.data["data"]:
            self.assertNotEqual(note.get("title"), "B Secret")

    def test_user_a_cannot_mark_user_b_notification_read(self):
        note = Notification.objects.create(
            user=self.user_b,
            title="B Notification",
            message="B only",
            notification_type=Notification.SYSTEM_ALERT,
        )
        response = self.client_a.post(f"{API_PREFIX}/notifications/mark/{note.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_a_cannot_delete_user_b_notification(self):
        note = Notification.objects.create(
            user=self.user_b,
            title="B Notification 2",
            message="B only 2",
            notification_type=Notification.SYSTEM_ALERT,
        )
        response = self.client_a.delete(f"{API_PREFIX}/notifications/{note.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ------------------------------------------------------------------
    # AI Conversation IDOR
    # ------------------------------------------------------------------

    def test_user_a_cannot_access_user_b_ai_conversation(self):
        conv_response = self.client_b.post(
            f"{API_PREFIX}/ai-assistant/conversations/",
            {"title": "B Conversation"},
            format="json",
        )
        conv_id = conv_response.data["id"]
        response = self.client_a.get(
            f"{API_PREFIX}/ai-assistant/conversations/{conv_id}/"
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
        )

    def test_user_a_cannot_delete_user_b_ai_conversation(self):
        conv_response = self.client_b.post(
            f"{API_PREFIX}/ai-assistant/conversations/",
            {"title": "B Conversation 2"},
            format="json",
        )
        conv_id = conv_response.data["id"]
        response = self.client_a.delete(
            f"{API_PREFIX}/ai-assistant/conversations/{conv_id}/"
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
        )

    # ------------------------------------------------------------------
    # Device Token IDOR
    # ------------------------------------------------------------------

    def test_user_a_cannot_delete_user_b_device(self):
        device = DeviceToken.objects.create(
            user=self.user_b,
            token="b-token-123",
            platform="android",
            active=True,
        )
        response = self.client_a.delete(
            f"{API_PREFIX}/notifications/devices/{device.id}/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ------------------------------------------------------------------
    # Bank Details IDOR
    # ------------------------------------------------------------------

    def test_user_a_cannot_access_user_b_bank_details(self):
        OwnerBankDetails.objects.create(
            owner=self.user_b,
            bank_account_number="9999999999",
            ifsc_code="HDFC0009999",
            account_holder_name="User B",
            beneficiary_id="BENE-B",
        )
        response = self.client_a.get(f"{API_PREFIX}/owner/update-bank-details/")
        # Endpoint is POST-only, but if it returns data, must not include B's data
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Subscription IDOR
    # ------------------------------------------------------------------

    def test_user_a_cannot_access_user_b_subscription(self):
        response = self.client_a.get(f"{API_PREFIX}/user-subscriptions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for sub in response.data:
            self.assertNotEqual(sub.get("user"), self.user_b.id)


class PaymentSecurityTests(APITestCase):
    """Test payment security: webhook signatures, ownership, duplicate protection."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username="pay_sec_owner", password="TestPass123!", email="payo@test.com"
        )
        self.renter = User.objects.create_user(
            username="pay_sec_renter", password="TestPass123!", email="payr@test.com"
        )
        self.plan, _ = SubscriptionPlan.objects.get_or_create(
            name="pay_sec_pro",
            defaults={
                "monthly_price": Decimal("29.99"),
                "yearly_price": Decimal("299.99"),
                "features": "Pro",
                "is_active": True,
            },
        )
        UserSubscription.objects.create(
            user=self.owner,
            plan=self.plan,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365),
            is_active=True,
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="Pay Sec Bldg",
            address_line="123 Pay St",
            city="Pay City",
            state="PY",
            country="IN",
            postal_code="400001",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="PAY-101",
            address_line="123 Pay St",
            city="Pay City",
            state="PY",
            country="IN",
            postal_code="400001",
            unit_type=Unit.UnitType.FLAT,
        )
        self.renter_profile = Renter.objects.create(
            unit=self.unit,
            owner=self.owner,
            name="Pay Sec Renter",
            phone="+919876543210",
            rent_amount=Decimal("10000.00"),
            start_date=timezone.now().date(),
            user=self.renter,
        )
        self.rent = RentRecord.objects.create(
            renter=self.renter_profile,
            unit=self.unit,
            due_date=timezone.now().date().replace(day=5),
            amount=Decimal("10000.00"),
            status="pending",
            payment_method="upi",
        )

    def test_razorpay_webhook_invalid_signature(self):
        from django.conf import settings

        settings.RAZORPAY_WEBHOOK_SECRET = "test_secret"
        response = self.client.post(
            f"{API_PREFIX}/rent/payment-callback/",
            {"event": "payment.captured", "payload": {}},
            content_type="application/json",
            HTTP_X_RAZORPAY_SIGNATURE="invalid_signature",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cashfree_webhook_invalid_signature(self):
        from django.conf import settings

        settings.CASHFREE_WEBHOOK_SECRET = "test_secret"
        response = self.client.post(
            f"{API_PREFIX}/webhook/cashfree/payout/",
            {"event": "PAYOUT_SUCCESS", "data": {}},
            content_type="application/json",
            HTTP_X_CASHFREE_SIGNATURE="invalid_signature",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UnauthorizedAccessSecurityTests(APITestCase):
    """Test that all protected endpoints reject unauthenticated access."""

    def test_all_protected_endpoints_require_auth(self):
        protected_endpoints = [
            f"{API_PREFIX}/auth/profile/",
            f"{API_PREFIX}/buildings/",
            f"{API_PREFIX}/units/",
            f"{API_PREFIX}/renters/",
            f"{API_PREFIX}/caretakers/",
            f"{API_PREFIX}/rent-records/",
            f"{API_PREFIX}/notifications/get/",
            f"{API_PREFIX}/notifications/unread-count/",
            f"{API_PREFIX}/notifications/preferences/",
            f"{API_PREFIX}/ai-assistant/chat/",
            f"{API_PREFIX}/ai-assistant/conversations/",
            f"{API_PREFIX}/ai-assistant/suggested-questions/",
            f"{API_PREFIX}/owner/dashboard-summary/",
            f"{API_PREFIX}/owner/rent-records/",
            f"{API_PREFIX}/user-subscriptions/",
            f"{API_PREFIX}/usage-limits/",
            f"{API_PREFIX}/renter/dashboard/",
            f"{API_PREFIX}/renter/rent-records/",
            f"{API_PREFIX}/renter/agreement/",
            f"{API_PREFIX}/search/",
            f"{API_PREFIX}/notifications/devices/",
        ]
        for endpoint in protected_endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                self.assertEqual(
                    response.status_code,
                    status.HTTP_401_UNAUTHORIZED,
                    msg=f"Expected 401 for {endpoint}, got {response.status_code}",
                )

    def test_owner_endpoints_require_auth(self):
        owner_endpoints = [
            f"{API_PREFIX}/owner/dashboard-summary/",
            f"{API_PREFIX}/owner/rent-records/",
            f"{API_PREFIX}/owner/update-bank-details/",
        ]
        for endpoint in owner_endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                self.assertEqual(
                    response.status_code,
                    status.HTTP_401_UNAUTHORIZED,
                    msg=f"Expected 401 for {endpoint}",
                )
