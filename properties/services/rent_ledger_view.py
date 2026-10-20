"""Authoritative read model for the rent collection ledger.

Every rule that decides what a ledger row shows lives here, on the server:

* the **row state** — which actions a row still allows (edit, cancel, remind,
  receipt, record part) and whether the row is locked;
* the **status badges** — the exact set of pills a row carries, in order;
* the **charge breakdown** — the late fee and discount lines;
* the **payment progress** — how much was received, what is still owed and
  the percentage the progress bar shows;
* the **part rules** — the bounds of the next part payment and the wording of
  every message the client may show;
* the **receipt card** — the very model the PDF is rendered from.

The web client (``rentsecure-web``) renders exactly what this module
computes.  It never re-derives a rule, so the ledger can never disagree with
the API about what a row means.

The rules encoded here are non-negotiable and documented in
``properties/RENT_COLLECTION_BUSINESS_RULES.md``.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from django.utils import timezone

from documents.receipt import build_receipt, group_indian, receipt_filename
from properties.models import RentRecord, RentRecordPart

ZERO = Decimal("0")
TWO_PLACES = Decimal("0.01")
DASH = "—"

# The ledger renders dates the way the web client renders them, with the
# Indian short month names (``05-Sept-2026``).  The receipt keeps its own
# format (``05 Oct 2026``) — see ``documents.receipt.format_date``.
LEDGER_MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sept",
    "Oct",
    "Nov",
    "Dec",
)

# The canonical wording of the part-payment rules.  The client shows these
# while the owner types, and the API answers with the very same sentences, so
# a message never changes shape between the two.
PART_PAYMENT_MESSAGES: dict[str, str] = {
    "amount_required": "Enter the amount received in this part.",
    "amount_too_large": (
        "This part is larger than the remaining balance of {balance}."
    ),
    "date_required": "Choose the date this part was received.",
    "date_before_due": "The part date cannot be earlier than the rent due date.",
}


def _to_decimal(value: Any) -> Decimal:
    """Read a money value without ever raising on ``None`` or junk."""
    if value is None:
        return ZERO
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return ZERO


def money_amount(value: Any) -> str:
    """Render a money amount the way the API renders it (``30000.00``)."""
    return str(_to_decimal(value).quantize(TWO_PLACES))


def format_money(value: Any) -> str:
    """Format a money value the way the ledger renders it (``₹30,000``)."""
    amount = _to_decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return f"₹{group_indian(int(amount))}"


def format_money_exact(value: Any) -> str:
    """Format a money value keeping the paise (``₹1,500.50``)."""
    amount = _to_decimal(value)
    sign = "-" if amount < ZERO else ""
    amount = abs(amount)
    whole = int(amount)
    fraction = amount - whole
    decimals = ""
    if fraction > ZERO:
        text = f"{fraction:.2f}".rstrip("0").rstrip(".")
        decimals = f".{text}" if text else ""
    return f"{sign}₹{group_indian(whole)}{decimals}"


def format_ledger_date(value: Any) -> str:
    """Format a date the way the ledger renders it (``05-Oct-2026``).

    Args:
        value: The date to format.

    Returns:
        The date, or a dash when there is none.
    """
    if not value:
        return DASH
    return f"{value.day:02d}-{LEDGER_MONTHS[value.month - 1]}-{value.year}"


def _status(rent_record: RentRecord) -> str:
    """The normalised status of a record."""
    return str(rent_record.status or RentRecord.Status.PENDING).lower()


def _parts(rent_record: RentRecord) -> list[RentRecordPart]:
    """The part payments of a record, in ledger order."""
    return list(rent_record.parts.all())


def build_row_state(rent_record: RentRecord) -> dict[str, Any]:
    """Every action state of one ledger row.

    The flags mirror the guards of the write endpoints exactly, so the UI
    never offers an action the backend would refuse.

    Args:
        rent_record: The record the row describes.

    Returns:
        The state of the row as plain data.
    """
    status = _status(rent_record)
    amount_paid = _to_decimal(rent_record.amount_paid)
    balance = rent_record.balance
    allows_parts = bool(getattr(rent_record.unit, "allow_partial_payments", False))

    is_settled = status == RentRecord.Status.PAID
    is_cancelled = status == RentRecord.Status.CANCELLED
    is_locked = is_settled or is_cancelled
    is_partially_paid = amount_paid > ZERO and not is_locked

    return {
        "status": status,
        "is_settled": is_settled,
        "is_cancelled": is_cancelled,
        "is_locked": is_locked,
        "is_partially_paid": is_partially_paid,
        "has_receipt": amount_paid > ZERO,
        "allows_parts": allows_parts,
        "can_edit": not is_locked,
        "can_cancel": not is_locked and amount_paid == ZERO,
        # A cancelled month is voided — it never talks to the renter again.
        "can_remind": not is_locked and balance > ZERO,
        # The settlement receipt only exists once the month is fully paid —
        # every part payment carries its own receipt automatically.
        "can_send_receipt": is_settled,
        "can_record_part": not is_locked and allows_parts and balance > ZERO,
    }


def build_status_badges(
    rent_record: RentRecord, state: dict[str, Any]
) -> list[dict[str, str]]:
    """Every status badge of a ledger row, in display order.

    A row can carry more than one badge because the states overlap:

    * **Pending** means the month is **not fully settled** — it is therefore
      on every open row, whatever else applies;
    * a month paid in instalments but not settled yet is `Partially paid`
      *and* `Pending` — the full rent is still outstanding;
    * an **overdue** month keeps its `Overdue` badge on top, so a partly paid
      overdue month reads `Overdue` + `Partially paid` + `Pending`;
    * a **settled** month is only `Paid`, a cancelled one only `Cancelled`.

    Args:
        rent_record: The record the row describes.
        state: The row state, as returned by :func:`build_row_state`.

    Returns:
        The badges of the row, in the order they are rendered.
    """
    status = state["status"]
    if status == RentRecord.Status.CANCELLED:
        return [{"tone": "cancelled", "label": "Cancelled"}]
    if status == RentRecord.Status.PAID:
        return [{"tone": "paid", "label": "Paid"}]

    badges: list[dict[str, str]] = []
    if status == RentRecord.Status.OVERDUE:
        badges.append({"tone": "overdue", "label": "Overdue"})
    if state["is_partially_paid"]:
        badges.append({"tone": "partial", "label": "Partially paid"})
    badges.append({"tone": "pending", "label": "Pending"})
    return badges


def build_charge_breakdown(rent_record: RentRecord) -> list[dict[str, str]]:
    """The late fee and discount lines shown under the billed amount.

    Args:
        rent_record: The record the row describes.

    Returns:
        The charge lines, empty when the month carries no extra charge.
    """
    lines: list[dict[str, str]] = []
    late_fee = _to_decimal(rent_record.late_fee)
    discount = _to_decimal(rent_record.discount)
    if late_fee > ZERO:
        lines.append(
            {"tone": "due", "label": f"+ {format_money_exact(late_fee)} late fee"}
        )
    if discount > ZERO:
        lines.append(
            {"tone": "settled", "label": f"− {format_money_exact(discount)} discount"}
        )
    return lines


def build_amounts(rent_record: RentRecord) -> dict[str, Any]:
    """The money of one ledger row.

    Args:
        rent_record: The record the row describes.

    Returns:
        The billed, received and outstanding amounts, both raw and ready to
        render.
    """
    amount = _to_decimal(rent_record.amount)
    amount_paid = _to_decimal(rent_record.amount_paid)
    total_due = rent_record.total_due
    balance = rent_record.balance

    return {
        "amount": money_amount(amount),
        "amount_paid": money_amount(amount_paid),
        "total_due": money_amount(total_due),
        "balance": money_amount(balance),
        "amount_display": format_money(amount),
        "amount_paid_display": format_money(amount_paid),
        "total_due_display": format_money(total_due),
        "balance_display": format_money(balance),
        "has_balance": balance > ZERO,
        "collected": amount_paid > ZERO,
        "has_charges": total_due != amount,
    }


def build_progress(
    rent_record: RentRecord, part_count: int, balance: Decimal
) -> dict[str, Any]:
    """How far the month has been collected.

    Args:
        rent_record: The record the row describes.
        part_count: How many part payments the record carries.
        balance: What is still owed on the record.

    Returns:
        The progress of the row, including the percentage of the bar.
    """
    total_due = rent_record.total_due
    amount_paid = _to_decimal(rent_record.amount_paid)

    if total_due > ZERO:
        percent = int(
            (amount_paid * 100 / total_due).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )
    else:
        percent = 0
    percent = max(0, min(100, percent))

    return {
        "paid_percent": percent,
        "part_count": part_count,
        "has_parts": part_count > 0,
        "settled": balance <= ZERO,
    }


def part_payment_messages(balance: Any) -> dict[str, str]:
    """The wording of every part-payment message.

    Args:
        balance: The remaining balance of the record.

    Returns:
        The messages, with the balance filled in.
    """
    return {
        "amount_required": PART_PAYMENT_MESSAGES["amount_required"],
        "amount_too_large": PART_PAYMENT_MESSAGES["amount_too_large"].format(
            balance=format_money_exact(balance)
        ),
        "date_required": PART_PAYMENT_MESSAGES["date_required"],
        "date_before_due": PART_PAYMENT_MESSAGES["date_before_due"],
    }


def build_part_rules(
    rent_record: RentRecord, state: dict[str, Any], *, today: date | None = None
) -> dict[str, Any]:
    """The bounds of the next part payment of a record.

    Args:
        rent_record: The record the row describes.
        state: The row state, as returned by :func:`build_row_state`.
        today: The day the record is read for — defaults to the local date.

    Returns:
        The rules of the next part and the messages that describe them.
    """
    due_date = rent_record.due_date
    balance = rent_record.balance
    late_fee = _to_decimal(rent_record.late_fee)
    status = state["status"]
    current_day = today or timezone.localdate()

    due_iso = due_date.isoformat() if due_date else ""
    default_paid_on = due_iso or current_day.isoformat()
    if (
        due_iso
        and status == RentRecord.Status.OVERDUE
        and due_date is not None
        and due_date < current_day
    ):
        default_paid_on = current_day.isoformat()

    return {
        "can_record_part": state["can_record_part"],
        "allows_parts": state["allows_parts"],
        "max_amount": money_amount(balance),
        "max_amount_display": format_money(balance),
        "min_paid_on": due_iso,
        "min_paid_on_display": format_ledger_date(due_date),
        "default_paid_on": default_paid_on,
        "due_date_display": format_ledger_date(due_date),
        "late_fee_included": (status == RentRecord.Status.OVERDUE and late_fee > ZERO),
        "late_fee_display": format_money(late_fee),
        "messages": part_payment_messages(balance),
    }


def build_ledger_view(
    rent_record: RentRecord, *, today: date | None = None
) -> dict[str, Any]:
    """Everything one ledger row shows, decided by the server.

    Args:
        rent_record: The record the row describes.
        today: The day the record is read for — defaults to the local date.

    Returns:
        The ledger view of the record: its state, amounts, progress, badges,
        charges, part rules and receipt.
    """
    state = build_row_state(rent_record)
    parts = _parts(rent_record)
    amounts = build_amounts(rent_record)

    return {
        "row_state": state,
        "amounts": amounts,
        "progress": build_progress(rent_record, len(parts), rent_record.balance),
        "status_badges": build_status_badges(rent_record, state),
        "charge_breakdown": build_charge_breakdown(rent_record),
        "part_rules": build_part_rules(rent_record, state, today=today),
        "receipt": asdict(build_receipt(rent_record)),
        "receipt_filename": receipt_filename(rent_record),
    }


def build_part_view(rent_record: RentRecord, part: RentRecordPart) -> dict[str, Any]:
    """Everything one part payment shows, decided by the server.

    Args:
        rent_record: The record the part belongs to.
        part: The part payment.

    Returns:
        The position of the part, the total received up to it and the receipt
        the PDF is rendered from.
    """
    parts = _parts(rent_record)
    sequence = len(parts)
    cumulative = ZERO
    for index, entry in enumerate(parts):
        cumulative += _to_decimal(entry.amount)
        if entry.id == part.id:
            sequence = index + 1
            break

    return {
        "sequence": sequence,
        "cumulative_amount": money_amount(cumulative),
        "receipt_filename": receipt_filename(rent_record, part),
        "receipt": asdict(build_receipt(rent_record, part)),
    }
