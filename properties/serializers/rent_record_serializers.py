from decimal import Decimal
from typing import Any, cast

from rest_framework import serializers

from rentsecure_be.type_compat import override

from ..models import RentRecord, RentRecordPart
from .renter_serializers import RenterSerializer
from .unit_serializers import UnitSerializer


class RentRecordPartSerializer(serializers.ModelSerializer):
    """Read-only projection of a part payment, embedded in the rent record."""

    payment_method_label = serializers.SerializerMethodField()
    amount_display = serializers.SerializerMethodField()

    class Meta:
        model = RentRecordPart
        fields = [
            "id",
            "amount",
            "amount_display",
            "paid_on",
            "payment_method",
            "payment_method_label",
            "transaction_id",
            "note",
            "receipt_no",
            "receipt_pdf",
            "created_at",
        ]
        read_only_fields = fields

    @override
    def get_payment_method_label(self, obj: RentRecordPart) -> str:
        return str(obj.get_payment_method_display())

    @override
    def get_amount_display(self, obj: RentRecordPart) -> str:
        return f"{obj.amount:,.2f}".rstrip("0").rstrip(".")


class PartPaymentSerializer(serializers.Serializer):
    """Payload accepted by ``POST /rent-records/{id}/payments/``."""

    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    paid_on = serializers.DateField()
    payment_method = serializers.ChoiceField(
        choices=RentRecord.PaymentMethod.choices,
        default=RentRecord.PaymentMethod.CASH,
    )
    transaction_id = serializers.CharField(
        max_length=100, required=False, allow_blank=True, default=""
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")

    @override
    def validate_amount(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("Part amount must be greater than zero.")
        return value


class RentRecordSerializer(serializers.ModelSerializer):
    renter = RenterSerializer(read_only=True)
    unit = UnitSerializer(read_only=True)
    parts = RentRecordPartSerializer(many=True, read_only=True)
    total_due = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    allow_partial_payments = serializers.SerializerMethodField()
    is_partially_paid = serializers.BooleanField(read_only=True)

    class Meta:
        model = RentRecord
        fields = "__all__"
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "payout_status",
            "payout_reference",
            "payment_link",
            "invoice_pdf",
            "razorpay_order_id",
            "payout_retries",
            "last_payout_retry",
            "payout_retry_count",
            "status",
            "payment_status",
            "amount_paid",
            "paid_on",
            "parts",
            "total_due",
            "balance",
            "is_partially_paid",
            "allow_partial_payments",
            "cancel_reason",
            "cancelled_at",
            "cancelled_by",
            "receipt_sent_at",
            "last_reminded_at",
        ]

    ALLOWED_UPDATE_FIELDS = {
        "notes",
        "adjustment_reason",
        "late_fee",
        "discount",
        "paid_on",
    }

    # Once money has been received the bill is frozen: only the ledger note
    # and the adjustment reason can still change.
    ALLOWED_UPDATE_FIELDS_AFTER_PAYMENT = {
        "notes",
        "adjustment_reason",
    }

    LOCKED_STATUSES = {RentRecord.Status.PAID, RentRecord.Status.CANCELLED}

    # ``unit`` and ``renter`` are rendered as nested objects, so DRF treats
    # them as read-only and drops the ids the clients send on write. They are
    # resolved back into model instances here, otherwise the ownership guards
    # in ``validate`` never see them and every create is rejected.
    WRITE_THROUGH_RELATIONS = ("unit", "renter")

    @override
    def to_internal_value(self, data: Any) -> dict[str, Any]:
        internal = super().to_internal_value(data)
        for field_name in self.WRITE_THROUGH_RELATIONS:
            if field_name in internal:
                continue
            raw = data.get(field_name)
            if raw is None or raw == "":
                continue
            internal[field_name] = self._resolve_relation(field_name, raw)
        return internal

    def _resolve_relation(self, field_name: str, raw: Any) -> Any:
        """Look up the unit / renter the client sent by id."""
        related_model = self.Meta.model._meta.get_field(field_name).related_model
        pk = raw.get("id") if isinstance(raw, dict) else raw
        try:
            return related_model.objects.get(pk=pk)
        except (related_model.DoesNotExist, ValueError, TypeError) as error:
            raise serializers.ValidationError(
                {field_name: f"Invalid {field_name}: {pk}"}
            ) from error

    @override
    def get_allow_partial_payments(self, obj: RentRecord) -> bool:
        return bool(obj.allow_partial_payments)

    @override
    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        self._validate_update_fields(data)
        user = self.context["request"].user
        unit = data.get("unit") or getattr(self.instance, "unit", None)
        renter = data.get("renter") or getattr(self.instance, "renter", None)
        self._validate_unit_ownership(unit, user)
        self._validate_renter_ownership(renter, user)
        self._validate_renter_unit_assignment(renter, unit)
        self._validate_amount_paid(data)
        self._validate_rent_month_and_date_paid(data)
        return data

    def _validate_update_fields(self, data: dict[str, Any]) -> None:
        if self.instance is None:
            return

        status = str(self.instance.status or "").lower()
        if status in self.LOCKED_STATUSES:
            raise serializers.ValidationError(
                {
                    "error": (
                        f"This rent record is {status} and can no longer be edited. "
                        "Cancelled and settled records are kept exactly as they were "
                        "recorded."
                    )
                }
            )

        allowed = set(self.ALLOWED_UPDATE_FIELDS)
        if (self.instance.amount_paid or Decimal("0")) > 0:
            allowed = set(self.ALLOWED_UPDATE_FIELDS_AFTER_PAYMENT)

        forbidden = set(self.initial_data.keys()) - allowed
        if forbidden:
            raise serializers.ValidationError(
                {"error": f"Cannot update fields: {', '.join(sorted(forbidden))}"}
            )

    def _validate_unit_ownership(self, unit: Any, user: Any) -> None:
        if not unit or unit.owner != user:
            raise serializers.ValidationError("You do not own the selected unit.")

    def _validate_renter_ownership(self, renter: Any, user: Any) -> None:
        if not renter or renter.unit.owner != user:
            raise serializers.ValidationError("You do not own the selected renter.")

    def _validate_renter_unit_assignment(self, renter: Any, unit: Any) -> None:
        if renter and unit and renter.unit.id != unit.id:
            raise serializers.ValidationError(
                "Renter is not assigned to the selected unit."
            )

    def _validate_amount_paid(self, data: dict[str, Any]) -> None:
        if "amount_paid" in data and data["amount_paid"] < 0:
            raise serializers.ValidationError("Amount paid cannot be negative.")

    def _validate_rent_month_and_date_paid(self, data: dict[str, Any]) -> None:
        due_date = data.get("due_date") or getattr(self.instance, "due_date", None)
        paid_on = data.get("paid_on") or getattr(self.instance, "paid_on", None)
        if due_date and paid_on and paid_on < due_date:
            raise serializers.ValidationError(
                "Date paid cannot be before the rent due date."
            )

    @override
    def update(
        self, instance: RentRecord, validated_data: dict[str, Any]
    ) -> RentRecord:
        return cast(RentRecord, super().update(instance, validated_data))

    def get_invoice_url(self, obj: RentRecord) -> str:
        if str(obj.status or "").lower() == RentRecord.Status.PAID and obj.invoice_pdf:
            url = obj.invoice_pdf.url
            return url if url else ""
        return ""
