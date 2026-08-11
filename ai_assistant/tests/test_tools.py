"""Tests for ai_assistant tools."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from ai_assistant.services.tools import (
    execute_tool,
    get_agreement_status,
    get_maintenance_summary,
    get_next_rent_due,
    get_notification_summary,
    get_occupancy_summary,
    get_payment_history,
    get_pending_rents,
    get_rent_collection_summary,
    get_renter_summary,
    get_subscription_status,
    get_vacant_units,
)

User = get_user_model()


class ToolsAuthorizationTest(TestCase):
    def test_renter_tools_return_error_without_profile(self):
        user = User.objects.create_user(username="norenter", password="testpass123")
        result = get_payment_history(user)
        self.assertIn("error", result)

        result = get_next_rent_due(user)
        self.assertIn("error", result)

        result = get_agreement_status(user)
        self.assertIn("error", result)


class ToolsStructureTest(TestCase):
    def test_get_pending_rents_structure(self):
        owner = User.objects.create_user(
            username="struct_owner", password="testpass123"
        )
        mock_rr = MagicMock()
        mock_rr.count.return_value = 0
        mock_rr.select_related.return_value = mock_rr
        mock_rr.__iter__ = lambda self: iter([])

        with patch(
            "ai_assistant.services.tools.RentRecord.objects.filter",
            return_value=mock_rr,
        ):
            result = get_pending_rents(owner)

        self.assertEqual(result["tool"], "get_pending_rents")
        self.assertIn("total_pending", result)
        self.assertIn("count", result)
        self.assertIn("records", result)

    def test_get_rent_collection_summary_structure(self):
        owner = User.objects.create_user(
            username="struct_owner2", password="testpass123"
        )
        mock_qs = MagicMock()
        mock_qs.aggregate.return_value = {"total": Decimal("0")}

        with patch(
            "ai_assistant.services.tools.RentRecord.objects.filter",
            return_value=mock_qs,
        ):
            result = get_rent_collection_summary(owner)

        self.assertEqual(result["tool"], "get_rent_collection_summary")
        self.assertIn("collected", result)
        self.assertIn("pending", result)
        self.assertIn("month", result)

    def test_get_vacant_units_structure(self):
        owner = User.objects.create_user(
            username="struct_owner3", password="testpass123"
        )
        mock_qs = MagicMock()
        mock_qs.count.return_value = 0
        mock_qs.__iter__ = lambda self: iter([])

        with patch(
            "ai_assistant.services.tools.Unit.objects.filter",
            return_value=mock_qs,
        ):
            result = get_vacant_units(owner)

        self.assertEqual(result["tool"], "get_vacant_units")
        self.assertIn("count", result)
        self.assertIn("units", result)

    def test_get_occupancy_summary_structure(self):
        owner = User.objects.create_user(
            username="struct_owner4", password="testpass123"
        )
        mock_qs = MagicMock()
        mock_qs.count.return_value = 10

        with patch(
            "ai_assistant.services.tools.Unit.objects.filter",
            return_value=mock_qs,
        ):
            result = get_occupancy_summary(owner)

        self.assertEqual(result["tool"], "get_occupancy_summary")
        self.assertIn("total_units", result)
        self.assertIn("occupied", result)
        self.assertIn("vacant", result)

    def test_get_renter_summary_structure(self):
        owner = User.objects.create_user(
            username="struct_owner5", password="testpass123"
        )
        mock_qs = MagicMock()
        mock_qs.count.return_value = 5
        mock_active = MagicMock()
        mock_active.count.return_value = 3
        mock_qs.filter.return_value = mock_active

        with patch(
            "ai_assistant.services.tools.Renter.objects.filter",
            return_value=mock_qs,
        ):
            result = get_renter_summary(owner)

        self.assertEqual(result["tool"], "get_renter_summary")
        self.assertIn("total_renters", result)
        self.assertIn("active", result)

    def test_get_subscription_status_structure(self):
        owner = User.objects.create_user(
            username="struct_owner6", password="testpass123"
        )
        result = get_subscription_status(owner)
        self.assertEqual(result["tool"], "get_subscription_status")
        self.assertIn("plan", result)

    def test_get_notification_summary_structure(self):
        owner = User.objects.create_user(
            username="struct_owner7", password="testpass123"
        )
        mock_notif = MagicMock()
        mock_notif.objects.filter.return_value.count.return_value = 3

        with patch.dict(
            "sys.modules",
            {"notification": MagicMock(models=MagicMock(Notification=mock_notif))},
        ):
            result = get_notification_summary(owner)

        self.assertEqual(result["tool"], "get_notification_summary")
        self.assertIn("unread_count", result)

    def test_get_maintenance_summary_structure(self):
        owner = User.objects.create_user(
            username="struct_owner8", password="testpass123"
        )
        result = get_maintenance_summary(owner)
        self.assertEqual(result["tool"], "get_maintenance_summary")
        self.assertIn("message", result)


class ExecuteToolTest(TestCase):
    def test_execute_known_tool(self):
        owner = User.objects.create_user(username="tooluser", password="testpass123")
        mock_rr = MagicMock()
        mock_rr.count.return_value = 0
        mock_rr.__iter__ = lambda self: iter([])

        with patch(
            "ai_assistant.services.tools.RentRecord.objects.filter",
            return_value=mock_rr,
        ):
            result = execute_tool("get_pending_rents", owner)

        self.assertIn("tool", result)

    def test_execute_unknown_tool(self):
        owner = User.objects.create_user(username="tooluser2", password="testpass123")
        result = execute_tool("nonexistent_tool", owner)
        self.assertIn("error", result)
