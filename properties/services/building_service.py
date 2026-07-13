"""Building Service Module.

Provides business logic for managing buildings.
Owns building creation, updates, validation, and owner-level operations.
"""

from __future__ import annotations

from typing import Any

from rest_framework.exceptions import PermissionDenied

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

        from ..feature_enforcer import FeatureEnforcer
        from ..models import Building

        enforcer = FeatureEnforcer(user)
        if not enforcer.can_create("max_buildings"):
            raise PermissionDenied("Building creation limit reached for your plan.")

        building = Building.objects.create(owner=user, **validated_data)
        enforcer.increment("max_buildings")
        cache.delete(f"buildings_user_{user.id}")
        return building

    @staticmethod
    def update_building(
        building: Any, user: Any, validated_data: dict[str, Any]
    ) -> Any:
        raise NotImplementedError

    @staticmethod
    def archive_building(building: Any, user: Any) -> None:
        raise NotImplementedError

    @staticmethod
    def get_owner_buildings(user: Any) -> Any:
        """Return buildings owned by the given user."""
        return BuildingRepository.owned_by(user)

    @staticmethod
    def validate_ownership(building: Any, user: Any) -> bool:
        raise NotImplementedError
