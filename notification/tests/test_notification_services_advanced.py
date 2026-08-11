"""Tests for notification services orchestrator and new services."""

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import NotificationPreference, UserProfile
from notification.models import Notification
from notification.services.maintenance_notify_service import (
    notify_maintenance_created,
    notify_maintenance_updated,
)
from notification.services.orchestrator import dispatch_notification
from notification.services.security_notify_service import (
    notify_account_status_changed,
    notify_email_changed,
    notify_new_login,
    notify_password_changed,
    notify_phone_changed,
)
from notification.services.subscription_notify_service import (
    _notify_subscription_expired,
    _notify_subscription_expiring,
)

User = get_user_model()


class DispatchNotificationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dispatch_user",
            email="dispatch@test.com",
            password="p",
            full_name="Dispatch User",
            phone="+911234567890",
        )
        NotificationPreference.objects.create(owner=self.user)
        UserProfile.objects.create(user=self.user)

    def test_creates_in_app_notification(self):
        note = dispatch_notification(
            user=self.user,
            title="Test",
            message="Test message",
            notification_type=Notification.SYSTEM_ALERT,
        )
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(note.user, self.user)
        self.assertEqual(note.title, "Test")
        self.assertEqual(note.message, "Test message")

    def test_does_not_create_duplicate_on_same_event(self):
        dispatch_notification(
            user=self.user,
            title="Test",
            message="Test message",
            notification_type=Notification.SYSTEM_ALERT,
        )
        dispatch_notification(
            user=self.user,
            title="Test",
            message="Test message",
            notification_type=Notification.SYSTEM_ALERT,
        )
        self.assertEqual(Notification.objects.count(), 2)

    def test_respects_push_disabled_preference(self):
        pref = NotificationPreference.objects.get(owner=self.user)
        pref.push_enabled = False
        pref.save()

        with patch(
            "notification.services.orchestrator.send_fcm_notification"
        ) as mock_push:
            dispatch_notification(
                user=self.user,
                title="Test",
                message="Test message",
                notification_type=Notification.SYSTEM_ALERT,
            )
            mock_push.assert_not_called()

    def test_respects_type_specific_preference(self):
        pref = NotificationPreference.objects.get(owner=self.user)
        pref.maintenance_push = False
        pref.save()

        with patch(
            "notification.services.orchestrator.send_fcm_notification"
        ) as mock_push:
            dispatch_notification(
                user=self.user,
                title="Test",
                message="Test message",
                notification_type=Notification.MAINTENANCE_CREATED,
            )
            mock_push.assert_not_called()

    def test_sets_delivered_at_when_push_succeeds(self):
        with patch(
            "notification.services.orchestrator.send_fcm_notification",
            return_value=True,
        ):
            note = dispatch_notification(
                user=self.user,
                title="Test",
                message="Test message",
                notification_type=Notification.SYSTEM_ALERT,
            )
            note.refresh_from_db()
            self.assertIsNotNone(note.delivered_at)
            self.assertIn("push", note.channels)

    def test_marks_delivered_at_for_whatsapp_when_push_disabled(self):
        pref = NotificationPreference.objects.get(owner=self.user)
        pref.push_enabled = False
        pref.save()

        with patch(
            "notification.services.orchestrator.send_whatsapp_message",
            return_value=True,
        ):
            note = dispatch_notification(
                user=self.user,
                title="Test",
                message="Test message",
                notification_type=Notification.SYSTEM_ALERT,
            )
            note.refresh_from_db()
            self.assertIsNotNone(note.delivered_at)


class SecurityNotificationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="security_user",
            email="security@test.com",
            password="p",
            full_name="Security User",
            phone="+911234567890",
        )

    @patch("notification.services.security_notify_service.dispatch_notification")
    def test_notify_new_login(self, mock_dispatch):
        notify_new_login(self.user, ip_address="1.2.3.4")
        mock_dispatch.assert_called_once()
        args = mock_dispatch.call_args
        self.assertEqual(args.kwargs["user"], self.user)
        self.assertEqual(args.kwargs["notification_type"], Notification.SYSTEM_ALERT)
        self.assertIn("new_login", args.kwargs["data"]["event"])

    @patch("notification.services.security_notify_service.dispatch_notification")
    def test_notify_password_changed(self, mock_dispatch):
        notify_password_changed(self.user)
        mock_dispatch.assert_called_once()
        args = mock_dispatch.call_args
        self.assertIn("password_changed", args.kwargs["data"]["event"])

    @patch("notification.services.security_notify_service.dispatch_notification")
    def test_notify_email_changed(self, mock_dispatch):
        notify_email_changed(self.user, "new@example.com")
        mock_dispatch.assert_called_once()
        args = mock_dispatch.call_args
        self.assertEqual(args.kwargs["data"]["new_email"], "new@example.com")

    @patch("notification.services.security_notify_service.dispatch_notification")
    def test_notify_phone_changed(self, mock_dispatch):
        notify_phone_changed(self.user, "+919999999999")
        mock_dispatch.assert_called_once()
        args = mock_dispatch.call_args
        self.assertEqual(args.kwargs["data"]["new_phone"], "+919999999999")

    @patch("notification.services.security_notify_service.dispatch_notification")
    def test_notify_account_status_changed(self, mock_dispatch):
        notify_account_status_changed(self.user, "active", "suspended")
        mock_dispatch.assert_called_once()
        args = mock_dispatch.call_args
        self.assertEqual(args.kwargs["data"]["old_status"], "active")
        self.assertEqual(args.kwargs["data"]["new_status"], "suspended")


class SubscriptionNotificationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="sub_user",
            email="sub@test.com",
            password="p",
            full_name="Sub User",
            phone="+911234567890",
        )
        self.plan = NotificationPreference.objects.create(owner=self.user)

    @patch("notification.services.subscription_notify_service.dispatch_notification")
    def test_notify_subscription_expiring(self, mock_dispatch):
        from core.models import SubscriptionPlan, UserSubscription

        plan = SubscriptionPlan.objects.create(
            name="pro",
            monthly_price=29.99,
            yearly_price=299.99,
            is_active=True,
        )
        sub = UserSubscription.objects.create(
            user=self.user,
            plan=plan,
            start_date="2025-01-01",
            end_date="2025-01-05",
            is_active=True,
        )
        _notify_subscription_expiring(sub, 3)
        mock_dispatch.assert_called_once()
        args = mock_dispatch.call_args
        self.assertEqual(
            args.kwargs["notification_type"], Notification.SUBSCRIPTION_EXPIRING
        )
        self.assertIn("3 day(s)", args.kwargs["message"])

    @patch("notification.services.subscription_notify_service.dispatch_notification")
    def test_notify_subscription_expired(self, mock_dispatch):
        from core.models import SubscriptionPlan, UserSubscription

        plan = SubscriptionPlan.objects.create(
            name="pro",
            monthly_price=29.99,
            yearly_price=299.99,
            is_active=True,
        )
        sub = UserSubscription.objects.create(
            user=self.user,
            plan=plan,
            start_date="2024-01-01",
            end_date="2024-12-31",
            is_active=True,
        )
        _notify_subscription_expired(sub)
        mock_dispatch.assert_called_once()
        args = mock_dispatch.call_args
        self.assertEqual(
            args.kwargs["notification_type"], Notification.SUBSCRIPTION_EXPIRED
        )


class MaintenanceNotificationTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="maint_owner",
            email="maint_owner@test.com",
            password="p",
            full_name="Maint Owner",
            phone="+911234567890",
        )
        self.renter_user = User.objects.create_user(
            username="maint_renter",
            email="maint_renter@test.com",
            password="p",
            full_name="Maint Renter",
            phone="+919876543210",
        )
        NotificationPreference.objects.create(owner=self.owner)
        UserProfile.objects.create(user=self.renter_user)

    @patch("notification.services.maintenance_notify_service.dispatch_notification")
    def test_notify_maintenance_created(self, mock_dispatch):
        maintenance = MagicMock()
        maintenance.id = 1
        maintenance.title = "Broken Tap"
        maintenance.priority = Notification.PRIORITY_MEDIUM
        maintenance.renter.user = self.renter_user
        maintenance.unit.unit = "101"
        maintenance.owner = self.owner

        notify_maintenance_created(maintenance)
        self.assertEqual(mock_dispatch.call_count, 2)

    @patch("notification.services.maintenance_notify_service.dispatch_notification")
    def test_notify_maintenance_updated(self, mock_dispatch):
        maintenance = MagicMock()
        maintenance.id = 1
        maintenance.title = "Broken Tap"
        maintenance.renter.user = self.renter_user
        maintenance.owner = self.owner

        notify_maintenance_updated(maintenance, "created", "in_progress")
        self.assertEqual(mock_dispatch.call_count, 2)
        args = mock_dispatch.call_args_list[0]
        self.assertEqual(
            args.kwargs["notification_type"], Notification.MAINTENANCE_UPDATED
        )
