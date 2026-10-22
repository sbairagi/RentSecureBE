from typing import Any, cast

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from rentsecure_be.type_compat import override

from ..models import Building, CareTaker, CareTakerActivity, CareTakerAssignment, Unit


class CareTakerAssignmentSerializer(serializers.ModelSerializer):
    """One property of the owner that is in the scope of the caretaker."""

    scope_type = serializers.CharField(read_only=True)
    scope_label = serializers.CharField(read_only=True)
    caretaker = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = CareTakerAssignment
        fields = [
            "id",
            "caretaker",
            "building",
            "unit",
            "scope_type",
            "scope_label",
            "assigned_at",
            "unassigned_at",
            "is_active",
            "notes",
        ]
        read_only_fields = [
            "id",
            "caretaker",
            "assigned_at",
            "unassigned_at",
            "is_active",
        ]


class CareTakerSerializer(serializers.ModelSerializer):
    """The caretaker as the owner sees them.

    The owner is never written by the client — the caretaker always belongs
    to the account that created them.
    """

    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    unit = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.filter(is_archived=False),
        required=False,
        allow_null=True,
    )
    assignments = CareTakerAssignmentSerializer(many=True, read_only=True)
    assignment_count = serializers.SerializerMethodField()
    property_count = serializers.SerializerMethodField()

    class Meta:
        model = CareTaker
        fields = [
            "id",
            "owner",
            "unit",
            "user",
            "name",
            "email",
            "phone",
            "alternate_phone",
            "address",
            "joining_date",
            "leaving_date",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
            "assignments",
            "assignment_count",
            "property_count",
        ]
        read_only_fields = [
            "id",
            "owner",
            "user",
            "created_at",
            "updated_at",
            "assignments",
            "assignment_count",
            "property_count",
        ]

    @override
    def get_assignment_count(self, obj: CareTaker) -> int:
        return obj.assignments.filter(is_active=True).count()

    @override
    def get_property_count(self, obj: CareTaker) -> int:
        """Return how many properties the caretaker looks after."""
        active = obj.assignments.filter(is_active=True)
        building_ids = list(
            active.exclude(building__isnull=True).values_list("building_id", flat=True)
        )
        unit_ids = list(
            active.exclude(unit__isnull=True).values_list("unit_id", flat=True)
        )
        if building_ids:
            unit_ids.extend(
                Unit.objects.filter(building_id__in=building_ids).values_list(
                    "id", flat=True
                )
            )
        return len(set(unit_ids))

    @override
    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        unit = data.get("unit") or getattr(self.instance, "unit", None)
        if unit is not None and user is not None and unit.owner_id != user.id:
            raise PermissionDenied("You do not own the selected unit.")

        phone = data.get("phone") or getattr(self.instance, "phone", None)
        owner = getattr(self.instance, "owner", None) or user
        if phone and owner is not None:
            same_phone = CareTaker.objects.filter(owner=owner, phone=phone).exclude(
                pk=getattr(self.instance, "pk", None)
            )
            if same_phone.exists():
                raise serializers.ValidationError(
                    {"phone": "This phone number is already on your team."}
                )
        return data

    @override
    def update(self, instance: CareTaker, validated_data: dict[str, Any]) -> CareTaker:
        unit = validated_data.get("unit")
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if unit is not None and user is not None and unit.owner_id != user.id:
            raise serializers.ValidationError("You do not own the selected unit.")
        return cast(CareTaker, super().update(instance, validated_data))


class CareTakerActivitySerializer(serializers.ModelSerializer):
    """One thing the team of the owner did."""

    action_label = serializers.SerializerMethodField()
    caretaker = serializers.SerializerMethodField()
    request_title = serializers.SerializerMethodField()
    property_label = serializers.SerializerMethodField()
    from_status_label = serializers.SerializerMethodField()
    to_status_label = serializers.SerializerMethodField()
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = CareTakerActivity
        fields = [
            "id",
            "action",
            "action_label",
            "summary",
            "detail",
            "caretaker",
            "request_title",
            "property_label",
            "from_status",
            "from_status_label",
            "to_status",
            "to_status_label",
            "actor_name",
            "created_at",
        ]
        read_only_fields = fields

    @override
    def get_caretaker(self, obj: CareTakerActivity) -> dict[str, Any]:
        return {"id": obj.caretaker_id, "name": obj.caretaker.name}

    @override
    def get_action_label(self, obj: CareTakerActivity) -> str:
        return dict(CareTakerActivity.Action.choices).get(obj.action, obj.action)

    @override
    def get_request_title(self, obj: CareTakerActivity) -> str:
        request = obj.maintenance_request
        return request.title if request is not None else ""

    @override
    def get_property_label(self, obj: CareTakerActivity) -> str:
        request = obj.maintenance_request
        if request is None:
            return ""
        unit = request.unit
        building = getattr(unit, "building", None)
        unit_label = getattr(unit, "unit", "") or ""
        building_label = getattr(building, "name", "") or ""
        if building_label and unit_label:
            return f"{building_label} · {unit_label}"
        return building_label or unit_label

    @override
    def get_from_status_label(self, obj: CareTakerActivity) -> str:
        return _maintenance_status_label(obj.from_status)

    @override
    def get_to_status_label(self, obj: CareTakerActivity) -> str:
        return _maintenance_status_label(obj.to_status)

    @override
    def get_actor_name(self, obj: CareTakerActivity) -> str:
        if obj.actor_id is None:
            return obj.caretaker.name
        return (
            getattr(obj.actor, "full_name", "")
            or getattr(obj.actor, "username", "")
            or obj.caretaker.name
        )


def _maintenance_status_label(value: str) -> str:
    """Return the label of a maintenance status."""
    if not value:
        return ""
    from ..models import MaintenanceRequest

    return dict(MaintenanceRequest.Status.choices).get(value, value)


class CareTakerAssignmentCreateSerializer(serializers.Serializer):
    """The payload of an assignment: one building or one unit."""

    building = serializers.PrimaryKeyRelatedField(
        queryset=Building.objects.filter(is_archived=False),
        required=False,
        allow_null=True,
    )
    unit = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.filter(is_archived=False),
        required=False,
        allow_null=True,
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    @override
    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        building = data.get("building")
        unit = data.get("unit")
        if bool(building) == bool(unit):
            raise serializers.ValidationError(
                "Choose either a building or a single unit for the caretaker."
            )
        return data
