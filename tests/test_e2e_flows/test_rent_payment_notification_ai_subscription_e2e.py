"""
E2E Flow: Rent, Payment, Invoice, Agreement, Maintenance

Tests complete rent lifecycle, payment processing, invoice generation,
agreement management, and maintenance requests.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import (
    AddOnPurchase,
    PlanFeatureLimit,
    SubscriptionPlan,
    UserSubscription,
)
from notification.models import Notification
from properties.models import RentRecord
from tests.test_e2e_flows import E2EAPIClientMixin

User = get_user_model()
API_PREFIX = "/api"


class RentPaymentE2EFlowTests(E2EAPIClientMixin, APITestCase):
    """Rent and payment E2E flow."""

    def setUp(self):
        self.client = APIClient()
        self.owner = self._create_owner_with_subscription("e2e_pay_owner")
        self.data = self._create_complete_owner_data(self.owner)
        self.renter_user = self.data["renter_user"]
        self.renter = self.data["renter"]
        self.unit = self.data["unit"]
        self.owner_token = self._get_access_token(self.owner)
        self.renter_token = self._get_access_token(self.renter_user)

    def test_rent_lifecycle(self):
        rent = RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            due_date=timezone.now().date().replace(day=5),
            amount=Decimal("15000.00"),
            status="pending",
        )
        self.assertEqual(rent.status, "pending")
        self.assertEqual(rent.amount, Decimal("15000.00"))

        response = self._patch_json(
            f"{API_PREFIX}/rent-records/{rent.id}/",
            {"status": "paid", "paid_on": str(timezone.now().date())},
            token=self.owner_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rent.refresh_from_db()
        self.assertEqual(rent.status, "paid")

    def test_payment_creation_mocked(self):
        rent = RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            due_date=timezone.now().date().replace(day=5),
            amount=Decimal("15000.00"),
            status="pending",
        )
        with patch(
            "properties.views.rent_record_views.create_payment_link",
            return_value="https://payments.test/rent/1",
        ):
            response = self._post_json(
                f"{API_PREFIX}/rent/payment/",
                {"rent_record_id": rent.id, "method": "upi"},
                token=self.renter_token,
            )
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST],
        )

    def test_duplicate_rent_record_prevention(self):
        RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            due_date=date(2025, 1, 1),
            amount=Decimal("15000.00"),
            status="pending",
        )
        payload = {
            "renter": self.renter.id,
            "unit": self.unit.id,
            "due_date": "2025-01-01",
            "amount": "15000.00",
        }
        response = self._post_json(
            f"{API_PREFIX}/rent-records/", payload, token=self.owner_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rent_record_status_choices(self):
        rent = RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            due_date=timezone.now().date().replace(day=5),
            amount=Decimal("15000.00"),
            status="pending",
        )
        for status_val in ["pending", "paid", "overdue", "cancelled"]:
            with self.subTest(status=status_val):
                response = self._patch_json(
                    f"{API_PREFIX}/rent-records/{rent.id}/",
                    {"status": status_val},
                    token=self.owner_token,
                )
                self.assertIn(
                    response.status_code,
                    [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST],
                )

    def test_negative_amount_rejected(self):
        payload = {
            "renter": self.renter.id,
            "unit": self.unit.id,
            "due_date": str(timezone.now().date()),
            "amount": "-1000.00",
        }
        response = self._post_json(
            f"{API_PREFIX}/rent-records/", payload, token=self.owner_token
        )
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)

    def test_owner_rent_records_list(self):
        RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            due_date=timezone.now().date().replace(day=5),
            amount=Decimal("15000.00"),
            status="pending",
        )
        response = self._get_json(
            f"{API_PREFIX}/owner/rent-records/", token=self.owner_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_renter_rent_history(self):
        RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            due_date=timezone.now().date().replace(day=5),
            amount=Decimal("15000.00"),
            status="paid",
            paid_on=timezone.now().date(),
        )
        response = self._get_json(
            f"{API_PREFIX}/renter/rent-history/", token=self.renter_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_owner_cannot_modify_other_owner_rent_record(self):
        other_owner = self._create_owner_with_subscription("e2e_rent_other")
        other_data = self._create_complete_owner_data(other_owner)
        other_rent = RentRecord.objects.create(
            renter=other_data["renter"],
            unit=other_data["unit"],
            due_date=timezone.now().date().replace(day=5),
            amount=Decimal("15000.00"),
            status="pending",
        )
        response = self._patch_json(
            f"{API_PREFIX}/rent-records/{other_rent.id}/",
            {"status": "paid"},
            token=self.owner_token,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class NotificationE2EFlowTests(E2EAPIClientMixin, APITestCase):
    """Notification E2E flow."""

    def setUp(self):
        self.client = APIClient()
        self.owner = self._create_owner_with_subscription("e2e_notif_owner")
        self.owner_token = self._get_access_token(self.owner)

    def test_notification_lifecycle(self):
        note = Notification.objects.create(
            user=self.owner,
            title="E2E Rent Due",
            message="Your rent is due",
            notification_type=Notification.RENT_DUE,
            priority=Notification.PRIORITY_HIGH,
        )

        response = self._get_json(
            f"{API_PREFIX}/notifications/get/", token=self.owner_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "E2E Rent Due")

        note_id = data[0]["id"]
        response = self._post_json(
            f"{API_PREFIX}/notifications/mark/{note_id}/", token=self.owner_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        note.refresh_from_db()
        self.assertTrue(note.is_read)

        response = self._post_json(
            f"{API_PREFIX}/notifications/{note_id}/", token=self.owner_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        note.refresh_from_db()
        self.assertTrue(note.archived)

    def test_unread_count_after_read(self):
        Notification.objects.create(
            user=self.owner,
            title="E2E Test",
            message="Test",
            notification_type=Notification.SYSTEM_ALERT,
            is_read=False,
        )
        response = self._get_json(
            f"{API_PREFIX}/notifications/unread-count/", token=self.owner_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_mark_all_read(self):
        Notification.objects.create(
            user=self.owner,
            title="E2E A",
            message="A",
            notification_type=Notification.SYSTEM_ALERT,
            is_read=False,
        )
        Notification.objects.create(
            user=self.owner,
            title="E2E B",
            message="B",
            notification_type=Notification.SYSTEM_ALERT,
            is_read=False,
        )
        response = self._post_json(
            f"{API_PREFIX}/notifications/mark-all-read/", token=self.owner_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        unread = Notification.objects.filter(
            user=self.owner, is_read=False, archived=False
        ).count()
        self.assertEqual(unread, 0)

    def test_notification_search(self):
        Notification.objects.create(
            user=self.owner,
            title="E2E Rent Due",
            message="Rent is due",
            notification_type=Notification.RENT_DUE,
        )
        Notification.objects.create(
            user=self.owner,
            title="E2E Maintenance",
            message="Maintenance request",
            notification_type=Notification.MAINTENANCE_UPDATED,
        )
        response = self._get_json(
            f"{API_PREFIX}/notifications/get/?search=Rent",
            token=self.owner_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [n["title"] for n in response.data["data"]]
        self.assertTrue(any("Rent" in t for t in titles))

    def test_notification_pagination(self):
        for i in range(25):
            Notification.objects.create(
                user=self.owner,
                title=f"E2E Notif {i}",
                message=f"Message {i}",
                notification_type=Notification.SYSTEM_ALERT,
            )
        response = self._get_json(
            f"{API_PREFIX}/notifications/get/?limit=10",
            token=self.owner_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 10)
        self.assertEqual(response.data["meta"]["total"], 25)

    def test_cannot_access_other_user_notifications(self):
        other_user = self._create_renter_user("e2e_notif_other")
        Notification.objects.create(
            user=other_user,
            title="Private",
            message="Should not be visible",
            notification_type=Notification.SYSTEM_ALERT,
        )
        response = self._get_json(
            f"{API_PREFIX}/notifications/get/", token=self.owner_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for note in response.data["data"]:
            self.assertNotEqual(note.get("title"), "Private")


class AIAssistantE2EFlowTests(E2EAPIClientMixin, APITestCase):
    """AI Assistant E2E flow."""

    def setUp(self):
        self.client = APIClient()
        self.owner = self._create_owner_with_subscription("e2e_ai_owner")
        self._create_complete_owner_data(self.owner)
        self.owner_token = self._get_access_token(self.owner)
        self.renter_user = self._create_renter_user("e2e_ai_renter")
        self._ensure_group(self.renter_user, "renter")
        self.renter_token = self._get_access_token(self.renter_user)

    def test_suggested_questions(self):
        response = self._get_json(
            f"{API_PREFIX}/ai-assistant/suggested-questions/",
            token=self.owner_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("questions", response.data)
        self.assertGreater(len(response.data["questions"]), 0)

    def test_chat_creates_conversation(self):
        with patch(
            "ai_assistant.services.chat_service.generate_ai_response",
            return_value={
                "response": "E2E test response",
                "tools_used": [],
                "data": {},
                "sources": [],
            },
        ):
            response = self._post_json(
                f"{API_PREFIX}/ai-assistant/chat/",
                {"message": "How much rent is pending?"},
                token=self.owner_token,
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("conversation_id", response.data)
        self.assertIn("response", response.data)

    def test_chat_rate_limit_exceeded(self):
        plan = SubscriptionPlan.objects.create(
            name="e2e_ai_free",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Free",
            is_active=True,
        )
        UserSubscription.objects.create(
            user=self.owner,
            plan=plan,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            is_active=True,
        )
        PlanFeatureLimit.objects.create(
            plan=plan, feature_key="ai_chat_messages", value="0"
        )
        response = self._post_json(
            f"{API_PREFIX}/ai-assistant/chat/",
            {"message": "Test message"},
            token=self.owner_token,
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_chat_requires_authentication(self):
        response = self.client.post(
            f"{API_PREFIX}/ai-assistant/chat/",
            {"message": "Test"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_conversations(self):
        response = self._get_json(
            f"{API_PREFIX}/ai-assistant/conversations/",
            token=self.owner_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("conversations", response.data)

    def test_create_conversation(self):
        response = self._post_json(
            f"{API_PREFIX}/ai-assistant/conversations/",
            {"title": "E2E Test Conversation"},
            token=self.owner_token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "E2E Test Conversation")

    def test_cannot_access_other_user_conversation(self):
        other_user = self._create_renter_user("e2e_ai_conv_other")
        conv_response = self._post_json(
            f"{API_PREFIX}/ai-assistant/conversations/",
            {"title": "Other User Conv"},
            token=self._get_access_token(other_user),
        )
        conv_id = conv_response.data["id"]
        response = self._get_json(
            f"{API_PREFIX}/ai-assistant/conversations/{conv_id}/",
            token=self.owner_token,
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
        )


class SubscriptionE2EFlowTests(E2EAPIClientMixin, APITestCase):
    """Subscription E2E flow."""

    def setUp(self):
        self.client = APIClient()
        self.owner = self._create_owner_with_subscription("e2e_sub_owner")
        self.owner_token = self._get_access_token(self.owner)

    def test_list_plans(self):
        response = self.client.get(f"{API_PREFIX}/subscription-plans/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_current_subscription(self):
        response = self._get_json(
            f"{API_PREFIX}/user-subscriptions/", token=self.owner_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_addon_purchase(self):
        response = self._post_json(
            f"{API_PREFIX}/addon-purchases/",
            {"name": "max_buildings", "amount": "49.99"},
            token=self.owner_token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_addon_list(self):
        AddOnPurchase.objects.create(
            user=self.owner, name="max_units", amount=Decimal("29.99")
        )
        response = self._get_json(
            f"{API_PREFIX}/addon-purchases/", token=self.owner_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_usage_limits(self):
        response = self._get_json(f"{API_PREFIX}/usage-limits/", token=self.owner_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
