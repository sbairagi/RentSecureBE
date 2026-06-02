"""
Monthly Rent Summary Service

Generates and sends monthly rent collection summaries to property owners.
Includes collected, pending, and defaulter information across all units.
"""

from datetime import date

from django.core.mail import send_mail
from django.db.models import Sum
from django.utils import timezone

from core.models import NotificationPreference
from properties.models import RentRecord


def get_monthly_rent_summary(owner, target_date=None):
    """
    Generate monthly rent collection summary for an owner.

    Args:
        owner: User object (property owner)
        target_date: Date to generate summary for (defaults to today)

    Returns:
        dict with keys: month, year, collected, pending, defaulters, units_data
    """
    if target_date is None:
        target_date = timezone.now().date()

    # Get first and last day of the month
    first_day = target_date.replace(day=1)
    if target_date.month == 12:
        last_day = date(target_date.year + 1, 1, 1).replace(day=1)
    else:
        last_day = date(target_date.year, target_date.month + 1, 1)

    # Filter rent records for this month
    rents = RentRecord.objects.filter(
        owner=owner, rent_month__gte=first_day, rent_month__lt=last_day
    ).select_related("renter", "unit")

    # Calculate aggregates
    collected = (
        rents.filter(payment_status=RentRecord.PaymentStatus.PAID).aggregate(
            total=Sum("amount_paid")
        )["total"]
        or 0
    )

    pending = (
        rents.filter(payment_status=RentRecord.PaymentStatus.PENDING).aggregate(
            total=Sum("amount_paid")
        )["total"]
        or 0
    )

    failed = (
        rents.filter(payment_status=RentRecord.PaymentStatus.FAILED).aggregate(
            total=Sum("amount_paid")
        )["total"]
        or 0
    )

    defaulters = (
        rents.filter(payment_status=RentRecord.PaymentStatus.PENDING)
        .values("renter")
        .distinct()
        .count()
    )

    return {
        "month": target_date.month,
        "year": target_date.year,
        "month_name": target_date.strftime("%B %Y"),
        "collected": float(collected),
        "pending": float(pending),
        "failed": float(failed),
        "defaulters": defaulters,
        "total_records": rents.count(),
    }


def send_monthly_rent_summary_email(owner, target_date=None, send_whatsapp=True):
    """
    Send monthly rent summary to an owner via email and WhatsApp.

    Args:
        owner: User object (property owner)
        target_date: Date to generate summary for
        send_whatsapp: Whether to also send via WhatsApp
    """
    summary = get_monthly_rent_summary(owner, target_date)

    # Build email message
    message_text = _build_summary_message(owner, summary)

    prefs, _ = NotificationPreference.objects.get_or_create(owner=owner)

    sent_any = False

    if prefs.monthly_summary_email and owner.email:
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
            print(f"Failed to send email to {owner.email}: {exc}")

    if send_whatsapp and prefs.monthly_summary_whatsapp and hasattr(owner, "profile"):
        whatsapp_number = getattr(owner.profile, "whatsapp_number", None)
        if whatsapp_number:
            try:
                from notification.services.whatsapp_service import send_whatsapp_message

                result = send_whatsapp_message(whatsapp_number, message_text)
                sent_any = sent_any or bool(result)
            except Exception as exc:
                print(f"Failed to send WhatsApp to {whatsapp_number}: {exc}")

    if not sent_any:
        print(
            f"No monthly summary notification was sent for {owner.email or owner.username}. Preferences: email={prefs.monthly_summary_email}, whatsapp={prefs.monthly_summary_whatsapp}"
        )

    return sent_any


def _build_summary_message(owner, summary):
    """Build formatted summary message."""
    message = (
        f"📊 Monthly Rent Summary – {summary['month_name']}\n\n"
        f"✅ Total Rent Collected: ₹{summary['collected']:,.2f}\n"
        f"⏳ Total Pending: ₹{summary['pending']:,.2f}\n"
        f"❌ Failed Payments: ₹{summary['failed']:,.2f}\n"
        f"👤 Defaulting Renters: {summary['defaulters']}\n"
        f"📋 Total Records Processed: {summary['total_records']}\n"
    )
    return message
