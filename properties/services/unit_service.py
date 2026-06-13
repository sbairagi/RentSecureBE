"""
Unit Service Module
===================

Provides business logic for managing unit status and operations.
Handles automatic synchronization of unit occupancy status based on renter data.

Type Safety
-----------
All public functions are fully annotated for strict mypy. Internal helpers
return explicit ``TypedDict`` payloads so callers can rely on a stable
shape without having to read the implementation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from ..models import Renter, Unit
from ..models.building_models import Building

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


# ---------------------------------------------------------------------------
# Typed payloads — keep the public contract stable & mypy-friendly.
# ---------------------------------------------------------------------------


class BuildingAnalytics(TypedDict):
    """Analytics payload for a single building."""

    building_id: int
    building_name: str
    total_units: int
    occupied_units: int
    vacant_units: int
    occupancy_rate: float


class OwnerAggregate(TypedDict):
    """Aggregated analytics across all buildings of an owner."""

    total_units: int
    occupied_units: int
    vacant_units: int
    overall_occupancy_rate: float


class OwnerAnalytics(TypedDict):
    """Comprehensive analytics payload for an owner."""

    owner_id: int
    total_buildings: int
    buildings: list[BuildingAnalytics]
    aggregate: OwnerAggregate


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


def update_unit_status(unit: Unit) -> None:
    """
    Auto-update unit's status based on active renters.

    A unit is marked as "occupied" if it has an active renter,
    otherwise it's marked as "vacant".

    Args:
        unit: The unit whose status should be updated.

    Side Effects:
        - Updates ``unit.status`` to ``OCCUPIED`` or ``VACANT``.
        - Updates ``unit.is_vacant`` denormalized field.
        - Persists changes to the database.
    """
    active_renter: bool = Renter.objects.filter(
        unit=unit, status__in=["active", "notice_period"]
    ).exists()

    new_status: str = (
        Unit.VacancyStatus.OCCUPIED if active_renter else Unit.VacancyStatus.VACANT
    )
    is_vacant: bool = not active_renter

    if unit.status != new_status or unit.is_vacant != is_vacant:
        unit.status = new_status
        unit.is_vacant = is_vacant
        unit.save(update_fields=["status", "is_vacant", "updated_at"])


def get_building_analytics(building: Building) -> BuildingAnalytics:
    """
    Get analytics for a specific building.

    Args:
        building: The ``Building`` instance to analyze.

    Returns:
        A :class:`BuildingAnalytics` ``TypedDict`` with totals and rates.
    """
    units = Unit.objects.filter(building=building, is_archived=False)
    total: int = units.count()
    occupied: int = units.filter(
        status__in=[Unit.VacancyStatus.OCCUPIED, "OCCUPIED"]
    ).count()
    vacant: int = total - occupied
    occupancy_rate: float = (
        round((occupied / total * 100), 2) if total > 0 else 0.0
    )

    return BuildingAnalytics(
        building_id=building.id,
        building_name=building.name,
        total_units=total,
        occupied_units=occupied,
        vacant_units=vacant,
        occupancy_rate=occupancy_rate,
    )


def get_owner_analytics(user: AbstractUser) -> OwnerAnalytics:
    """
    Get comprehensive analytics for all buildings owned by a user.

    Args:
        user: The owning user (any ``AbstractUser`` implementation).

    Returns:
        An :class:`OwnerAnalytics` ``TypedDict`` with per-building details
        and aggregate totals.
    """
    buildings = Building.objects.filter(owner=user, is_archived=False)
    buildings_data: list[BuildingAnalytics] = []

    total_units = 0
    total_occupied = 0
    total_vacant = 0

    for building in buildings:
        analytics = get_building_analytics(building)
        buildings_data.append(analytics)

        total_units += analytics["total_units"]
        total_occupied += analytics["occupied_units"]
        total_vacant += analytics["vacant_units"]

    return OwnerAnalytics(
        owner_id=user.id,
        total_buildings=len(buildings_data),
        buildings=buildings_data,
        aggregate=OwnerAggregate(
            total_units=total_units,
            occupied_units=total_occupied,
            vacant_units=total_vacant,
            overall_occupancy_rate=(
                round((total_occupied / total_units * 100), 2)
                if total_units > 0
                else 0.0
            ),
        ),
    )
