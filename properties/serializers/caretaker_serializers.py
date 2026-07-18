from typing import Any, cast

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from shared.type_compat import override

from ..models import Caretaker


class CaretakerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caretaker
        fields = "__all__"
        extra_kwargs = {
            "id_proof": {"required": False},
        }

    @override
    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        user = self.context["request"].user
        unit = data.get("unit") or getattr(self.instance, "unit", None)
        if unit and unit.owner != user:
            raise PermissionDenied("You do not own the selected unit.")
        return data

    @override
    def update(self, instance: Caretaker, validated_data: dict[str, Any]) -> Caretaker:
        unit = validated_data.get("unit")
        if unit and unit.owner != self.context["request"].user:
            raise serializers.ValidationError("You do not own the selected unit.")
        return cast(Caretaker, super().update(instance, validated_data))
