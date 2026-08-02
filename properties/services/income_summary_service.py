"""Income summary service.

Generates and sends income summary PDFs for property owners.
"""

from __future__ import annotations

import logging
import os
import tempfile
from datetime import date
from typing import TYPE_CHECKING, Any, TypedDict

from django.db.models import Sum
from django.utils import timezone

from core.models import User

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class IncomeSummary(TypedDict):
    start: date
    end: date
    period: str
    total_received: float
    total_failed: float
    total_records: int
    rents: list[Any]


def _get_period_start(now: date, period: str) -> date:
    if period == "monthly":
        return now.replace(day=1)
    if period == "quarterly":
        month = (now.month - 1) // 3 * 3 + 1
        return now.replace(month=month, day=1)
    if period == "yearly":
        if now.month >= 4:
            return now.replace(month=4, day=1)
        return now.replace(year=now.year - 1, month=4, day=1)
    return now.replace(day=1)


def get_income_summary(owner: User, period: str = "monthly") -> IncomeSummary:
    """Build income summary for the given owner and period."""
    now = timezone.now().date()
    start = _get_period_start(now, period)

    from properties.models import RentRecord

    rents = RentRecord.objects.filter(
        unit__owner=owner, created_at__gte=start, created_at__lte=now
    ).select_related("renter", "unit")

    total_received: float = float(
        rents.filter(payout_status="SUCCESS").aggregate(total=Sum("amount"))["total"]
        or 0
    )

    total_failed: float = float(
        rents.filter(payout_status="FAILED").aggregate(total=Sum("amount"))["total"]
        or 0
    )

    return IncomeSummary(
        start=start,
        end=now,
        period=period,
        total_received=total_received,
        total_failed=total_failed,
        total_records=rents.count(),
        rents=list(rents),
    )


def generate_income_summary_pdf(owner: User, period: str = "monthly") -> bytes:
    """Render income summary PDF bytes for the given owner."""
    from weasyprint import HTML

    from django.template.loader import render_to_string

    summary = get_income_summary(owner, period)
    context: dict[str, Any] = {
        "owner": owner,
        "summary": summary,
    }
    html_string = render_to_string("pdf/income_summary.html", context)
    return HTML(string=html_string).write_pdf()


def send_income_summary_whatsapp(owner: User, period: str = "monthly") -> bool:
    """Send the owner's income summary PDF via WhatsApp."""
    try:
        pdf_bytes = generate_income_summary_pdf(owner, period=period)
        fd, path = tempfile.mkstemp(suffix=".pdf", prefix=f"income_summary_{period}_")
        try:
            with os.fdopen(fd, "wb") as pdf_file:
                pdf_file.write(pdf_bytes)
        except Exception:
            os.close(fd)
            raise

        from notification.services.whatsapp_service import send_whatsapp_file

        phone = getattr(owner, "whatsapp_number", None)
        if not phone:
            logger.warning("Owner %s has no whatsapp_number", owner.username)
            return False

        return send_whatsapp_file(
            phone,
            path,
            "application/pdf",
            user=owner,
            rent_record=None,
        )
    except Exception as exc:
        logger.exception(
            "Failed to send income summary WhatsApp to %s: %s",
            owner.username,
            exc,
        )
        return False
