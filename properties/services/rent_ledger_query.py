"""The ledger query — the filters, the facets and the pagination of the ledger.

A ledger that grows is not a list any more: the owner needs to narrow it down
and to walk through it.  Both are **server** work:

* the **filters** — period, building, unit and status — are multi-select;
* the **facets** — the values of every filter — are grouped by the server and
  carry the number of records behind every value;
* the **pagination** — the page, the page size and the totals — is decided by
  the server, which also decides how many rows a page may hold.

The client sends the filters it applied and the page it wants; it renders the
answer.  It never groups, counts or slices the ledger on its own.

The rules live in ``properties/RENT_COLLECTION_BUSINESS_RULES.md`` (§7).
"""

from __future__ import annotations

import math
from typing import Any

from django.db.models import Count, Q, QuerySet
from django.db.models.functions import ExtractMonth, ExtractYear
from django.utils import timezone

from documents.receipt import MONTH_NAMES
from properties.models import RentRecord
from properties.services.rent_amounts import build_amounts

#: The page sizes the ledger offers.  A size that is not on the list is
#: refused and the default is used instead.
PAGE_SIZES: tuple[int, ...] = (10, 25, 50, 75, 100)

#: The page size the ledger starts with.
DEFAULT_PAGE_SIZE: int = 25

#: The filters of the ledger, in the order the columns carry them.
FILTER_FIELDS: tuple[str, ...] = ("period", "building", "unit", "status")

#: The value that asks for every month of the period filter.
ALL_PERIODS = "all"

#: The label of every status of a record — the same word the badge carries.
STATUS_LABELS: dict[str, str] = {
    "pending": "Pending",
    "overdue": "Overdue",
    "paid": "Paid",
    "cancelled": "Cancelled",
}

#: The order the statuses are offered in.
STATUS_ORDER: tuple[str, ...] = ("pending", "overdue", "paid", "cancelled")


def parse_values(raw: Any) -> list[str]:
    """Read a multi-value query parameter.

    Both ``?unit=3&unit=7`` and ``?unit=3,7`` are accepted, and every value
    is kept only once.

    Args:
        raw: The raw value of the parameter — a string, a list of strings or
            ``None``.

    Returns:
        The values of the parameter, without empties and without duplicates.
    """
    if raw is None:
        return []
    parts: list[str] = []
    if isinstance(raw, (list, tuple)):
        for item in raw:
            parts.extend(str(item).split(","))
    else:
        parts = str(raw).split(",")

    values: list[str] = []
    for part in parts:
        cleaned = str(part).strip()
        if cleaned and cleaned not in values:
            values.append(cleaned)
    return values


def read_param(params: Any, key: str) -> Any:
    """Read a parameter that may be sent more than once.

    ``?status=paid&status=cancelled`` and ``?status=paid,cancelled`` are the
    same request; both are read here.

    Args:
        params: The query parameters of the request.
        key: The name of the parameter.

    Returns:
        The value of the parameter — a list when it was sent more than once.
    """
    getlist = getattr(params, "getlist", None)
    if callable(getlist):
        values = getlist(key)
        if values:
            return values
    return params.get(key)


def parse_page(raw: Any) -> int:
    """Read the page that is asked for.

    Args:
        raw: The raw value of the ``page`` parameter.

    Returns:
        The page number — never below one.
    """
    try:
        page = int(str(raw).strip())
    except (TypeError, ValueError):
        return 1
    return max(1, page)


def parse_page_size(raw: Any) -> int:
    """Read the page size that is asked for.

    A size that is not on the list is refused — the ledger answers with the
    default size instead of an arbitrary one.

    Args:
        raw: The raw value of the ``page_size`` parameter.

    Returns:
        The number of rows a page may hold.
    """
    try:
        size = int(str(raw).strip())
    except (TypeError, ValueError):
        return DEFAULT_PAGE_SIZE
    return size if size in PAGE_SIZES else DEFAULT_PAGE_SIZE


