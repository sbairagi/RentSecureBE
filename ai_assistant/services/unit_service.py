# services/unit_service.py

from properties.models import Renter


def update_unit_status(unit):
    active_renter = Renter.objects.filter(unit=unit, status="active").first()
    unit.status = "occupied" if active_renter else "vacant"
    unit.save()