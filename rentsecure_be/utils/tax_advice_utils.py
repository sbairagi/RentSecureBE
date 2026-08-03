"""Tax advisory utilities for personalized tax saving suggestions.

All public functions declare precise parameter and return types so they
can be invoked safely from DRF views, services, and management commands.
"""

# mypy: disable-error-code="import-untyped"

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db.models import Sum

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


def get_rent_income(user: AbstractUser) -> int:
    """Return the total paid rent received across all units owned by the user.

    Args:
        user: Property owner whose rent income is being calculated.

    Returns:
        Total rent amount (as integer) received for paid rent records.
    """
    from properties.models.rent_record_models import RentRecord  # nosonar

    total = (
        RentRecord.objects.filter(unit__owner=user, status="PAID").aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )
    return int(total)


def suggest_tax_savings(user: AbstractUser) -> list[dict[str, Any]]:
    """Generate personalized tax saving suggestions based on the user's profile.

    Recommendations cover:
    - Section 80C (ELSS, PPF, LIC)
    - Section 80D (Health Insurance)
    - Section 24(b) (Home Loan Interest)
    - Section 80GG (Rent Paid / No HRA)

    Args:
        user: Authenticated user whose profile data drives the suggestions.

    Returns:
        A list of suggestion dicts, each containing ``section``, ``tip``,
        and ``potential_saving`` keys.
    """
    try:
        from core.models import UserProfile

        profile = user.userprofile
    except UserProfile.DoesNotExist:
        return []

    suggestions: list[dict[str, Any]] = []

    # 80C - Max 1.5L
    elss_invested = profile.elss_investment or 0
    if elss_invested < 150000:
        remaining = min(150000 - elss_invested, 150000)
        suggestions.append(
            {
                "section": "80C",
                "tip": (
                    "You can invest up to ₹1.5L in ELSS, PPF, or LIC for 80C benefit."
                ),
                "potential_saving": int(remaining * 0.2),
            }
        )

    # 80D - Health Insurance
    if not profile.has_health_insurance:
        suggestions.append(
            {
                "section": "80D",
                "tip": (
                    "Buy health insurance for family to save up to ₹25,000 under 80D."
                ),
                "potential_saving": 25000 * 0.2,
            }
        )

    # Home Loan Interest (Section 24b)
    home_loan_interest = profile.home_loan_interest or 0
    if home_loan_interest > 0:
        suggestions.append(
            {
                "section": "24(b)",
                "tip": (
                    f"You're eligible for ₹{home_loan_interest} deduction "
                    "on home loan interest."
                ),
                "potential_saving": int(min(home_loan_interest, 200000) * 0.2),
            }
        )

    # Rent Paid / No HRA
    if not profile.receives_hra and (profile.rent_paid or 0) > 0:
        suggestions.append(
            {
                "section": "80GG",
                "tip": "You can claim deduction for rent paid under section 80GG.",
                "potential_saving": 60000 * 0.2,
            }
        )

    return suggestions
