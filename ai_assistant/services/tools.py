from __future__ import annotations

from typing import Any

from django.db.models import Sum
from django.utils import timezone

from properties.models import Renter, RentRecord, Unit


def _get_owner(user: Any) -> Any:
    return user


def _get_renter_profile(user: Any) -> Any | None:
    try:
        return user.renter_profile
    except Exception:
        return None


def get_pending_rents(user: Any) -> dict[str, Any]:
    owner = _get_owner(user)
    records = RentRecord.objects.filter(
        renter__unit__owner=owner,
        status__in=[RentRecord.Status.PENDING, RentRecord.Status.OVERDUE],
    ).select_related("renter", "unit")

    total = sum(r.amount for r in records)
    items = [
        {
            "renter": r.renter.name if r.renter else "",
            "unit": r.unit.unit if r.unit else "",
            "amount": str(r.amount),
            "due_date": r.due_date.isoformat(),
            "status": r.status,
        }
        for r in records[:50]
    ]

    return {
        "tool": "get_pending_rents",
        "total_pending": str(total),
        "count": records.count(),
        "records": items,
    }


def get_rent_collection_summary(user: Any) -> dict[str, Any]:
    owner = _get_owner(user)
    today = timezone.localdate()
    month_start = today.replace(day=1)

    paid = (
        RentRecord.objects.filter(
            renter__unit__owner=owner,
            status=RentRecord.Status.PAID,
            paid_on__gte=month_start,
        ).aggregate(total=Sum("amount"))["total"]
        or 0
    )

    pending = (
        RentRecord.objects.filter(
            renter__unit__owner=owner,
            status__in=[RentRecord.Status.PENDING, RentRecord.Status.OVERDUE],
            due_date__gte=month_start,
        ).aggregate(total=Sum("amount"))["total"]
        or 0
    )

    return {
        "tool": "get_rent_collection_summary",
        "month": today.strftime("%B %Y"),
        "collected": str(paid),
        "pending": str(pending),
        "currency": "INR",
    }


def get_vacant_units(user: Any) -> dict[str, Any]:
    owner = _get_owner(user)
    units = Unit.objects.filter(owner=owner, is_vacant=True, is_archived=False)

    items = [
        {
            "unit": u.unit,
            "building": u.building.name if u.building else "",
            "unit_type": u.unit_type,
            "city": u.city,
        }
        for u in units[:50]
    ]

    return {
        "tool": "get_vacant_units",
        "count": units.count(),
        "units": items,
    }


def get_occupancy_summary(user: Any) -> dict[str, Any]:
    owner = _get_owner(user)
    total = Unit.objects.filter(owner=owner, is_archived=False).count()
    occupied = Unit.objects.filter(
        owner=owner, is_vacant=False, is_archived=False
    ).count()
    vacant = total - occupied

    return {
        "tool": "get_occupancy_summary",
        "total_units": total,
        "occupied": occupied,
        "vacant": vacant,
        "occupancy_rate": f"{(occupied / total * 100) if total else 0:.1f}%",
    }


def get_renter_summary(user: Any) -> dict[str, Any]:
    owner = _get_owner(user)
    renters = Renter.objects.filter(unit__owner=owner)
    active = renters.filter(status=Renter.RenterStatus.ACTIVE).count()
    notice = renters.filter(status=Renter.RenterStatus.NOTICE_PERIOD).count()
    total = renters.count()

    return {
        "tool": "get_renter_summary",
        "total_renters": total,
        "active": active,
        "notice_period": notice,
    }


def get_payment_history(user: Any) -> dict[str, Any]:
    renter_profile = _get_renter_profile(user)
    if renter_profile is None:
        return {
            "tool": "get_payment_history",
            "error": "Renter profile not found",
            "records": [],
        }

    records = (
        RentRecord.objects.filter(renter=renter_profile)
        .select_related("unit")
        .order_by("-due_date")[:20]
    )

    items = [
        {
            "unit": r.unit.unit if r.unit else "",
            "amount": str(r.amount),
            "due_date": r.due_date.isoformat(),
            "paid_on": r.paid_on.isoformat() if r.paid_on else None,
            "status": r.status,
        }
        for r in records
    ]

    return {
        "tool": "get_payment_history",
        "records": items,
    }


