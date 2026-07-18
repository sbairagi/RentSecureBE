"""Tests for notification views."""

from unittest.mock import MagicMock, patch

from rest_framework.test import APIRequestFactory, force_authenticate

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from notification.models import DeviceToken, Notification
from notification.views import (
    get_notifications,
    mark_notification_read,
    register_fcm_token,
    save_device_token,
)

User = get_user_model()


def _jwt_request(user, method="GET", data=None, path="/test"):
    from rest_framework_simplejwt.tokens import RefreshToken

    from django.test import RequestFactory

    factory = RequestFactory()
    token = RefreshToken.for_user(user).access_token
    if data:
        import json

        req = getattr(factory, method.lower())(
            path,
            data=json.dumps(data),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
    else:
        req = getattr(factory, method.lower())(
            path, HTTP_AUTHORIZATION=f"Bearer {token}"
        )
    return req


def _anon_request(method="GET", data=None, path="/test"):
    from django.test import RequestFactory

    factory = RequestFactory()
    if data:
        import json

        req = getattr(factory, method.lower())(
            path,
            data=json.dumps(data),
            content_type="application/json",
        )
    else:
        req = getattr(factory, method.lower())(path)
    req.user = AnonymousUser()
    return req


class NotificationViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="notif_view_user",
            email="notif@test.com",
            password="p",
            full_name="Notif View",
            phone="+1",
        )

    def test_get_notifications_returns_list(self):
        Notification.objects.create(user=self.user, title="T1", message="M1")
        Notification.objects.create(
            user=self.user, title="T2", message="M2", is_read=True
        )
        response = get_notifications(_jwt_request(self.user))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_get_notifications_anonymous_returns_401(self):
        response = get_notifications(_anon_request())
        self.assertEqual(response.status_code, 401)

    def test_mark_notification_read(self):
        note = Notification.objects.create(user=self.user, title="T", message="M")
        response = mark_notification_read(
            _jwt_request(self.user, method="POST"), note.id
        )
        self.assertEqual(response.status_code, 200)
        note.refresh_from_db()
        self.assertTrue(note.is_read)

    def test_mark_notification_read_anonymous_returns_401(self):
        response = mark_notification_read(_anon_request(method="POST"), 1)
        self.assertEqual(response.status_code, 401)

    def test_save_device_token(self):
        response = save_device_token(
            _jwt_request(self.user, method="POST", data={"token": "test-token-123"}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(DeviceToken.objects.filter(user=self.user).exists())

    def test_save_device_token_anonymous_returns_401(self):
        response = save_device_token(_anon_request(method="POST", data={"token": "t"}))
        self.assertEqual(response.status_code, 401)

    def test_register_fcm_token(self):
        response = register_fcm_token(
            _jwt_request(
                self.user,
                method="POST",
                data={"token": "fcm-token-123", "type": "android"},
            ),
        )
        self.assertEqual(response.status_code, 200)

    def test_register_fcm_token_missing_token_returns_400(self):
        response = register_fcm_token(
            _jwt_request(
                self.user, method="POST", data={"token": "", "type": "android"}
            ),
        )
        self.assertEqual(response.status_code, 400)

    def test_register_fcm_token_anonymous_returns_401(self):
        response = register_fcm_token(
            _anon_request(method="POST", data={"token": "t", "type": "android"}),
        )
        self.assertEqual(response.status_code, 401)


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
