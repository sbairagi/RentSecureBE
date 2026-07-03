"""Extra charge service.

Pure service layer for monthly extra-charge generation and retrieval.
All public functions are fully typed and side-effect-isolated.
"""

from __future__ import annotations

from datetime import date, timedelta

from django.db.models import QuerySet

from ..models import ExtraCharge, Renter


def generate_monthly_extra_charges() -> list[ExtraCharge]:
    """Generate the monthly maintenance and electricity charges for all
    active renters.

    Idempotent per (renter, name, due_date) tuple — calling repeatedly in
    the same month is safe.

    Returns:
        The list of newly created :class:`ExtraCharge` instances. The list
        is empty if nothing new was created.
    """
    today: date = date.today()
    maintenance_date: date = date(today.year, today.month, 5)
    electricity_date: date = date(today.year, today.month, 15)
    created: list[ExtraCharge] = []

    active_renters: QuerySet[Renter] = Renter.objects.filter(
        status=Renter.RenterStatus.ACTIVE
    )
    for renter in active_renters:
        if not ExtraCharge.objects.filter(
            renter=renter,
            unit=renter.unit,
            name="Maintenance",
            due_date=maintenance_date,
        ).exists():
            created.append(
                ExtraCharge.objects.create(
                    renter=renter,
                    unit=renter.unit,
                    name="Maintenance",
                    amount=500,
                    due_date=maintenance_date,
                )
            )

        if not ExtraCharge.objects.filter(
            renter=renter,
            unit=renter.unit,
            name="Electricity",
            due_date=electricity_date,
        ).exists():
            created.append(
                ExtraCharge.objects.create(
                    renter=renter,
                    unit=renter.unit,
                    name="Electricity",
                    amount=1000,
                    due_date=electricity_date,
                )
            )

    return created


def get_due_extra_charges(days: int = 3) -> QuerySet[ExtraCharge]:
    """Return extra charges that become due within the next ``days`` days.

    Args:
        days: Lookahead window in days. Defaults to ``3``.

    Returns:
        A ``QuerySet`` of :class:`ExtraCharge` instances with related
        renter and unit pre-fetched for efficient iteration.
    """
    target_date: date = date.today() + timedelta(days=days)
    return ExtraCharge.objects.filter(
        status=ExtraCharge.Status.DUE,
        due_date__lte=target_date,
    ).select_related("renter", "unit")
