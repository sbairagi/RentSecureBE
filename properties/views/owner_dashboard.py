# mypy: ignore-errors

from datetime import date, timedelta

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response

from django.contrib.auth.models import AnonymousUser
from django.db.models import Q, Sum
from django.db.models.functions import TruncMonth

from ..models import ITRTracker, PropertyTaxRecord, RentRecord
from ..services.tax_estimation_service import estimate_tax


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def owner_dashboard_summary(request: DRFRequest) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=401)
    owner = request.user
    today = date.today()
    current_month = today.replace(day=1)
    previous_six_months = (current_month - timedelta(days=180)).replace(day=1)

    rents = RentRecord.objects.filter(unit__owner=owner)

    total_rent_collected = (
        rents.filter(status=RentRecord.Status.PAID).aggregate(total=Sum("amount"))[
            "total"
        ]
        or 0
    )

    rent_collected_this_month = (
        rents.filter(
            status=RentRecord.Status.PAID, due_date__gte=current_month
        ).aggregate(total=Sum("amount"))["total"]
        or 0
    )

    payouts = {
        "success": rents.filter(payout_status="SUCCESS").count(),
        "pending": rents.filter(payout_status="PENDING").count(),
        "failed": rents.filter(payout_status="FAILED").count(),
    }

    rent_payment_trends = (
        rents.filter(
            status=RentRecord.Status.PAID,
            due_date__gte=previous_six_months,
        )
        .annotate(month=TruncMonth("due_date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    trend_data = [
        {
            "month": item["month"].strftime("%Y-%m"),
            "total": float(item["total"] or 0),
        }
        for item in rent_payment_trends
    ]

    monthly_rent_trend = [
        {
            "month": item["month"].strftime("%b"),
            "amount": float(item["total"] or 0),
        }
        for item in rent_payment_trends
    ]

    rent_defaulters = rents.filter(
        Q(status=RentRecord.Status.PENDING),
        due_date__lt=today,
    ).select_related("renter", "unit")

    defaulters_data = [
        {
            "renter_name": rent.renter.name if rent.renter else "",
            "unit_name": getattr(rent.unit, "unit", None),
            "amount": float(rent.amount),
            "due_date": rent.due_date,
            "status": rent.status,
        }
        for rent in rent_defaulters
    ]

    pending_rent = (
        rents.exclude(status=RentRecord.Status.PAID).aggregate(total=Sum("amount"))[
            "total"
        ]
        or 0
    )

    taxes = PropertyTaxRecord.objects.filter(property__owner=owner)

    tax_paid_this_month = (
        taxes.filter(paid=True, paid_date__gte=current_month).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    tax_trends = (
        taxes.filter(
            paid=True,
            paid_date__gte=previous_six_months,
        )
        .annotate(month=TruncMonth("paid_date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    monthly_tax_trend = [
        {
            "month": item["month"].strftime("%b"),
            "amount": float(item["total"] or 0),
        }
        for item in tax_trends
    ]

    summary = {
        "total_rent_collected": float(total_rent_collected),
        "rent_collected_this_month": float(rent_collected_this_month),
        "tax_paid_this_month": float(tax_paid_this_month),
        "pending_rent": float(pending_rent),
        "payouts": payouts,
        "upcoming_tax_dues": [],
        "rent_payment_trends": trend_data,
        "monthly_rent_trend": monthly_rent_trend,
        "monthly_tax_trend": monthly_tax_trend,
        "rent_defaulters": defaulters_data,
    }

    return Response(summary)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def income_summary(request: DRFRequest) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=401)

    owner = request.user
    profile = getattr(owner, "userprofile", None) or getattr(owner, "profile", None)
    salary = getattr(profile, "salary", 0) or 0
    other_income = getattr(profile, "other_income", 0) or 0

    rent_income = float(
        RentRecord.objects.filter(unit__owner=owner, payout_status="SUCCESS").aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    total_income = float(salary) + float(other_income) + rent_income
    tax_estimate = estimate_tax(total_income)

    return Response(
        {
            "rent_income": rent_income,
            "salary": float(salary),
            "other_income": float(other_income),
            "total_income": total_income,
            "estimated_tax": tax_estimate.tax,
            "tax_brackets": tax_estimate.brackets,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def itr_tracker_summary(request: DRFRequest) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=401)

    owner = request.user
    tracker, _ = ITRTracker.objects.get_or_create(user=owner)

    fy_start = tracker.fy_start
    fy_end = tracker.fy_end
    if fy_start and fy_end:
        fy = f"{fy_start.year}-{fy_end.year}"
    else:
        today = date.today()
        fy_start_year = today.year if today.month >= 4 else today.year - 1
        fy = f"{fy_start_year}-{fy_start_year + 1}"

    return Response(
        {
            "fy": fy,
            "total_rent_income": float(tracker.total_rent_income or 0),
            "total_deductions": float(tracker.total_deductions or 0),
            "ca_review_status": tracker.ca_review_status,
            "last_updated": tracker.last_updated,
        }
    )
