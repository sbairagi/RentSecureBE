"""Building Repository Module.

Provides low-level ORM access for the Building model.
No business logic, validation, or HTTP concerns.
"""

from __future__ import annotations

from typing import Any

from ..models.building_models import Building


class BuildingRepository:
    """Repository for Building ORM operations."""

    @staticmethod
    def get_by_id(building_id: int) -> Building | None:
        """Return a Building by primary key, or None."""
        return Building.objects.filter(pk=building_id).first()

    @staticmethod
    def get_queryset() -> Any:
        """Return the base Building queryset."""
        return Building.objects.all()

    @staticmethod
    def owned_by(user: Any) -> Any:
        """Return buildings owned by the given user."""
        return Building.objects.filter(owner=user)

    @staticmethod
    def active() -> Any:
        """Return non-archived buildings."""
        return Building.objects.filter(is_archived=False)

    @staticmethod
    def active_owned_by(user: Any) -> Any:
        """Return non-archived buildings owned by the given user."""
        return Building.objects.filter(owner=user, is_archived=False)

    @staticmethod
    def with_related() -> Any:
        """Return buildings with related owner prefetched."""
        return Building.objects.select_related("owner")
