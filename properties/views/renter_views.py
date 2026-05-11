from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.core.cache import cache
from ..models import Renter
from ..serializers import RenterSerializer
from ..feature_enforcer import FeatureEnforcer


class RenterViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RenterSerializer

    def get_queryset(self):
        cache_key = f'renters_user_{self.request.user.id}'
        renters = cache.get(cache_key)
        if renters is None:
            renters = Renter.objects.filter(unit__owner=self.request.user, status__in=["active", "notice_period"])
            cache.set(cache_key, renters, timeout=300)
        return renters

    def perform_create(self, serializer):
        unit = serializer.validated_data.get('unit')
        if not unit or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")

        enforcer = FeatureEnforcer(self.request.user)
        if not enforcer.can_create('max_renters'):
            raise PermissionDenied("Renter limit reached for your plan.")

        serializer.save()
        enforcer.increment('max_renters')
        cache.delete(f'renters_user_{self.request.user.id}')

    def perform_update(self, serializer):
        unit = serializer.validated_data.get('unit') or serializer.instance.unit
        if unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        serializer.save()
        cache.delete(f'renters_user_{self.request.user.id}')

    def perform_destroy(self, instance):
        if instance.unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement('max_renters')
        cache.delete(f'renters_user_{self.request.user.id}')
