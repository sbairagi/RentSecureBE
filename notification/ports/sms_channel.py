from __future__ import annotations

from typing import Protocol


class SMSChannel(Protocol):
    def send_sms(self, phone: str, message: str) -> bool: ...
