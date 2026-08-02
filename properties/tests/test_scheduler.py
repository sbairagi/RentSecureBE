"""Tests for reminder_time support in scheduler and alert preferences."""

from datetime import time, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils.timezone import now

from core.models import User, UserProfile
from properties.models import Building, Renter, RentRecord, RentReminderLog, Unit
from properties.scheduler import _should_send_reminder, process_late_rent_followups


class ReminderTimeSchedulerTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="reminder_owner",
            password="p",
            full_name="ReminderOwner",
            phone="+91",
            whatsapp_number="+919876543210",
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="ReminderB",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="R1",
            unit_type="flat",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="ReminderRenter",
            phone="+911234567890",
            email="rr@test.com",
            rent_amount=10000,
            start_date=now().date(),
        )
        self.renter.whatsapp_number = "+919999999999"
        self.renter.save()
        self.rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=10000,
            payment_method="upi",
            status="PENDING",
            due_date=now().date() - timedelta(days=1),
        )

    @patch("properties.scheduler.now")
    def test_should_send_reminder_when_time_matches(self, mock_now):
        mock_now.return_value.time.return_value = time(9, 0)
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.reminder_time = time(9, 0)
        profile.save(update_fields=["reminder_time"])
        self.assertTrue(_should_send_reminder(self.owner))

    @patch("properties.scheduler.now")
    def test_should_send_reminder_when_time_does_not_match(self, mock_now):
        mock_now.return_value.time.return_value = time(9, 0)
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.reminder_time = time(10, 0)
        profile.save(update_fields=["reminder_time"])
        self.assertFalse(_should_send_reminder(self.owner))

    @patch("properties.scheduler.now")
    def test_should_send_reminder_when_no_profile(self, mock_now):
        mock_now.return_value.time.return_value = time(9, 0)
        UserProfile.objects.filter(user=self.owner).delete()
        self.assertTrue(_should_send_reminder(self.owner))

    def test_process_late_rent_followups_respects_reminder_time(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.reminder_time = time(0, 0)
        profile.save(update_fields=["reminder_time"])
        count = process_late_rent_followups()
        self.assertEqual(count, 0)
        self.assertEqual(RentReminderLog.objects.count(), 0)

    def test_process_late_rent_followups_sends_when_time_matches(self):
        current_time = now().time()
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.reminder_time = current_time
        profile.save(update_fields=["reminder_time"])
        with patch("properties.scheduler.send_late_rent_reminder") as mock_send:
            with patch("properties.scheduler.alert_owner_about_delay") as mock_alert:
                count = process_late_rent_followups()
                self.assertEqual(count, 1)
                mock_send.assert_called_once_with(self.rent)
                mock_alert.assert_called_once_with(self.rent)
