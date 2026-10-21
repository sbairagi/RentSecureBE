"""The money of a scope — what was billed, what came in, what is still owed.

Every screen that shows money calls this module: the cards above the ledger,
the dashboard of the owner and the reports page.  They must never disagree,
so they must never add the numbers up their own way.

The rules that shape the numbers are documented in
``properties/RENT_COLLECTION_BUSINESS_RULES.md`` (§"The money of a scope").
The two that matter most:

* the **late fee is a charge, not rent** — the renter pays the bill
  (``rent + late fee - discount``), and the late fee is collected **with the
  bill**: it comes in when the month is settled, while the month is still open
  the money received is credited to the rent and the late fee is still owed;
* the **collection rate measures the rent only** and is therefore capped at
  100% — the late fee is counted on its own card.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db.models import Case, DecimalField, F, Q, QuerySet, Sum, Value, When
from django.db.models.functions import Greatest
from django.utils import timezone

#: The rate can never be above this — the rent is either collected or it is
#: not, and the late fee is counted on its own card.
MAX_COLLECTION_RATE = 100.0

ZERO = Decimal("0")
TWO_PLACES = Decimal("0.01")


def _money(value: Any) -> float:
    """Render a money value as a float with two decimals.

    Args:
        value: The value of the database — a ``Decimal``, a number or ``None``.

    Returns:
        The value rounded to two decimals.
    """
    if value is None:
        return 0.0
    return float(Decimal(value).quantize(TWO_PLACES))


def settled_late_fee() -> Case:
    """The late fee of a record — counted only when the month is settled.

    While a month is open the money that came in is credited to the rent, so
    the late fee is still owed; when the month is settled the whole bill was
    paid and the late fee came in with it.

    Returns:
        The expression that reads the late fee of a settled record.
    """
    return Case(
        When(status="paid", then=F("late_fee")),
        default=Value(Decimal("0")),
        output_field=DecimalField(),
    )


def rent_collected() -> Greatest:
    """The rent that came in — the money received without the late fee.

    Returns:
        The expression of the rent collected by a record.
    """
    return Greatest(
        F("amount_paid") - settled_late_fee(),
        Value(Decimal("0")),
        output_field=DecimalField(),
    )


def _balance() -> Greatest:
    """The money still to collect on a record — never below zero.

    Returns:
        The expression of the balance of a record.
    """
    return Greatest(
        F("amount") + F("late_fee") - F("discount") - F("amount_paid"),
        Value(Decimal("0")),
        output_field=DecimalField(),
    )


def build_amounts(
    queryset: QuerySet[Any],
    *,
    today: Any = None,
) -> dict[str, float]:
    """The money of a set of rent records.

    The scope is whatever the caller passes in — the filtered ledger, the
    dashboard of the owner or the report of a period.  The numbers always
    mean the same thing.

    Args:
        queryset: The rent records of the scope.
        today: The day the "overdue" bucket is measured against.  Defaults to
            the local date of the server.

    Returns:
        The expected, the collected, the pending, the overdue, the late fees
        and the collection rate of the scope.
    """
    if today is None:
        today = timezone.localdate()

    settled = settled_late_fee()
    balance = _balance()
    open_records = ~Q(status__iexact="cancelled")
    overdue_records = Q(status__iexact="overdue") | (
        Q(status__iexact="pending") & Q(due_date__lt=today)
    )

    totals = queryset.aggregate(
        expected=Sum("amount", filter=open_records),
        received=Sum("amount_paid", filter=open_records),
        collected=Sum(rent_collected(), filter=open_records),
        pending=Sum(balance, filter=open_records & ~Q(status__iexact="paid")),
        overdue=Sum(balance, filter=open_records & overdue_records),
        late_fee_billed=Sum("late_fee", filter=open_records),
        late_fee_collected=Sum(settled, filter=open_records),
    )

    expected = _money(totals["expected"])
    collected = _money(totals["collected"])
    late_fee_billed = _money(totals["late_fee_billed"])
    late_fee_collected = _money(totals["late_fee_collected"])

    rate = 0.0
    if expected > 0:
        rate = min(round((collected / expected) * 100, 1), MAX_COLLECTION_RATE)

    return {
        "expected": expected,
        "collected": collected,
        "received": _money(totals["received"]),
        "pending": _money(totals["pending"]),
        "overdue": _money(totals["overdue"]),
        "late_fee_billed": late_fee_billed,
        "late_fee_collected": late_fee_collected,
        "late_fee_pending": _money(
            max(ZERO, Decimal(str(late_fee_billed)) - Decimal(str(late_fee_collected)))
        ),
        "collection_rate": rate,
    }
