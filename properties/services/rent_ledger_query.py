"""The ledger query — the filters, the facets and the pagination of the ledger.

A ledger that grows is not a list any more: the owner needs to narrow it down
and to walk through it.  Both are **server** work:

* the **filters** — building, unit and status — are multi-select;
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

from properties.models import RentRecord

#: The page sizes the ledger offers.  A size that is not on the list is
#: refused and the default is used instead.
PAGE_SIZES: tuple[int, ...] = (10, 25, 50, 75, 100)

#: The page size the ledger starts with.
DEFAULT_PAGE_SIZE: int = 25

#: The filters of the ledger, in the order the columns carry them.
FILTER_FIELDS: tuple[str, ...] = ("building", "unit", "status")

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
    buildings: list[str] | None = None,
    units: list[str] | None = None,
    statuses: list[str] | None = None,
) -> QuerySet[RentRecord]:
    """Apply the filters of the ledger.

    Every filter is a multi-select: an empty list leaves the ledger alone and
    a list narrows it down to the rows that carry **any** of the values.

    Args:
        queryset: The ledger to filter.
        buildings: The ids of the buildings that were picked.
        units: The ids of the units that were picked.
        statuses: The statuses that were picked.

    Returns:
        The filtered rows.
    """
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
        buildings: The ids of the buildings that were picked.
        units: The ids of the units that were picked.
        statuses: The statuses that were picked.

    Returns:
        The filters with their options.
    """
    buildings = buildings or []
    units = units or []
    statuses = statuses or []

    building_rows = (
        apply_filters(queryset, units=units, statuses=statuses)
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
        apply_filters(queryset, buildings=buildings, statuses=statuses)
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
        apply_filters(queryset, buildings=buildings, units=units)
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

    return {
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


def build_ledger_page(owner: Any, params: Any) -> dict[str, Any]:
    """The ledger of an owner — one page of rows, the filters and the pagination.

    Args:
        owner: The owner whose ledger is read.
        params: The query parameters of the request.

    Returns:
        The rows of the page, the grouped filter options, the counts of the
        ledger and the state of the pagination.
    """
    get = params.get

    base = RentRecord.objects.filter(unit__owner=owner)
    search = (get("search") or "").strip()
    base = apply_search(base, search)

    buildings = parse_values(read_param(params, "building"))
    units = parse_values(read_param(params, "unit"))
    statuses = [
        value.lower()
        for value in parse_values(read_param(params, "status"))
        if value.lower() in STATUS_LABELS
    ]

    filtered = apply_filters(base, buildings=buildings, units=units, statuses=statuses)

    total = filtered.count()
    page_size = parse_page_size(get("page_size"))
    total_pages = max(1, math.ceil(total / page_size)) if total else 1
    page = min(parse_page(get("page")), total_pages)

    rows = list(
        filtered.order_by("-due_date", "id")[(page - 1) * page_size : page * page_size]
        .select_related("renter", "unit", "unit__building")
        .prefetch_related("parts")
    )

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
            base, buildings=buildings, units=units, statuses=statuses
        ),
        "selected_filters": {
            "building": buildings,
            "unit": units,
            "status": statuses,
        },
        "summary": build_summary(filtered),
        "results": rows,
    }
