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
    notification_preferences,
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
        assert len(response.data["data"]) == 2

    def test_returns_empty_list_when_no_notifications(self, user):
        response = _auth_client(user).get(f"{NOTIFICATIONS_PREFIX}/get/")
        assert response.status_code == 200
        assert response.data["data"] == []
        assert response.data["meta"]["total"] == 0

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

    def test_empty_token_returns_400(self, user):
        response = _auth_client(user).post(
            f"{NOTIFICATIONS_PREFIX}/save-token/",
            {"token": ""},
            format="json",
        )
        assert response.status_code == 400

    def test_missing_token_key_returns_400(self, user):
        response = _auth_client(user).post(
            f"{NOTIFICATIONS_PREFIX}/save-token/",
            {},
            format="json",
        )
        assert response.status_code == 400

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


class TestUnreadCount:
    def test_returns_zero_when_no_notifications(self, user):
        response = _auth_client(user).get(f"{NOTIFICATIONS_PREFIX}/unread-count/")
        assert response.status_code == 200
        assert response.data["count"] == 0

    def test_returns_correct_unread_count(self, user):
        Notification.objects.create(user=user, title="T1", message="M1", is_read=False)
        Notification.objects.create(user=user, title="T2", message="M2", is_read=True)
        Notification.objects.create(user=user, title="T3", message="M3", is_read=False)
        response = _auth_client(user).get(f"{NOTIFICATIONS_PREFIX}/unread-count/")
        assert response.status_code == 200
        assert response.data["count"] == 2

    def test_excludes_archived_from_unread_count(self, user):
        note = Notification.objects.create(
            user=user, title="T", message="M", is_read=False
        )
        note.archived = True
        note.save(update_fields=["archived"])
        response = _auth_client(user).get(f"{NOTIFICATIONS_PREFIX}/unread-count/")
        assert response.status_code == 200
        assert response.data["count"] == 0


class TestMarkAllNotificationsRead:
    def test_marks_all_unread_as_read(self, user):
        n1 = Notification.objects.create(
            user=user, title="T1", message="M1", is_read=False
        )
        n2 = Notification.objects.create(
            user=user, title="T2", message="M2", is_read=False
        )
        n3 = Notification.objects.create(
            user=user, title="T3", message="M3", is_read=True
        )
        response = _auth_client(user).post(f"{NOTIFICATIONS_PREFIX}/mark-all-read/")
        assert response.status_code == 200
        n1.refresh_from_db()
        n2.refresh_from_db()
        n3.refresh_from_db()
        assert n1.is_read is True
        assert n2.is_read is True
        assert n3.is_read is True

    def test_returns_zero_count_when_nothing_to_mark(self, user):
        Notification.objects.create(user=user, title="T", message="M", is_read=True)
        response = _auth_client(user).post(f"{NOTIFICATIONS_PREFIX}/mark-all-read/")
        assert response.status_code == 200

    def test_excludes_archived_from_mark_all_read(self, user):
        n1 = Notification.objects.create(
            user=user, title="T1", message="M1", is_read=False
        )
        n2 = Notification.objects.create(
            user=user, title="T2", message="M2", is_read=False
        )
        n2.archived = True
        n2.save(update_fields=["archived"])
        response = _auth_client(user).post(f"{NOTIFICATIONS_PREFIX}/mark-all-read/")
        assert response.status_code == 200
        n1.refresh_from_db()
        n2.refresh_from_db()
        assert n1.is_read is True
        assert n2.is_read is False


class TestDeleteNotification:
    def test_archives_notification(self, user):
        note = Notification.objects.create(user=user, title="T", message="M")
        response = _auth_client(user).delete(f"{NOTIFICATIONS_PREFIX}/{note.id}/")
        assert response.status_code == 200
        note.refresh_from_db()
        assert note.archived is True

    def test_returns_404_for_other_users_notification(self, user):
        other = User.objects.create_user(
            username="other_del", email="od@test.com", password="p"
        )
        note = Notification.objects.create(user=other, title="T", message="M")
        response = _auth_client(user).delete(f"{NOTIFICATIONS_PREFIX}/{note.id}/")
        assert response.status_code == 404

    def test_post_also_archives_notification(self, user):
        note = Notification.objects.create(user=user, title="T", message="M")
        response = _auth_client(user).post(f"{NOTIFICATIONS_PREFIX}/{note.id}/")
        assert response.status_code == 200
        note.refresh_from_db()
        assert note.archived is True


class TestNotificationPreferences:
    def test_get_preferences_creates_default(self, user):
        response = _auth_client(user).get(f"{NOTIFICATIONS_PREFIX}/preferences/")
        assert response.status_code == 200
        assert "push_enabled" in response.data
        assert "receive_rent_alerts" in response.data

    def test_update_preferences(self, user):
        from core.models import NotificationPreference

        pref = NotificationPreference.objects.create(owner=user, push_enabled=True)
        response = _auth_client(user).post(
            f"{NOTIFICATIONS_PREFIX}/preferences/",
            {"push_enabled": False},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["push_enabled"] is False
        pref.refresh_from_db()
        assert pref.push_enabled is False

    def test_anonymous_returns_401(self):
        req = _make_anon_request("GET")
        with patch(
            "rest_framework.permissions.IsAuthenticated.has_permission",
            return_value=True,
        ):
            response = notification_preferences(req)
        assert response.status_code == 401


class TestListDevices:
    def test_returns_empty_list_when_no_devices(self, user):
        response = _auth_client(user).get(f"{NOTIFICATIONS_PREFIX}/devices/")
        assert response.status_code == 200
        assert response.data == []

    def test_returns_user_devices(self, user):
        DeviceToken.objects.create(user=user, token="t1", platform="android")
        DeviceToken.objects.create(user=user, token="t2", platform="ios")
        response = _auth_client(user).get(f"{NOTIFICATIONS_PREFIX}/devices/")
        assert response.status_code == 200
        assert len(response.data) == 2


class TestUnregisterDevice:
    def test_deactivates_device(self, user):
        device = DeviceToken.objects.create(user=user, token="t1", platform="android")
        response = _auth_client(user).delete(
            f"{NOTIFICATIONS_PREFIX}/devices/{device.id}/"
        )
        assert response.status_code == 200
        device.refresh_from_db()
        assert device.active is False

    def test_returns_404_for_other_users_device(self, user):
        other = User.objects.create_user(
            username="other_unreg", email="ou@test.com", password="p"
        )
        device = DeviceToken.objects.create(user=other, token="t1", platform="android")
        response = _auth_client(user).delete(
            f"{NOTIFICATIONS_PREFIX}/devices/{device.id}/"
        )
        assert response.status_code == 404


class TestNotificationTypes:
    def test_returns_all_notification_types(self, user):
        response = _auth_client(user).get(f"{NOTIFICATIONS_PREFIX}/types/")
        assert response.status_code == 200
        assert len(response.data) > 0
        values = [t["value"] for t in response.data]
        assert "rent_due" in values
        assert "payment_success" in values
        assert "payout_success" in values
