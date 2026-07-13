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

from typing import Any, TypedDict

from rest_framework import serializers

from core.models import User

from ..constants import UNITS_CACHE_TIMEOUT
from ..models import Renter, Unit
from ..models.building_models import Building
from ..repositories.unit_repository import UnitRepository

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
# Business workflow helpers
# ---------------------------------------------------------------------------


def validate_building_access(building: Building | None, user: User) -> None:
    """Raise ``ValidationError`` when the user does not own the building."""
    if building is None or building.owner != user:
        raise serializers.ValidationError("You do not own the selected building.")


def validate_coordinates(latitude: float | None, longitude: float | None) -> None:
    """Raise ``ValidationError`` when coordinates are outside valid ranges."""
    if latitude is not None and not -90 <= latitude <= 90:
        raise serializers.ValidationError("Latitude must be between -90 and 90.")
    if longitude is not None and not -180 <= longitude <= 180:
        raise serializers.ValidationError("Longitude must be between -180 and 180.")


def prepare_unit_creation(validated_data: dict[str, Any], user: User) -> dict[str, Any]:
    """Inject the owner into ``validated_data`` for unit creation."""
    validated_data["owner"] = user
    return validated_data


# ---------------------------------------------------------------------------
# UnitService
# ---------------------------------------------------------------------------


class UnitService:
    """Service for unit business workflows.

    Expected responsibilities:
    - Unit queryset building with caching and free-plan enforcement
    - Unit ownership validation
    - Unit creation/deletion quota enforcement
    - Cache key management for unit queries
    """

    UNIT_CACHE_KEY = "units_user_{user_id}"
    UNIT_CACHE_TIMEOUT = UNITS_CACHE_TIMEOUT

    @staticmethod
    def get_unit_cache_key(user_id: int) -> str:
        """Return the cache key for a user's unit queryset."""
        return f"units_user_{user_id}"

    @staticmethod
    def get_unit_queryset(user: Any) -> Any:
        """Build unit queryset with caching and free-plan enforcement."""
        from django.core.cache import cache

        from ..feature_enforcer import FeatureEnforcer
        from ..models import Unit

        cache_key = UnitService.get_unit_cache_key(user.id)
        units = cache.get(cache_key)
        if units is None:
            units = Unit.objects.filter(owner=user)
            cache.set(cache_key, units, timeout=UnitService.UNIT_CACHE_TIMEOUT)

        enforcer = FeatureEnforcer(user)
        if enforcer.is_expired() and enforcer.is_past_grace_period():
            free_limit = enforcer.get_free_plan_limit("max_units")
            active_units = units.filter(is_archived=False)
            if free_limit == "unlimited":
                return active_units
            return active_units[:free_limit]

        return units

    @staticmethod
    def validate_unit_access(unit: Any, user: Any) -> None:
        """Raise ``ValueError`` when the user does not own the unit."""
        if unit is None or unit.owner != user:
            raise ValueError("You do not have permission to access this unit.")

    @staticmethod
    def can_create_unit(user: Any) -> bool:
        """Check if the user can create a unit based on plan limits."""
        from ..feature_enforcer import FeatureEnforcer

        enforcer = FeatureEnforcer(user)
        return enforcer.can_create("max_units")

    @staticmethod
    def increment_unit_quota(user: Any) -> None:
        """Increment the user's unit creation quota."""
        from ..feature_enforcer import FeatureEnforcer

        enforcer = FeatureEnforcer(user)
        enforcer.increment("max_units")

    @staticmethod
    def decrement_unit_quota(user: Any) -> None:
        """Decrement the user's unit creation quota."""
        from ..feature_enforcer import FeatureEnforcer

        enforcer = FeatureEnforcer(user)
        enforcer.decrement("max_units")


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
    units = UnitRepository.by_building_active(building)
    total: int = units.count()
    occupied: int = units.filter(
        status__in=[Unit.VacancyStatus.OCCUPIED, "OCCUPIED"]
    ).count()
    vacant: int = total - occupied
    occupancy_rate: float = round((occupied / total * 100), 2) if total > 0 else 0.0

    return BuildingAnalytics(
        building_id=building.id,
        building_name=building.name,
        total_units=total,
        occupied_units=occupied,
        vacant_units=vacant,
        occupancy_rate=occupancy_rate,
    )


def get_owner_analytics(user: User) -> OwnerAnalytics:
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
