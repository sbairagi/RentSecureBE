from __future__ import annotations

import logging
from typing import Any

from firebase_admin import messaging

from django.utils import timezone

from notification.models import DeviceToken

logger = logging.getLogger(__name__)


def send_fcm_notification(
    user: Any,
    title: str,
    body: str,
    data: dict | None = None,
    priority: str = "high",
    notification_type: str = "",
) -> bool:
    try:
        tokens = list(
            DeviceToken.objects.filter(user=user, active=True, fcm_token__isnull=False)
            .exclude(fcm_token="")
            .values_list("fcm_token", flat=True)
        )

        if not tokens:
            logger.info("No active FCM tokens for user %s", user.pk)
            return False

        android_config = messaging.AndroidConfig(
            priority=priority,
            notification=messaging.AndroidNotification(
                channel_id="default",
                sound="default",
            ),
        )
        apns_config = messaging.APNSConfig(
            headers={"apns-priority": "10" if priority == "high" else "5"},
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    sound="default",
                    badge=1,
                ),
            ),
        )

        for token in tokens:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(title=title, body=body),
                    data={**(data or {}), "notification_type": notification_type},
                    token=token,
                    android=android_config,
                    apns=apns_config,
                )
                response = messaging.send(message)
                logger.info("FCM sent to user %s: %s", user.pk, response)

                DeviceToken.objects.filter(fcm_token=token).update(
                    last_used=timezone.now()
                )
            except messaging.UnregisteredError:
                DeviceToken.objects.filter(fcm_token=token).update(active=False)
            except Exception as e:
                logger.exception("Failed to send FCM to token %s: %s", token[:8], e)

        return True
    except Exception as e:
        logger.exception("Failed to send FCM notification to user %s: %s", user.pk, e)
        return False


def send_push_notification(user: Any, title: str, message: str) -> bool | None:
    return send_fcm_notification(user, title, message)
