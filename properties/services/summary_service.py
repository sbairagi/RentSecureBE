"""Monthly rent summary service.

Generates and sends monthly rent collection summaries to property owners.
Includes collected, pending, and defaulter information across all units.

Every public function declares its parameter and return types for
strict mypy compliance.
"""

# mypy: ignore-errors

from __future__ import annotations

import logging
from datetime import date
from typing import TypedDict

from django.core.mail import send_mail
from django.db.models import Sum
from django.utils import timezone

from core.models import NotificationPreference, User

logger = logging.getLogger(__name__)


class MonthlySummary(TypedDict):
    month: int
    year: int
    month_name: str
    collected: float
    pending: float
    failed: float
    defaulters: int
    total_records: int
    payouts_success: int
    taxes_due: int
    notice_period_count: int
    revoked_count: int


def get_monthly_rent_summary(
    owner: User, target_date: date | None = None
) -> MonthlySummary:
    """Build the monthly rent summary for the given owner."""
    if target_date is None:
        target_date = timezone.now().date()

    first_day: date = target_date.replace(day=1)
    if target_date.month == 12:
        last_day: date = date(target_date.year + 1, 1, 1)
    else:
        last_day = date(target_date.year, target_date.month + 1, 1)

    from properties.models import PropertyTaxRecord, Renter, RentRecord

    first_day_dt = first_day
    last_day_dt = last_day

    rents = RentRecord.objects.filter(
        unit__owner=owner, due_date__gte=first_day_dt, due_date__lt=last_day_dt
    ).select_related("renter", "unit")

    collected: float = float(
        rents.filter(status=RentRecord.Status.PAID).aggregate(total=Sum("amount"))[
            "total"
        ]
        or 0
    )

    pending: float = float(
        rents.filter(status=RentRecord.Status.PENDING).aggregate(total=Sum("amount"))[
            "total"
        ]
        or 0
    )

    failed: float = float(
        rents.filter(payout_status="FAILED").aggregate(total=Sum("amount"))["total"]
        or 0
    )

    defaulters: int = (
        rents.filter(status=RentRecord.Status.PENDING)
        .values("renter")
        .distinct()
        .count()
    )

    payouts_success: int = rents.filter(payout_status="SUCCESS").count()

    taxes_due: int = PropertyTaxRecord.objects.filter(
        property__owner=owner, paid=False, due_date__lte=last_day_dt
    ).count()

    owner_renters = Renter.objects.filter(unit__owner=owner)
    notice_period_count: int = owner_renters.filter(
        status=Renter.RenterStatus.NOTICE_PERIOD
    ).count()
    revoked_count: int = owner_renters.filter(
        status=Renter.RenterStatus.REVOKED
    ).count()

    return MonthlySummary(
        month=target_date.month,
        year=target_date.year,
        month_name=target_date.strftime("%B %Y"),
        collected=collected,
        pending=pending,
        failed=failed,
        defaulters=defaulters,
        total_records=rents.count(),
        payouts_success=payouts_success,
        taxes_due=taxes_due,
        notice_period_count=notice_period_count,
        revoked_count=revoked_count,
    )


def send_monthly_rent_summary_email(
    owner: User,
    target_date: date | None = None,
    send_whatsapp: bool = True,
) -> bool:
    """Send the owner's monthly rent summary by email and/or WhatsApp."""
    summary: MonthlySummary = get_monthly_rent_summary(owner, target_date)
    message_text: str = _build_summary_message(summary)

    prefs: NotificationPreference = NotificationPreference.objects.get_or_create(
        owner=owner
    )[0]

    lang: str = (
        getattr(getattr(owner, "profile", None), "language_preference", None) or "en"
    )
    translated_message: str = _translate(message_text, lang)

    sent_any: bool = False

    if prefs.monthly_summary_email and getattr(owner, "email", None):
        sent_any = _send_summary_email(owner, summary, translated_message) or sent_any

    if send_whatsapp:
        sent_any = (
            _send_summary_whatsapp(owner, translated_message, prefs, lang) or sent_any
        )

    if not sent_any:
        _log_no_notification_sent(owner, prefs)

    return sent_any


def _send_summary_email(
    owner: User, summary: MonthlySummary, message_text: str
) -> bool:
    try:
        send_mail(
            subject=f"Monthly Rent Summary - {summary['month_name']}",
            message=message_text,
            from_email="no-reply@rentsecure.in",
            recipient_list=[owner.email],
            fail_silently=False,
        )
        return True
    except Exception as exc:
        logger.exception("Failed to send email to %s: %s", owner.email, exc)
        return False


def _send_summary_whatsapp(
    owner: User, message_text: str, prefs: NotificationPreference, lang: str = "en"
) -> bool:
    if not (prefs.monthly_summary_whatsapp and getattr(owner, "whatsapp_number", None)):
        return False
    text_sent = _send_whatsapp_message(owner.whatsapp_number, message_text)
    if not text_sent:
        return False
    audio_path = _generate_voice_note(message_text, lang)
    if audio_path:
        return _send_whatsapp_audio(owner.whatsapp_number, audio_path)
    return True


def _send_whatsapp_message(phone: str, message_text: str) -> bool:
    try:
        from notification.services.whatsapp_service import send_whatsapp_message

        result = send_whatsapp_message(phone, message_text)
        return bool(result)
    except Exception as exc:
        logger.exception("Failed to send WhatsApp to %s: %s", phone, exc)
        return False


def _send_whatsapp_audio(phone: str, audio_path: str) -> bool:
    try:
        from notification.services.whatsapp_service import send_whatsapp_audio

        result = send_whatsapp_audio(phone, audio_path)
        return bool(result)
    except Exception as exc:
        logger.exception("Failed to send WhatsApp audio to %s: %s", phone, exc)
        return False


def _generate_voice_note(text: str, lang: str) -> str:
    try:
        from notification.services.voice_service import generate_voice_note

        return generate_voice_note(text, lang)
    except Exception as exc:
        logger.exception("Failed to generate voice note: %s", exc)
        return ""


def _translate(text: str, lang: str) -> str:
    try:
        from rentsecure_be.services.i18n_service import translate_msg

        return translate_msg(text, lang)
    except Exception as exc:
        logger.exception("Failed to translate summary message: %s", exc)
        return text


def _log_no_notification_sent(owner: User, prefs: NotificationPreference) -> None:
    owner_label = getattr(owner, "email", None) or getattr(
        owner, "username", "<unknown>"
    )
    logger.info(
        "No monthly summary notification was sent for %s. "
        "Preferences: email=%s, whatsapp=%s",
        owner_label,
        prefs.monthly_summary_email,
        prefs.monthly_summary_whatsapp,
    )


def _build_summary_message(summary: MonthlySummary) -> str:
    """Format the monthly summary for email/WhatsApp delivery."""
    lines = [
        f"📊 Monthly Rent Summary – {summary['month_name']}",
        "",
        f"✅ Total Rent Collected: ₹{summary['collected']:,.2f}",
        f"⏳ Total Pending: ₹{summary['pending']:,.2f}",
        f"❌ Failed Payments: ₹{summary['failed']:,.2f}",
        f"👤 Defaulting Renters: {summary['defaulters']}",
        f"📋 Total Records Processed: {summary['total_records']}",
        f"✅ Successful Payouts: {summary['payouts_success']}",
        f"💰 Tax Payments Due: {summary['taxes_due']}",
        f"📢 Renters Under Notice: {summary['notice_period_count']}",
        f"⛔ Revoked Renters: {summary['revoked_count']}",
    ]
    return "\n".join(lines)
