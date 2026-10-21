from typing import Any, cast

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from rentsecure_be.type_compat import override

from ..models import Building, CareTaker, CareTakerAssignment, Unit


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
