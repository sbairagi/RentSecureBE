"""Visitor service layer — business logic helpers."""

import logging
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from core.models import User
from visitors.models import Visitor

logger = logging.getLogger(__name__)


def get_visitor_stats(user: User) -> dict[str, int]:
    """Return visitor statistics for the given user."""
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())

    base_filter = Q(building__owner=user) | Q(created_by=user)

    qs = Visitor.objects.filter(base_filter, is_archived=False)

    return {
        "total": qs.count(),
        "pending_approval": qs.filter(status=Visitor.Status.PENDING_APPROVAL).count(),
        "approved": qs.filter(status=Visitor.Status.APPROVED).count(),
        "checked_in": qs.filter(status=Visitor.Status.CHECKED_IN).count(),
        "checked_out": qs.filter(status=Visitor.Status.CHECKED_OUT).count(),
        "rejected": qs.filter(status=Visitor.Status.REJECTED).count(),
        "expired": qs.filter(status=Visitor.Status.EXPIRED).count(),
        "cancelled": qs.filter(status=Visitor.Status.CANCELLED).count(),
        "blocked": qs.filter(status=Visitor.Status.BLOCKED).count(),
        "today": qs.filter(visit_date=today).count(),
        "this_week": qs.filter(visit_date__gte=week_start).count(),
    }


def mark_expired_visitors() -> int:
    """Mark all approved visitors whose expected_departure has passed as expired."""
    now = timezone.now()
    expired_visitors = Visitor.objects.filter(
        status__in=[Visitor.Status.APPROVED, Visitor.Status.PENDING_APPROVAL],
        expected_departure__lt=now,
        is_archived=False,
    )
    count = 0
    for visitor in expired_visitors:
        visitor.mark_expired()
        count += 1
    if count:
        logger.info("Marked %d visitors as expired", count)
    return count


def get_recent_visitors(user: User, limit: int = 10) -> list[Visitor]:
    """Return recent visitor activity for the given user."""
    return list(
        Visitor.objects.filter(
            Q(building__owner=user) | Q(created_by=user),
            is_archived=False,
        )
        .select_related("renter", "unit", "building", "approved_by", "verified_by")
        .order_by("-created_at")[:limit]
    )
