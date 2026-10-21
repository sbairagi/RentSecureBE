from rest_framework import serializers

from properties.models import Caretaker, MaintenanceRequest, Renter, Unit
from properties.services.caretaker_scope import covers_unit


class MaintenanceRequestSerializer(serializers.ModelSerializer):
    unit_name = serializers.CharField(source="unit.unit", read_only=True)
    building_name = serializers.CharField(
        source="unit.building.name", read_only=True, allow_null=True
    )
    renter_name = serializers.CharField(
        source="renter.name", read_only=True, allow_null=True
    )
    caretaker_name = serializers.CharField(
        source="assigned_caretaker.name", read_only=True, allow_null=True
    )

    class Meta:
        model = MaintenanceRequest
        fields = "__all__"
        read_only_fields = ("owner", "reported_at", "updated_at", "resolved_at")

    def validate(self, attrs):
        request = self.context["request"]
        instance = self.instance
        unit = attrs.get("unit") or getattr(instance, "unit", None)
        renter = attrs.get("renter", getattr(instance, "renter", None))
        caretaker = attrs.get(
            "assigned_caretaker", getattr(instance, "assigned_caretaker", None)
        )

        if not isinstance(unit, Unit) or unit.owner_id != request.user.id:
            raise serializers.ValidationError({"unit": "Choose a unit you own."})
        if renter and (not isinstance(renter, Renter) or renter.unit_id != unit.id):
            raise serializers.ValidationError(
                {"renter": "The renter must belong to the selected unit."}
            )
        if caretaker and (
            not isinstance(caretaker, Caretaker)
            or caretaker.owner_id != unit.owner_id
            or not covers_unit(caretaker, unit)
        ):
            raise serializers.ValidationError(
                {"assigned_caretaker": "Choose a caretaker assigned to this unit."}
            )
        return attrs
