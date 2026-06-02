from datetime import date, timedelta

from django.db.models import Q, Sum
from django.db.models.functions import TruncMonth
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import RentRecord


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def owner_dashboard_summary(request):
    owner = request.user
    today = date.today()
    current_month = today.replace(day=1)
    previous_six_months = (current_month - timedelta(days=180)).replace(day=1)

    rents = RentRecord.objects.filter(owner=owner)

    total_rent_collected = (
        rents.filter(payment_status=RentRecord.PaymentStatus.PAID).aggregate(
            total=Sum("amount_paid")
        )["total"]
        or 0
    )

    rent_collected_this_month = (
        rents.filter(
            payment_status=RentRecord.PaymentStatus.PAID, rent_month__gte=current_month
        ).aggregate(total=Sum("amount_paid"))["total"]
        or 0
    )

    payouts = {
        "success": rents.filter(payout_status="SUCCESS").count(),
        "pending": rents.filter(payout_status="PENDING").count(),
        "failed": rents.filter(payout_status="FAILED").count(),
    }

    rent_payment_trends = (
        rents.filter(
            payment_status=RentRecord.PaymentStatus.PAID,
            rent_month__gte=previous_six_months,
        )
        .annotate(month=TruncMonth("rent_month"))
        .values("month")
        .annotate(total=Sum("amount_paid"))
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
        Q(payment_status=RentRecord.PaymentStatus.PENDING) | Q(payment_status="UNPAID"),
        rent_due_date__lt=today,
    ).select_related("renter", "unit")

    defaulters_data = [
        {
            "renter_name": rent.renter.name,
            "unit_name": getattr(rent.unit, "unit", None),
            "amount": float(rent.amount_paid),
            "due_date": rent.due_date,
            "status": rent.payment_status,
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
