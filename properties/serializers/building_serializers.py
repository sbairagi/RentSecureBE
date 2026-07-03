from typing import Any, cast

from rest_framework import serializers

from rentsecure_be.type_compat import override

from ..models import Building
from .unit_serializers import UnitSerializer


class BuildingSerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True, read_only=True)

    class Meta:
        model = Building
        fields = "__all__"
        read_only_fields = ["owner"]

    @override
    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        return data

    @override
    def create(self, validated_data: dict[str, Any]) -> Building:
        validated_data["owner"] = self.context["request"].user
        return cast(Building, super().create(validated_data))

    @override
    def update(self, instance: Building, validated_data: dict[str, Any]) -> Building:
        if "owner" in validated_data:
            validated_data.pop("owner")
        return cast(Building, super().update(instance, validated_data))