def get_next_rent_due(user: Any) -> dict[str, Any]:
    renter_profile = _get_renter_profile(user)
    if renter_profile is None:
        return {"tool": "get_next_rent_due", "error": "Renter profile not found"}

    next_due = (
        RentRecord.objects.filter(
            renter=renter_profile,
            status__in=[RentRecord.Status.PENDING, RentRecord.Status.OVERDUE],
        )
        .order_by("due_date")
        .first()
    )

    if next_due is None:
        return {"tool": "get_next_rent_due", "message": "No upcoming rent due"}

    return {
        "tool": "get_next_rent_due",
        "unit": next_due.unit.unit if next_due.unit else "",
        "amount": str(next_due.amount),
        "due_date": next_due.due_date.isoformat(),
        "status": next_due.status,
    }


def get_agreement_status(user: Any) -> dict[str, Any]:
    renter_profile = _get_renter_profile(user)
    if renter_profile is None:
        return {"tool": "get_agreement_status", "error": "Renter profile not found"}

    latest = renter_profile.rent_agreement_drafts.order_by("-generated_at").first()

    if latest is None:
        return {"tool": "get_agreement_status", "message": "No agreement found"}

    return {
        "tool": "get_agreement_status",
        "has_agreement": bool(latest.file),
        "generated_at": (
            latest.generated_at.isoformat() if latest.generated_at else None
        ),
    }


def get_subscription_status(user: Any) -> dict[str, Any]:
    try:
        sub = user.usersubscription
        return {
            "tool": "get_subscription_status",
            "plan": sub.plan.name if sub.plan else "free",
            "start_date": sub.start_date.isoformat() if sub.start_date else None,
            "end_date": sub.end_date.isoformat() if sub.end_date else None,
            "is_active": sub.is_active if hasattr(sub, "is_active") else True,
        }
    except Exception:
        return {
            "tool": "get_subscription_status",
            "plan": "free",
            "is_active": False,
        }


def get_notification_summary(user: Any) -> dict[str, Any]:
    from notification.models import Notification

    count = Notification.objects.filter(user=user, is_read=False).count()
    return {
        "tool": "get_notification_summary",
        "unread_count": count,
    }


def get_maintenance_summary(user: Any) -> dict[str, Any]:
    return {
        "tool": "get_maintenance_summary",
        "message": "Maintenance tracking is not available in the current version.",
        "records": [],
    }


AI_TOOLS: dict[str, Any] = {
    "get_pending_rents": {
        "description": "Get pending and overdue rent records for the owner.",
        "function": get_pending_rents,
    },
    "get_rent_collection_summary": {
        "description": "Get monthly rent collection summary for the owner.",
        "function": get_rent_collection_summary,
    },
    "get_vacant_units": {
        "description": "Get list of vacant units for the owner.",
        "function": get_vacant_units,
    },
    "get_occupancy_summary": {
        "description": "Get occupancy summary for the owner.",
        "function": get_occupancy_summary,
    },
    "get_renter_summary": {
        "description": "Get renter statistics for the owner.",
        "function": get_renter_summary,
    },
    "get_payment_history": {
        "description": "Get payment history for the renter.",
        "function": get_payment_history,
    },
    "get_next_rent_due": {
        "description": "Get next rent due for the renter.",
        "function": get_next_rent_due,
    },
    "get_agreement_status": {
        "description": "Get agreement status for the renter.",
        "function": get_agreement_status,
    },
    "get_subscription_status": {
        "description": "Get subscription status for the user.",
        "function": get_subscription_status,
    },
    "get_notification_summary": {
        "description": "Get notification summary for the user.",
        "function": get_notification_summary,
    },
    "get_maintenance_summary": {
        "description": "Get maintenance summary (placeholder).",
        "function": get_maintenance_summary,
    },
}


def execute_tool(tool_name: str, user: Any) -> dict[str, Any]:
    tool = AI_TOOLS.get(tool_name)
    if tool is None:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return tool["function"](user)
    except Exception as exc:
        return {"error": str(exc), "tool": tool_name}


def get_available_tools_definition() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "description": info["description"],
            "parameters": {"type": "object", "properties": {}},
        }
        for name, info in AI_TOOLS.items()
    ]
