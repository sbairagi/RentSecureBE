from __future__ import annotations

from django.conf import settings
from django.core.mail import EmailMessage


class EmailAdapter:
    def send_email(
        self,
        subject: str,
        message: str,
        recipient_list: list[str],
        from_email: str | None = None,
        attachments: list[tuple[str, bytes, str]] | None = None,
    ) -> bool:
        try:
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=from_email or getattr(settings, "DEFAULT_FROM_EMAIL", None),
                to=recipient_list,
            )
            if attachments:
                for filename, content, content_type in attachments:
                    email.attach(filename, content, content_type)
            email.send(fail_silently=False)
            return True
        except Exception:
            return False
