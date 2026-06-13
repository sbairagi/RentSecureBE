"""Renter Onboarding Service.

Handles sending onboarding invites and managing the renter self-service flow.
All public functions are fully typed and idempotent where appropriate.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from notification.services.whatsapp_service import send_whatsapp_message
from properties.models import Renter
from properties.utils.onboarding_utils import generate_onboarding_link

if TYPE_CHECKING:
    pass  # Renter already imported at module level

logger = logging.getLogger(__name__)


def send_renter_onboarding_invite(renter: Renter) -> bool:
    """Send a WhatsApp onboarding invite to a renter.

    Args:
        renter: The :class:`Renter` instance to invite.

    Returns:
        ``True`` if the invite was delivered, ``False`` otherwise.
    """
    if not renter.phone:
        logger.error("Renter %s has no phone number. Cannot send invite.", renter.id)
        return False

    try:
        link: str = generate_onboarding_link(renter)

        owner_name: str = (
            renter.unit.building.owner.full_name  # type: ignore[union-attr]
            if getattr(renter.unit, "building", None)
            else "Your landlord"
        )
        unit_info: str = (
            f"{renter.unit.unit} - {renter.unit.building.name}"  # type: ignore[union-attr]
            if getattr(renter.unit, "building", None)
            else renter.unit.unit
        )

        message: str = (
            f"👋 Welcome to RentSecure!\n\n"
            f"Your landlord {owner_name} has invited you to complete "
            f"your onboarding.\n\n"
            f"📍 Property: {unit_info}\n"
            f"💰 Monthly Rent: ₹{renter.rent_amount}\n\n"
            f"Please complete your KYC verification here:\n"
            f"{link}\n\n"
            f"This helps us ensure secure rent transactions for both "
            f"you and your landlord."
        )

        result: bool = bool(send_whatsapp_message(renter.phone, message))

        if result:
            renter.onboarding_status = Renter.OnboardingStatus.LINK_SENT
            renter.save(update_fields=["onboarding_status"])
            logger.info(
                "Onboarding invite sent to renter %s (%s)", renter.id, renter.phone
            )
            return True

        logger.warning(
            "Failed to send WhatsApp to renter %s (%s)", renter.id, renter.phone
        )
        return False
    except Exception as exc:
        logger.exception(
            "Error sending onboarding invite to renter %s: %s", renter.id, exc
        )
        return False


def send_renter_onboarding_reminder(renter: Renter) -> bool:
    """Send a reminder to a renter who received an onboarding link but never finished it.

    Args:
        renter: The :class:`Renter` instance.

    Returns:
        ``True`` if the reminder was sent successfully.
    """
    if renter.onboarding_status != Renter.OnboardingStatus.LINK_SENT:
        logger.warning(
            "Renter %s is not in LINK_SENT status. Skipping reminder.", renter.id
        )
        return False

    if not renter.phone:
        return False

    try:
        link: str = generate_onboarding_link(renter)
        message: str = (
            f"⏰ Reminder: Your onboarding is pending!\n\n"
            f"Please complete your KYC verification to activate your account:\n"
            f"{link}\n\n"
            f"Questions? Contact your landlord or our support team."
        )

        result: bool = bool(send_whatsapp_message(renter.phone, message))
        logger.info("Onboarding reminder sent to renter %s", renter.id)
        return result
    except Exception as exc:
        logger.exception("Error sending reminder to renter %s: %s", renter.id, exc)
        return False


def notify_owner_renter_completed_kyc(renter: Renter) -> bool:
    """Notify the owner that a renter has completed KYC.

    Args:
        renter: The :class:`Renter` whose owner should be notified.

    Returns:
        ``True`` if the WhatsApp was sent, otherwise ``False``.
    """
    from notification.services.whatsapp_service import (
        send_whatsapp_message as _send_whatsapp,
    )

    owner = getattr(renter.unit, "owner", None)
    if owner is None:
        logger.warning("Renter %s has no associated owner.", renter.id)
        return False

    profile = getattr(owner, "profile", None)
    whatsapp_number: str | None = getattr(profile, "whatsapp_number", None) if profile else None
    if not whatsapp_number:
        logger.warning(
            "Owner %s has no WhatsApp number. Cannot send notification.", owner.id
        )
        return False

    try:
        message: str = (
            f"✅ Great news! Renter {renter.name} has completed KYC "
            f"verification.\n\n"
            f"📍 Unit: {renter.unit.unit}\n"
            f"💰 Rent: ₹{renter.rent_amount}\n\n"
            f"Their account is now activated. You can monitor rent "
            f"payments from your dashboard."
        )

        result: bool = bool(_send_whatsapp(whatsapp_number, message))
        logger.info("KYC completion notification sent to owner %s", owner.id)
        return result
    except Exception as exc:
        logger.exception(
            "Error notifying owner %s about renter KYC: %s", owner.id, exc
        )
        return False
