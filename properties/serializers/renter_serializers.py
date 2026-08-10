from typing import Any, cast

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from rentsecure_be.type_compat import override

from ..models import ExtraCharge, RentAgreementDraft, Renter, RentRecord, Unit


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


class RenterUnitSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = [
            "id",
            "unit",
            "unit_type",
            "building",
            "address_line",
            "landmark",
            "city",
            "state",
            "country",
            "postal_code",
        ]


class RenterBuildingSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = [
            "id",
            "building",
        ]


class RenterProfileSerializer(serializers.ModelSerializer):
    unit = RenterUnitSummarySerializer(read_only=True)
    building = serializers.SerializerMethodField()
    id_proof_url = serializers.SerializerMethodField()
    rent_agreement_url = serializers.SerializerMethodField()

    class Meta:
        model = Renter
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "alternate_phone",
            "emergency_contact_name",
            "emergency_contact_number",
            "status",
            "rent_amount",
            "start_date",
            "end_date",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
            "renter_image",
            "whatsapp_number",
            "rent_due_date",
            "late_payment_count",
            "missed_rents",
            "is_flagged",
            "flagged_reason",
            "is_agreement_revoked",
            "revocation_reason",
            "revoked_by_owner",
            "revoked_on",
            "vacated_on",
            "status_changed_at",
            "notice_start_date",
            "onboarding_status",
            "kyc_status",
            "unit",
            "building",
            "id_proof_url",
            "rent_agreement_url",
        ]
        read_only_fields = fields

    @override
    def get_building(self, obj: Renter) -> dict[str, Any] | None:
        unit = obj.unit
        if not unit or not unit.building:
            return None
        return {
            "id": unit.building.id,
            "name": unit.building.name,
            "address_line": unit.building.address_line,
            "city": unit.building.city,
            "state": unit.building.state,
            "country": unit.building.country,
            "postal_code": unit.building.postal_code,
        }

    @override
    def get_id_proof_url(self, obj: Renter) -> str | None:
        if obj.id_proof:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.id_proof.url)
            return obj.id_proof.url
        return None

    @override
    def get_rent_agreement_url(self, obj: Renter) -> str | None:
        if obj.rent_agreement:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.rent_agreement.url)
            return obj.rent_agreement.url
        return None


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


class RenterRentRecordDetailSerializer(serializers.ModelSerializer):
    due_date = serializers.DateField(source="rent_due_date")
    amount = serializers.DecimalField(
        source="amount_paid", max_digits=10, decimal_places=2
    )
    invoice_url = serializers.SerializerMethodField()
    unit_name = serializers.CharField(source="unit.unit", read_only=True)
    building_name = serializers.CharField(source="unit.building.name", read_only=True)
    payment_status = serializers.CharField(source="status", read_only=True)

    class Meta:
        model = RentRecord
        fields = [
            "id",
            "due_date",
            "amount",
            "late_fee",
            "discount",
            "payment_status",
            "payment_method",
            "paid_on",
            "transaction_id",
            "invoice_url",
            "payment_link",
            "notes",
            "unit_name",
            "building_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    @override
    def get_invoice_url(self, obj: RentRecord) -> str:
        if obj.status == "PAID" and obj.invoice_pdf:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.invoice_pdf.url)
            return obj.invoice_pdf.url
        return ""


class RenterAgreementSerializer(serializers.ModelSerializer):
    unit_name = serializers.CharField(source="unit.unit", read_only=True)
    building_name = serializers.CharField(source="unit.building.name", read_only=True)
    document_url = serializers.SerializerMethodField()

    class Meta:
        model = RentAgreementDraft
        fields = [
            "id",
            "renter",
            "unit",
            "unit_name",
            "building_name",
            "generated_at",
            "file",
            "leegality_document_id",
            "owner_signed",
            "renter_signed",
            "document_url",
        ]
        read_only_fields = fields

    @override
    def get_document_url(self, obj: RentAgreementDraft) -> str | None:
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class RenterDocumentSerializer(serializers.ModelSerializer):
    id_proof_url = serializers.SerializerMethodField()
    rent_agreement_url = serializers.SerializerMethodField()

    class Meta:
        model = Renter
        fields = [
            "id",
            "name",
            "id_proof_url",
            "rent_agreement_url",
        ]
        read_only_fields = fields

    @override
    def get_id_proof_url(self, obj: Renter) -> str | None:
        if obj.id_proof:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.id_proof.url)
            return obj.id_proof.url
        return None

    @override
    def get_rent_agreement_url(self, obj: Renter) -> str | None:
        if obj.rent_agreement:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.rent_agreement.url)
            return obj.rent_agreement.url
        return None


class RenterDashboardSerializer(serializers.Serializer):
    profile = RenterProfileSerializer(read_only=True)
    current_rent = RenterRentRecordDetailSerializer(read_only=True, allow_null=True)
    recent_payments = RenterRentRecordSerializer(many=True, read_only=True)
    agreement = RenterAgreementSerializer(read_only=True, allow_null=True)
    notifications_unread_count = serializers.IntegerField(read_only=True)
    extra_charges_count = serializers.IntegerField(read_only=True)


class RenterExtraChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtraCharge
        fields = [
            "id",
            "name",
            "amount",
            "due_date",
            "status",
            "is_paid",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
