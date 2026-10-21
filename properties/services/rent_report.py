"""The rent report — the ledger as a workbook the owner can keep.

The report is made by the **server** from the **same filters as the ledger**:
the period, the building, the unit, the status and the search.  It holds the
**whole** filtered ledger — never only the page that was on screen — and the
same money the cards show, so a downloaded report and the screen can never
disagree.

The rules live in ``properties/RENT_COLLECTION_BUSINESS_RULES.md`` (§"The
report download").
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

import xlsxwriter

from properties.services.rent_amounts import build_amounts
from properties.services.rent_ledger_query import period_label

#: The columns of the sheet that holds the rows.
REPORT_COLUMNS: tuple[tuple[str, str], ...] = (
    ("Property", "property"),
    ("Unit", "unit"),
    ("Renter", "renter"),
    ("Period", "period"),
    ("Due date", "due_date"),
    ("Rent", "rent"),
    ("Late fee", "late_fee"),
    ("Discount", "discount"),
    ("Total due", "total_due"),
    ("Received", "received"),
    ("Balance", "balance"),
    ("Paid on", "paid_on"),
    ("Status", "status"),
    ("Parts", "parts"),
)


def _money(value: Any) -> float:
    """Render a money value as a float.

    Args:
        value: The value of the record.

    Returns:
        The value as a float.
    """
    return float(value or 0)


def _building_name(record: Any) -> str:
    """The property of a record.

    Args:
        record: The rent record.

    Returns:
        The name of the building the unit belongs to.
    """
    building = getattr(record.unit, "building", None)
    return getattr(building, "name", "") or record.unit.building_name or ""


def build_rent_report(scope: dict[str, Any]) -> tuple[bytes, str]:
    """Build the workbook of a ledger scope.

    The workbook carries the **rows** of the scope and a **Summary** sheet with
    the money of the scope — the same numbers the cards above the ledger show.

    Args:
        scope: The scope of the request, as ``build_ledger_scope`` returns it.

    Returns:
        The bytes of the workbook and the name of the file.
    """
    rows = scope["rows"]
    amounts = build_amounts(scope["queryset"])
    periods = scope["periods"]

    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})

    title = workbook.add_format({"bold": True, "font_size": 13})
    label = workbook.add_format({"bold": True})
    money = workbook.add_format({"num_format": "#,##0.00"})

    sheet = workbook.add_worksheet("Rent report")
    for column, (heading, _) in enumerate(REPORT_COLUMNS):
        sheet.write(0, column, heading)
    for index, record in enumerate(rows, start=1):
        sheet.write(index, 0, _building_name(record))
        sheet.write(index, 1, record.unit.unit if record.unit else "")
        sheet.write(index, 2, record.renter.name if record.renter else "")
        sheet.write(
            index,
            3,
            period_label(f"{record.due_date.year:04d}-{record.due_date.month:02d}"),
        )
        sheet.write(index, 4, record.due_date.isoformat())
        sheet.write_number(index, 5, _money(record.amount), money)
        sheet.write_number(index, 6, _money(record.late_fee), money)
        sheet.write_number(index, 7, _money(record.discount), money)
        sheet.write_number(index, 8, _money(record.total_due), money)
        sheet.write_number(index, 9, _money(record.amount_paid), money)
        sheet.write_number(index, 10, _money(record.balance), money)
        sheet.write(index, 11, record.paid_on.isoformat() if record.paid_on else "")
        sheet.write(index, 12, record.get_status_display())
        sheet.write(index, 13, len(record.parts.all()) if record.parts else 0)
    sheet.freeze_panes(1, 0)
    if rows:
        sheet.autofilter(0, 0, len(rows), len(REPORT_COLUMNS) - 1)

    summary = workbook.add_worksheet("Summary")
    summary.write(0, 0, "Rent report", title)
    summary.write(2, 0, "Period", label)
    summary.write(
        2,
        1,
        (
            ", ".join(period_label(period) for period in periods)
            if periods
            else "All months"
        ),
    )
    summary.write(3, 0, "Records", label)
    summary.write(3, 1, len(rows))
    summary.write(4, 0, "Expected rent", label)
    summary.write_number(4, 1, amounts["expected"], money)
    summary.write(5, 0, "Collected rent", label)
    summary.write_number(5, 1, amounts["collected"], money)
    summary.write(6, 0, "Pending", label)
    summary.write_number(6, 1, amounts["pending"], money)
    summary.write(7, 0, "Overdue", label)
    summary.write_number(7, 1, amounts["overdue"], money)
    summary.write(8, 0, "Late fee billed", label)
    summary.write_number(8, 1, amounts["late_fee_billed"], money)
    summary.write(9, 0, "Late fee collected", label)
    summary.write_number(9, 1, amounts["late_fee_collected"], money)
    summary.write(10, 0, "Late fee pending", label)
    summary.write_number(10, 1, amounts["late_fee_pending"], money)
    summary.write(11, 0, "Collection rate", label)
    summary.write_number(11, 1, amounts["collection_rate"])
    summary.write(
        13,
        0,
        "The late fee is a charge, not rent — the collection rate measures the rent.",
        title,
    )

    workbook.close()
    output.seek(0)
    name = f"rent-report-{'all-months' if not periods else periods[0]}.xlsx"
    return output.getvalue(), name
