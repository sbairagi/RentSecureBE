from __future__ import annotations

import logging
from typing import Any

from fcm_django.models import FCMDevice  # type: ignore[import-untyped]
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response

from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from django.utils import timezone

from core.models import NotificationPreference
from notification.models import DeviceToken, Notification
from notification.serializers import (
    DeviceTokenCreateSerializer,
    DeviceTokenSerializer,
    NotificationPreferenceSerializer,
    NotificationPreferenceUpdateSerializer,
    NotificationSerializer,
    UnreadCountSerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Notification List
# ---------------------------------------------------------------------------


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_notifications(request: DRFRequest) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    user = request.user
    notifications_qs = user.notifications.filter(archived=False)

    search = request.query_params.get("search")
    notification_type = request.query_params.get("type")
    read_status = request.query_params.get("read_status")
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")

    if search:
        notifications_qs = notifications_qs.filter(
            Q(title__icontains=search) | Q(message__icontains=search)
        )
    if notification_type:
        notifications_qs = notifications_qs.filter(notification_type=notification_type)
    if read_status == "read":
        notifications_qs = notifications_qs.filter(is_read=True)
    elif read_status == "unread":
        notifications_qs = notifications_qs.filter(is_read=False)
    if date_from:
        notifications_qs = notifications_qs.filter(created_at__gte=date_from)
    if date_to:
        notifications_qs = notifications_qs.filter(created_at__lte=date_to)

    try:
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 20))
    except (ValueError, TypeError):
        page = 1
        limit = 20

    page = max(page, 1)
    limit = max(min(limit, 100), 1)

    total = notifications_qs.count()
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    start = (page - 1) * limit
    end = start + limit
    page_qs = notifications_qs[start:end]

    serializer = NotificationSerializer(page_qs, many=True)
    return Response(
        {
            "data": serializer.data,
            "meta": {
                "total": total,
                "page": page,
                "limit": limit,
                "totalPages": total_pages,
            },
        }
    )


# ---------------------------------------------------------------------------
# Unread Count
# ---------------------------------------------------------------------------


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def unread_count(request: DRFRequest) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    count = request.user.notifications.filter(is_read=False, archived=False).count()
    serializer = UnreadCountSerializer({"count": count})
    return Response(serializer.data)


# ---------------------------------------------------------------------------
# Mark Single Notification Read
# ---------------------------------------------------------------------------


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notification_read(request: DRFRequest, notification_id: int) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        note = request.user.notifications.get(id=notification_id)
    except Notification.DoesNotExist:
        return Response(
            {"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND
        )

    if not note.is_read:
        note.is_read = True
        note.read_at = timezone.now()
        note.save(update_fields=["is_read", "read_at"])

    return Response({"status": "Marked as read"})


# ---------------------------------------------------------------------------
# Mark All Notifications Read
# ---------------------------------------------------------------------------


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request: DRFRequest) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    now = timezone.now()
    updated = request.user.notifications.filter(is_read=False, archived=False).update(
        is_read=True, read_at=now
    )
    return Response({"status": f"{updated} notifications marked as read"})


# ---------------------------------------------------------------------------
# Delete / Archive Notification
# ---------------------------------------------------------------------------


