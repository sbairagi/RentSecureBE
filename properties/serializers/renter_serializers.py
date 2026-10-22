from typing import Any, cast

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from documents.receipt import receipt_filename
from rentsecure_be.type_compat import override

from ..models import ExtraCharge, RentAgreementDraft, Renter, RentRecord, Unit
from .rent_record_serializers import RentRecordPartSerializer


class RenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Renter
        fields = "__all__"
        read_only_fields = [
            "id",
            "user",
            "created_at",
            "updated_at",
        ]
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
    unit_label = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    owner_phone = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()
    caretakers = serializers.SerializerMethodField()

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
            "unit_label",
            "owner_name",
            "owner_phone",
            "owner_email",
            "caretakers",
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
    def get_unit_label(self, obj: Renter) -> str:
        """Return the name of the home the renter lives in."""
        return getattr(obj.unit, "unit", "") or ""

    @override
    def get_owner_name(self, obj: Renter) -> str:
        """Return the name of the owner of the home."""
        owner = getattr(obj.unit, "owner", None)
        return getattr(owner, "full_name", "") or getattr(owner, "username", "")

    @override
    def get_owner_phone(self, obj: Renter) -> str:
        """Return the phone number of the owner."""
        owner = getattr(obj.unit, "owner", None)
        return getattr(owner, "phone", "") or ""

    @override
    def get_owner_email(self, obj: Renter) -> str:
        """Return the e-mail of the owner."""
        owner = getattr(obj.unit, "owner", None)
        return getattr(owner, "email", "") or ""

    @override
    def get_caretakers(self, obj: Renter) -> list[dict[str, str]]:
        """Return the caretakers that look after the home of the renter."""
        from properties.services.caretaker_scope import caretakers_for_unit

        if obj.unit_id is None:
            return []
        caretakers = caretakers_for_unit(obj.unit).select_related("owner")
        return [
            {
                "id": caretaker.id,
                "name": caretaker.name,
                "phone": caretaker.phone,
                "alternate_phone": caretaker.alternate_phone,
            }
            for caretaker in caretakers
        ]

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
    payment_status = serializers.SerializerMethodField()

    class Meta:
        model = RentRecord
        fields = ["due_date", "amount", "late_fee", "payment_status", "invoice_url"]

    def get_invoice_url(self, obj: RentRecord) -> str:
        if obj.status == "PAID":
            return obj.invoice_pdf.url or ""
        return ""

    @override
    def get_payment_status(self, obj: RentRecord) -> str:
        """Return the status the renter reads on the record."""
        from properties.services.renter_portal_service import effective_status

        return effective_status(obj)


class RenterRentRecordDetailSerializer(serializers.ModelSerializer):
    due_date = serializers.DateField(source="rent_due_date")
    amount = serializers.DecimalField(
        source="amount_paid", max_digits=10, decimal_places=2
    )
    invoice_url = serializers.SerializerMethodField()
    unit_name = serializers.CharField(source="unit.unit", read_only=True)
    building_name = serializers.CharField(source="unit.building.name", read_only=True)
    payment_status = serializers.SerializerMethodField()
    receipt_no = serializers.SerializerMethodField()
    renter_name = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    rent_amount = serializers.DecimalField(
        source="total_due", max_digits=10, decimal_places=2, read_only=True
    )
    amount_paid = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_partially_paid = serializers.BooleanField(read_only=True)
    parts = RentRecordPartSerializer(many=True, read_only=True)

    class Meta:
        model = RentRecord
        fields = [
            "id",
            "due_date",
            "amount",
            "rent_amount",
            "amount_paid",
            "balance",
            "is_partially_paid",
            "late_fee",
            "discount",
            "payment_status",
            "payment_method",
            "paid_on",
            "transaction_id",
            "invoice_url",
            "receipt_no",
            "renter_name",
            "owner_name",
            "payment_link",
            "notes",
            "unit_name",
            "building_name",
            "parts",
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

    @override
    def get_payment_status(self, obj: RentRecord) -> str:
        """Return the status the renter reads on the record."""
        from properties.services.renter_portal_service import effective_status

        return effective_status(obj)

    def get_receipt_no(self, obj: RentRecord) -> str:
        """Return the reference of the receipt the renter downloads."""
        return receipt_filename(obj)

    def get_renter_name(self, obj: RentRecord) -> str:
        """Return the name of the renter the record belongs to."""
        renter = obj.renter
        if renter is None:
            return ""
        return getattr(renter, "name", "") or ""

    def get_owner_name(self, obj: RentRecord) -> str:
        """Return the name of the owner of the flat the record belongs to."""
        owner = getattr(obj.unit, "owner", None)
        if owner is None:
            return ""
        return getattr(owner, "full_name", "") or owner.username


class RenterAgreementSerializer(serializers.ModelSerializer):
    unit_name = serializers.CharField(source="unit.unit", read_only=True)
    building_name = serializers.CharField(source="unit.building.name", read_only=True)
    document_url = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    signature_progress = serializers.IntegerField(read_only=True)
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = RentAgreementDraft
        fields = [
            "id",
            "renter",
            "unit",
            "unit_name",
            "building_name",
            "agreement_number",
            "status",
            "status_label",
            "signature_progress",
            "generated_at",
            "file",
            "leegality_document_id",
            "owner_signed",
            "renter_signed",
            "document_url",
            "monthly_rent",
            "security_deposit",
            "start_date",
            "end_date",
            "rent_due_day",
            "payment_mode",
            "notice_period_months",
            "jurisdiction",
            "witness_name",
            "special_clauses",
            "owner_signed_at",
            "renter_signed_at",
            "document_generated_at",
            "owner_name",
        ]
        read_only_fields = fields

    @override
    def get_owner_name(self, obj: RentAgreementDraft) -> str:
        """Return the name of the owner who signed the agreement."""
        owner = getattr(obj.unit, "owner", None)
        if owner is None:
            return ""
        return getattr(owner, "full_name", "") or owner.username

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
