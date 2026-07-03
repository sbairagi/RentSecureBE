# services/unit_service.py

from typing import Any

from properties.models import Renter


def update_unit_status(unit: Any) -> None:
    active_renter = Renter.objects.filter(unit=unit, status="active").first()
    unit.status = "occupied" if active_renter else "vacant"
    unit.save()
