"""CA partner matchmaking service.

Matches authenticated users with verified Chartered Accountants based on
city, NRI status, and investment income profile.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from finance.models import CAPartner

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


def match_ca(user: AbstractUser) -> CAPartner | None:
    """Return the best available CA partner for the given user.

    Matching rules:
    - NRI users are matched with ``NRI_TAX`` specialists.
    - Users with ``total_investment_income`` > 100000 are matched with
      ``INVESTMENT_TAX`` specialists.
    - All other users are matched with ``ITR_FILING`` specialists.

    City matching is case-insensitive and requires the user profile to have
    a non-empty ``city`` value.

    Args:
        user: Authenticated user seeking a CA match.

    Returns:
        The highest-rated available ``CAPartner`` for the user's profile,
        or ``None`` if no match is found.
    """
    try:
        from core.models import UserProfile

        profile = user.userprofile
    except UserProfile.DoesNotExist:
        return None

    if not profile.city:
        return None

    specialization = "ITR_FILING"

    if profile.is_nri:
        specialization = "NRI_TAX"
    elif (profile.total_investment_income or 0) > 100000:
        specialization = "INVESTMENT_TAX"

    return (
        CAPartner.objects.filter(
            city__iexact=profile.city,
            specialization=specialization,
            available=True,
        )
        .order_by("-rating")
        .first()
    )
