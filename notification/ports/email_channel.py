from __future__ import annotations

from typing import Protocol


class EmailChannel(Protocol):
    def send_email(
        self,
        subject: str,
        message: str,
        recipient_list: list[str],
        from_email: str | None = None,
        attachments: list[tuple[str, bytes, str]] | None = None,
    ) -> bool: ...
