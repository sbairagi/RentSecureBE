"""Rent monitor service.

Tracks renter payment behavior and automatically flags or revokes
renters based on missed payments.
"""

from __future__ import annotations

import logging
from typing import Any

from django.utils import timezone

from properties.models import Caretaker, Renter, RentRecord

logger = logging.getLogger(__name__)


def check_renter_defaulter_status() -> int:
    """Evaluate all active renters for missed payments.

    Returns the number of renters updated.
    """
    active_renters = Renter.objects.filter(
        status=Renter.RenterStatus.ACTIVE
    ).select_related("unit", "user")

    updated = 0
    for renter in active_renters:
        missed_count = RentRecord.objects.filter(
            renter=renter,
            status=RentRecord.Status.PENDING,
        ).count()

        if missed_count >= 3 and renter.status != Renter.RenterStatus.REVOKED:
            renter.status = Renter.RenterStatus.REVOKED
            renter.missed_rents = missed_count
            renter.is_agreement_revoked = True
            renter.revoked_by_owner = False
            renter.revoked_on = timezone.now()
            renter.revocation_reason = (
                "Automatically revoked after 3 missed rent payments."
            )
            renter.save()
            _notify_revoke(renter)
            updated += 1

        elif missed_count == 2 and renter.status != Renter.RenterStatus.NOTICE_PERIOD:
            renter.status = Renter.RenterStatus.NOTICE_PERIOD
            renter.missed_rents = missed_count
            renter.is_flagged = True
            renter.flagged_reason = "2 missed rent payments."
            renter.save()
            _notify_notice_period(renter)
            updated += 1

    return updated


def _notify_revoke(renter: Renter) -> None:
    msg = (
        "❌ Your rent agreement has been revoked because you missed " "3 rent payments."
    )
    _notify_all_parties(renter, msg)


def _notify_notice_period(renter: Renter) -> None:
    msg = (
        "⚠️ You have missed 2 rent payments. "
        "Your agreement may be cancelled if rent is not paid on time."
    )
    _notify_all_parties(renter, msg)


def _notify_all_parties(renter: Renter, message: str) -> None:
    lang = _renter_lang(renter)
    renter_user = getattr(renter, "user", None)
    phone = renter.whatsapp_number or getattr(renter_user, "whatsapp_number", None)
    if phone:
        _notify_user(phone, message, lang, renter_user, context="renter")

    owner = renter.unit.owner
    owner_phone = getattr(owner, "whatsapp_number", None) or getattr(
        getattr(owner, "profile", None), "whatsapp_number", None
    )
    if owner_phone:
        owner_lang = (
            getattr(getattr(owner, "profile", None), "language_preference", None)
            or "en"
        )
        _notify_user(owner_phone, message, owner_lang, owner, context="owner")

    caretakers = Caretaker.objects.filter(
        unit=renter.unit, is_active=True
    ).select_related("user")
    for caretaker in caretakers:
        caretaker_user = caretaker.user
        if not caretaker_user:
            continue

        caretaker_phone = getattr(caretaker_user, "whatsapp_number", None) or getattr(
            getattr(caretaker_user, "profile", None), "whatsapp_number", None
        )
        if not caretaker_phone:
            continue

        caretaker_profile = getattr(caretaker_user, "profile", None)
        caretaker_lang = getattr(caretaker_profile, "language_preference", None) or "en"
        _notify_user(
            caretaker_phone,
            message,
            caretaker_lang,
            caretaker_user,
            context="caretaker",
        )


def _notify_user(
    phone: str,
    message: str,
    lang: str,
    user: Any,
    context: str,
) -> None:
    try:
        from rentsecure_be.services.i18n_service import translate_msg

        translated = translate_msg(message, lang)
    except Exception:
        translated = message

    try:
        from notification.services.whatsapp_service import send_whatsapp_message

        send_whatsapp_message(
            phone,
            translated,
            user=user,
            rent_record=None,
        )
    except Exception:
        logger.exception(
            "Failed to send WhatsApp message to %s %s",
            context,
            getattr(user, "pk", "unknown"),
        )

    try:
        from notification.services.voice_service import generate_voice_note
        from notification.services.whatsapp_service import send_whatsapp_audio

        audio_path = generate_voice_note(translated, lang)
        if audio_path:
            send_whatsapp_audio(
                phone,
                audio_path,
                user=user,
                rent_record=None,
            )
    except Exception:
        logger.exception(
            "Failed to send voice note to %s %s",
            context,
            getattr(user, "pk", "unknown"),
        )


def _renter_lang(renter: Renter) -> str:
    profile = getattr(getattr(renter, "user", None), "profile", None)
    return getattr(profile, "language_preference", None) or "en"
