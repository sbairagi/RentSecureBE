from typing import Any, cast

from rest_framework import serializers

from shared.type_compat import override

from ..models import RentAgreementDraft, Unit, UnitDocument, UnitImage
from ..services.unit_service import (
    prepare_unit_creation,
    validate_building_access,
    validate_coordinates,
)

NOT_UNIT_OWNER = "You do not own the selected unit."


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = "__all__"
        read_only_fields = ["owner"]

    @override
    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        user = self.context["request"].user
        building = data.get("building") or getattr(self.instance, "building", None)
        validate_building_access(building, user)
        validate_coordinates(
            data.get("latitude", getattr(self.instance, "latitude", None)),
            data.get("longitude", getattr(self.instance, "longitude", None)),
        )
        return data

    @override
    def create(self, validated_data: dict[str, Any]) -> Unit:
        prepare_unit_creation(validated_data, self.context["request"].user)
        return cast(Unit, super().create(validated_data))

    @override
    def update(self, instance: Unit, validated_data: dict[str, Any]) -> Unit:
        building = validated_data.get("building")
        if building is not None:
            validate_building_access(building, self.context["request"].user)
        return cast(Unit, super().update(instance, validated_data))


class UnitImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitImage
        fields = "__all__"

    @override
    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        user = self.context["request"].user
        unit = data.get("unit") or getattr(self.instance, "unit", None)
        if unit and unit.owner != user:
            raise serializers.ValidationError(NOT_UNIT_OWNER)  # noqa: S1192
        return data

    @override
    def update(self, instance: UnitImage, validated_data: dict[str, Any]) -> UnitImage:
        unit = validated_data.get("unit")
        if unit and unit.owner != self.context["request"].user:
            raise serializers.ValidationError(NOT_UNIT_OWNER)
        return cast(UnitImage, super().update(instance, validated_data))


class UnitDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitDocument
        fields = "__all__"

    @override
    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        user = self.context["request"].user
        unit = data.get("unit") or getattr(self.instance, "unit", None)
        if unit and unit.owner != user:
            raise serializers.ValidationError(NOT_UNIT_OWNER)
        return data

    @override
    def update(
        self, instance: UnitDocument, validated_data: dict[str, Any]
    ) -> UnitDocument:
        unit = validated_data.get("unit")
        if unit and unit.owner != self.context["request"].user:
            raise serializers.ValidationError(NOT_UNIT_OWNER)
        return cast(UnitDocument, super().update(instance, validated_data))


class RentAgreementDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentAgreementDraft
        fields = "__all__"
        read_only_fields = ["user", "generated_at"]

    @override
    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        request_user = self.context["request"].user
        renter = data.get("renter")
        unit = data.get("unit")
        if not renter or not unit:
            raise serializers.ValidationError("Both renter and unit are required.")
        if unit.owner != request_user:
            raise serializers.ValidationError(NOT_UNIT_OWNER)
        if renter.unit != unit:
            raise serializers.ValidationError(
                "Renter does not belong to the selected unit."
            )
        return data
