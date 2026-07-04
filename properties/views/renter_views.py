from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache

from core.models import User
from rentsecure_be.type_compat import override

from ..feature_enforcer import FeatureEnforcer
from ..models import Renter, Unit
from ..serializers import RenterSerializer
from ..services.unit_service import update_unit_status
from ..utils import check_feature_limit

if TYPE_CHECKING:
    from django.db.models import QuerySet


class RenterViewSet(viewsets.ModelViewSet[Renter]):
    """CRUD for renters owned by the authenticated user.

    Uses a per-user cache (5 minute TTL) for list views to reduce
    database pressure on the dashboard.
    """

    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]
    serializer_class = RenterSerializer

    @override
    def get_queryset(self) -> QuerySet[Renter]:
        """Return the active/notice-period renters owned by the user."""
        if isinstance(self.request.user, AnonymousUser):
            return Renter.objects.none()
        user = self.request.user
        cache_key: str = f"renters_user_{user.id}"
        renters: QuerySet[Renter] | None = cache.get(cache_key)
        if renters is None:
            renters = Renter.objects.filter(
                unit__owner=user,
                status__in=["active", "notice_period"],
            )
            cache.set(cache_key, renters, timeout=300)
        return renters

    @override
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new renter, enforcing the per-plan limit first."""
        user = cast(User, request.user)
        allowed, current_usage, subscription_limit, add_on_limit = check_feature_limit(
            user, "max_renters"
        )
        if not allowed:
            payload: dict[str, Any] = {
                "error": "You've reached your renter limit.",
                "required_add_on": "max_renters",
                "subscription_limit": subscription_limit,
                "add_on_limit": add_on_limit,
                "current_usage": current_usage,
            }
            return Response(payload, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    @override
    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        """Persist a new renter, enforce ownership, and update unit state."""
        unit: Unit | None = serializer.validated_data.get("unit")
        if unit is None or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")  # noqa: S1192

        enforcer = FeatureEnforcer(self.request.user)
        if not enforcer.can_create("max_renters"):
            raise PermissionDenied("Renter limit reached for your plan.")

        serializer.save()
        enforcer.increment("max_renters")
        update_unit_status(unit)
        cache.delete(f"renters_user_{self.request.user.id}")

    @override
    def perform_update(self, serializer: BaseSerializer[Any]) -> None:
        """Persist updates and refresh unit state."""
        instance = serializer.instance
        unit: Unit | None = serializer.validated_data.get("unit") or (
            instance.unit if instance else None
        )
        if unit is None or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        serializer.save()
        update_unit_status(unit)
        cache.delete(f"renters_user_{self.request.user.id}")

    @override
    def perform_destroy(self, instance: Renter) -> None:
        """Delete a renter and free up plan quota."""
        if instance.unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        unit: Unit = instance.unit
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement("max_renters")
        update_unit_status(unit)
        cache.delete(f"renters_user_{self.request.user.id}")
