from typing import Any

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import BaseSerializer

from rentsecure_be.type_compat import override

from ..models import Building
from ..serializers import BuildingSerializer
from ..services.building_service import BuildingService


class BuildingViewSet(viewsets.ModelViewSet[Building]):
    serializer_class = BuildingSerializer
    permission_classes = [IsAuthenticated]

    @override
    def get_queryset(self) -> Any:
        return BuildingService.get_owner_buildings(self.request.user)

    @override
    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        building = BuildingService.create_building(
            self.request.user, serializer.validated_data
        )
        serializer.instance = building

    @override
    def perform_update(self, serializer: BaseSerializer[Any]) -> None:
        building = BuildingService.update_building(
            serializer.instance, self.request.user, serializer.validated_data
        )
        serializer.instance = building

    @override
    def perform_destroy(self, instance: Building) -> None:
        BuildingService.archive_building(instance, self.request.user)
