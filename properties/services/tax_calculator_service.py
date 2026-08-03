"""Tax and HRA calculation utilities for ITR features."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_STANDARD_DEDUCTION = Decimal("50000")
DEFAULT_REPAIRS_LIMIT = Decimal("30000")
DEFAULT_REPAIRS_RATE = Decimal("0.30")


class InvalidInputError(Exception):
    """Raised when calculation inputs are invalid."""


def _to_decimal(value: Any, field: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (TypeError, ValueError) as exc:
        raise InvalidInputError(
            f"Invalid numeric value for '{field}': {value!r}"
        ) from exc


def calculate_hra_exemption(
    salary: Any,
    rent_paid: Any,
    city_type: str = "non_metro",
    hra_received: Any = 0,
) -> Decimal:
    """Calculate HRA exemption using the least-of-three rule.

    Returns:
        Decimal: eligible HRA exemption amount, never negative.
    """
    salary_dec = _to_decimal(salary, "salary")
    rent_paid_dec = _to_decimal(rent_paid, "rent_paid")
    hra_received_dec = _to_decimal(hra_received, "hra_received")

    if salary_dec < 0 or rent_paid_dec < 0 or hra_received_dec < 0:
        raise InvalidInputError(
            "Salary, rent_paid, and hra_received must be non-negative."
        )

    city_type_lower = (city_type or "non_metro").lower()
    metro_cities = {
        "metro",
        "urban",
        "mumbai",
        "delhi",
        "bangalore",
        "chennai",
        "kolkata",
        "hyderabad",
    }
    if city_type_lower in metro_cities:
        metro_ratio = Decimal("0.50")
    else:
        metro_ratio = Decimal("0.40")

    basic_cap = salary_dec * metro_ratio
    rent_minus_10_percent = rent_paid_dec - (salary_dec * Decimal("0.10"))
    actual_hra = hra_received_dec

    eligible = min(basic_cap, rent_minus_10_percent, actual_hra)
    return max(eligible, Decimal("0"))


def calculate_standard_deduction() -> Decimal:
    """Return the standard deduction for salaried ITR filers."""
    return DEFAULT_STANDARD_DEDUCTION


def calculate_repairs_and_tax_deduction(rent_paid: Any) -> Decimal:
    """Return repairs/property tax deduction, capped at the statutory limit."""
    rent_paid_dec = _to_decimal(rent_paid, "rent_paid")
    if rent_paid_dec < 0:
        raise InvalidInputError("rent_paid must be non-negative.")
    return min(rent_paid_dec * DEFAULT_REPAIRS_RATE, DEFAULT_REPAIRS_LIMIT)


def build_deduction_suggestions(
    monthly_salary: Any = 0,
    monthly_rent: Any = 0,
    monthly_hra: Any = 0,
    city: str = "non_metro",
) -> dict[str, Any]:
    """Build deduction suggestions for ITR based on user inputs."""
    try:
        hra_exempt = calculate_hra_exemption(
            salary=monthly_salary,
            rent_paid=monthly_rent,
            city_type=city,
            hra_received=monthly_hra,
        )
    except InvalidInputError:
        logger.exception("Failed to calculate HRA exemption.")
        hra_exempt = Decimal("0")

    try:
        standard = calculate_standard_deduction()
    except Exception:
        logger.exception("Failed to calculate standard deduction.")
        standard = DEFAULT_STANDARD_DEDUCTION

    try:
        repairs = calculate_repairs_and_tax_deduction(monthly_rent)
    except InvalidInputError:
        logger.exception("Failed to calculate repairs deduction.")
        repairs = Decimal("0")

    return {
        "hra_exemption": float(hra_exempt),
        "standard_deduction": float(standard),
        "repairs_and_tax": float(repairs),
        "total_suggested_deductions": float(hra_exempt + standard + repairs),
        "messages": [
            f"You can claim ₹{hra_exempt:,.0f} deduction under HRA section 10(13A).",
            (
                f"Standard deduction of ₹{standard:,.0f} is available for "
                f"salaried persons."
            ),
            f"Repairs & property tax deduction: ₹{repairs:,.0f}.",
        ],
    }
