from typing import Any, cast

from rest_framework import serializers

from rentsecure_be.type_compat import override

from ..models import RentRecord


class RentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentRecord
        fields = "__all__"
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "owner",
            "payout_status",
            "status",
            "payout_reference",
            "payment_link",
            "invoice_pdf",
            "razorpay_order_id",
            "payout_retries",
            "last_payout_retry",
            "payout_retry_count",
        ]

    ALLOWED_UPDATE_FIELDS = {"notes", "adjustment_reason", "late_fee", "discount"}

    @override
    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if self.instance is not None:
            forbidden = set(self.initial_data.keys()) - self.ALLOWED_UPDATE_FIELDS
            if forbidden:
                raise serializers.ValidationError(
                    {"error": f"Cannot update fields: {', '.join(sorted(forbidden))}"}
                )

        user = self.context["request"].user
        unit = data.get("unit") or getattr(self.instance, "unit", None)
        renter = data.get("renter") or getattr(self.instance, "renter", None)

        if not unit or unit.owner != user:
            raise serializers.ValidationError("You do not own the selected unit.")
        if not renter or renter.unit.owner != user:
            raise serializers.ValidationError("You do not own the selected renter.")
        if renter.unit.id != unit.id:
            raise serializers.ValidationError(
                "Renter is not assigned to the selected unit."
            )
        if "amount_paid" in data and data["amount_paid"] < 0:
            raise serializers.ValidationError("Amount paid cannot be negative.")

        rent_month = data.get("rent_month") or getattr(
            self.instance, "rent_month", None
        )
        date_paid = data.get("date_paid") or getattr(self.instance, "date_paid", None)
        if rent_month and date_paid and date_paid < rent_month:
            raise serializers.ValidationError(
                "Date paid cannot be before the rent month."
            )
        return data

    @override
    def update(
        self, instance: RentRecord, validated_data: dict[str, Any]
    ) -> RentRecord:
        return cast(RentRecord, super().update(instance, validated_data))

    def get_invoice_url(self, obj: RentRecord) -> str:
        if obj.status == "PAID" and obj.invoice_pdf:
            url = obj.invoice_pdf.url
            return url if url else ""
        return ""
