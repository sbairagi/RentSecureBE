"""ITR summary PDF service.

Generates a formatted ITR Summary PDF for property owners including:
- Owner details
- Financial year rent income breakdown
- Tenant-wise and unit-wise income details
- Totals for CA submission
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from django.db.models import Sum

from core.models import User

logger = logging.getLogger(__name__)


def _get_fy_dates(for_date: date) -> tuple[date, date, int, int]:
    """Return ``(fy_start, fy_end, fy_start_year, fy_end_year)``."""
    fy_start_year = for_date.year if for_date.month >= 4 else for_date.year - 1
    fy_start = date(fy_start_year, 4, 1)
    fy_end = date(fy_start_year + 1, 3, 31)
    return fy_start, fy_end, fy_start_year, fy_start_year + 1


def get_itr_summary_data(owner: User, fy_start: date, fy_end: date) -> dict[str, Any]:
    """Build ITR summary context data for the given owner and FY range."""
    from properties.models import RentRecord

    rent_records = (
        RentRecord.objects.filter(
            unit__owner=owner,
            created_at__date__gte=fy_start,
            created_at__date__lte=fy_end,
            payout_status="SUCCESS",
        )
        .select_related("renter", "unit")
        .order_by("-created_at")
    )

    total_income = float(rent_records.aggregate(total=Sum("amount"))["total"] or 0)

    return {
        "owner": owner,
        "fy_start": fy_start,
        "fy_end": fy_end,
        "rent_records": list(rent_records),
        "total_income": total_income,
        "record_count": rent_records.count(),
    }


def generate_itr_summary_pdf(owner: User, fy_start: date, fy_end: date) -> bytes:
    """Render ITR summary PDF bytes for the given owner and FY range."""
    from weasyprint import HTML

    from django.template.loader import render_to_string

    context = get_itr_summary_data(owner, fy_start, fy_end)
    html_string = render_to_string("pdf/itr_summary.html", context)
    return HTML(string=html_string).write_pdf()
