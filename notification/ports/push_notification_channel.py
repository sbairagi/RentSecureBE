from __future__ import annotations

from typing import Any, Protocol


class PushNotificationChannel(Protocol):
    def send_push_notification(
        self, user: Any, title: str, message: str
    ) -> bool | None: ...
