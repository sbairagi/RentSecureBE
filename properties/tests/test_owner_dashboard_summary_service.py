"""Tests for owner dashboard summary service."""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from core.models import User, UserProfile
from properties.models import Building, PropertyTaxRecord, Renter, RentRecord, Unit
from properties.services.owner_dashboard_summary_service import (
    _build_summary_message,
    _get_owner_language,
    _get_owner_name,
    _get_owner_whatsapp,
    build_owner_summary,
    run_daily_owner_summaries,
    send_summary_to_owner,
)


class OwnerDashboardSummaryServiceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="dashboard_owner",
            password="p",
            full_name="DashboardOwner",
            phone="+1",
            email="dashboard@test.com",
            whatsapp_number="+919876543210",
        )
        self.other_owner = User.objects.create_user(
            username="other_dashboard_owner",
            password="p",
            full_name="OtherOwner",
            phone="+1",
            email="other@test.com",
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="DashboardB",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="D1",
            unit_type="flat",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        self.unit.is_vacant = True
        self.unit.last_vacated_at = timezone.now().date()
        self.unit.save(update_fields=["is_vacant", "last_vacated_at"])

        self.occupied_unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="D2",
            unit_type="flat",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        self.occupied_unit.is_vacant = False
        self.occupied_unit.last_vacated_at = None
        self.occupied_unit.save(update_fields=["is_vacant", "last_vacated_at"])

        self.renter = Renter.objects.create(
            unit=self.occupied_unit,
            name="DashboardRenter",
            phone="+911234567890",
            email="renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
        )
        self.renter.is_flagged = True
        self.renter.save(update_fields=["is_flagged"])

        self.pending_rent = RentRecord.objects.create(
            unit=self.occupied_unit,
            renter=self.renter,
            amount=Decimal("10000"),
            due_date=timezone.now().date(),
            status=RentRecord.Status.PENDING,
            payment_method=RentRecord.PaymentMethod.UPI,
        )
        self.overdue_tax = PropertyTaxRecord.objects.create(
            property=self.building,
            amount=Decimal("5000"),
            due_date=timezone.now().date() - timedelta(days=1),
            paid=False,
        )

    def test_build_owner_summary_counts_vacant_units(self):
        summary = build_owner_summary(self.owner)
        self.assertEqual(summary["vacant_units"], 1)

    def test_build_owner_summary_sums_pending_rents(self):
        summary = build_owner_summary(self.owner)
        self.assertEqual(summary["pending_rent_amount"], 10000.0)

    def test_build_owner_summary_counts_overdue_taxes(self):
        summary = build_owner_summary(self.owner)
        self.assertEqual(summary["overdue_taxes"], 1)

    def test_build_owner_summary_counts_flagged_renters(self):
        summary = build_owner_summary(self.owner)
        self.assertEqual(summary["flagged_renters"], 1)

    def test_build_owner_summary_excludes_other_owner_data(self):
        summary = build_owner_summary(self.other_owner)
        self.assertEqual(summary["vacant_units"], 0)
        self.assertEqual(summary["pending_rent_amount"], 0.0)
        self.assertEqual(summary["overdue_taxes"], 0)
        self.assertEqual(summary["flagged_renters"], 0)

    def test_build_owner_summary_ignores_paid_taxes(self):
        self.overdue_tax.paid = True
        self.overdue_tax.save(update_fields=["paid"])
        summary = build_owner_summary(self.owner)
        self.assertEqual(summary["overdue_taxes"], 0)

    def test_build_owner_summary_ignores_future_taxes(self):
        PropertyTaxRecord.objects.create(
            property=self.building,
            amount=Decimal("5000"),
            due_date=timezone.now().date() + timedelta(days=1),
            paid=False,
        )
        summary = build_owner_summary(self.owner)
        self.assertEqual(summary["overdue_taxes"], 1)

    def test_get_owner_name_uses_full_name(self):
        self.assertEqual(_get_owner_name(self.owner), "DashboardOwner")

    def test_get_owner_language_from_profile(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.language_preference = "hi"
        profile.save(update_fields=["language_preference"])
        self.assertEqual(_get_owner_language(self.owner), "hi")

    def test_get_owner_language_defaults_to_en(self):
        self.assertEqual(_get_owner_language(self.owner), "en")

    def test_get_owner_whatsapp_from_profile(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.whatsapp_number = "+919999999999"
        profile.save(update_fields=["whatsapp_number"])
        self.assertEqual(_get_owner_whatsapp(self.owner), "+919999999999")

    def test_get_owner_whatsapp_falls_back_to_user_field(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.whatsapp_number = ""
        profile.save(update_fields=["whatsapp_number"])
        self.assertEqual(_get_owner_whatsapp(self.owner), "+919876543210")

    def test_build_summary_message_format(self):
        summary = build_owner_summary(self.owner)
        message = _build_summary_message(summary, "TestOwner")
        self.assertIn("Hello TestOwner", message)
        self.assertIn("Vacant Units: 1", message)
        self.assertIn("Pending Rents: ₹10,000.00", message)
        self.assertIn("Overdue Taxes: 1", message)
        self.assertIn("Flagged Renters: 1", message)
        self.assertIn("RentSecure dashboard", message)

    @patch("properties.services.owner_dashboard_summary_service._send_whatsapp_message")
    @patch(
        "properties.services.owner_dashboard_summary_service._generate_voice_note",
        return_value="/tmp/test.mp3",
    )
    @patch(
        "properties.services.owner_dashboard_summary_service._translate",
        side_effect=lambda text, lang: text,
    )
    def test_send_summary_to_owner_sends_whatsapp(
        self, mock_translate, mock_voice, mock_send
    ):
        mock_send.return_value = True
        result = send_summary_to_owner(self.owner)
        self.assertTrue(result)
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        self.assertIn("Hello DashboardOwner", args[1])

    @patch(
        "properties.services.owner_dashboard_summary_service._send_whatsapp_message",
        return_value=False,
    )
    def test_send_summary_to_owner_returns_false_on_send_failure(self, mock_send):
        result = send_summary_to_owner(self.owner)
        self.assertFalse(result)

    def test_send_summary_to_owner_skips_without_whatsapp(self):
        self.owner.whatsapp_number = ""
        self.owner.save(update_fields=["whatsapp_number"])
        result = send_summary_to_owner(self.owner)
        self.assertFalse(result)

    def test_build_owner_summary_respects_disabled_vacancy_alerts(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.receive_vacancy_alerts = False
        profile.save(update_fields=["receive_vacancy_alerts"])
        summary = build_owner_summary(self.owner)
        self.assertEqual(summary["vacant_units"], 0)

    def test_build_owner_summary_respects_disabled_rent_alerts(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.receive_rent_alerts = False
        profile.save(update_fields=["receive_rent_alerts"])
        summary = build_owner_summary(self.owner)
        self.assertEqual(summary["pending_rent_amount"], 0.0)

    def test_build_owner_summary_respects_disabled_tax_alerts(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.receive_tax_alerts = False
        profile.save(update_fields=["receive_tax_alerts"])
        summary = build_owner_summary(self.owner)
        self.assertEqual(summary["overdue_taxes"], 0)

    def test_build_owner_summary_respects_disabled_flagged_alerts(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.receive_flagged_alerts = False
        profile.save(update_fields=["receive_flagged_alerts"])
        summary = build_owner_summary(self.owner)
        self.assertEqual(summary["flagged_renters"], 0)

    def test_build_summary_message_omits_zero_sections(self):
        summary = {
            "vacant_units": 0,
            "pending_rent_amount": 0.0,
            "overdue_taxes": 0,
            "flagged_renters": 0,
        }
        message = _build_summary_message(summary, "TestOwner")
        self.assertNotIn("Vacant Units:", message)
        self.assertNotIn("Pending Rents:", message)
        self.assertNotIn("Overdue Taxes:", message)
        self.assertNotIn("Flagged Renters:", message)
        self.assertIn("Hello TestOwner", message)
        self.assertIn("RentSecure dashboard", message)

    @patch("properties.services.owner_dashboard_summary_service.send_summary_to_owner")
    def test_run_daily_owner_summaries_respects_daily_frequency(self, mock_send):
        mock_send.return_value = True
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.alert_frequency = "daily"
        profile.save(update_fields=["alert_frequency"])
        count = run_daily_owner_summaries()
        self.assertEqual(count, 1)
        mock_send.assert_called_once_with(self.owner)

    @patch("django.utils.timezone.now")
    @patch("properties.services.owner_dashboard_summary_service.send_summary_to_owner")
    def test_run_daily_owner_summaries_skips_weekly_on_non_monday(
        self, mock_send, mock_now
    ):
        mock_now.return_value = datetime(2026, 8, 2, tzinfo=timezone.utc)
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.alert_frequency = "weekly"
        profile.save(update_fields=["alert_frequency"])
        count = run_daily_owner_summaries()
        self.assertEqual(count, 0)
        mock_send.assert_not_called()

    @patch("django.utils.timezone.now")
    @patch("properties.services.owner_dashboard_summary_service.send_summary_to_owner")
    def test_run_daily_owner_summaries_skips_monthly_on_non_first(
        self, mock_send, mock_now
    ):
        mock_now.return_value = datetime(2026, 8, 2, tzinfo=timezone.utc)
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.alert_frequency = "monthly"
        profile.save(update_fields=["alert_frequency"])
        count = run_daily_owner_summaries()
        self.assertEqual(count, 0)
        mock_send.assert_not_called()
