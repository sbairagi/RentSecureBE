"""Comprehensive pytest tests for notification/views.py targeting ≥95% coverage."""

import json
from unittest.mock import MagicMock, patch

import pytest
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from notification.models import DeviceToken, Notification
from notification.views import (
    get_notifications,
    mark_notification_read,
    register_fcm_token,
    save_device_token,
)

User = get_user_model()
NOTIFICATIONS_PREFIX = "/api/notifications"


def _auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture(autouse=True)
def _mock_fcm(db):
    with patch("notification.views.FCMDevice") as mock_fcm:
        mock_fcm.objects.update_or_create.return_value = (MagicMock(), True)
        yield mock_fcm


def _make_anon_request(method="GET", data=None):
    factory = RequestFactory()
    if data:
        req = getattr(factory, method.lower())(
            "/test",
            data=json.dumps(data),
            content_type="application/json",
        )
    else:
        req = getattr(factory, method.lower())("/test")
    req.user = AnonymousUser()
    return req


class TestGetNotifications:
    def test_returns_list_for_authenticated_user(self, user):
        Notification.objects.create(user=user, title="T1", message="M1")
        Notification.objects.create(user=user, title="T2", message="M2", is_read=True)
        response = _auth_client(user).get(f"{NOTIFICATIONS_PREFIX}/get/")
        assert response.status_code == 200
        assert len(response.data) == 2

    def test_returns_empty_list_when_no_notifications(self, user):
        response = _auth_client(user).get(f"{NOTIFICATIONS_PREFIX}/get/")
        assert response.status_code == 200
        assert response.data == []

    def test_anonymous_returns_401(self):
        req = _make_anon_request("GET")
        with patch(
            "rest_framework.permissions.IsAuthenticated.has_permission",
            return_value=True,
        ):
            response = get_notifications(req)
        assert response.status_code == 401


class TestMarkNotificationRead:
    def test_marks_notification_as_read(self, user):
        note = Notification.objects.create(user=user, title="T", message="M")
        response = _auth_client(user).post(f"{NOTIFICATIONS_PREFIX}/mark/{note.id}/")
        assert response.status_code == 200
        note.refresh_from_db()
        assert note.is_read is True

    def test_anonymous_returns_401(self):
        req = _make_anon_request("POST")
        with patch(
            "rest_framework.permissions.IsAuthenticated.has_permission",
            return_value=True,
        ):
            response = mark_notification_read(req, 1)
        assert response.status_code == 401


class TestSaveDeviceToken:
    def test_creates_device_token(self, user):
        response = _auth_client(user).post(
            f"{NOTIFICATIONS_PREFIX}/save-token/",
            {"token": "test-token-123"},
            format="json",
        )
        assert response.status_code == 200
        assert DeviceToken.objects.filter(user=user, token="test-token-123").exists()

    def test_updates_existing_device_token(self, user):
        DeviceToken.objects.create(user=user, token="old-token")
        response = _auth_client(user).post(
            f"{NOTIFICATIONS_PREFIX}/save-token/",
            {"token": "new-token-456"},
            format="json",
        )
        assert response.status_code == 200
        assert DeviceToken.objects.filter(user=user, token="new-token-456").exists()

    def test_empty_token_skips_update_and_returns_200(self, user):
        response = _auth_client(user).post(
            f"{NOTIFICATIONS_PREFIX}/save-token/",
            {"token": ""},
            format="json",
        )
        assert response.status_code == 200
        assert response.data == {"status": "saved"}
        assert not DeviceToken.objects.filter(user=user).exists()

    def test_missing_token_key_skips_update_and_returns_200(self, user):
        response = _auth_client(user).post(
            f"{NOTIFICATIONS_PREFIX}/save-token/",
            {},
            format="json",
        )
        assert response.status_code == 200
        assert response.data == {"status": "saved"}

    def test_anonymous_returns_400(self):
        req = _make_anon_request("POST", {})
        with patch(
            "rest_framework.permissions.IsAuthenticated.has_permission",
            return_value=True,
        ):
            response = save_device_token(req)
        assert response.status_code == 400


class TestRegisterFCMToken:
    def test_registers_token_successfully(self, user, _mock_fcm):
        response = _auth_client(user).post(
            f"{NOTIFICATIONS_PREFIX}/register-fcm/",
            {"token": "fcm-token-123", "type": "android"},
            format="json",
        )
        assert response.status_code == 200
        _mock_fcm.objects.update_or_create.assert_called_once_with(
            user=user,
            registration_id="fcm-token-123",
            defaults={"type": "android", "active": True},
        )

    def test_registers_token_defaults_type_to_android(self, user, _mock_fcm):
        response = _auth_client(user).post(
            f"{NOTIFICATIONS_PREFIX}/register-fcm/",
            {"token": "fcm-token-456"},
            format="json",
        )
        assert response.status_code == 200
        _mock_fcm.objects.update_or_create.assert_called_once_with(
            user=user,
            registration_id="fcm-token-456",
            defaults={"type": "android", "active": True},
        )

    def test_missing_token_returns_400(self, user):
        response = _auth_client(user).post(
            f"{NOTIFICATIONS_PREFIX}/register-fcm/",
            {"token": "", "type": "android"},
            format="json",
        )
        assert response.status_code == 400

    def test_anonymous_returns_401(self):
        req = _make_anon_request("POST", {})
        with patch(
            "rest_framework.permissions.IsAuthenticated.has_permission",
            return_value=True,
        ):
            response = register_fcm_token(req)
        assert response.status_code == 401
