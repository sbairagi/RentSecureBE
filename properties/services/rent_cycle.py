"""The rent cycle of a unit.

A unit is billed once per month, so the ledger of a unit is a **chain of
months**: the record that follows a settled month is always due on the same
day of the next month — clamped to the length of that month, because the
31st of January is followed by the 28th of February (the 29th in a leap
year).

A month may only be billed once the previous one is settled, so the chain
never breaks and never skips a month:

* the anchor of the cycle is the **most recent** rent record of the unit;
* a settled anchor lets the owner bill **the next month** and nothing else;
* an open anchor (pending or overdue, paid in part or not at all) blocks
  the next month until it is settled;
* a cancelled anchor is voided, so the chain continues with the month that
  follows it.

The rules are binding and documented in
``properties/RENT_COLLECTION_BUSINESS_RULES.md``.
"""

from __future__ import annotations

import calendar
from datetime import date
from typing import Any

from documents.receipt import format_period, month_name
from properties.models import RentRecord, Unit
from properties.services.rent_ledger_view import format_ledger_date, format_money


def days_in_month(year: int, month: int) -> int:
    """The number of days of a month (28, 29, 30 or 31).

    Args:
        year: The year of the month.
        month: The month (1-12).

    Returns:
        The length of the month.
    """
    return calendar.monthrange(year, month)[1]


def next_cycle_due_date(due_date: date) -> date:
    """The due date of the month that follows a due date.

    The day of the month is kept, clamped to the length of the month that
    follows: the 31st of January is followed by the 28th of February, and by
    the 29th in a leap year.

    Args:
        due_date: The due date of the month that is billed.

    Returns:
        The due date of the next cycle.
    """
    year = due_date.year
    month = due_date.month + 1
    if month > 12:
        year, month = year + 1, 1
    return date(year, month, min(due_date.day, days_in_month(year, month)))


def month_label(value: date) -> str:
    """The month of a date the way the owner reads it (October 2026).

    The name comes from the shared month list, so the label never changes
    with the locale of the machine the server runs on.

    Args:
        value: The date to label.

    Returns:
        The name of the month and the year.
    """
    return format_period(value)


def cycle_anchor(unit: Unit) -> RentRecord | None:
    """The record that anchors the cycle of a unit.

    Args:
        unit: The unit to read the cycle of.

    Returns:
        The most recent rent record of the unit, or ``None`` when it has no
        rent history yet.
    """
    return RentRecord.objects.filter(unit=unit).order_by("-due_date", "-id").first()


def open_cycle_records(unit: Unit) -> list[RentRecord]:
    """Every month of a unit that is still open, oldest first.

    A month is open while it is pending or overdue — paid in part or not at
    all.  A cancelled month is voided and a settled month is closed, so
    neither of them holds the chain.

    Args:
        unit: The unit to read the open months of.

    Returns:
        The open months of the unit, oldest first.
    """
    return list(
        RentRecord.objects.filter(
            unit=unit,
            status__in=[RentRecord.Status.PENDING, RentRecord.Status.OVERDUE],
        ).order_by("due_date", "id")
    )


