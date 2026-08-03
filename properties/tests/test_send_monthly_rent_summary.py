"""Tests for send_monthly_rent_summary management command."""

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from core.models import NotificationPreference, User
from properties.management.commands.send_monthly_rent_summary import Command
from properties.models import Building, Renter, RentRecord, Unit


class SendMonthlyRentSummaryTests(TestCase):
    def setUp(self):
        self.command = Command()
        self.owner = User.objects.create_user(
            username="digest_owner",
            password="p",
            full_name="DigestOwner",
            phone="+1",
            email="digest@test.com",
            whatsapp_number="+919876543210",
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="DigestB",
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
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="DigestRenter",
            phone="+911234567890",
            email="renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
        )

    @patch("properties.services.summary_service._send_summary_email")
    @patch("properties.services.summary_service._send_summary_whatsapp")
    def test_sends_summary_to_owner(self, mock_whatsapp, mock_email):
        NotificationPreference.objects.create(
            owner=self.owner, monthly_summary_whatsapp=True
        )
        today = timezone.now().date()
        RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("10000"),
            due_date=today,
            paid_on=today,
            status=RentRecord.Status.PAID,
            payout_status="SUCCESS",
        )
        self.command.handle(user_id=self.owner.id)
        mock_email.assert_called_once()
        mock_whatsapp.assert_called_once()

    @patch("properties.services.summary_service._send_summary_email")
    @patch("properties.services.summary_service._send_summary_whatsapp")
    def test_skips_whatsapp_when_preference_disabled(self, mock_whatsapp, mock_email):
        NotificationPreference.objects.create(
            owner=self.owner, monthly_summary_whatsapp=False
        )
        today = timezone.now().date()
        RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("10000"),
            due_date=today,
            paid_on=today,
            status=RentRecord.Status.PAID,
            payout_status="SUCCESS",
        )
        self.command.handle(user_id=self.owner.id)
        mock_email.assert_called_once()
        mock_whatsapp.assert_not_called()

    @patch("properties.services.summary_service._send_summary_email")
    @patch("properties.services.summary_service._send_summary_whatsapp")
    def test_sends_email_even_without_records(self, mock_whatsapp, mock_email):
        NotificationPreference.objects.create(
            owner=self.owner, monthly_summary_whatsapp=True
        )
        self.command.handle(user_id=self.owner.id)
        mock_email.assert_called_once()
        mock_whatsapp.assert_called_once()
