"""Tests for reminder_time support in scheduler and alert preferences."""

from datetime import datetime, time, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

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
            start_date=timezone.now().date(),
        )
        self.renter.whatsapp_number = "+919999999999"
        self.renter.save()
        self.rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=10000,
            payment_method="upi",
            status="PENDING",
            due_date=timezone.now().date() - timedelta(days=1),
        )

    def _mock_now(self, target_time: time) -> patch:
        """Create a mock for `properties.scheduler.now` returning a timezone-aware datetime."""
        mock_dt = datetime.combine(timezone.now().date(), target_time)
        mock_dt = timezone.make_aware(mock_dt)
        return patch("properties.scheduler.now", return_value=mock_dt)

    def test_should_send_reminder_when_time_matches(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.reminder_time = time(9, 0)
        profile.save(update_fields=["reminder_time"])
        with self._mock_now(time(9, 0)):
            self.assertTrue(_should_send_reminder(self.owner))

    def test_should_send_reminder_within_window(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.reminder_time = time(9, 0)
        profile.save(update_fields=["reminder_time"])
        with self._mock_now(time(9, 4)):
            self.assertTrue(_should_send_reminder(self.owner))

    def test_should_send_reminder_outside_window(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.reminder_time = time(9, 0)
        profile.save(update_fields=["reminder_time"])
        with self._mock_now(time(9, 6)):
            self.assertFalse(_should_send_reminder(self.owner))

    def test_should_send_reminder_when_no_profile(self):
        UserProfile.objects.filter(user=self.owner).delete()
        with self._mock_now(time(9, 0)):
            self.assertTrue(_should_send_reminder(self.owner))

    def test_process_late_rent_followups_respects_reminder_time(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.reminder_time = time(1, 0)
        profile.save(update_fields=["reminder_time"])
        with self._mock_now(time(0, 0)):
            with patch("properties.scheduler.send_late_rent_reminder") as mock_send:
                with patch(
                    "properties.scheduler.alert_owner_about_delay"
                ) as mock_alert:
                    count = process_late_rent_followups()
        self.assertEqual(count, 0)
        self.assertEqual(RentReminderLog.objects.count(), 0)
        mock_send.assert_not_called()
        mock_alert.assert_not_called()

    def test_process_late_rent_followups_sends_when_time_matches(self):
        current_time = timezone.now()
        profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        profile.reminder_time = current_time.time()
        profile.save(update_fields=["reminder_time"])
        with patch("properties.scheduler.send_late_rent_reminder") as mock_send:
            with patch("properties.scheduler.alert_owner_about_delay") as mock_alert:
                count = process_late_rent_followups()
                self.assertEqual(count, 1)
                mock_send.assert_called_once_with(self.rent)
                mock_alert.assert_called_once_with(self.rent)
