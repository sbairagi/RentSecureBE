"""The catalogue of rent-collection rules the clients need.

The web client checks a form against this catalogue before it sends anything,
so the owner gets the answer immediately; the server re-checks the very same
rules and answers with the very same wording.  Both sides read the limits and
the messages from here, so the client can never drift away from the API.

The rules encoded here are non-negotiable and documented in
``properties/RENT_COLLECTION_BUSINESS_RULES.md``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from properties.services.rent_ledger_view import (
    format_money,
    format_money_exact,
    money_amount,
)

ZERO = Decimal("0")

# A rent record is billed for a positive amount, capped at ten lakhs.
MIN_RENT_AMOUNT = Decimal("0.01")
MAX_RENT_AMOUNT = Decimal("1000000")

# The canonical wording of every rule the create / edit / cancel forms guard.
RENT_RULE_MESSAGES: dict[str, str] = {
    "unit_required": "Choose the unit this rent belongs to.",
    "renter_required": "Choose the renter who made this payment.",
    "amount_required": "Enter a rent amount greater than zero.",
    "amount_max": "The rent amount cannot be more than {amount}.",
    "due_date_required": "Choose the rent period this record covers.",
    "charges_non_negative": "Late fee and discount cannot be negative.",
    "duplicate_period": "A rent record for this unit and period already exists.",
    "charges_frozen": (
        "The late fee and the discount are frozen once a payment has been " "received."
    ),
    "cancel_reason_required": (
        "A reason is required so the ledger history explains the cancellation."
    ),
    "parts_enabled": (
        "This unit allows part payments, so each instalment can be recorded "
        "as it arrives."
    ),
    "parts_disabled": (
        "Part payments are off for this unit — turn them on in the unit "
        "details to split the rent."
    ),
    "cycle": (
        "A unit is billed one month at a time — the month that follows a "
        "settled month is the only one that may be created, and a month that "
        "is still open has to be settled first."
    ),
}


def message(key: str, **values: Any) -> str:
    """Read one canonical message, filled in with the given values.

    Args:
        key: The key of the message.
        **values: The placeholders of the message.

    Returns:
        The wording of the rule.
    """
    return RENT_RULE_MESSAGES[key].format(**values)


def build_rent_rules() -> dict[str, Any]:
    """Every rule a rent-collection form has to respect.

    Returns:
        The limits, the flags and the wording of the rent-collection rules.
    """
    return {
        "amount": {
            "min": money_amount(MIN_RENT_AMOUNT),
            "max": money_amount(MAX_RENT_AMOUNT),
            "max_display": format_money(MAX_RENT_AMOUNT),
            "required_message": RENT_RULE_MESSAGES["amount_required"],
            "max_message": message("amount_max", amount=format_money(MAX_RENT_AMOUNT)),
        },
        "charges": {
            "non_negative_message": RENT_RULE_MESSAGES["charges_non_negative"],
            "freeze_after_payment": True,
            "frozen_message": RENT_RULE_MESSAGES["charges_frozen"],
        },
        "duplicate": {
            "allowed": False,
            "message": RENT_RULE_MESSAGES["duplicate_period"],
        },
        "cancel": {
            "requires_reason": True,
            "reason_message": RENT_RULE_MESSAGES["cancel_reason_required"],
        },
        "required": {
            "unit_message": RENT_RULE_MESSAGES["unit_required"],
            "renter_message": RENT_RULE_MESSAGES["renter_required"],
            "due_date_message": RENT_RULE_MESSAGES["due_date_required"],
        },
        "parts": {
            "enabled_hint": RENT_RULE_MESSAGES["parts_enabled"],
            "disabled_hint": RENT_RULE_MESSAGES["parts_disabled"],
        },
        # A unit is billed one month at a time.  The cycle of a unit is
        # anchored on the due date of its most recent record: the next record
        # is due on the same day of the following month, clamped to the length
        # of that month.  The per-unit state comes from
        # ``GET /api/rent-records/cycle/?unit=<id>``.
        "cycle": {
            "one_month_at_a_time": True,
            "message": RENT_RULE_MESSAGES["cycle"],
        },
        # How a month is billed: the rent, plus the late fee, minus the
        # discount.  The client previews a form that is not saved yet with
        # these components; the server owns the authoritative total.
        "total_due": {
            "components": [
                {"field": "amount", "sign": 1},
                {"field": "late_fee", "sign": 1},
                {"field": "discount", "sign": -1},
            ],
        },
        "zero_display": format_money(ZERO),
        "zero_exact_display": format_money_exact(ZERO),
    }
