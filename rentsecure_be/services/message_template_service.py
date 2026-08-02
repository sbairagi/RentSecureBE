"""Utility for rendering localized WhatsApp message templates."""

from __future__ import annotations

from typing import Any

from rentsecure_be.constants.messages import (
    RENT_REMINDER_TEMPLATES,
    TAX_REMINDER_TEMPLATES,
)


def get_rent_reminder_msg(
    name: str,
    amount: Any,
    due_date: Any,
    lang: str = "en",
) -> str:
    """Return a localized rent reminder message.

    Args:
        name: Renter or owner name.
        amount: Rent amount.
        due_date: Date-like object with ``strftime``.
        lang: Language code, e.g. ``"en"``, ``"hi"``, ``"mr"``.

    Returns:
        Formatted reminder string in the requested language.
    """
    template = RENT_REMINDER_TEMPLATES.get(lang, RENT_REMINDER_TEMPLATES["en"])
    return template.format(
        name=name,
        amount=amount,
        due_date=due_date.strftime("%d-%m-%Y"),
    )


def get_tax_reminder_msg(
    name: str,
    amount: Any,
    due_date: Any,
    lang: str = "en",
) -> str:
    """Return a localized tax reminder message.

    Args:
        name: Owner name.
        amount: Tax amount.
        due_date: Date-like object with ``strftime``.
        lang: Language code, e.g. ``"en"``, ``"hi"``, ``"mr"``.

    Returns:
        Formatted reminder string in the requested language.
    """
    template = TAX_REMINDER_TEMPLATES.get(lang, TAX_REMINDER_TEMPLATES["en"])
    return template.format(
        name=name,
        amount=amount,
        due_date=due_date.strftime("%d-%m-%Y"),
    )
