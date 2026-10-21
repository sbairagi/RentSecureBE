from __future__ import annotations

from datetime import date, timedelta

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from django.db.models import F, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.utils import timezone

from properties.models import (
    Building,
    MaintenanceRequest,
    RentAgreementDraft,
    RentRecord,
    Unit,
)
from properties.services.rent_amounts import build_amounts, rent_collected
from properties.services.rent_ledger_query import build_ledger_scope
from properties.services.rent_report import build_rent_report


def _report_dates(request: Request) -> tuple[date, date] | Response:
    today = timezone.localdate()
    start_value = request.query_params.get("start_date")
    end_value = request.query_params.get("end_date")
    try:
        start = date.fromisoformat(start_value) if start_value else today.replace(day=1)
        end = date.fromisoformat(end_value) if end_value else today
    except ValueError:
        return Response({"detail": "Dates must use YYYY-MM-DD format."}, status=400)
    if start > end:
        return Response(
            {"detail": "Start date must be on or before end date."}, status=400
        )
    return start, end


def _report_scope(request: Request):
    owner = request.user
    building_id = request.query_params.get("building")
    units = Unit.objects.filter(owner=owner, is_archived=False)
    if building_id:
        units = units.filter(building_id=building_id)
    return owner, units


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def owner_reports(request: Request) -> Response:
    """Return owner-scoped rent, occupancy, agreement, and maintenance summaries."""
    dates = _report_dates(request)
    if isinstance(dates, Response):
        return dates
    start, end = dates
    owner, units = _report_scope(request)
    unit_ids = units.values_list("id", flat=True)

    rent_rows = RentRecord.objects.filter(
        unit_id__in=unit_ids, due_date__range=(start, end)
    ).exclude(status=RentRecord.Status.CANCELLED)
    # The money of the period — expected, collected, the late fees and the
    # collection rate.  The rate measures the **rent** only, so a period that
    # was settled with a late fee can never push it above 100%.
    period_amounts = build_amounts(rent_rows)
    expected = period_amounts["expected"]
    collected = period_amounts["collected"]
    overdue_rows = rent_rows.filter(
        due_date__lt=timezone.localdate(),
        status__in=[RentRecord.Status.PENDING, RentRecord.Status.OVERDUE],
    )
    previous_days = (end - start).days + 1
    previous_start = start - timedelta(days=previous_days)
    # The rent that was collected in the period before — the same rule as the
    # period itself, so the comparison means something.
    previous_collected = build_amounts(
        RentRecord.objects.filter(
            unit_id__in=unit_ids,
            due_date__range=(previous_start, start - timedelta(days=1)),
        ).exclude(status=RentRecord.Status.CANCELLED)
    )["collected"]

    trend = (
        rent_rows.annotate(month=TruncMonth("due_date"))
        .values("month")
        .annotate(
            expected=Sum("amount"),
            collected=Sum(rent_collected()),
        )
        .order_by("month")
    )
    monthly = [
        {
            "month": row["month"].strftime("%Y-%m"),
            "expected": float(row["expected"] or 0),
            "collected": float(row["collected"] or 0),
        }
        for row in trend
    ]

    unit_count = units.count()
    occupied = units.filter(status=Unit.VacancyStatus.OCCUPIED).count()
    building_id = request.query_params.get("building")
    building_count = Building.objects.filter(
        owner=owner,
        is_archived=False,
        **({"id": building_id} if building_id else {}),
    ).count()
    agreements = RentAgreementDraft.objects.filter(user=owner, unit_id__in=unit_ids)
    agreement_total = agreements.count()
    agreement_signed = agreements.filter(owner_signed=True, renter_signed=True).count()
    agreement_awaiting = (
        agreements.filter(owner_signed=False).count()
        + agreements.filter(owner_signed=True, renter_signed=False).count()
    )
    maintenance = MaintenanceRequest.objects.filter(
        owner=owner, unit_id__in=unit_ids, reported_at__date__range=(start, end)
    )
    maintenance_open = maintenance.filter(status=MaintenanceRequest.Status.OPEN).count()
    maintenance_in_progress = maintenance.filter(
        status__in=[
            MaintenanceRequest.Status.IN_PROGRESS,
            MaintenanceRequest.Status.WAITING,
        ]
    ).count()
    maintenance_resolved = maintenance.filter(
        status__in=[
            MaintenanceRequest.Status.RESOLVED,
            MaintenanceRequest.Status.CLOSED,
        ]
    ).count()
    # The overdue bucket is the money still to collect: total billed minus
    # what has already been received on those records.
    overdue_amount = float(
        overdue_rows.aggregate(
            total=Sum(F("amount") + F("late_fee") - F("discount")) - Sum("amount_paid")
        )["total"]
        or 0
    )

    return Response(
        {
            "period": {"start_date": start.isoformat(), "end_date": end.isoformat()},
            "summary": {
                "rent_expected": expected,
                "rent_collected": collected,
                "rent_received": period_amounts["received"],
                "collection_rate": period_amounts["collection_rate"],
                "late_fee_billed": period_amounts["late_fee_billed"],
                "late_fee_collected": period_amounts["late_fee_collected"],
                "late_fee_pending": period_amounts["late_fee_pending"],
                "previous_rent_collected": previous_collected,
                "overdue_amount": overdue_amount,
                "overdue_count": overdue_rows.count(),
                "buildings": building_count,
                "units": unit_count,
                "occupied_units": occupied,
                "vacant_units": unit_count - occupied,
                "occupancy_rate": (
                    round(occupied / unit_count * 100, 1) if unit_count else 0
                ),
                "agreement_total": agreement_total,
                "agreement_awaiting": agreement_awaiting,
                "agreement_signed": agreement_signed,
                "maintenance_open": maintenance_open,
                "maintenance_in_progress": maintenance_in_progress,
                "maintenance_resolved": maintenance_resolved,
            },
            "monthly_collection": monthly,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_owner_rent_report(request: Request) -> HttpResponse | Response:
    """Export the rent report of the owner as a workbook.

    The reports page sends a date range (``start_date`` / ``end_date``); the
    rent ledger sends its own filters (``period``, ``building``, ``unit``,
    ``status``, ``search``).  Both end in the same workbook — the rows and a
    summary sheet with the money of the scope.
    """
    owner = request.user
    if request.query_params.get("start_date") or request.query_params.get("end_date"):
        dates = _report_dates(request)
        if isinstance(dates, Response):
            return dates
        start, end = dates
        _owner, units = _report_scope(request)
        records = RentRecord.objects.filter(
            unit_id__in=units.values_list("id", flat=True),
            due_date__range=(start, end),
        )
        scope = {
            "rows": list(
                records.select_related("unit", "unit__building", "renter").order_by(
                    "due_date", "unit__unit"
                )
            ),
            "queryset": records,
            "periods": _months_between(start, end),
        }
    else:
        try:
            scope = build_ledger_scope(owner, request.query_params)
        except ValueError as error:
            return Response({"detail": str(error)}, status=400)

    content, name = build_rent_report(scope)
    response = HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{name}"'
    return response


def _months_between(start: date, end: date) -> list[str]:
    """The months a date range covers — written ``YYYY-MM``.

    Args:
        start: The first day of the range.
        end: The last day of the range.

    Returns:
        The months of the range, oldest first.
    """
    months: list[str] = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        months.append(f"{year:04d}-{month:02d}")
        month += 1
        if month > 12:
            year, month = year + 1, 1
    return months
