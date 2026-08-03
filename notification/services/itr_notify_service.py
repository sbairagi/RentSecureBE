"""ITR summary notification service.

Sends a WhatsApp text + optional voice note to the property owner
with their financial-year rent summary.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from django.utils.timezone import now

from notification.services.voice_service import generate_voice_note  # nosonar
from notification.services.whatsapp_service import send_whatsapp_audio  # nosonar
from notification.services.whatsapp_service import (
    send_whatsapp_message,  # nosonar; nosonar
)
from rentsecure_be.services.i18n_service import translate_msg  # nosonar

logger = logging.getLogger(__name__)


def get_itr_summary_for_owner(user: Any) -> tuple[int, int, float]:
    """Return ``(fy_start_year, fy_end_year, total_rent)`` for the owner."""
    from django.db.models import Sum

    today = now().date()
    fy_start_year = today.year if today.month >= 4 else today.year - 1
    fy_start = datetime(fy_start_year, 4, 1).date()
    fy_end = datetime(fy_start_year + 1, 3, 31).date()

    rent_records = user.properties_rent_records.filter(
        created_at__date__gte=fy_start,
        created_at__date__lte=fy_end,
        payout_status="SUCCESS",
    )

    total = rent_records.aggregate(total=Sum("amount"))["total"] or 0
    return fy_start_year, fy_start_year + 1, float(total)


def notify_itr_summary(owner: Any) -> None:
    """Send an ITR summary WhatsApp message + voice note to the owner."""
    try:
        fy_start, fy_end, total = get_itr_summary_for_owner(owner)
    except Exception:
        logger.exception("Failed to calculate ITR summary for owner %s", owner.id)
        return

    msg = (
        f"Namaste! Aapka {fy_start}-{fy_end} ka kul kiraya "
        f"₹{total:,.2f} hai. ITR filing ke liye taiyaar rahiye."
    )

    profile = getattr(owner, "profile", None)
    lang = getattr(profile, "language_preference", None) or "en"
    phone = getattr(profile, "whatsapp_number", None) or owner.phone or ""

    try:
        translated_text = translate_msg(msg, lang)
    except Exception:
        logger.exception("Translation failed for ITR summary owner %s", owner.id)
        translated_text = msg

    try:
        if phone:
            send_whatsapp_message(
                phone,
                translated_text,
                user=owner,
                rent_record=None,
            )
    except Exception:
        logger.exception("ITR summary WhatsApp text failed for owner %s", owner.id)

    try:
        audio_path = generate_voice_note(translated_text, lang)
        if audio_path and phone:
            send_whatsapp_audio(
                phone,
                audio_path,
                user=owner,
                rent_record=None,
            )
    except Exception:
        logger.exception("ITR summary WhatsApp audio failed for owner %s", owner.id)
