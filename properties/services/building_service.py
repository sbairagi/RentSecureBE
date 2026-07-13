"""Building Service Module.

Provides business logic for managing buildings.
Owns building creation, updates, validation, and owner-level operations.
"""

from __future__ import annotations

from typing import Any

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
        raise NotImplementedError

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
