from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.core.cache import cache
from ..models import Building
from ..serializers import BuildingSerializer
from ..feature_enforcer import FeatureEnforcer
from ..constants import BUILDINGS_CACHE_TIMEOUT


class BuildingViewSet(viewsets.ModelViewSet):
    serializer_class = BuildingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        cache_key = f"buildings_user_{user.id}"
        enforcer = FeatureEnforcer(user)

        buildings = cache.get(cache_key)
        if buildings is None:
            buildings = Building.objects.filter(owner=user)
            cache.set(cache_key, buildings, timeout=BUILDINGS_CACHE_TIMEOUT)

        if enforcer.is_expired() and enforcer.is_past_grace_period():
            free_limit = enforcer.get_free_plan_limit('max_buildings')
            active_buildings = buildings.filter(is_archived=False)
            if free_limit == 'unlimited':
                return active_buildings
            return active_buildings[:free_limit]

        return buildings

    def perform_create(self, serializer):
        user = self.request.user
        enforcer = FeatureEnforcer(user)

        if not enforcer.can_create('max_buildings'):
            raise PermissionDenied("Building creation limit reached for your plan.")

        serializer.save(owner=user)
        enforcer.increment('max_buildings')
        cache.delete(f"buildings_user_{user.id}")

    def perform_update(self, serializer):
        if serializer.instance.owner != self.request.user:
            raise PermissionDenied("You do not have permission to update this building.")
        serializer.save()
        cache.delete(f"buildings_user_{self.request.user.id}")

    def perform_destroy(self, instance):
        if instance.owner != self.request.user:
            raise PermissionDenied("You do not have permission to delete this building.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement('max_buildings')
        cache.delete(f"buildings_user_{self.request.user.id}")
