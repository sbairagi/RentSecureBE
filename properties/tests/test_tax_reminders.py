"""Tests for send_tax_reminders management command."""

from datetime import date
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from core.models import User
from management.commands.send_tax_reminders import Command
from properties.models import Building, PropertyTaxRecord, Unit


class SendTaxRemindersTests(TestCase):
    def setUp(self):
        self.command = Command()
        self.owner = User.objects.create_user(
            username="tax_reminder_owner",
            password="p",
            full_name="TaxReminderOwner",
            phone="+1",
            email="taxrem@test.com",
            whatsapp_number="+919876543210",
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="TaxReminderB",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="TR1",
            unit_type="flat",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )

    def test_skips_paid_taxes(self):
        PropertyTaxRecord.objects.create(
            property=self.building,
            amount="5000",
            due_date=date.today(),
            paid=True,
            paid_date=date.today(),
        )
        with patch(
            "notification.services.schedule_reminders.send_whatsapp_message"
        ) as mock_send:
            self.command.handle()
        mock_send.assert_not_called()

    def test_sends_reminder_for_upcoming_unpaid_tax(self):
        target_date = timezone.now().date() + timezone.timedelta(days=3)
        PropertyTaxRecord.objects.create(
            property=self.building,
            amount="5000",
            due_date=target_date,
            paid=False,
        )
        with patch(
            "notification.services.schedule_reminders.send_whatsapp_message"
        ) as mock_send:
            with patch(
                "notification.services.schedule_reminders.send_whatsapp_audio"
            ) as mock_audio:
                with patch(
                    "notification.services.schedule_reminders.generate_voice_note",
                    return_value="/tmp/test.mp3",
                ):
                    self.command.handle()
        mock_send.assert_called_once()
        mock_audio.assert_called_once()

    def test_skips_owner_without_whatsapp(self):
        self.owner.whatsapp_number = ""
        self.owner.save(update_fields=["whatsapp_number"])
        target_date = timezone.now().date() + timezone.timedelta(days=3)
        PropertyTaxRecord.objects.create(
            property=self.building,
            amount="5000",
            due_date=target_date,
            paid=False,
        )
        with patch(
            "notification.services.schedule_reminders.send_whatsapp_message"
        ) as mock_send:
            with patch(
                "notification.services.schedule_reminders.send_whatsapp_audio"
            ) as mock_audio:
                with patch(
                    "notification.services.schedule_reminders.generate_voice_note",
                    return_value="/tmp/test.mp3",
                ):
                    self.command.handle()
        mock_send.assert_not_called()
        mock_audio.assert_not_called()
