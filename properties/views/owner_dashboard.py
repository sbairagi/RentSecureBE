from datetime import date, timedelta

from django.contrib.auth.models import AnonymousUser
from django.db.models import Q, Sum
from django.db.models.functions import TruncMonth
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response

from ..models import RentRecord


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

    summary = {
        "total_rent_collected": float(total_rent_collected),
        "rent_collected_this_month": float(rent_collected_this_month),
        "payouts": payouts,
        "upcoming_tax_dues": [],
        "rent_payment_trends": trend_data,
        "rent_defaulters": defaulters_data,
    }

    return Response(summary)
