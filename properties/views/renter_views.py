from django.core.cache import cache
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..feature_enforcer import FeatureEnforcer
from ..models import Renter
from ..serializers import RenterSerializer
from ..services.unit_service import update_unit_status
from ..utils import check_feature_limit


class RenterViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RenterSerializer

    def get_queryset(self):
        cache_key = f'renters_user_{self.request.user.id}'
        renters = cache.get(cache_key)
        if renters is None:
            renters = Renter.objects.filter(
                unit__owner=self.request.user,
                status__in=["active", "notice_period"]
            )
            cache.set(cache_key, renters, timeout=300)
        return renters

    def create(self, request, *args, **kwargs):
        allowed, current_usage, subscription_limit, add_on_limit = (
            check_feature_limit(request.user, 'max_renters')
        )
        if not allowed:
            return Response({
                'error': "You’ve reached your renter limit.",
                'required_add_on': 'max_renters',
                'subscription_limit': subscription_limit,
                'add_on_limit': add_on_limit,
                'current_usage': current_usage,
            }, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        unit = serializer.validated_data.get('unit')
        if not unit or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")

        enforcer = FeatureEnforcer(self.request.user)
        if not enforcer.can_create('max_renters'):
            raise PermissionDenied("Renter limit reached for your plan.")

        serializer.save()
        enforcer.increment('max_renters')
        update_unit_status(unit)  # Auto-update unit occupancy status
        cache.delete(f'renters_user_{self.request.user.id}')

    def perform_update(self, serializer):
        unit = serializer.validated_data.get('unit') or serializer.instance.unit
        if unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        serializer.save()
        update_unit_status(unit)  # Auto-update unit occupancy status
        cache.delete(f'renters_user_{self.request.user.id}')

    def perform_destroy(self, instance):
        if instance.unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        unit = instance.unit
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement('max_renters')
        update_unit_status(unit)  # Auto-update unit occupancy status
        cache.delete(f'renters_user_{self.request.user.id}')
