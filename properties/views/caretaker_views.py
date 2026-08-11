from typing import Any

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from rentsecure_be.type_compat import override

from ..feature_enforcer import FeatureEnforcer
from ..models import Caretaker, Unit
from ..serializers import CaretakerSerializer


class CaretakerPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "limit"
    max_page_size = 100


class CaretakerViewSet(viewsets.ModelViewSet[Caretaker]):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]
    serializer_class = CaretakerSerializer
    pagination_class = CaretakerPagination

    @override
    def get_queryset(self) -> Any:
        if isinstance(self.request.user, AnonymousUser):
            return Caretaker.objects.none()
        user = self.request.user
        queryset = Caretaker.objects.filter(unit__owner=user).select_related(
            "unit", "user"
        )

        search = self.request.GET.get("search")
        if search:
            queryset = (
                queryset.filter(name__icontains=search)
                | queryset.filter(phone__icontains=search)
                | queryset.filter(email__icontains=search)
            )

        unit_id = self.request.GET.get("unit")
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)

        is_active = self.request.GET.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        ordering = self.request.GET.get("ordering")
        if ordering:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by("-joining_date")

        return queryset

    @override
    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        unit: Unit | None = serializer.validated_data.get("unit")
        if not unit or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")  # noqa: S1192

        enforcer = FeatureEnforcer(self.request.user)
        if not enforcer.can_create("max_caretakers"):
            raise PermissionDenied("Caretaker limit reached for your plan.")

        serializer.save()
        enforcer.increment("max_caretakers")

    @override
    def perform_update(self, serializer: BaseSerializer[Any]) -> None:
        instance = serializer.instance
        unit: Unit | None = serializer.validated_data.get("unit") or (
            instance.unit if instance else None
        )
        if unit is None or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        serializer.save()

    @override
    def perform_destroy(self, instance: Caretaker) -> None:
        if instance.unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement("max_caretakers")

    @override
    @action(detail=True, methods=["post"])
    def deactivate(self, request: Any, pk: Any = None) -> Response:
        instance = self.get_object()
        if instance.unit.owner != request.user:
            raise PermissionDenied("You do not own the selected unit.")
        instance.is_active = False
        instance.leaving_date = timezone.localdate()
        instance.save(update_fields=["is_active", "leaving_date", "updated_at"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @override
    @action(detail=True, methods=["get"])
    def history(self, request: Any, pk: Any = None) -> Response:
        instance = self.get_object()
        if instance.unit.owner != request.user:
            raise PermissionDenied("You do not own the selected unit.")
        history_qs = instance.history.all().order_by("-history_date")[:50]
        data = [
            {
                "id": record.history_id,
                "action": record.history_type,
                "changed_by": getattr(record.history_user, "email", None)
                or getattr(record.history_user, "username", None),
                "timestamp": record.history_date.isoformat(),
                "data": {
                    "name": record.name,
                    "phone": record.phone,
                    "email": record.email,
                    "is_active": record.is_active,
                    "unit": record.unit_id,
                    "joining_date": (
                        record.joining_date.isoformat() if record.joining_date else None
                    ),
                    "leaving_date": (
                        record.leaving_date.isoformat() if record.leaving_date else None
                    ),
                },
            }
            for record in history_qs
        ]
        return Response(data)
