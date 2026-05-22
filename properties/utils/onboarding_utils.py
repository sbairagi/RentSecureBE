"""
Renter Onboarding Utilities

Generates secure onboarding links and tokens for renter self-service KYC.
"""

import secrets

from django.conf import settings
from django.utils import timezone


def generate_onboarding_token(renter):
    """
    Generate a unique, secure token for renter onboarding.

    Args:
        renter: Renter instance

    Returns:
        str: Secure random token
    """
    token = secrets.token_urlsafe(32)
    renter.onboarding_token = token
    renter.onboarding_link_sent_at = timezone.now()
    renter.save(update_fields=['onboarding_token', 'onboarding_link_sent_at'])
    return token


def generate_onboarding_link(renter):
    """
    Generate a complete onboarding link for renter.

    Link format: https://app.rentsecure.com/onboard-renter/<token>/

    Args:
        renter: Renter instance

    Returns:
        str: Full onboarding URL
    """
    if not renter.onboarding_token:
        generate_onboarding_token(renter)

    token = renter.onboarding_token
    base_url = settings.FRONTEND_URL or "https://app.rentsecure.com"
    return f"{base_url}/onboard-renter/{token}/"


def verify_onboarding_token(token):
    """
    Verify that an onboarding token is valid and belongs to an active renter.

    Args:
        token: Onboarding token to verify

    Returns:
        Renter instance if valid, None otherwise
    """
    from properties.models import Renter

    try:
        renter = Renter.objects.get(onboarding_token=token)
        # Ensure token hasn't expired (e.g., 90 days)
        from datetime import timedelta
        if renter.onboarding_link_sent_at:
            expiry_date = renter.onboarding_link_sent_at + timedelta(days=90)
            if timezone.now() > expiry_date:
                return None
        return renter
    except Renter.DoesNotExist:
        return None


def mark_onboarding_completed(renter):
    """
    Mark renter's onboarding as completed.

    Args:
        renter: Renter instance
    """
    from properties.models import Renter

    renter.onboarding_status = Renter.OnboardingStatus.COMPLETED
    renter.save(update_fields=['onboarding_status'])


def mark_kyc_verified(renter):
    """
    Mark renter's KYC as verified.

    Args:
        renter: Renter instance
    """
    from properties.models import Renter

    renter.kyc_status = Renter.KYCStatus.VERIFIED
    renter.save(update_fields=['kyc_status'])
