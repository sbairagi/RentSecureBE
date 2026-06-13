"""Monthly rent summary service.

Generates and sends monthly rent collection summaries to property owners.
Includes collected, pending, and defaulter information across all units.

Every public function declares its parameter and return types for
strict mypy compliance.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING, TypedDict

from django.core.mail import send_mail
from django.db.models import Sum
from django.utils import timezone

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

    from core.models import NotificationPreference

logger = logging.getLogger(__name__)


class MonthlySummary(TypedDict):
    """Typed shape for the result of :func:`get_monthly_rent_summary`."""

    month: int
    year: int
    month_name: str
    collected: float
    pending: float
    failed: float
    defaulters: int
    total_records: int


def get_monthly_rent_summary(
    owner: AbstractUser, target_date: date | None = None
) -> MonthlySummary:
    """Build the monthly rent summary for the given owner.

    Args:
        owner: The owning user.
        target_date: Date within the target month. Defaults to today.

    Returns:
        A :class:`MonthlySummary` payload aggregating the month's rent.
    """
    if target_date is None:
        target_date = timezone.now().date()

    first_day: date = target_date.replace(day=1)
    if target_date.month == 12:
        last_day: date = date(target_date.year + 1, 1, 1)
    else:
        last_day = date(target_date.year, target_date.month + 1, 1)

    from properties.models import RentRecord

    rents = RentRecord.objects.filter(
        owner=owner, rent_month__gte=first_day, rent_month__lt=last_day
    ).select_related("renter", "unit")

    collected: float = float(
        rents.filter(payment_status=RentRecord.PaymentStatus.PAID).aggregate(
            total=Sum("amount_paid")
        )["total"]
        or 0
    )

    pending: float = float(
        rents.filter(payment_status=RentRecord.PaymentStatus.PENDING).aggregate(
            total=Sum("amount_paid")
        )["total"]
        or 0
    )

    failed: float = float(
        rents.filter(payment_status=RentRecord.PaymentStatus.FAILED).aggregate(
            total=Sum("amount_paid")
        )["total"]
        or 0
    )

    defaulters: int = (
        rents.filter(payment_status=RentRecord.PaymentStatus.PENDING)
        .values("renter")
        .distinct()
        .count()
    )

    return MonthlySummary(
        month=target_date.month,
        year=target_date.year,
        month_name=target_date.strftime("%B %Y"),
        collected=collected,
        pending=pending,
        failed=failed,
        defaulters=defaulters,
        total_records=rents.count(),
    )


def send_monthly_rent_summary_email(
    owner: AbstractUser,
    target_date: date | None = None,
    send_whatsapp: bool = True,
) -> bool:
    """Send the owner's monthly rent summary by email and/or WhatsApp.

    Args:
        owner: The owning user.
        target_date: Optional date within the target month.
        send_whatsapp: When ``True``, also send via WhatsApp if the owner
            has opted-in.

    Returns:
        ``True`` if at least one channel succeeded, otherwise ``False``.
    """
    summary: MonthlySummary = get_monthly_rent_summary(owner, target_date)
    message_text: str = _build_summary_message(summary)

    prefs: NotificationPreference = NotificationPreference.objects.get_or_create(
        owner=owner
    )[0]

    sent_any: bool = False

    if prefs.monthly_summary_email and getattr(owner, "email", None):
        try:
            send_mail(
                subject=f"Monthly Rent Summary - {summary['month_name']}",
                message=message_text,
                from_email="no-reply@rentsecure.in",
                recipient_list=[owner.email],
                fail_silently=False,
            )
            sent_any = True
        except Exception as exc:
            logger.exception("Failed to send email to %s: %s", owner.email, exc)

    if send_whatsapp and prefs.monthly_summary_whatsapp and hasattr(owner, "profile"):
        whatsapp_number = getattr(owner.profile, "whatsapp_number", None)
        if whatsapp_number:
            try:
                from notification.services.whatsapp_service import (
                    send_whatsapp_message,
                )

                result = send_whatsapp_message(whatsapp_number, message_text)
                sent_any = sent_any or bool(result)
            except Exception as exc:
                logger.exception(
                    "Failed to send WhatsApp to %s: %s", whatsapp_number, exc
                )

    if not sent_any:
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

    return sent_any


def _build_summary_message(summary: MonthlySummary) -> str:
    """Format the monthly summary for email/WhatsApp delivery."""
    return (
        f"📊 Monthly Rent Summary – {summary['month_name']}\n\n"
        f"✅ Total Rent Collected: ₹{summary['collected']:,.2f}\n"
        f"⏳ Total Pending: ₹{summary['pending']:,.2f}\n"
        f"❌ Failed Payments: ₹{summary['failed']:,.2f}\n"
        f"👤 Defaulting Renters: {summary['defaulters']}\n"
        f"📋 Total Records Processed: {summary['total_records']}\n"
    )
