"""Tests for notification/views.py — notification and device-token endpoints."""

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