def current_period(today: Any = None) -> str:
    """The month the ledger starts with.

    The default of the period filter is the month of the **server's** clock —
    never the one of the client, and never the one of the browser.

    Args:
        today: The day the month is read from.  Defaults to the local date of
            the server.

    Returns:
        The period of the month, written ``YYYY-MM``.
    """
    if today is None:
        today = timezone.localdate()
    return f"{today.year:04d}-{today.month:02d}"


def period_label(period: str) -> str:
    """The name of a period — the month and the year, in the fixed wording.

    The month names come from the shared list, so the same month is never
    written in two languages.

    Args:
        period: The period, written ``YYYY-MM``.

    Returns:
        The label of the period — "October 2026".
    """
    try:
        year, month = str(period).split("-")
        return f"{MONTH_NAMES[int(month) - 1]} {int(year)}"
    except (AttributeError, IndexError, TypeError, ValueError):
        return str(period)


def parse_periods(raw: Any) -> list[str]:
    """Read the periods that are asked for.

    The period of the ledger is the month of the due date, written
    ``YYYY-MM``.  ``?period=2026-10`` and ``?period=2026-10,2026-09`` are both
    accepted, and ``?period=all`` asks for every month.

    Args:
        raw: The raw value of the parameter — a string, a list of strings or
            ``None``.

    Returns:
        The periods of the parameter, without duplicates.  An empty list means
        every month.

    Raises:
        ValueError: When a period is not written ``YYYY-MM``.
    """
    if raw is None:
        return []
    parts: list[str] = []
    if isinstance(raw, (list, tuple)):
        for item in raw:
            parts.extend(str(item).split(","))
    else:
        parts = str(raw).split(",")

    periods: list[str] = []
    for part in parts:
        cleaned = str(part).strip()
        if not cleaned:
            continue
        if cleaned.lower() == ALL_PERIODS:
            return []
        year, _, month = cleaned.partition("-")
        if (
            len(year) != 4
            or len(month) != 2
            or not year.isdigit()
            or not month.isdigit()
        ):
            raise ValueError("The period must be written YYYY-MM, or 'all'.")
        if not 1 <= int(month) <= 12:
            raise ValueError("The month of a period must be between 01 and 12.")
        period = f"{int(year):04d}-{int(month):02d}"
        if period not in periods:
            periods.append(period)
    return periods


def apply_search(
    queryset: QuerySet[RentRecord], search: str | None
) -> QuerySet[RentRecord]:
    """Narrow the ledger down to the rows that carry the search text.

    The search covers the renter, the unit, the building, the transaction
    reference and the notes.

    Args:
        queryset: The ledger to search.
        search: The text to look for.

    Returns:
        The rows that match.
    """
    text = (search or "").strip()
    if not text:
        return queryset
    return queryset.filter(
        Q(renter__name__icontains=text)
        | Q(unit__unit__icontains=text)
        | Q(unit__building__name__icontains=text)
        | Q(transaction_id__icontains=text)
        | Q(notes__icontains=text)
    )


def apply_filters(
    queryset: QuerySet[RentRecord],
    *,
    periods: list[str] | None = None,
    buildings: list[str] | None = None,
    units: list[str] | None = None,
    statuses: list[str] | None = None,
) -> QuerySet[RentRecord]:
    """Apply the filters of the ledger.

    Every filter is a multi-select: an empty list leaves the ledger alone and
    a list narrows it down to the rows that carry **any** of the values.  The
    period filter narrows the ledger down to the months of the due date.

    Args:
        queryset: The ledger to filter.
        periods: The months (``YYYY-MM``) that were picked.
        buildings: The ids of the buildings that were picked.
        units: The ids of the units that were picked.
        statuses: The statuses that were picked.

    Returns:
        The filtered rows.
    """
    if periods:
        condition = Q()
        for period in periods:
            year, _, month = period.partition("-")
            condition |= Q(due_date__year=int(year), due_date__month=int(month))
        queryset = queryset.filter(condition)
    if buildings:
        queryset = queryset.filter(unit__building_id__in=buildings)
    if units:
        queryset = queryset.filter(unit_id__in=units)
    if statuses:
        condition = Q()
        for status in statuses:
            condition |= Q(status__iexact=status)
        queryset = queryset.filter(condition)
    return queryset


