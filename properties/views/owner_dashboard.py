# mypy: ignore-errors

from datetime import date, timedelta

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response

from django.contrib.auth.models import AnonymousUser
from django.db.models import Q, Sum
from django.db.models.functions import TruncMonth

from ..models import (
    Building,
    Caretaker,
    ITRTracker,
    PropertyTaxRecord,
    RentAgreementDraft,
    Renter,
    RentRecord,
    Unit,
)
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
def owner_dashboard(request: DRFRequest) -> Response:
    """Comprehensive owner dashboard endpoint.

    Returns all data needed for the owner dashboard in a single call:
    - Quick statistics (buildings, units, renters, caretakers, collections)
    - Recent items (payments, tenants, agreements, notifications)
    - Pending tasks (rent due today, expiring agreements, verifications, payouts)
    - Analytics trends (rent collection, occupancy, revenue)
    """
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=401)

    owner = request.user
    today = date.today()
    current_month = today.replace(day=1)
    previous_six_months = (current_month - timedelta(days=180)).replace(day=1)

    # ----------------------------------------------------------------
    # Quick Statistics
    # ----------------------------------------------------------------
    total_buildings = Building.objects.filter(owner=owner, is_archived=False).count()
    total_units = Unit.objects.filter(owner=owner, is_archived=False).count()
    occupied_units = Unit.objects.filter(
        owner=owner, is_archived=False, status=Unit.VacancyStatus.OCCUPIED
    ).count()
    vacant_units = total_units - occupied_units
    occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0.0

    active_renters = Renter.objects.filter(
        unit__owner=owner, status=Renter.RenterStatus.ACTIVE
    ).count()

    caretakers_count = Caretaker.objects.filter(
        unit__owner=owner, is_active=True
    ).count()

    rents = RentRecord.objects.filter(unit__owner=owner)

    monthly_collection = float(
        rents.filter(
            status=RentRecord.Status.PAID,
            due_date__gte=current_month,
        ).aggregate(total=Sum("amount"))["total"]
        or 0
    )

    pending_collection = float(
        rents.exclude(status=RentRecord.Status.PAID).aggregate(total=Sum("amount"))[
            "total"
        ]
        or 0
    )

    # ----------------------------------------------------------------
    # Analytics Trends
    # ----------------------------------------------------------------
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

    monthly_rent_trend = [
        {
            "month": item["month"].strftime("%b"),
            "amount": float(item["total"] or 0),
        }
        for item in rent_payment_trends
    ]

    revenue_trend = monthly_rent_trend

    collection_trend = [
        {
            "month": item["month"].strftime("%b"),
            "amount": float(item["total"] or 0),
        }
        for item in rent_payment_trends
    ]

    # Occupancy trend (last 6 months)
    occupancy_trend = []
    for i in range(5, -1, -1):
        month_start = (current_month - timedelta(days=30 * i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(
            days=1
        )
        total_at_month = Unit.objects.filter(
            owner=owner, is_archived=False, created_at__lte=month_end
        ).count()
        occupied_at_month = Unit.objects.filter(
            owner=owner,
            is_archived=False,
            status=Unit.VacancyStatus.OCCUPIED,
            created_at__lte=month_end,
        ).count()
        rate = (occupied_at_month / total_at_month * 100) if total_at_month > 0 else 0.0
        occupancy_trend.append(
            {
                "month": month_start.strftime("%b"),
                "rate": round(rate, 1),
            }
        )

    # ----------------------------------------------------------------
    # Recent Items
    # ----------------------------------------------------------------
    recent_rent_payments = list(
        rents.filter(status=RentRecord.Status.PAID)
        .select_related("renter", "unit")
        .order_by("-due_date")[:5]
        .values(
            "id",
            "renter__name",
            "unit__unit",
            "unit__building__name",
            "amount",
            "due_date",
            "status",
            "payment_method",
        )
    )
    recent_rent_payments = [
        {
            "id": item["id"],
            "renter_name": item["renter__name"] or "",
            "unit_name": item["unit__unit"] or "",
            "building_name": item["unit__building__name"] or "",
            "amount": float(item["amount"]),
            "due_date": item["due_date"],
            "status": item["status"],
            "payment_method": item["payment_method"],
        }
        for item in recent_rent_payments
    ]

    recent_tenants = list(
        Renter.objects.filter(unit__owner=owner)
        .select_related("unit")
        .order_by("-start_date")[:5]
        .values(
            "id",
            "name",
            "phone",
            "unit__unit",
            "unit__building__name",
            "status",
            "start_date",
            "rent_amount",
        )
    )
    recent_tenants = [
        {
            "id": item["id"],
            "name": item["name"],
            "phone": item["phone"],
            "unit_name": item["unit__unit"] or "",
            "building_name": item["unit__building__name"] or "",
            "status": item["status"],
            "start_date": item["start_date"],
            "rent_amount": float(item["rent_amount"]),
        }
        for item in recent_tenants
    ]

    recent_agreements = list(
        RentAgreementDraft.objects.filter(user=owner)
        .select_related("renter", "unit")
        .order_by("-generated_at")[:5]
        .values(
            "id",
            "renter__name",
            "unit__unit",
            "generated_at",
            "owner_signed",
            "renter_signed",
        )
    )
    recent_agreements = [
        {
            "id": item["id"],
            "renter_name": item["renter__name"] or "",
            "unit_name": item["unit__unit"] or "",
            "generated_at": item["generated_at"],
            "owner_signed": item["owner_signed"],
            "renter_signed": item["renter_signed"],
        }
        for item in recent_agreements
    ]

    # ----------------------------------------------------------------
    # Pending Tasks
    # ----------------------------------------------------------------
    rent_due_today = list(
        rents.filter(status=RentRecord.Status.PENDING, due_date=today)
        .select_related("renter", "unit")
        .order_by("-due_date")[:10]
        .values(
            "id",
            "renter__name",
            "unit__unit",
            "amount",
            "due_date",
        )
    )
    rent_due_today = [
        {
            "id": item["id"],
            "renter_name": item["renter__name"] or "",
            "unit_name": item["unit__unit"] or "",
            "amount": float(item["amount"]),
            "due_date": item["due_date"],
        }
        for item in rent_due_today
    ]

    agreements_expiring = list(
        RentAgreementDraft.objects.filter(user=owner)
        .select_related("renter", "unit")
        .order_by("-generated_at")[:10]
        .values(
            "id",
            "renter__name",
            "unit__unit",
            "generated_at",
            "owner_signed",
            "renter_signed",
        )
    )
    agreements_expiring = [
        {
            "id": item["id"],
            "renter_name": item["renter__name"] or "",
            "unit_name": item["unit__unit"] or "",
            "generated_at": item["generated_at"],
            "owner_signed": item["owner_signed"],
            "renter_signed": item["renter_signed"],
        }
        for item in agreements_expiring
    ]

    pending_verification = Renter.objects.filter(
        unit__owner=owner, kyc_status=Renter.KYCStatus.PENDING
    ).count()

    # Maintenance requests - currently no dedicated model; return empty list
    maintenance_requests = []

    pending_payouts = rents.filter(
        payout_status__in=["PENDING", "FAILED"]
    ).select_related("renter", "unit")[:10]
    pending_payouts = [
        {
            "id": rent.id,
            "renter_name": rent.renter.name if rent.renter else "",
            "unit_name": rent.unit.unit if rent.unit else "",
            "amount": float(rent.amount),
            "payout_status": rent.payout_status,
        }
        for rent in pending_payouts
    ]

    # ----------------------------------------------------------------
    # Notifications Preview
    # ----------------------------------------------------------------
    notifications = owner.notifications.order_by("-created_at")[:5]
    notifications_preview = [
        {
            "id": note.id,
            "title": note.title,
            "message": note.message,
            "is_read": note.is_read,
            "created_at": note.created_at,
        }
        for note in notifications
    ]
    unread_count = owner.notifications.filter(is_read=False).count()

    # ----------------------------------------------------------------
    # Subscription & Feature Limits
    # ----------------------------------------------------------------
    try:
        subscription = owner.usersubscription
        current_plan = {
            "id": subscription.plan_id,
            "name": subscription.plan.name if subscription.plan else "free",
            "monthly_price": (
                str(subscription.plan.monthly_price) if subscription.plan else "0"
            ),
            "yearly_price": (
                str(subscription.plan.yearly_price) if subscription.plan else "0"
            ),
            "features": subscription.plan.features if subscription.plan else "",
            "is_active": subscription.plan.is_active if subscription.plan else False,
            "start_date": str(subscription.start_date),
            "end_date": str(subscription.end_date),
            "is_active_subscription": subscription.is_active,
            "is_yearly": subscription.is_yearly,
        }
    except Exception:
        current_plan = None

    from core.models import UsageLimit

    usage_limits = UsageLimit.objects.filter(user=owner)
    feature_usage = [
        {
            "feature_key": limit.feature_key,
            "usage_count": limit.usage_count,
            "updated_at": limit.updated_at,
        }
        for limit in usage_limits
    ]

    # ----------------------------------------------------------------
    # Build response
    # ----------------------------------------------------------------
    data = {
        "stats": {
            "total_buildings": total_buildings,
            "total_units": total_units,
            "occupied_units": occupied_units,
            "vacant_units": vacant_units,
            "active_renters": active_renters,
            "caretakers": caretakers_count,
            "monthly_collection": monthly_collection,
            "pending_collection": pending_collection,
            "occupancy_rate": round(occupancy_rate, 1),
        },
        "analytics": {
            "monthly_rent_collection": monthly_rent_trend,
            "occupancy_rate": round(occupancy_rate, 1),
            "occupancy_trend": occupancy_trend,
            "revenue_trend": revenue_trend,
            "collection_trend": collection_trend,
        },
        "recent": {
            "rent_payments": recent_rent_payments,
            "tenants": recent_tenants,
            "agreements": recent_agreements,
            "notifications": notifications_preview,
        },
        "pending_tasks": {
            "rent_due_today": rent_due_today,
            "agreements_expiring": agreements_expiring,
            "pending_verification": pending_verification,
            "maintenance_requests": maintenance_requests,
            "pending_payouts": pending_payouts,
        },
        "notifications": {
            "preview": notifications_preview,
            "unread_count": unread_count,
        },
        "subscription": current_plan,
        "feature_usage": feature_usage,
        "payouts": {
            "success": rents.filter(payout_status="SUCCESS").count(),
            "pending": rents.filter(payout_status="PENDING").count(),
            "failed": rents.filter(payout_status="FAILED").count(),
        },
    }

    return Response(data)


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
