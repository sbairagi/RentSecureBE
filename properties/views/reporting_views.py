from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO

import xlsxwriter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from django.db.models import Q, Sum
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
    rent_summary = rent_rows.aggregate(
        expected=Sum("amount"),
        collected=Sum("amount", filter=Q(status=RentRecord.Status.PAID)),
    )
    expected = float(rent_summary["expected"] or 0)
    collected = float(rent_summary["collected"] or 0)
    overdue_rows = rent_rows.filter(
        due_date__lt=timezone.localdate(),
        status__in=[RentRecord.Status.PENDING, RentRecord.Status.OVERDUE],
    )
    previous_days = (end - start).days + 1
    previous_start = start - timedelta(days=previous_days)
    previous_collected = float(
        RentRecord.objects.filter(
            unit_id__in=unit_ids,
            status=RentRecord.Status.PAID,
            due_date__range=(previous_start, start - timedelta(days=1)),
        ).aggregate(total=Sum("amount"))["total"]
        or 0
    )

    trend = (
        rent_rows.annotate(month=TruncMonth("due_date"))
        .values("month")
        .annotate(
            expected=Sum("amount"),
            collected=Sum("amount", filter=Q(status=RentRecord.Status.PAID)),
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
    overdue_amount = float(overdue_rows.aggregate(total=Sum("amount"))["total"] or 0)

    return Response(
        {
            "period": {"start_date": start.isoformat(), "end_date": end.isoformat()},
            "summary": {
                "rent_expected": expected,
                "rent_collected": collected,
                "collection_rate": (
                    round(collected / expected * 100, 1) if expected else 0
                ),
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
    """Export the same owner-scoped, date/property-filtered rent rows as Excel."""
    dates = _report_dates(request)
    if isinstance(dates, Response):
        return dates
    start, end = dates
    _owner, units = _report_scope(request)
    records = (
        RentRecord.objects.filter(
            unit_id__in=units.values_list("id", flat=True),
            due_date__range=(start, end),
        )
        .select_related("unit", "unit__building", "renter")
        .order_by("due_date", "unit__unit")
    )
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    sheet = workbook.add_worksheet("Rent report")
    headers = [
        "Property",
        "Unit",
        "Renter",
        "Due date",
        "Amount",
        "Payment status",
        "Payout status",
    ]
    for column, label in enumerate(headers):
        sheet.write(0, column, label)
    row_index = 0
    for row_index, record in enumerate(records, start=1):
        sheet.write(
            row_index,
            0,
            (
                record.unit.building.name
                if record.unit.building
                else record.unit.building_name
            ),
        )
        sheet.write(row_index, 1, record.unit.unit)
        sheet.write(row_index, 2, record.renter.name if record.renter else "")
        sheet.write(row_index, 3, record.due_date.isoformat())
        sheet.write_number(row_index, 4, float(record.amount))
        sheet.write(row_index, 5, record.status)
        sheet.write(row_index, 6, record.payout_status)
    sheet.freeze_panes(1, 0)
    sheet.autofilter(0, 0, max(1, row_index if records else 1), len(headers) - 1)
    workbook.close()
    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        'attachment; filename="securenest-rent-report.xlsx"'
    )
    return response
