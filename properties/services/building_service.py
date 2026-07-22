"""Building Service Module.

Provides business logic for managing buildings.
Owns building creation, updates, validation, and owner-level operations.
"""

from __future__ import annotations

from typing import Any, cast

from rest_framework.exceptions import PermissionDenied

from core.events.domain.publisher import DomainEventPublisher

from ..constants import BUILDINGS_CACHE_TIMEOUT
from ..feature_enforcer import FeatureEnforcer
from ..repositories.building_repository import BuildingRepository


class BuildingService:
    """Service for building business workflows.

    Expected responsibilities:
    - Building creation and ownership validation
    - Building archive/restore operations
    - Building search and filtering
    - Owner-level building aggregation
    """

    @staticmethod
    def create_building(user: Any, validated_data: dict[str, Any]) -> Any:
        """Create a building for the given user after enforcing plan limits."""
        from django.core.cache import cache

        from ..models import Building

        enforcer = FeatureEnforcer(user)
        if not enforcer.can_create("max_buildings"):
            raise PermissionDenied("Building creation limit reached for your plan.")

        building = Building.objects.create(owner=user, **validated_data)
        enforcer.increment("max_buildings")
        cache.delete(f"buildings_user_{user.id}")

        from uuid import UUID

        from django.db import transaction

        from core.events.domain.property_events import BuildingCreated

        event = BuildingCreated(
            aggregate_id=UUID(int=building.pk),
            building_id=UUID(int=building.pk),
            owner_id=UUID(int=user.pk),
            name=building.name,
            city=building.city,
        )

        transaction.on_commit(
            lambda: DomainEventPublisher.get_instance().publish(event)
        )

        return building

    @staticmethod
    def update_building(
        building: Any, user: Any, validated_data: dict[str, Any]
    ) -> Any:
        """Update a building after ownership validation."""
        from django.core.cache import cache

        if building.owner != user:
            raise PermissionDenied(
                "You do not have permission to update this building."
            )
        changed_fields = list(validated_data.keys())
        for attr, value in validated_data.items():
            setattr(building, attr, value)
        building.save(update_fields=list(validated_data.keys()))
        cache.delete(f"buildings_user_{user.id}")

        from uuid import UUID

        from django.db import transaction

        from core.events.domain.property_events import BuildingUpdated

        event = BuildingUpdated(
            aggregate_id=UUID(int=building.pk),
            building_id=UUID(int=building.pk),
            owner_id=UUID(int=user.pk),
            changed_fields=changed_fields,
        )

        transaction.on_commit(
            lambda: DomainEventPublisher.get_instance().publish(event)
        )

        return building

    @staticmethod
    def archive_building(building: Any, user: Any) -> None:
        """Archive a building after ownership validation."""
        from django.core.cache import cache

        if building.owner != user:
            raise PermissionDenied(
                "You do not have permission to delete this building."
            )
        building.is_archived = True
        building.save(update_fields=["is_archived"])
        enforcer = FeatureEnforcer(user)
        enforcer.decrement("max_buildings")
        cache.delete(f"buildings_user_{user.id}")

        from uuid import UUID

        from django.db import transaction

        from core.events.domain.property_events import BuildingArchived

        event = BuildingArchived(
            aggregate_id=UUID(int=building.pk),
            building_id=UUID(int=building.pk),
            owner_id=UUID(int=user.pk),
        )

        transaction.on_commit(
            lambda: DomainEventPublisher.get_instance().publish(event)
        )

    @staticmethod
    def get_owner_buildings(user: Any) -> Any:
        """Return buildings owned by the given user with caching and free-plan
        enforcement.
        """
        from django.core.cache import cache

        cache_key = f"buildings_user_{user.id}"
        enforcer = FeatureEnforcer(user)

        buildings = cache.get(cache_key)
        if buildings is None:
            buildings = BuildingRepository.owned_by(user)
            cache.set(cache_key, buildings, timeout=BUILDINGS_CACHE_TIMEOUT)

        if enforcer.is_expired() and enforcer.is_past_grace_period():
            free_limit = enforcer.get_free_plan_limit("max_buildings")
            active_buildings = buildings.filter(is_archived=False)
            if free_limit == "unlimited":
                return active_buildings
            return active_buildings[:free_limit]

        return buildings

    @staticmethod
    def validate_ownership(building: Any, user: Any) -> bool:
        """Return True if the user owns the building."""
        return cast(bool, building.owner == user)
