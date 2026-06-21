from typing import Any, cast

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from rentsecure_be.type_compat import override

from ..models import Renter, RentRecord


class RenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Renter
        fields = "__all__"
        extra_kwargs = {
            "id_proof": {"required": False},
            "rent_agreement": {"required": False},
        }

    @override
    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        user = self.context["request"].user
        unit = data.get("unit") or getattr(self.instance, "unit", None)
        if unit and unit.owner != user:
            raise PermissionDenied("You do not own the selected unit.")
        return data

    @override
    def update(self, instance: Renter, validated_data: dict[str, Any]) -> Renter:
        unit = validated_data.get("unit")
        if unit and unit.owner != self.context["request"].user:
            raise serializers.ValidationError("You do not own the selected unit.")
        return cast(Renter, super().update(instance, validated_data))


class RenterRentRecordSerializer(serializers.ModelSerializer):
    due_date = serializers.DateField(source="rent_due_date")
    amount = serializers.DecimalField(
        source="amount_paid", max_digits=10, decimal_places=2
    )
    invoice_url = serializers.SerializerMethodField()

    class Meta:
        model = RentRecord
        fields = ["due_date", "amount", "late_fee", "payment_status", "invoice_url"]

    def get_invoice_url(self, obj: RentRecord) -> str:
        if obj.status == "PAID":
            return obj.invoice_pdf.url or ""
        return ""
