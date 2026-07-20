"""Tests for notification views."""

from unittest.mock import MagicMock, patch

from rest_framework.test import APIRequestFactory, force_authenticate

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from notification.models import Notification
from notification.views import (
    get_notifications,
    mark_notification_read,
    register_fcm_token,
    save_device_token,
)

User = get_user_model()


class GetNotificationsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="notif_user",
            email="nu@test.com",
            password="p",
            full_name="Notif User",
            phone="+1",
        )

    def _make_request(self, user=None):
        request = self.factory.get("/api/notifications/")
        if user is not None:
            force_authenticate(request, user=user)
        return request

    def test_anonymous_user_returns_403(self):
        request = self._make_request(user=AnonymousUser())
        response = get_notifications(request)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_user_returns_notifications(self):
        Notification.objects.create(user=self.user, title="Test", message="Hello")
        request = self._make_request(user=self.user)
        response = get_notifications(request)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)


class MarkNotificationReadTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="mark_user",
            email="mu@test.com",
            password="p",
            full_name="Mark User",
            phone="+1",
        )

    def _make_request(self, user=None):
        request = self.factory.post("/api/notifications/mark-read/")
        request.data = {}
        if user is not None:
            force_authenticate(request, user=user)
        return request

    def test_anonymous_user_returns_403(self):
        request = self._make_request(user=AnonymousUser())
        response = mark_notification_read(request, notification_id=1)
        self.assertEqual(response.status_code, 403)

    def test_mark_notification_read_success(self):
        note = Notification.objects.create(
            user=self.user, title="Test", message="Hello"
        )
        request = self._make_request(user=self.user)
        response = mark_notification_read(request, notification_id=note.id)
        self.assertEqual(response.status_code, 200)
        note.refresh_from_db()
        self.assertTrue(note.is_read)


class SaveDeviceTokenTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="token_user",
            email="tu@test.com",
            password="p",
            full_name="Token User",
            phone="+1",
        )

    def _make_request(self, data=None, user=None):
        request = self.factory.post("/api/save-device-token/", data=data or {})
        if user is not None:
            force_authenticate(request, user=user)
        return request

    def test_anonymous_user_returns_403(self):
        request = self._make_request(user=AnonymousUser())
        response = save_device_token(request)
        self.assertEqual(response.status_code, 403)

    def test_save_device_token_success(self):
        request = self._make_request(data={"token": "test-token-123"}, user=self.user)
        response = save_device_token(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "saved")

    def test_save_device_token_missing_token(self):
        request = self._make_request(data={}, user=self.user)
        response = save_device_token(request)
        self.assertEqual(response.status_code, 200)


class RegisterFcmTokenTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="fcm_user",
            email="fu@test.com",
            password="p",
            full_name="FCM User",
            phone="+1",
        )

    def _make_request(self, data=None, user=None):
        request = self.factory.post("/api/register-fcm-token/", data=data or {})
        if user is not None:
            force_authenticate(request, user=user)
        return request

    def test_anonymous_user_returns_403(self):
        request = self._make_request(user=AnonymousUser())
        response = register_fcm_token(request)
        self.assertEqual(response.status_code, 403)

    def test_register_fcm_token_missing_token_returns_400(self):
        request = self._make_request(data={}, user=self.user)
        response = register_fcm_token(request)
        self.assertEqual(response.status_code, 400)

    def test_register_fcm_token_success(self):
        request = self._make_request(
            data={"token": "fcm-token-123", "type": "android"}, user=self.user
        )
        with patch("notification.views.FCMDevice") as mock_fcm:
            mock_device = MagicMock()
            mock_fcm.objects.update_or_create.return_value = (mock_device, True)
            response = register_fcm_token(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["status"], "Token registered")
