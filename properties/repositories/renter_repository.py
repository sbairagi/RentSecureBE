"""Renter Repository Module.

Provides low-level ORM access for the Renter model.
No business logic, validation, or HTTP concerns.
"""

from __future__ import annotations

from typing import Any

from ..models.renter_models import Renter


class RenterRepository:
    """Repository for Renter ORM operations."""

    @staticmethod
    def get_by_id(renter_id: int) -> Renter | None:
        """Return a Renter by primary key, or None."""
        return Renter.objects.filter(pk=renter_id).first()

    @staticmethod
    def get_queryset() -> Any:
        """Return the base Renter queryset."""
        return Renter.objects.all()

    @staticmethod
    def owned_by(user: Any) -> Any:
        """Return renters whose unit is owned by the given user."""
        return Renter.objects.filter(unit__owner=user)

    @staticmethod
    def active() -> Any:
        """Return active renters."""
        return Renter.objects.filter(status="active")

    @staticmethod
    def by_unit(unit: Any) -> Any:
        """Return renters for a given unit."""
        return Renter.objects.filter(unit=unit)

    @staticmethod
    def with_related() -> Any:
        """Return renters with related unit and building prefetched."""
        return Renter.objects.select_related("unit", "unit__building")
