"""
Renter Onboarding Service

Handles sending onboarding invites and managing the renter self-service flow.
"""

import logging
from django.utils import timezone
from notification.services.whatsapp_service import send_whatsapp_message
from properties.utils.onboarding_utils import generate_onboarding_link
from properties.models import Renter

logger = logging.getLogger(__name__)


def send_renter_onboarding_invite(renter):
    """
    Send WhatsApp invite to renter with secure onboarding link.
    
    Args:
        renter: Renter instance to invite
        
    Returns:
        bool: True if invite was sent, False otherwise
    """
    if not renter.phone:
        logger.error(f"Renter {renter.id} has no phone number. Cannot send invite.")
        return False
    
    try:
        # Generate onboarding link
        link = generate_onboarding_link(renter)
        
        # Build message
        owner_name = renter.unit.building.owner.full_name if renter.unit.building else "Your landlord"
        unit_info = f"{renter.unit.unit} - {renter.unit.building.name}" if renter.unit.building else renter.unit.unit
        
        message = (
            f"👋 Welcome to RentSecure!\n\n"
            f"Your landlord {owner_name} has invited you to complete your onboarding.\n\n"
            f"📍 Property: {unit_info}\n"
            f"💰 Monthly Rent: ₹{renter.rent_amount}\n\n"
            f"Please complete your KYC verification here:\n"
            f"{link}\n\n"
            f"This helps us ensure secure rent transactions for both you and your landlord."
        )
        
        # Send WhatsApp
        result = send_whatsapp_message(renter.phone, message)
        
        if result:
            # Update status
            renter.onboarding_status = Renter.OnboardingStatus.LINK_SENT
            renter.save(update_fields=['onboarding_status'])
            logger.info(f"Onboarding invite sent to renter {renter.id} ({renter.phone})")
            return True
        else:
            logger.warning(f"Failed to send WhatsApp to renter {renter.id} ({renter.phone})")
            return False
            
    except Exception as exc:
        logger.exception(f"Error sending onboarding invite to renter {renter.id}: {exc}")
        return False


def send_renter_onboarding_reminder(renter):
    """
    Send a reminder to renter who received onboarding link but hasn't completed it.
    
    Args:
        renter: Renter instance
        
    Returns:
        bool: True if reminder was sent
    """
    if renter.onboarding_status != Renter.OnboardingStatus.LINK_SENT:
        logger.warning(f"Renter {renter.id} is not in LINK_SENT status. Skipping reminder.")
        return False
    
    if not renter.phone:
        return False
    
    try:
        link = generate_onboarding_link(renter)
        message = (
            f"⏰ Reminder: Your onboarding is pending!\n\n"
            f"Please complete your KYC verification to activate your account:\n"
            f"{link}\n\n"
            f"Questions? Contact your landlord or our support team."
        )
        
        result = send_whatsapp_message(renter.phone, message)
        logger.info(f"Onboarding reminder sent to renter {renter.id}")
        return result
        
    except Exception as exc:
        logger.exception(f"Error sending reminder to renter {renter.id}: {exc}")
        return False


def notify_owner_renter_completed_kyc(renter):
    """
    Notify owner when renter completes KYC.
    
    Args:
        renter: Renter instance
    """
    from notification.services.whatsapp_service import send_whatsapp_message
    
    owner = renter.unit.owner
    
    if not hasattr(owner, 'profile') or not owner.profile.whatsapp_number:
        logger.warning(f"Owner {owner.id} has no WhatsApp number. Cannot send notification.")
        return False
    
    try:
        message = (
            f"✅ Great news! Renter {renter.name} has completed KYC verification.\n\n"
            f"📍 Unit: {renter.unit.unit}\n"
            f"💰 Rent: ₹{renter.rent_amount}\n\n"
            f"Their account is now activated. You can monitor rent payments from your dashboard."
        )
        
        result = send_whatsapp_message(owner.profile.whatsapp_number, message)
        logger.info(f"KYC completion notification sent to owner {owner.id}")
        return result
        
    except Exception as exc:
        logger.exception(f"Error notifying owner {owner.id} about renter KYC: {exc}")
        return False
