from datetime import date, timedelta

from ..models import ExtraCharge, Renter


def generate_monthly_extra_charges():
    today = date.today()
    maintenance_date = date(today.year, today.month, 5)
    electricity_date = date(today.year, today.month, 15)
    created = []

    active_renters = Renter.objects.filter(status=Renter.RenterStatus.ACTIVE)
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


def get_due_extra_charges(days=3):
    target_date = date.today() + timedelta(days=days)
    return ExtraCharge.objects.filter(
        status=ExtraCharge.Status.DUE, due_date__lte=target_date
    ).select_related("renter", "unit")