@api_view(["DELETE", "POST"])
@permission_classes([IsAuthenticated])
def delete_notification(request: DRFRequest, notification_id: int) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        note = request.user.notifications.get(id=notification_id)
    except Notification.DoesNotExist:
        return Response(
            {"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND
        )

    note.archived = True
    note.save(update_fields=["archived"])
    return Response({"status": "Notification archived"})


# ---------------------------------------------------------------------------
# Save Device Token (Expo / generic)
# ---------------------------------------------------------------------------


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_device_token(request: DRFRequest) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = DeviceTokenCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    device_token, _ = DeviceToken.objects.update_or_create(
        user=request.user,
        token=data["token"],
        defaults={
            "device_id": data.get("device_id", ""),
            "platform": data["platform"],
            "fcm_token": data.get("fcm_token", ""),
            "active": True,
        },
    )

    # Also register with fcm-django if fcm_token provided
    if data.get("fcm_token"):
        FCMDevice.objects.update_or_create(
            user=request.user,
            registration_id=data["fcm_token"],
            defaults={"type": data["platform"], "active": True},
        )

    return Response(
        {
            "status": "saved",
            "device_id": device_token.id,
        }
    )


# ---------------------------------------------------------------------------
# Register FCM Token
# ---------------------------------------------------------------------------


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_fcm_token(request: DRFRequest) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    token = request.data.get("token")
    device_type = request.data.get("type", "android")
    expo_token = request.data.get("expo_token", "")

    if not token:
        return Response({"error": "Token required"}, status=status.HTTP_400_BAD_REQUEST)

    FCMDevice.objects.update_or_create(
        user=request.user,
        registration_id=token,
        defaults={"type": device_type, "active": True},
    )

    # Also save as DeviceToken
    if expo_token:
        DeviceToken.objects.update_or_create(
            user=request.user,
            token=expo_token,
            defaults={
                "platform": device_type,
                "fcm_token": token,
                "active": True,
            },
        )

    return Response({"status": "Token registered"})


# ---------------------------------------------------------------------------
# List User Devices
# ---------------------------------------------------------------------------


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_devices(request: DRFRequest) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    devices = DeviceToken.objects.filter(user=request.user)
    serializer = DeviceTokenSerializer(devices, many=True)
    return Response(serializer.data)


# ---------------------------------------------------------------------------
# Unregister / Deactivate Device
# ---------------------------------------------------------------------------


@api_view(["DELETE", "POST"])
@permission_classes([IsAuthenticated])
def unregister_device(request: DRFRequest, device_id: int) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        device = DeviceToken.objects.get(id=device_id, user=request.user)
    except DeviceToken.DoesNotExist:
        return Response({"error": "Device not found"}, status=status.HTTP_404_NOT_FOUND)

    device.active = False
    device.save(update_fields=["active"])

    # Also deactivate fcm-django device if exists
    fcm_devices = FCMDevice.objects.filter(
        user=request.user, registration_id=device.fcm_token
    )
    for fcm_device in fcm_devices:
        fcm_device.active = False
        fcm_device.save(update_fields=["active"])

    return Response({"status": "Device unregistered"})


# ---------------------------------------------------------------------------
# Notification Preferences
# ---------------------------------------------------------------------------


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def notification_preferences(request: DRFRequest) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    preference, _ = NotificationPreference.objects.get_or_create(owner=request.user)

    if request.method == "GET":
        serializer = NotificationPreferenceSerializer(preference)
        return Response(serializer.data)

    serializer = NotificationPreferenceUpdateSerializer(
        preference, data=request.data, partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(NotificationPreferenceSerializer(preference).data)


# ---------------------------------------------------------------------------
# Notification Types
# ---------------------------------------------------------------------------


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_types(_request: DRFRequest) -> Response:
    types = [
        {"value": value, "label": label}
        for value, label in Notification.NOTIFICATION_TYPE_CHOICES
    ]
    return Response(types)


# ---------------------------------------------------------------------------
# Create Notification (internal use — webhooks, services)
# ---------------------------------------------------------------------------


def create_notification(
    user: Any,
    title: str,
    message: str,
    notification_type: str = Notification.SYSTEM_ALERT,
    resource_type: str = "",
    resource_id: str = "",
    data: dict | None = None,
    priority: str = Notification.PRIORITY_MEDIUM,
    channels: list[str] | None = None,
    action_url: str = "",
    action_label: str = "",
    image_url: str = "",
) -> Notification:
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        resource_type=resource_type,
        resource_id=resource_id,
        data=data or {},
        priority=priority,
        channels=channels or [],
        action_url=action_url,
        action_label=action_label,
        image_url=image_url,
    )
    return notification
