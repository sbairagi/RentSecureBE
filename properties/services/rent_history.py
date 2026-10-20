"""The history of one rent record.

The story of a month is three things in one list:

* the **audit trail** — every change the record went through (created,
  updated), kept by ``django-simple-history``;
* the **action log** — every action a user took on the record: the month
  was created, the details were edited, the month was cancelled and why,
  the reminder was sent, the receipt was delivered (or could not be);
* the **part payments** — every instalment that was received against the
  month, each with its own amount, date, mode and reference.

All three are ordered from the newest to the oldest, and all three are the
server's: the client renders what this module builds and never rebuilds an
entry of its own.  An action that changed the record carries the id of the
audit entry it explains, so one action is never listed twice.

The rules that shape the trail are documented in
``properties/RENT_COLLECTION_BUSINESS_RULES.md``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from properties.models import RentRecord

# How many entries the history shows.  The trail of a month is short; the cap
# only guards against a record that was changed hundreds of times.
HISTORY_LIMIT = 50

ZERO = Decimal("0")
TWO_PLACES = Decimal("0.01")


def _money(value: Any) -> str:
    """Render a money value the way the API renders it (``30000.00``)."""
    return str(Decimal(value or 0).quantize(TWO_PLACES))


def _total_due(amount: Any, late_fee: Any, discount: Any) -> Decimal:
    """The bill of a snapshot — never negative, exactly like the record."""
    return max(
        ZERO,
        Decimal(amount or 0) + Decimal(late_fee or 0) - Decimal(discount or 0),
    )


def _changed_by(user: Any) -> str:
    """Who made the change — the email of the user, or an empty string."""
    if user is None:
        return ""
    return str(getattr(user, "email", "") or getattr(user, "username", "") or "")


def _snapshot(record: Any) -> dict[str, Any]:
    """The state of a record at one moment.

    Args:
        record: One row of the historical table.

    Returns:
        The money and the dates of the record as they stood then.
    """
    amount = record.amount or ZERO
    late_fee = record.late_fee or ZERO
    discount = record.discount or ZERO
    amount_paid = record.amount_paid or ZERO
    total_due = _total_due(amount, late_fee, discount)
    balance = max(ZERO, total_due - amount_paid)

    return {
        "status": str(record.status or ""),
        "amount": _money(amount),
        "amount_paid": _money(amount_paid),
        "late_fee": _money(late_fee),
        "discount": _money(discount),
        "total_due": _money(total_due),
        "balance": _money(balance),
        "due_date": record.due_date.isoformat() if record.due_date else None,
        "paid_on": record.paid_on.isoformat() if record.paid_on else None,
        "payment_method": record.payment_method or "",
        "transaction_id": record.transaction_id or "",
        "notes": record.notes or "",
        "cancel_reason": record.cancel_reason or "",
        "unit": record.unit_id,
        "renter": record.renter_id,
    }


def _history_entry(record: Any) -> dict[str, Any]:
    """One change of the record, with the snapshot it left behind.

    Args:
        record: One row of the historical table.

    Returns:
        The entry of the audit trail.
    """
    return {
        "id": record.history_id,
        "action": record.history_type,
        "changed_by": _changed_by(record.history_user),
        "timestamp": record.history_date.isoformat(),
        "data": _snapshot(record),
    }


def _action_entry(action: Any, snapshot: dict[str, Any] | None) -> dict[str, Any]:
    """One action a user took on the record.

    Args:
        action: One row of the action log.
        snapshot: The state of the record the action left behind, if the
            action changed the record.

    Returns:
        The entry of the action log.
    """
    data: dict[str, Any] = {
        "action": action.kind,
        "summary": action.summary or "",
        "detail": action.detail or "",
        "outcome": action.outcome or "",
    }
    if snapshot:
        data.update(snapshot)
    return {
        "id": action.id,
        "action": action.kind,
        "changed_by": _changed_by(action.actor),
        "timestamp": action.created_at.isoformat(),
        "data": data,
    }


def _part_entry(part: Any) -> dict[str, Any]:
    """One part payment received against the month.

    Args:
        part: The part payment.

    Returns:
        The entry of the trail.
    """
    return {
        "id": part.id,
        "action": "part",
        "changed_by": _changed_by(part.created_by),
        "timestamp": part.created_at.isoformat(),
        "data": {
            "amount": _money(part.amount),
            "paid_on": part.paid_on.isoformat() if part.paid_on else None,
            "payment_method": part.payment_method or "",
            "transaction_id": part.transaction_id or "",
            "note": part.note or "",
        },
    }


def build_rent_history(
    rent_record: RentRecord, *, limit: int = HISTORY_LIMIT
) -> list[dict[str, Any]]:
    """The history of a rent record — the changes, the actions and the parts.

    Args:
        rent_record: The record the history belongs to.
        limit: How many entries the history carries at most.

    Returns:
        The entries of the history, newest first.
    """
    history_rows = list(rent_record.history.all().order_by("-history_date"))
    snapshots = {int(row.history_id): _snapshot(row) for row in history_rows}
    actions = list(rent_record.actions.all())

    # An action that changed the record explains the audit entry of that
    # change — the entry is not listed a second time beside it.
    explained = {
        int(action.history_id) for action in actions if action.history_id is not None
    }

    entries = [
        _history_entry(row)
        for row in history_rows
        if int(row.history_id) not in explained
    ]
    entries.extend(_part_entry(part) for part in rent_record.parts.all())
    entries.extend(
        _action_entry(action, snapshots.get(action.history_id)) for action in actions
    )

    entries.sort(
        key=lambda entry: (entry["timestamp"] or "", entry["id"]), reverse=True
    )
    return entries[:limit]
