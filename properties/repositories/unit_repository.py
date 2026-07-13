"""Unit Repository Module.

Provides low-level ORM access for the Unit model.
No business logic, validation, or HTTP concerns.
"""

from __future__ import annotations

from typing import Any

from ..models import Unit


class UnitRepository:
    """Repository for Unit ORM operations."""

    @staticmethod
    def get_by_id(unit_id: int) -> Unit | None:
        """Return a Unit by primary key, or None."""
        return Unit.objects.filter(pk=unit_id).first()

    @staticmethod
    def get_queryset() -> Any:
        """Return the base Unit queryset."""
        return Unit.objects.all()

    @staticmethod
    def owned_by(user: Any) -> Any:
        """Return units owned by the given user."""
        return Unit.objects.filter(owner=user)

    @staticmethod
    def active() -> Any:
        """Return non-archived units."""
        return Unit.objects.filter(is_archived=False)

    @staticmethod
    def active_owned_by(user: Any) -> Any:
        """Return non-archived units owned by the given user."""
        return Unit.objects.filter(owner=user, is_archived=False)

    @staticmethod
    def with_related() -> Any:
        """Return units with related owner and building prefetched."""
        return Unit.objects.select_related("owner", "building")

    @staticmethod
    def by_building(building: Any) -> Any:
        """Return units for a given building."""
        return Unit.objects.filter(building=building)

    @staticmethod
    def by_building_and_owner(building: Any, user: Any) -> Any:
        """Return units for a given building and owner."""
        return Unit.objects.filter(building=building, owner=user)
