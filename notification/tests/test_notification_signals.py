"""Tests for notification/signals.py auto-push dispatch."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import NotificationPreference
from notification.models import Notification

User = get_user_model()


class NotificationSignalTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="signal_user",
            email="signal@test.com",
            password="p",
            full_name="Signal User",
            phone="+911234567890",
        )
        NotificationPreference.objects.create(owner=self.user)

    @patch("notification.services.notifications.send_fcm_notification")
    def test_push_dispatched_on_notification_create(self, mock_send_fcm):
        note = Notification.objects.create(
            user=self.user,
            title="Signal Test",
            message="Testing signal dispatch",
            notification_type=Notification.SYSTEM_ALERT,
        )
        mock_send_fcm.assert_called_once()
        args = mock_send_fcm.call_args
        self.assertEqual(args.kwargs["user"], self.user)
        self.assertEqual(args.kwargs["title"], "Signal Test")
        self.assertEqual(args.kwargs["notification_type"], Notification.SYSTEM_ALERT)
        self.assertEqual(args.kwargs["data"]["notification_id"], str(note.id))

    @patch("notification.services.notifications.send_fcm_notification")
    def test_push_not_dispatched_on_update(self, mock_send_fcm):
        note = Notification.objects.create(
            user=self.user,
            title="Signal Test",
            message="Testing signal dispatch",
            notification_type=Notification.SYSTEM_ALERT,
        )
        mock_send_fcm.reset_mock()
        note.title = "Updated Title"
        note.save()
        mock_send_fcm.assert_not_called()

    @patch("notification.services.notifications.send_fcm_notification")
    def test_push_not_dispatched_when_push_disabled(self, mock_send_fcm):
        pref = NotificationPreference.objects.get(owner=self.user)
        pref.push_enabled = False
        pref.save()

        Notification.objects.create(
            user=self.user,
            title="Signal Test",
            message="Testing signal dispatch",
            notification_type=Notification.SYSTEM_ALERT,
        )
        mock_send_fcm.assert_not_called()

    @patch("notification.services.notifications.send_fcm_notification")
    def test_push_not_dispatched_when_type_pref_disabled(self, mock_send_fcm):
        pref = NotificationPreference.objects.get(owner=self.user)
        pref.system_push = False
        pref.save()

        Notification.objects.create(
            user=self.user,
            title="Signal Test",
            message="Testing signal dispatch",
            notification_type=Notification.SYSTEM_ALERT,
        )
        mock_send_fcm.assert_not_called()
