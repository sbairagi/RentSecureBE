import logging
from datetime import timedelta
from typing import Any

from django.utils import timezone

from notification.models import Notification
from notification.services import notifications as notification_services
from notification.services.sms_service import send_sms
from notification.services.whatsapp_service import send_whatsapp_message

logger = logging.getLogger(__name__)


def _get_user_whatsapp_number(user: Any) -> str:
    profile = getattr(user, "userprofile", None) or getattr(user, "profile", None)
    if profile:
        return getattr(profile, "whatsapp_number", "") or ""
    return getattr(user, "whatsapp_number", "") or ""


def _get_user_phone(user: Any) -> str:
    return getattr(user, "phone", "") or ""


def _send_whatsapp(user: Any, message: str) -> bool:
    phone = _get_user_whatsapp_number(user)
    if not phone:
        return False
    try:
        return send_whatsapp_message(phone, message, user=user, rent_record=None)
    except Exception:
        logger.exception("WhatsApp send failed for user %s", getattr(user, "pk", None))
        return False


def _send_sms(user: Any, message: str) -> bool:
    phone = _get_user_phone(user)
    if not phone:
        return False
    try:
        return send_sms(phone, message)
    except Exception:
        logger.exception("SMS send failed for user %s", getattr(user, "pk", None))
        return False


def _dispatch_push_notification(
    user: Any,
    title: str,
    message: str,
    notification_type: str,
    channels: list[str] | None,
) -> bool:
    if "push" in (channels or []):
        return False
    try:
        from core.models import NotificationPreference

        pref, _ = NotificationPreference.objects.get_or_create(owner=user)
        if pref.push_enabled:
            type_pref_map = {
                Notification.RENT_DUE: "rent_alerts_push",
                Notification.RENT_PAYMENT_SUCCESS: "rent_alerts_push",
                Notification.RENT_PAYMENT_FAILED: "rent_alerts_push",
                Notification.AGREEMENT_EXPIRING: "agreement_push",
                Notification.AGREEMENT_SIGNED: "agreement_push",
                Notification.MAINTENANCE_CREATED: "maintenance_push",
                Notification.MAINTENANCE_UPDATED: "maintenance_push",
                Notification.VISITOR_REQUEST: "visitor_push",
                Notification.VISITOR_APPROVED: "visitor_push",
                Notification.SUBSCRIPTION_EXPIRING: "subscription_push",
                Notification.SUBSCRIPTION_EXPIRED: "subscription_push",
                Notification.DOCUMENT_SHARED: "system_push",
                Notification.SYSTEM_ALERT: "system_push",
                Notification.PAYOUT_SUCCESS: "rent_alerts_push",
                Notification.PAYOUT_FAILED: "rent_alerts_push",
                Notification.RENTER_STATUS_CHANGE: "rent_alerts_push",
                Notification.ITR_REMINDER: "system_push",
                Notification.TAX_REMINDER: "system_push",
                Notification.EXTRA_CHARGE_REMINDER: "rent_alerts_push",
            }
            pref_key = type_pref_map.get(notification_type)
            if not pref_key or getattr(pref, pref_key, False):
                return bool(
                    notification_services.send_fcm_notification(
                        user, title, message, notification_type=notification_type
                    )
                )
    except Exception:
        logger.exception(
            "Failed to check push preferences for user %s",
            getattr(user, "pk", None),
        )
    return False


def dispatch_notification(
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
    idempotency_window_minutes: int = 5,
) -> Notification:
    existing = (
        Notification.objects.filter(
            user=user,
            notification_type=notification_type,
            resource_type=resource_type or "",
            resource_id=resource_id or "",
            is_read=False,
            archived=False,
        )
        .filter(
            created_at__gte=timezone.now()
            - timedelta(minutes=idempotency_window_minutes)
        )
        .first()
    )

    if existing:
        return existing

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

    push_ok = _dispatch_push_notification(
        user, title, message, notification_type, channels
    )
    wa_ok = False
    sms_ok = False

    if "whatsapp" not in (channels or []):
        wa_ok = _send_whatsapp(user, message)

    if not wa_ok and "sms" not in (channels or []):
        sms_ok = _send_sms(user, message)

    sent_channels: list[str] = []
    if push_ok:
        sent_channels.append("push")
    if wa_ok:
        sent_channels.append("whatsapp")
    if sms_ok:
        sent_channels.append("sms")

    if sent_channels:
        notification.delivered_at = timezone.now()
        notification.channels = sent_channels
        notification.save(update_fields=["delivered_at", "channels"])

    return notification
