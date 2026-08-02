"""Tests for scheduled reminder management command."""

from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils.timezone import now

from core.models import User, UserProfile
from management.commands.send_scheduled_reminders import Command
from notification.services.schedule_reminders import process_rent_reminders
from properties.models import Building, Renter, RentRecord, Unit
from properties.models.renter_models import RentReminderLog


class SendScheduledRemindersCommandTest(TestCase):
    def test_command_calls_rent_and_tax_processors(self):
        cmd = Command()
        with patch(
            "management.commands.send_scheduled_reminders.process_rent_reminders"
        ) as mock_rent:
            with patch(
                "management.commands.send_scheduled_reminders.process_tax_reminders"
            ) as mock_tax:
                cmd.handle()
                mock_rent.assert_called_once()
                mock_tax.assert_called_once()


class ProcessRentRemindersDedupTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="dedup_owner",
            password="p",
            full_name="DedupOwner",
            phone="+91",
            whatsapp_number="+919876543210",
        )
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.reminder_time = now().time()
        profile.save(update_fields=["reminder_time"])
        self.building = Building.objects.create(
            owner=self.owner,
            name="DedupB",
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
            name="DedupRenter",
            phone="+911234567890",
            email="dedup@test.com",
            rent_amount=10000,
            start_date=now().date(),
        )
        self.renter.whatsapp_number = "+919999999999"
        self.renter.save()
        target_date = now().date() + timedelta(days=3)
        self.rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=10000,
            payment_method="upi",
            status="PENDING",
            due_date=target_date,
        )

    @patch("notification.services.schedule_reminders.send_whatsapp_message")
    @patch("notification.services.schedule_reminders.generate_voice_note")
    def test_process_rent_reminders_creates_log(self, mock_voice, mock_send):
        mock_send.return_value = True
        mock_voice.return_value = None
        process_rent_reminders()
        self.assertEqual(
            RentReminderLog.objects.filter(
                renter=self.renter, message_type="DUE"
            ).count(),
            1,
        )

    @patch("notification.services.schedule_reminders.send_whatsapp_message")
    @patch("notification.services.schedule_reminders.generate_voice_note")
    def test_process_rent_reminders_skips_duplicate_same_day(
        self, mock_voice, mock_send
    ):
        RentReminderLog.objects.create(renter=self.renter, message_type="DUE")
        process_rent_reminders()
        mock_send.assert_not_called()
