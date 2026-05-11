from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.core.cache import cache
from ..models import Caretaker
from ..serializers import CaretakerSerializer
from ..feature_enforcer import FeatureEnforcer


class CaretakerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CaretakerSerializer

    def get_queryset(self):
        cache_key = f'caretakers_user_{self.request.user.id}'
        caretakers = cache.get(cache_key)
        if caretakers is None:
            caretakers = Caretaker.objects.filter(unit__owner=self.request.user)
            cache.set(cache_key, caretakers, timeout=300)
        return caretakers

    def perform_create(self, serializer):
        unit = serializer.validated_data.get('unit')
        if not unit or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")

        enforcer = FeatureEnforcer(self.request.user)
        if not enforcer.can_create('max_caretakers'):
            raise PermissionDenied("Caretaker limit reached for your plan.")

        serializer.save()
        enforcer.increment('max_caretakers')
        cache.delete(f'caretakers_user_{self.request.user.id}')

    def perform_update(self, serializer):
        unit = serializer.validated_data.get('unit') or serializer.instance.unit
        if unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        serializer.save()
        cache.delete(f'caretakers_user_{self.request.user.id}')

    def perform_destroy(self, instance):
        if instance.unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement('max_caretakers')
        cache.delete(f'caretakers_user_{self.request.user.id}')
