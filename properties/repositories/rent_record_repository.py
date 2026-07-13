"""RentRecord Repository Module.

Provides low-level ORM access for the RentRecord model.
No business logic, validation, or HTTP concerns.
"""

from __future__ import annotations

from typing import Any

from ..models.rent_record_models import RentRecord


class RentRecordRepository:
    """Repository for RentRecord ORM operations."""

    @staticmethod
    def get_by_id(rent_id: int) -> RentRecord | None:
        """Return a RentRecord by primary key, or None."""
        return RentRecord.objects.filter(pk=rent_id).first()

    @staticmethod
    def get_queryset() -> Any:
        """Return the base RentRecord queryset."""
        return RentRecord.objects.all()

    @staticmethod
    def owned_by(user: Any) -> Any:
        """Return rent records for units owned by the given user."""
        return RentRecord.objects.filter(unit__owner=user)

    @staticmethod
    def by_unit(unit: Any) -> Any:
        """Return rent records for a given unit."""
        return RentRecord.objects.filter(unit=unit)

    @staticmethod
    def by_status(status: str) -> Any:
        """Return rent records with the given status."""
        return RentRecord.objects.filter(status=status)

    @staticmethod
    def with_related() -> Any:
        """Return rent records with related unit and renter prefetched."""
        return RentRecord.objects.select_related("unit", "renter", "unit__owner")
