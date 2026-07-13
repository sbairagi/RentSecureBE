from typing import Any

from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import BaseSerializer

from django.core.cache import cache

from rentsecure_be.type_compat import override

from ..constants import BUILDINGS_CACHE_TIMEOUT
from ..feature_enforcer import FeatureEnforcer
from ..models import Building
from ..serializers import BuildingSerializer
from ..services.building_service import BuildingService


class BuildingViewSet(viewsets.ModelViewSet[Building]):
    serializer_class = BuildingSerializer
    permission_classes = [IsAuthenticated]

    @override
    def get_queryset(self) -> Any:
        user = self.request.user
        cache_key = f"buildings_user_{user.id}"
        enforcer = FeatureEnforcer(user)

        buildings = cache.get(cache_key)
        if buildings is None:
            buildings = Building.objects.filter(owner=user)
            cache.set(cache_key, buildings, timeout=BUILDINGS_CACHE_TIMEOUT)

        if enforcer.is_expired() and enforcer.is_past_grace_period():
            free_limit = enforcer.get_free_plan_limit("max_buildings")
            active_buildings = buildings.filter(is_archived=False)
            if free_limit == "unlimited":
                return active_buildings
            return active_buildings[:free_limit]

        return buildings

    @override
    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        building = BuildingService.create_building(
            self.request.user, serializer.validated_data
        )
        serializer.instance = building

    @override
    def perform_update(self, serializer: BaseSerializer[Any]) -> None:
        if serializer.instance.owner != self.request.user:
            raise PermissionDenied(
                "You do not have permission to update this building."
            )
        serializer.save()
        cache.delete(f"buildings_user_{self.request.user.id}")

    @override
    def perform_destroy(self, instance: Building) -> None:
        if instance.owner != self.request.user:
            raise PermissionDenied(
                "You do not have permission to delete this building."
            )
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement("max_buildings")
        cache.delete(f"buildings_user_{self.request.user.id}")
