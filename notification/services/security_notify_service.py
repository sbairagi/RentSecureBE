import logging
from typing import Any

from django.utils import timezone

from notification.models import Notification
from notification.services.orchestrator import dispatch_notification

logger = logging.getLogger(__name__)


def notify_new_login(user: Any, ip_address: str = "", user_agent: str = "") -> None:
    if not user or not getattr(user, "is_active", False):
        return
    dispatch_notification(
        user=user,
        title="New Login Detected",
        message=(
            "A new login was detected on your account. "
            f"IP: {ip_address or 'unknown'}. "
            "If this was not you, please secure your account immediately."
        ),
        notification_type=Notification.SYSTEM_ALERT,
        resource_type="security",
        resource_id=str(user.pk),
        priority=Notification.PRIORITY_HIGH,
        data={
            "event": "new_login",
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": timezone.now().isoformat(),
        },
    )


def notify_password_changed(user: Any) -> None:
    if not user or not getattr(user, "is_active", False):
        return
    dispatch_notification(
        user=user,
        title="Password Changed",
        message=(
            "Your account password was changed successfully. "
            "If you did not make this change, please contact support."
        ),
        notification_type=Notification.SYSTEM_ALERT,
        resource_type="security",
        resource_id=str(user.pk),
        priority=Notification.PRIORITY_HIGH,
        data={"event": "password_changed", "timestamp": timezone.now().isoformat()},
    )


def notify_email_changed(user: Any, new_email: str) -> None:
    if not user or not getattr(user, "is_active", False):
        return
    dispatch_notification(
        user=user,
        title="Email Address Changed",
        message=(
            f"Your account email was updated to {new_email}. "
            "If you did not make this change, please contact support."
        ),
        notification_type=Notification.SYSTEM_ALERT,
        resource_type="security",
        resource_id=str(user.pk),
        priority=Notification.PRIORITY_HIGH,
        data={
            "event": "email_changed",
            "new_email": new_email,
            "timestamp": timezone.now().isoformat(),
        },
    )


def notify_phone_changed(user: Any, new_phone: str) -> None:
    if not user or not getattr(user, "is_active", False):
        return
    dispatch_notification(
        user=user,
        title="Phone Number Changed",
        message=(
            f"Your account phone number was updated to {new_phone}. "
            "If you did not make this change, please contact support."
        ),
        notification_type=Notification.SYSTEM_ALERT,
        resource_type="security",
        resource_id=str(user.pk),
        priority=Notification.PRIORITY_HIGH,
        data={
            "event": "phone_changed",
            "new_phone": new_phone,
            "timestamp": timezone.now().isoformat(),
        },
    )


def notify_account_status_changed(user: Any, old_status: str, new_status: str) -> None:
    if not user or not getattr(user, "is_active", False):
        return
    dispatch_notification(
        user=user,
        title="Account Status Updated",
        message=f"Your account status was changed from {old_status} to {new_status}.",
        notification_type=Notification.SYSTEM_ALERT,
        resource_type="security",
        resource_id=str(user.pk),
        priority=Notification.PRIORITY_URGENT,
        data={
            "event": "account_status_changed",
            "old_status": old_status,
            "new_status": new_status,
            "timestamp": timezone.now().isoformat(),
        },
    )
