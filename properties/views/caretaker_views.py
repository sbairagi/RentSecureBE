from typing import Any

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from django.utils import timezone

from rentsecure_be.type_compat import override

from ..feature_enforcer import FeatureEnforcer
from ..models import Building, CareTaker, CareTakerAssignment, Unit
from ..serializers.caretaker_serializers import (
    CareTakerActivitySerializer,
    CareTakerAssignmentCreateSerializer,
    CareTakerAssignmentSerializer,
    CareTakerSerializer,
)
from ..services.caretaker_activity import team_activity


class CareTakerPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "limit"
    max_page_size = 100


class CareTakerViewSet(viewsets.ModelViewSet[CareTaker]):
    """The team of an owner.

    A caretaker works for one owner and is given buildings and standalone
    units of that owner as assignments. The owner manages the team here:
    hiring, editing, assigning properties and removing a caretaker.
    """

    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]
    serializer_class = CareTakerSerializer
    pagination_class = CareTakerPagination

    @override
    def get_queryset(self) -> Any:
        if isinstance(self.request.user, AnonymousUser):
            return CareTaker.objects.none()
        user = self.request.user
        queryset = (
            CareTaker.objects.filter(owner=user)
            .select_related("owner", "unit", "user")
            .prefetch_related("assignments__building", "assignments__unit")
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
            queryset = queryset.filter(
                Q(unit_id=unit_id)
                | Q(assignments__unit_id=unit_id, assignments__is_active=True)
            )

        building_id = self.request.GET.get("building")
        if building_id:
            queryset = queryset.filter(
                assignments__building_id=building_id, assignments__is_active=True
            )

        is_active = self.request.GET.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        ordering = self.request.GET.get("ordering")
        if ordering:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by("-joining_date")

        return queryset.distinct()

    @override
    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        user = self.request.user
        unit = serializer.validated_data.get("unit")
        if unit is not None and unit.owner_id != user.id:
            raise PermissionDenied("You do not own the selected unit.")  # noqa: S1192

        enforcer = FeatureEnforcer(user)
        if not enforcer.can_create("max_caretakers"):
            raise PermissionDenied("CareTaker limit reached for your plan.")

        enforcer.increment("max_caretakers")
        serializer.save(owner=user)

    @override
    def perform_update(self, serializer: BaseSerializer[Any]) -> None:
        instance = serializer.instance
        user = self.request.user
        unit = serializer.validated_data.get("unit")
        if unit is None and instance is not None:
            unit = instance.unit
        if unit is not None and unit.owner_id != user.id:
            raise PermissionDenied("You do not own the selected unit.")
        if instance is not None and instance.owner_id != user.id:
            raise PermissionDenied("You do not own this caretaker.")
        if unit is None and instance is None:
            raise PermissionDenied("You do not own the selected unit.")
        serializer.save()

    @override
    def perform_destroy(self, instance: CareTaker) -> None:
        if instance.owner_id != self.request.user.id:
            raise PermissionDenied("You do not own this caretaker.")
        FeatureEnforcer(self.request.user).decrement("max_caretakers")
        instance.delete()

    @override
    @action(detail=True, methods=["post"])
    def deactivate(self, request: Any, pk: Any = None) -> Response:
        instance = self.get_object()
        instance.is_active = False
        instance.leaving_date = timezone.localdate()
        instance.save(update_fields=["is_active", "leaving_date", "updated_at"])
        instance.assignments.filter(is_active=True).update(
            is_active=False, unassigned_at=timezone.now()
        )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @override
    @action(detail=True, methods=["get"])
    def history(self, request: Any, pk: Any = None) -> Response:
        instance = self.get_object()
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
                    "owner": record.owner_id,
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

    @override
    @action(detail=True, methods=["get", "post"], url_path="assignments")
    def assignments(self, request: Any, pk: Any = None) -> Response:
        """List and create the properties of the caretaker."""
        caretaker = self.get_object()

        if request.method == "GET":
            queryset = caretaker.assignments.select_related("building", "unit")
            if request.GET.get("include_inactive") != "true":
                queryset = queryset.filter(is_active=True)
            return Response(
                {"data": CareTakerAssignmentSerializer(queryset, many=True).data}
            )

        payload = CareTakerAssignmentCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data

        building = data.get("building")
        unit = data.get("unit")
        if building is not None:
            if building.owner_id != caretaker.owner_id:
                raise PermissionDenied("You do not own the selected building.")
            if caretaker.assignments.filter(building=building, is_active=True).exists():
                raise ValidationError("That building is already assigned.")
            assignment = CareTakerAssignment.objects.create(
                caretaker=caretaker,
                building=building,
                assigned_by=request.user,
                notes=data.get("notes", ""),
            )
        else:
            if unit is None:
                raise ValidationError("Choose a unit for the caretaker.")
            if unit.owner_id != caretaker.owner_id:
                raise PermissionDenied("You do not own the selected unit.")
            if caretaker.assignments.filter(unit=unit, is_active=True).exists():
                raise ValidationError("That unit is already assigned.")
            assignment = CareTakerAssignment.objects.create(
                caretaker=caretaker,
                unit=unit,
                assigned_by=request.user,
                notes=data.get("notes", ""),
            )

        return Response(CareTakerAssignmentSerializer(assignment).data, status=201)

    @override
    @action(
        detail=True,
        methods=["delete"],
        url_path=r"assignments/(?P<assignment_id>[0-9]+)",
    )
    def remove_assignment(
        self, request: Any, pk: Any = None, assignment_id: int = 0
    ) -> Response:
        """Take a property out of the scope of the caretaker."""
        caretaker = self.get_object()
        assignment = caretaker.assignments.filter(pk=assignment_id).first()
        if assignment is None:
            raise ValidationError("That assignment does not exist.")
        assignment.is_active = False
        assignment.unassigned_at = timezone.now()
        assignment.save(update_fields=["is_active", "unassigned_at"])
        return Response(status=204)

    @override
    @action(detail=False, methods=["get"], url_path="team-activity")
    def team_activity(self, request: Any) -> Response:
        """What the team of the owner did — the caretaker panel of the owner.

        The trail is the caretaker's own work: the job they took, the status
        they moved a request to and the notes they left. It is scoped to the
        owner, so a caretaker of another owner never shows up here.
        """
        caretaker_id = request.GET.get("caretaker")
        if caretaker_id:
            try:
                caretaker_id = int(caretaker_id)
            except (TypeError, ValueError):
                raise ValidationError("That caretaker does not exist.") from None
            if not CareTaker.objects.filter(
                pk=caretaker_id, owner=request.user
            ).exists():
                raise ValidationError("That caretaker does not exist.")

        try:
            limit = int(request.GET.get("limit", 20))
        except (TypeError, ValueError):
            limit = 20
        limit = max(1, min(limit, 100))

        queryset = team_activity(request.user, caretaker_id)
        count = queryset.count()
        serializer = CareTakerActivitySerializer(
            queryset[:limit], many=True, context={"request": request}
        )
        return Response({"data": {"count": count, "results": serializer.data}})

    @override
    @action(detail=False, methods=["get"], url_path="assignable-properties")
    def assignable_properties(self, request: Any) -> Response:
        """The buildings and units of the owner that can be assigned."""
        owner = request.user
        buildings = Building.objects.filter(owner=owner, is_archived=False).values(
            "id", "name", "city", "address_line"
        )
        units = (
            Unit.objects.filter(owner=owner, is_archived=False)
            .select_related("building")
            .values(
                "id",
                "unit",
                "building_name",
                "building__name",
                "city",
                "status",
            )
        )
        assigned_buildings = set(
            CareTakerAssignment.objects.filter(
                caretaker__owner=owner, is_active=True, building__isnull=False
            ).values_list("building_id", flat=True)
        )
        assigned_units = set(
            CareTakerAssignment.objects.filter(
                caretaker__owner=owner, is_active=True, unit__isnull=False
            ).values_list("unit_id", flat=True)
        )
        return Response(
            {
                "data": {
                    "buildings": [
                        {
                            "id": item["id"],
                            "name": item["name"],
                            "city": item["city"],
                            "address_line": item["address_line"],
                            "assigned": item["id"] in assigned_buildings,
                        }
                        for item in buildings
                    ],
                    "units": [
                        {
                            "id": item["id"],
                            "unit": item["unit"],
                            "building": item["building__name"],
                            "city": item["city"],
                            "status": item["status"],
                            "assigned": item["id"] in assigned_units,
                        }
                        for item in units
                    ],
                }
            }
        )


CaretakerViewSet = CareTakerViewSet
