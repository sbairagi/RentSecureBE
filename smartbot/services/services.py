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
        rents = RentRecord.objects.filter(renter=renter).order_by("-rent_month")

        # 1. Missed 2+ consecutive months
        # Use the same slice window the original implementation used
        # (3 records) to preserve closest behavioural parity.
        recent = list(rents[:3])
        if len(recent) >= 2 and all(r.payment_status == "PENDING" for r in recent[:2]):
            _, created = AIAlert.objects.get_or_create(
                owner=owner,
                alert_type="Missed Rent",
                message=f"{renter.name} missed last 2+ months rent.",
            )
            if created:
                alerts_created += 1

        # 2. Irregular rent pattern — use canonical field names
        #    (RentRecord has no ``paid_date``; it is ``date_paid``)
        past_six = rents.filter(paid_on__gte=six_months_ago)
        delayed_count = sum(
            1
            for r in past_six
            if r.payment_status == "PAID"
            and r.date_paid is not None
            and r.date_paid > r.due_date
        )
        if delayed_count >= 3:
            _, created = AIAlert.objects.get_or_create(
                owner=owner,
                alert_type="Irregular Rent",
                message=f"{renter.name} has delayed rent 3+ times recently.",
            )
            if created:
                alerts_created += 1

    return alerts_created
