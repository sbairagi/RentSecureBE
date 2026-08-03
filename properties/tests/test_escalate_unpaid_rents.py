"""Tests for escalate_unpaid_rents management command."""

from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from properties.management.commands.escalate_unpaid_rents import Command
from properties.models import Building, Caretaker, Renter, RentRecord, Unit

User = get_user_model()


class EscalateUnpaidRentsTests(TestCase):
    def setUp(self):
        self.command = Command()
        self.owner = User.objects.create_user(
            username="escalation_owner",
            password="p",
            full_name="EscalationOwner",
            phone="+1",
            email="escalation_owner@test.com",
            whatsapp_number="+919876543210",
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="EscalationB",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="E1",
            unit_type="flat",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        self.renter_user = User.objects.create_user(
            username="escalation_renter",
            password="p",
            full_name="EscalationRenter",
            phone="+1",
            email="renter@test.com",
            whatsapp_number="+919876543211",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            user=self.renter_user,
            name="TestRenter",
            phone="+911234567890",
            email="renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
        )

    def _create_overdue_rent(self, due_date):
        return RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("10000"),
            due_date=due_date,
            status=RentRecord.Status.PENDING,
            payout_status="PENDING",
        )

    @patch("notification.services.whatsapp_service.send_whatsapp_message")
    def test_escalates_rent_three_days_past_due(self, mock_whatsapp):
        due_date = timezone.now().date() - timezone.timedelta(days=3)
        self._create_overdue_rent(due_date)

        self.command.handle()
        self.assertEqual(mock_whatsapp.call_count, 2)

    @patch("notification.services.whatsapp_service.send_whatsapp_message")
    def test_skips_already_escalated_renter(self, mock_whatsapp):
        from properties.models.renter_models import RentReminderLog

        due_date = timezone.now().date() - timezone.timedelta(days=3)
        self._create_overdue_rent(due_date)
        RentReminderLog.objects.create(renter=self.renter, message_type="ESCALATION")

        self.command.handle()
        mock_whatsapp.assert_not_called()

    @patch("notification.services.whatsapp_service.send_whatsapp_message")
    def test_skips_rent_less_than_three_days(self, mock_whatsapp):
        due_date = timezone.now().date() - timezone.timedelta(days=2)
        self._create_overdue_rent(due_date)

        self.command.handle()
        mock_whatsapp.assert_not_called()

    @patch("notification.services.whatsapp_service.send_whatsapp_message")
    def test_escalates_to_caretaker_when_assigned(self, mock_whatsapp):
        caretaker_user = User.objects.create_user(
            username="caretaker_esc",
            password="p",
            full_name="CaretakerEsc",
            phone="+1",
            email="caretaker_esc@test.com",
            whatsapp_number="+919876543212",
        )
        Caretaker.objects.create(
            unit=self.unit,
            user=caretaker_user,
            name="EscCaretaker",
            phone="+911234567892",
            joining_date=timezone.now().date(),
            is_active=True,
        )
        due_date = timezone.now().date() - timezone.timedelta(days=3)
        self._create_overdue_rent(due_date)

        self.command.handle()
        self.assertEqual(mock_whatsapp.call_count, 3)

    @patch("notification.services.whatsapp_service.send_whatsapp_message")
    def test_dry_run_does_not_send(self, mock_whatsapp):
        due_date = timezone.now().date() - timezone.timedelta(days=3)
        self._create_overdue_rent(due_date)

        self.command.handle(dry_run=True)
        mock_whatsapp.assert_not_called()
