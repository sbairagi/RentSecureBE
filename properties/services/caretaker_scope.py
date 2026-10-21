"""The scope of a caretaker.

A caretaker works for one owner and is given buildings and standalone units
of that owner. These helpers answer one question in one place: which
properties belong to a caretaker, and which caretakers look after a home.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import Q, QuerySet

if TYPE_CHECKING:
    from properties.models import CareTaker, Unit


def assigned_building_ids(caretaker: CareTaker) -> set[int]:
    """Return the buildings assigned to the caretaker."""
    return set(
        caretaker.assignments.filter(
            is_active=True, building__isnull=False
        ).values_list("building_id", flat=True)
    )


def assigned_unit_ids(caretaker: CareTaker) -> set[int]:
    """Return the homes the caretaker looks after.

    A building assignment covers every unit of that building, a unit
    assignment covers a single home. When the caretaker has no assignment
    yet, the legacy home unit is used.
    """
    from properties.models import Unit

    unit_ids = set(
        caretaker.assignments.filter(is_active=True, unit__isnull=False).values_list(
            "unit_id", flat=True
        )
    )
    building_ids = assigned_building_ids(caretaker)
    if building_ids:
        unit_ids |= set(
            Unit.objects.filter(building_id__in=building_ids).values_list(
                "id", flat=True
            )
        )
    if not unit_ids and caretaker.unit_id:
        unit_ids.add(caretaker.unit_id)
    return unit_ids


def scope_queryset(caretaker: CareTaker) -> QuerySet[Unit]:
    """Return the units of the caretaker as a queryset."""
    from properties.models import Unit

    return Unit.objects.filter(id__in=assigned_unit_ids(caretaker))


def covers_unit(caretaker: CareTaker, unit: Unit) -> bool:
    """Return whether the caretaker looks after the given home."""
    if caretaker.owner_id != unit.owner_id:
        return False
    return unit.id in assigned_unit_ids(caretaker)


def caretakers_for_unit(unit: Unit) -> QuerySet[CareTaker]:
    """Return the active caretakers that look after the given home.

    A caretaker is in the scope of a home when the home is assigned to them
    directly, when its building is assigned to them, or — for the older data
    without any assignment — when the home is their registered home unit.
    """
    from properties.models import CareTaker

    return (
        CareTaker.objects.filter(
            Q(assignments__unit=unit, assignments__is_active=True)
            | Q(
                assignments__building_id=unit.building_id,
                assignments__is_active=True,
            )
            | Q(unit=unit)
        )
        .filter(is_active=True)
        .distinct()
    )