def build_cycle_state(
    unit: Unit,
    *,
    anchor: RentRecord | None = None,
    open_records: list[RentRecord] | None = None,
) -> dict[str, Any]:
    """Where the cycle of a unit stands and which month may be billed next.

    The chain is held by **every** open month of the unit, not only by the
    newest one: a month that is still pending or overdue has to be settled
    before a later month may be billed, whatever happened to the months in
    between.  That is what keeps an imported history from opening a hole in
    the chain.

    Args:
        unit: The unit to read the cycle of.
        anchor: The record that anchors the cycle — read from the database
            when it is not given.
        open_records: The open months of the unit — read from the database
            when they are not given.

    Returns:
        The cycle of the unit: the month that is billed, whether it is
        settled, the month that may be billed next, the length of that
        month and the wording of the rule.
    """
    if anchor is None:
        anchor = cycle_anchor(unit)
    if open_records is None:
        open_records = open_cycle_records(unit)

    if anchor is None:
        return {
            "unit": unit.id,
            "has_cycle": False,
            "allowed": True,
            "previous_due_date": None,
            "previous_due_date_display": None,
            "previous_month": None,
            "previous_status": None,
            "previous_is_settled": False,
            "previous_is_open": False,
            "blocking_due_date": None,
            "blocking_month": None,
            "balance_due": "0.00",
            "balance_due_display": format_money(0),
            "next_due_date": None,
            "next_due_date_display": None,
            "next_month": None,
            "next_month_days": 0,
            "clamped": False,
            "clamp_note": "",
            "message": (
                "This unit has no rent history yet — its first record starts "
                "the cycle."
            ),
            "blocked_message": "",
            "mismatch_message": "",
        }

    status = str(anchor.status or RentRecord.Status.PENDING).lower()
    is_settled = status == RentRecord.Status.PAID
    is_cancelled = status == RentRecord.Status.CANCELLED
    anchor_is_open = not is_settled and not is_cancelled

    # The oldest open month holds the chain — it is the one that has to be
    # settled before anything else may be billed.
    blocker = open_records[0] if open_records else None
    is_open = blocker is not None

    next_due = next_cycle_due_date(anchor.due_date)
    next_days = days_in_month(next_due.year, next_due.month)
    clamped = next_due.day != anchor.due_date.day
    balance = blocker.balance if blocker is not None else anchor.balance

    clamp_note = ""
    if clamped:
        clamp_note = (
            f"The {anchor.due_date.day}th does not exist in "
            f"{month_name(next_due.month)} ({next_days} days) — the next cycle is "
            f"due on the {next_due.day}th."
        )

    if is_open:
        blocked_message = (
            f"The rent for {month_label(blocker.due_date)} is still open — "
            f"{format_money(balance)} is still due. Settle it before you bill "
            f"{month_label(next_due)}."
        )
    else:
        blocked_message = ""

    if is_cancelled:
        cycle_message = (
            f"The rent for {month_label(anchor.due_date)} was cancelled — the "
            f"next cycle is due {format_ledger_date(next_due)}. "
            f"{month_name(next_due.month)} has {next_days} days."
        )
    else:
        cycle_message = (
            f"The rent for {month_label(anchor.due_date)} is settled — the next "
            f"cycle is due {format_ledger_date(next_due)}. "
            f"{month_name(next_due.month)} has {next_days} days."
        )
    if clamp_note:
        cycle_message = f"{cycle_message} {clamp_note}"

    mismatch_message = (
        f"The next cycle for this unit is due {format_ledger_date(next_due)} "
        f"({month_name(next_due.month)} has {next_days} days)."
    )

    return {
        "unit": unit.id,
        "has_cycle": True,
        "allowed": not is_open,
        "previous_due_date": anchor.due_date.isoformat(),
        "previous_due_date_display": format_ledger_date(anchor.due_date),
        "previous_month": month_label(anchor.due_date),
        "previous_status": status,
        "previous_is_settled": is_settled,
        "previous_is_open": anchor_is_open,
        # The open month that holds the chain — the one that has to be
        # settled before the next month may be billed.
        "blocking_due_date": (
            blocker.due_date.isoformat() if blocker is not None else None
        ),
        "blocking_month": (
            month_label(blocker.due_date) if blocker is not None else None
        ),
        "balance_due": f"{balance:.2f}",
        "balance_due_display": format_money(balance),
        "next_due_date": next_due.isoformat(),
        "next_due_date_display": format_ledger_date(next_due),
        "next_month": month_label(next_due),
        "next_month_days": next_days,
        "clamped": clamped,
        "clamp_note": clamp_note,
        "message": cycle_message if not is_open else blocked_message,
        "blocked_message": blocked_message,
        "mismatch_message": mismatch_message,
    }


def cycle_violation(unit: Unit, due_date: date | None) -> str:
    """The reason a due date may not be billed for a unit.

    Args:
        unit: The unit the record belongs to.
        due_date: The due date the record would carry.

    Returns:
        The message that explains the refusal, or an empty string when the
        record may be created.
    """
    state = build_cycle_state(unit)
    if not state["allowed"]:
        return str(state["blocked_message"])
    expected = state["next_due_date"]
    if expected and due_date is not None and due_date.isoformat() != expected:
        return str(state["mismatch_message"])
    return ""
