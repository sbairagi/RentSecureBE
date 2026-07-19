from __future__ import annotations

from typing import Any

from fcm_django.models import FCMDevice  # type: ignore[import-untyped]


class FirebaseAdapter:
    def send_push_notification(
        self, user: Any, title: str, message: str
    ) -> bool | None:
        devices = FCMDevice.objects.filter(user=user, active=True)
        if devices.exists():
            devices.send_message(title=title, body=message)
        return None
