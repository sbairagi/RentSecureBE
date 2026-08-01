"""Tests for send_monthly_summaries_with_csv management command."""

from decimal import Decimal
from unittest.mock import patch

from django.core.mail import EmailMessage
from django.test import TestCase
from django.utils import timezone

from core.models import NotificationPreference, User
from properties.management.commands.send_monthly_summaries_with_csv import Command
from properties.models import Building, Renter, RentRecord, Unit


class SendMonthlySummariesWithCsvTests(TestCase):
    def setUp(self):
        self.command = Command()
        self.owner = User.objects.create_user(
            username="monthly_owner",
            password="p",
            full_name="MonthlyOwner",
            phone="+1",
            email="monthly@test.com",
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="MonthlyB",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="M1",
            unit_type="flat",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="MonthlyRenter",
            phone="+911234567890",
            email="renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
        )

    @patch("properties.services.receipt_service.send_rent_receipt_email")
    def test_skips_owner_without_email(self, mock_receipt):
        self.owner.email = ""
        self.owner.save(update_fields=["email"])
        owners = User.objects.filter(units__isnull=False).distinct()
        self.assertEqual(owners.count(), 1)
        with patch.object(EmailMessage, "send") as mock_send:
            self.command.handle(owner_id=self.owner.id)
        mock_send.assert_not_called()

    @patch("properties.services.receipt_service.send_rent_receipt_email")
    def test_sends_email_with_csv_attachment(self, mock_receipt):
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
        month_str = today.strftime("%Y-%m")
        with patch.object(EmailMessage, "send") as mock_send:
            self.command.handle(owner_id=self.owner.id, month=month_str)
        self.assertEqual(mock_send.call_count, 1)

    @patch("properties.services.receipt_service.send_rent_receipt_email")
    def test_respects_notification_preference_email_off(self, mock_receipt):
        NotificationPreference.objects.create(
            owner=self.owner, monthly_summary_email=False
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
        month_str = today.strftime("%Y-%m")
        with patch.object(EmailMessage, "send") as mock_send:
            self.command.handle(owner_id=self.owner.id, month=month_str)
        mock_send.assert_not_called()

    @patch("properties.services.receipt_service.send_rent_receipt_email")
    def test_skips_when_no_records(self, mock_receipt):
        today = timezone.now().date()
        month_str = today.strftime("%Y-%m")
        with patch.object(EmailMessage, "send") as mock_send:
            self.command.handle(owner_id=self.owner.id, month=month_str)
        mock_send.assert_not_called()
