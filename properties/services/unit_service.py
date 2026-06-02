"""
Unit Service Module

Provides business logic for managing unit status and operations.
Handles automatic synchronization of unit occupancy status based on renter data.
"""

from ..models import Renter, Unit


def update_unit_status(unit: Unit) -> None:
    """
    Auto-update unit's status based on active renters.

    A unit is marked as "occupied" if it has an active renter,
    otherwise it's marked as "vacant".

    Args:
        unit (Unit): The unit whose status should be updated

    Returns:
        None

    Side Effects:
        - Updates unit.status to "occupied" or "vacant"
        - Updates unit.is_vacant denormalized field
        - Saves changes to database
    """
    # Check if there's an active renter
    active_renter = Renter.objects.filter(
        unit=unit, status__in=["active", "notice_period"]
    ).exists()

    # Determine new status
    new_status = (
        Unit.VacancyStatus.OCCUPIED if active_renter else Unit.VacancyStatus.VACANT
    )
    is_vacant = not active_renter

    # Only update if status has changed
    if unit.status != new_status or unit.is_vacant != is_vacant:
        unit.status = new_status
        unit.is_vacant = is_vacant
        unit.save(update_fields=["status", "is_vacant", "updated_at"])


def get_building_analytics(building) -> dict:
    """
    Get analytics for a specific building.

    Args:
        building: The Building object

    Returns:
        dict: Analytics with total, occupied, and vacant counts
    """
    from ..models import Unit

    units = Unit.objects.filter(building=building, is_archived=False)
    total = units.count()
    occupied = units.filter(
        status__in=[Unit.VacancyStatus.OCCUPIED, "OCCUPIED"]
    ).count()
    vacant = total - occupied

    return {
        "building_id": building.id,
        "building_name": building.name,
        "total_units": total,
        "occupied_units": occupied,
        "vacant_units": vacant,
        "occupancy_rate": round((occupied / total * 100), 2) if total > 0 else 0,
    }


def get_owner_analytics(user) -> dict:
    """
    Get comprehensive analytics for all buildings owned by a user.

    Args:
        user: The User/owner object

    Returns:
        dict: Aggregated analytics across all buildings
    """
    from ..models import Building

    buildings = Building.objects.filter(owner=user, is_archived=False)
    buildings_data = []

    total_units = 0
    total_occupied = 0
    total_vacant = 0

    for building in buildings:
        analytics = get_building_analytics(building)
        buildings_data.append(analytics)

        total_units += analytics["total_units"]
        total_occupied += analytics["occupied_units"]
        total_vacant += analytics["vacant_units"]

    return {
        "owner_id": user.id,
        "total_buildings": len(buildings_data),
        "buildings": buildings_data,
        "aggregate": {
            "total_units": total_units,
            "occupied_units": total_occupied,
            "vacant_units": total_vacant,
            "overall_occupancy_rate": (
                round((total_occupied / total_units * 100), 2) if total_units > 0 else 0
            ),
        },
    }
