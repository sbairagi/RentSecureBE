"""Owner dashboard summary service.

Generates WhatsApp daily/weekly dashboard summaries for property owners
covering vacant units, pending rent payments, overdue property taxes,
and flagged renters.
"""

from __future__ import annotations

import logging
from typing import TypedDict

from django.db.models import Sum
from django.utils import timezone

from core.models import User, UserProfile

logger = logging.getLogger(__name__)


class OwnerDashboardSummary(TypedDict):
    """Summary payload for an owner's dashboard notification."""

    vacant_units: int
    pending_rent_amount: float
    overdue_taxes: int
    flagged_renters: int


def build_owner_summary(owner: User) -> OwnerDashboardSummary:
    """Build the dashboard summary for the given owner.

    Respects the owner's alert preferences from ``UserProfile`` so
    disabled alert types are omitted from the payload.
    """
    from properties.models import PropertyTaxRecord, Renter, RentRecord, Unit

    today = timezone.now().date()

    try:
        profile = UserProfile.objects.get(user=owner)
    except UserProfile.DoesNotExist:
        profile = None

    if profile is not None and not profile.receive_vacancy_alerts:
        vacant_units = 0
    else:
        vacant_units = Unit.objects.filter(owner=owner, is_vacant=True).count()

    if profile is not None and not profile.receive_rent_alerts:
        pending_rent_amount = 0.0
    else:
        pending_rent_amount = float(
            RentRecord.objects.filter(
                unit__owner=owner,
                status=RentRecord.Status.PENDING,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

    if profile is not None and not profile.receive_tax_alerts:
        overdue_taxes = 0
    else:
        overdue_taxes = PropertyTaxRecord.objects.filter(
            property__owner=owner,
            paid=False,
            due_date__lt=today,
        ).count()

    if profile is not None and not profile.receive_flagged_alerts:
        flagged_renters = 0
    else:
        flagged_renters = Renter.objects.filter(
            unit__owner=owner,
            is_flagged=True,
        ).count()

    return OwnerDashboardSummary(
        vacant_units=vacant_units,
        pending_rent_amount=pending_rent_amount,
        overdue_taxes=overdue_taxes,
        flagged_renters=flagged_renters,
    )


def _get_owner_name(owner: User) -> str:
    return getattr(owner, "full_name", None) or owner.get_full_name() or owner.username


def _get_owner_language(owner: User) -> str:
    try:
        profile = UserProfile.objects.get(user=owner)
        lang = getattr(profile, "language_preference", None)
        if lang:
            return lang
    except UserProfile.DoesNotExist:
        pass
    return "en"


def _get_owner_whatsapp(owner: User) -> str:
    try:
        profile = UserProfile.objects.get(user=owner)
        number = getattr(profile, "whatsapp_number", None)
        if number:
            return number
    except UserProfile.DoesNotExist:
        pass
    return getattr(owner, "whatsapp_number", "") or ""


def _build_summary_message(summary: OwnerDashboardSummary, owner_name: str) -> str:
    """Format the dashboard summary for WhatsApp delivery.

    Only includes sections with non-zero values so owners do not
    receive noisy messages for categories they do not care about.
    """
    lines = [
        f"\U0001f44b Hello {owner_name},",
        "",
        "Here is your RentSecure Summary:",
        "",
    ]
    if summary["vacant_units"]:
        lines.append(f"\U0001f3da Vacant Units: {summary['vacant_units']}")
    if summary["pending_rent_amount"]:
        amount = f"\u20b9{summary['pending_rent_amount']:,.2f}"
        lines.append(f"\U0001f4b0 Pending Rents: {amount}")
    if summary["overdue_taxes"]:
        lines.append(f"\U0001f4c5 Overdue Taxes: {summary['overdue_taxes']}")
    if summary["flagged_renters"]:
        lines.append(f"\U0001f6a9 Flagged Renters: {summary['flagged_renters']}")
    lines.append("")
    lines.append("\U0001f4cc To view more, visit your RentSecure dashboard.")
    return "\n".join(lines)


def _translate(text: str, lang: str) -> str:
    try:
        from rentsecure_be.services.i18n_service import translate_msg

        return translate_msg(text, lang)
    except Exception as exc:
        logger.exception("Failed to translate dashboard summary: %s", exc)
        return text


def _generate_voice_note(text: str, lang: str) -> str:
    try:
        from notification.services.voice_service import generate_voice_note

        return generate_voice_note(text, lang)
    except Exception as exc:
        logger.exception("Failed to generate voice note: %s", exc)
        return ""


def _send_whatsapp_message(phone: str, text: str) -> bool:
    try:
        from notification.services.whatsapp_service import send_whatsapp_message

        return bool(send_whatsapp_message(phone, text))
    except Exception as exc:
        logger.exception("Failed to send WhatsApp to %s: %s", phone, exc)
        return False


def _send_whatsapp_audio(phone: str, audio_path: str) -> bool:
    try:
        from notification.services.whatsapp_service import send_whatsapp_audio

        return bool(send_whatsapp_audio(phone, audio_path))
    except Exception as exc:
        logger.exception("Failed to send WhatsApp audio to %s: %s", phone, exc)
        return False


def send_summary_to_owner(owner: User) -> bool:
    """Build and send the dashboard summary to a single owner via WhatsApp.

    The summary is translated to the owner's preferred language and
    accompanied by a generated voice note when possible.

    Args:
        owner: The property owner to notify.

    Returns:
        ``True`` if the WhatsApp text was sent successfully.
    """
    summary = build_owner_summary(owner)
    name = _get_owner_name(owner)
    lang = _get_owner_language(owner)
    phone = _get_owner_whatsapp(owner)

    if not phone:
        logger.info("Skipping owner %s: no WhatsApp number configured.", owner.username)
        return False

    message = _build_summary_message(summary, name)
    translated = _translate(message, lang)

    text_sent = _send_whatsapp_message(phone, translated)
    if not text_sent:
        return False

    audio_path = _generate_voice_note(translated, lang)
    if audio_path:
        _send_whatsapp_audio(phone, audio_path)

    return True


def run_daily_owner_summaries() -> int:
    """Send dashboard summaries to all property owners.

    Respects each owner's ``UserProfile.alert_frequency`` setting:
    - ``daily``   → send every run
    - ``weekly``  → send only on Mondays
    - ``monthly`` → send only on the 1st of the month

    Returns:
        The number of owners for whom a notification was attempted.
    """
    today = timezone.now().date()
    frequency_map = {
        "daily": True,
        "weekly": today.weekday() == 0,
        "monthly": today.day == 1,
    }

    owners = User.objects.filter(units__isnull=False).distinct()
    count = 0
    for owner in owners:
        try:
            frequency = owner.userprofile.alert_frequency
        except UserProfile.DoesNotExist:
            frequency = "weekly"
        if not frequency_map.get(frequency, False):
            continue
        if send_summary_to_owner(owner):
            count += 1
    return count


def run_weekly_owner_summaries() -> int:
    """Send weekly dashboard summaries to all property owners.

    Returns:
        The number of owners for whom a notification was attempted.
    """
    return run_daily_owner_summaries()