def build_facets(
    queryset: QuerySet[RentRecord],
    *,
    periods: list[str] | None = None,
    buildings: list[str] | None = None,
    units: list[str] | None = None,
    statuses: list[str] | None = None,
) -> dict[str, Any]:
    """The grouped options of every filter.

    The options of a filter are grouped by the server and carry the number of
    records behind every value.  Every filter is counted with the **other**
    filters applied — the options of the unit filter therefore only carry the
    units of the buildings that were picked.

    Args:
        queryset: The ledger of the owner (the search already applied).
        periods: The months that were picked.
        buildings: The ids of the buildings that were picked.
        units: The ids of the units that were picked.
        statuses: The statuses that were picked.

    Returns:
        The filters with their options.
    """
    periods = periods or []
    buildings = buildings or []
    units = units or []
    statuses = statuses or []

    building_rows = (
        apply_filters(queryset, periods=periods, units=units, statuses=statuses)
        .values("unit__building_id", "unit__building__name")
        .annotate(count=Count("id"))
    )
    building_options = sorted(
        (
            {
                "value": str(row["unit__building_id"] or ""),
                "label": row["unit__building__name"] or "Without a building",
                "meta": "",
                "count": row["count"],
                "selected": str(row["unit__building_id"] or "") in buildings,
            }
            for row in building_rows
        ),
        key=lambda option: option["label"].lower(),
    )

    unit_rows = (
        apply_filters(queryset, periods=periods, buildings=buildings, statuses=statuses)
        .values("unit_id", "unit__unit", "unit__building__name")
        .annotate(count=Count("id"))
    )
    unit_options = sorted(
        (
            {
                "value": str(row["unit_id"] or ""),
                "label": row["unit__unit"] or "—",
                "meta": row["unit__building__name"] or "",
                "count": row["count"],
                "selected": str(row["unit_id"] or "") in units,
            }
            for row in unit_rows
        ),
        key=lambda option: (option["label"].lower(), option["meta"].lower()),
    )

    status_rows = (
        apply_filters(queryset, periods=periods, buildings=buildings, units=units)
        .values("status")
        .annotate(count=Count("id"))
    )
    status_counts: dict[str, int] = {}
    for row in status_rows:
        key = str(row["status"] or "").lower()
        status_counts[key] = status_counts.get(key, 0) + row["count"]
    status_options = [
        {
            "value": status,
            "label": STATUS_LABELS[status],
            "meta": "",
            "count": status_counts.get(status, 0),
            "selected": status in statuses,
        }
        for status in STATUS_ORDER
        if status_counts.get(status)
    ]

    # The months of the ledger — counted with the other filters, without the
    # period filter itself, so the owner can see what every month holds.
    period_rows = (
        apply_filters(queryset, buildings=buildings, units=units, statuses=statuses)
        .annotate(period=ExtractYear("due_date") * 100 + ExtractMonth("due_date"))
        .values("period")
        .annotate(count=Count("id"))
    )
    period_options: list[dict[str, Any]] = []
    for row in sorted(period_rows, key=lambda row: row["period"], reverse=True):
        value = f"{int(row['period']) // 100:04d}-{int(row['period']) % 100:02d}"
        period_options.append(
            {
                "value": value,
                "label": period_label(value),
                "meta": "",
                "count": row["count"],
                "selected": value in periods,
            }
        )
    period_options.insert(
        0,
        {
            "value": ALL_PERIODS,
            "label": "All months",
            "meta": "",
            "count": sum(option["count"] for option in period_options),
            "selected": not periods,
        },
    )

    return {
        "period": {
            "key": "period",
            "label": "Period",
            "searchable": False,
            "options": period_options,
        },
        "building": {
            "key": "building",
            "label": "Building",
            "searchable": True,
            "options": building_options,
        },
        "unit": {
            "key": "unit",
            "label": "Unit",
            "searchable": True,
            "options": unit_options,
        },
        "status": {
            "key": "status",
            "label": "Status",
            "searchable": True,
            "options": status_options,
        },
    }


