from rest_framework import serializers

from ..models import ExtraCharge


class ExtraChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtraCharge
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        request = self.context["request"]
        user = request.user
        renter = data.get("renter") or getattr(self.instance, "renter", None)
        unit = data.get("unit") or getattr(self.instance, "unit", None)

        if not renter or not unit:
            raise serializers.ValidationError("Renter and unit are required.")

        if renter.unit.id != unit.id:
            raise serializers.ValidationError(
                "Renter does not belong to the selected unit."
            )

        if unit.owner != user:
            raise serializers.ValidationError("You do not own the selected unit.")

        if data.get("amount") is not None and data["amount"] < 0:
            raise serializers.ValidationError("Amount cannot be negative.")

        return data

    def update(self, instance, validated_data):
        user = self.context["request"].user
        unit = validated_data.get("unit", instance.unit)
        renter = validated_data.get("renter", instance.renter)

        if unit.owner != user:
            raise serializers.ValidationError("You do not own the selected unit.")
        if renter.unit.id != unit.id:
            raise serializers.ValidationError(
                "Renter does not belong to the selected unit."
            )

        return super().update(instance, validated_data)
