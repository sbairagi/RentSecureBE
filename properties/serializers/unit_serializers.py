from typing import Any, cast

from rest_framework import serializers

from rentsecure_be.type_compat import override

from ..models import RentAgreementDraft, Unit, UnitDocument, UnitImage


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = "__all__"
        read_only_fields = ["owner"]

    @override
    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        user = self.context["request"].user
        building = data.get("building") or getattr(self.instance, "building", None)
        if building and building.owner != user:
            raise serializers.ValidationError("You do not own the selected building.")
        latitude = data.get("latitude", getattr(self.instance, "latitude", None))
        longitude = data.get("longitude", getattr(self.instance, "longitude", None))
        if latitude is not None and not -90 <= latitude <= 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        if longitude is not None and not -180 <= longitude <= 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        return data

    @override
    def create(self, validated_data: dict[str, Any]) -> Unit:
        validated_data["owner"] = self.context["request"].user
        return cast(Unit, super().create(validated_data))

    @override
    def update(self, instance: Unit, validated_data: dict[str, Any]) -> Unit:
        building = validated_data.get("building")
        if building and building.owner != self.context["request"].user:
            raise serializers.ValidationError("You do not own the selected building.")
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
            raise serializers.ValidationError("You do not own the selected unit.")
        return data

    @override
    def update(self, instance: UnitImage, validated_data: dict[str, Any]) -> UnitImage:
        unit = validated_data.get("unit")
        if unit and unit.owner != self.context["request"].user:
            raise serializers.ValidationError("You do not own the selected unit.")
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
            raise serializers.ValidationError("You do not own the selected unit.")
        return data

    @override
    def update(
        self, instance: UnitDocument, validated_data: dict[str, Any]
    ) -> UnitDocument:
        unit = validated_data.get("unit")
        if unit and unit.owner != self.context["request"].user:
            raise serializers.ValidationError("You do not own the selected unit.")
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
            raise serializers.ValidationError("You do not own the selected unit.")
        if renter.unit != unit:
            raise serializers.ValidationError(
                "Renter does not belong to the selected unit."
            )
        return data
