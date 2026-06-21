from typing import Any

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import BaseSerializer

from rentsecure_be.type_compat import override

from ..feature_enforcer import FeatureEnforcer
from ..models import Caretaker, Unit
from ..serializers import CaretakerSerializer


class CaretakerViewSet(viewsets.ModelViewSet[Caretaker]):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]
    serializer_class = CaretakerSerializer

    @override
    def get_queryset(self) -> Any:
        if isinstance(self.request.user, AnonymousUser):
            return Caretaker.objects.none()
        user = self.request.user
        cache_key = f"caretakers_user_{user.id}"
        caretakers = cache.get(cache_key)
        if caretakers is None:
            caretakers = Caretaker.objects.filter(unit__owner=user)
            cache.set(cache_key, caretakers, timeout=300)
        return caretakers

    @override
    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        unit: Unit | None = serializer.validated_data.get("unit")
        if not unit or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")

        enforcer = FeatureEnforcer(self.request.user)
        if not enforcer.can_create("max_caretakers"):
            raise PermissionDenied("Caretaker limit reached for your plan.")

        serializer.save()
        enforcer.increment("max_caretakers")
        cache.delete(f"caretakers_user_{self.request.user.id}")

    @override
    def perform_update(self, serializer: BaseSerializer[Any]) -> None:
        unit: Unit | None = (
            serializer.validated_data.get("unit") or serializer.instance.unit
        )
        if unit is None or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        serializer.save()
        cache.delete(f"caretakers_user_{self.request.user.id}")

    @override
    def perform_destroy(self, instance: Caretaker) -> None:
        if instance.unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement("max_caretakers")
        cache.delete(f"caretakers_user_{self.request.user.id}")
