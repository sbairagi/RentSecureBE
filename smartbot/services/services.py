"""Smartbot AI alert generation service.

Produces AI-driven alerts for owners based on their renters' payment
history. The implementation only relies on fields that actually exist
on :class:`properties.models.RentRecord` and :class:`properties.models.Renter`.
"""

from datetime import date, timedelta
from typing import Any

from properties.models import Renter, RentRecord

from ..models import AIAlert


def generate_ai_alerts(owner: Any) -> int:
    """Generate AI alerts for ``owner`` based on each renter's payment history.

    Returns the number of newly created alerts.
    """
    today: date = date.today()
    six_months_ago: date = today - timedelta(days=180)

    renters = Renter.objects.filter(
        unit__owner=owner, status__in=["active", "notice_period"]
    )

    alerts_created = 0
    for renter in renters:
        rents = RentRecord.objects.filter(renter=renter).order_by("-due_date")
        alerts_created += _generate_alerts_for_renter(
            renter, rents, six_months_ago, owner
        )

    return alerts_created


def _generate_alerts_for_renter(
    renter: Renter,
    rents: Any,
    six_months_ago: date,
    owner: Any,
) -> int:
    alerts_created = 0
    recent = list(rents[:3])

    if _has_missed_consecutive_months(recent):
        _, created = AIAlert.objects.get_or_create(
            owner=owner,
            alert_type="Missed Rent",
            message=f"{renter.name} missed last 2+ months rent.",
        )
        if created:
            alerts_created += 1

    if _has_irregular_rent_pattern(rents, six_months_ago):
        _, created = AIAlert.objects.get_or_create(
            owner=owner,
            alert_type="Irregular Rent",
            message=f"{renter.name} has delayed rent 3+ times recently.",
        )
        if created:
            alerts_created += 1

    return alerts_created


def _has_missed_consecutive_months(recent: list[RentRecord]) -> bool:
    return len(recent) >= 2 and all(r.status == "PENDING" for r in recent[:2])


def _has_irregular_rent_pattern(rents: Any, six_months_ago: date) -> bool:
    past_six = rents.filter(paid_on__gte=six_months_ago)
    delayed_count = 0
    for r in past_six:
        if r.status == "PAID" and r.paid_on is not None and r.paid_on > r.due_date:
            delayed_count += 1
    return delayed_count >= 3