def build_summary(queryset: QuerySet[RentRecord]) -> dict[str, int]:
    """Count the rows of the ledger by state.

    The counts belong to the **whole** filtered ledger, not to the page that is
    on screen — the card above the table states the truth about the ledger.

    Args:
        queryset: The filtered ledger.

    Returns:
        The number of records per state.
    """
    totals = queryset.aggregate(
        paid=Count("id", filter=Q(status__iexact="paid")),
        pending=Count("id", filter=Q(status__iexact="pending")),
        overdue=Count("id", filter=Q(status__iexact="overdue")),
        cancelled=Count("id", filter=Q(status__iexact="cancelled")),
        partially_paid=Count(
            "id", filter=Q(amount_paid__gt=0) & ~Q(status__iexact="paid")
        ),
    )
    return {key: int(value or 0) for key, value in totals.items()}


def build_ledger_scope(owner: Any, params: Any) -> dict[str, Any]:
    """The scope of a ledger request — the filters and the rows they select.

    The page of the ledger and the report of the ledger read the **same**
    scope, so a downloaded report always holds exactly the rows the owner was
    looking at.

    Args:
        owner: The owner whose ledger is read.
        params: The query parameters of the request.

    Returns:
        The periods, the buildings, the units, the statuses, the search and
        the rows of the scope.

    Raises:
        ValueError: When a period is not written ``YYYY-MM``.
    """
    get = params.get

    base = RentRecord.objects.filter(unit__owner=owner)
    search = (get("search") or "").strip()
    base = apply_search(base, search)

    raw_period = read_param(params, "period")
    if raw_period is None:
        periods = [current_period()]
    else:
        periods = parse_periods(raw_period)
    buildings = parse_values(read_param(params, "building"))
    units = parse_values(read_param(params, "unit"))
    statuses = [
        value.lower()
        for value in parse_values(read_param(params, "status"))
        if value.lower() in STATUS_LABELS
    ]

    filtered = apply_filters(
        base, periods=periods, buildings=buildings, units=units, statuses=statuses
    )
    rows = list(
        filtered.order_by("-due_date", "id")
        .select_related("renter", "unit", "unit__building")
        .prefetch_related("parts")
    )
    return {
        "base": base,
        "rows": rows,
        "queryset": filtered,
        "periods": periods,
        "buildings": buildings,
        "units": units,
        "statuses": statuses,
        "search": search,
    }


def build_ledger_page(owner: Any, params: Any) -> dict[str, Any]:
    """The ledger of an owner — one page of rows, the filters and the pagination.

    The **period** filter is the month of the due date, and it starts on the
    current month of the server: a client that sends no period gets the month
    that is running.  ``?period=all`` asks for every month.

    Args:
        owner: The owner whose ledger is read.
        params: The query parameters of the request.

    Returns:
        The rows of the page, the grouped filter options, the counts of the
        ledger, the money of the scope and the state of the pagination.

    Raises:
        ValueError: When a period is not written ``YYYY-MM``.
    """
    get = params.get

    scope = build_ledger_scope(owner, params)
    periods = scope["periods"]
    buildings = scope["buildings"]
    units = scope["units"]
    statuses = scope["statuses"]
    search = scope["search"]
    filtered = scope["queryset"]

    total = filtered.count()
    page_size = parse_page_size(get("page_size"))
    total_pages = max(1, math.ceil(total / page_size)) if total else 1
    page = min(parse_page(get("page")), total_pages)

    rows = scope["rows"][(page - 1) * page_size : page * page_size]

    first_row = (page - 1) * page_size + 1 if total else 0
    last_row = min(page * page_size, total)

    return {
        "count": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "previous_page": page - 1 if page > 1 else None,
        "next_page": page + 1 if page < total_pages else None,
        "first_row": first_row,
        "last_row": last_row,
        "page_sizes": list(PAGE_SIZES),
        "search": search,
        "filters": build_facets(
            scope["base"],
            periods=periods,
            buildings=buildings,
            units=units,
            statuses=statuses,
        ),
        "selected_filters": {
            "period": periods,
            "building": buildings,
            "unit": units,
            "status": statuses,
        },
        "summary": build_summary(filtered),
        "amounts": build_amounts(filtered),
        "results": rows,
    }
