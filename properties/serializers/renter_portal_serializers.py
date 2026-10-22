"""Serializers for the renter facing part of the portal.

The renter reads the home they live in, the homes they can rent next, the
viewing they booked, the maintenance of their flat, the agreement they have
to sign and the police verification they have to submit.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from properties.models import (
    MaintenanceRequest,
    PoliceVerification,
    RentAgreementDraft,
    Renter,
    Unit,
    ViewingAppointment,
)


class RenterListingSerializer(serializers.ModelSerializer):
    """A home a renter can book a viewing for."""

    building_name = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    expected_rent = serializers.SerializerMethodField()
    available_from = serializers.SerializerMethodField()

    class Meta:
        model = Unit
        fields = [
            "id",
            "unit",
            "unit_type",
            "building_name",
            "owner_name",
            "city",
            "state",
            "address_line",
            "landmark",
            "postal_code",
            "expected_rent",
            "available_from",
            "status",
        ]

    def get_building_name(self, obj: Unit) -> str:
        """Return the name of the building the unit belongs to."""
        return getattr(obj.building, "name", "") or obj.building_name or ""

    def get_owner_name(self, obj: Unit) -> str:
        """Return the name of the owner, so the renter knows who to deal with."""
        return getattr(obj.owner, "full_name", "") or obj.owner.username

    def get_city(self, obj: Unit) -> str:
        """Return the city of the unit."""
        return obj.city or getattr(obj.building, "city", "") or ""

    def get_state(self, obj: Unit) -> str:
        """Return the state of the unit."""
        return obj.state or getattr(obj.building, "state", "") or ""

    def get_expected_rent(self, obj: Unit) -> str:
        """Return the expected rent of the unit."""
        renter = (
            Renter.objects.filter(unit=obj, is_active=True)
            .order_by("-start_date")
            .first()
        )
        amount = getattr(renter, "rent_amount", None) or getattr(obj, "rent_amount", 0)
        return str(amount)

    def get_available_from(self, obj: Unit) -> str:
        """Return the date the unit is available from."""
        if obj.last_vacated_at:
            return obj.last_vacated_at.isoformat()
        return ""


class ViewingAppointmentSerializer(serializers.ModelSerializer):
    """A viewing appointment booked by a renter."""

    unit_label = serializers.SerializerMethodField()
    building_name = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = ViewingAppointment
        fields = [
            "id",
            "unit",
            "unit_label",
            "building_name",
            "city",
            "owner_name",
            "scheduled_for",
            "mode",
            "notes",
            "status",
            "owner_note",
            "created_at",
        ]
        read_only_fields = [
            "unit",
            "status",
            "owner_note",
            "created_at",
        ]

    def get_unit_label(self, obj: ViewingAppointment) -> str:
        """Return the unit of the appointment."""
        return obj.unit.unit

    def get_building_name(self, obj: ViewingAppointment) -> str:
        """Return the building of the appointment."""
        return getattr(obj.unit.building, "name", "") or obj.unit.building_name or ""

    def get_city(self, obj: ViewingAppointment) -> str:
        """Return the city of the appointment."""
        return obj.unit.city or getattr(obj.unit.building, "city", "") or ""

    def get_owner_name(self, obj: ViewingAppointment) -> str:
        """Return the owner who has to answer the request."""
        return getattr(obj.unit.owner, "full_name", "") or obj.unit.owner.username

    def validate_scheduled_for(self, value: Any) -> Any:
        """Refuse a slot in the past."""
        from django.utils import timezone

        if value < timezone.now():
            raise serializers.ValidationError(
                "The appointment has to be scheduled in the future."
            )
        return value


class RenterMaintenanceSerializer(serializers.ModelSerializer):
    """A maintenance request of the flat the renter lives in."""

    unit_label = serializers.SerializerMethodField()
    building_name = serializers.SerializerMethodField()
    caretaker_name = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = MaintenanceRequest
        fields = [
            "id",
            "title",
            "description",
            "category",
            "priority",
            "status",
            "status_label",
            "unit_label",
            "building_name",
            "caretaker_name",
            "reported_at",
            "updated_at",
            "resolved_at",
        ]
        read_only_fields = [
            "status",
            "reported_at",
            "updated_at",
            "resolved_at",
        ]

    def get_unit_label(self, obj: MaintenanceRequest) -> str:
        """Return the unit of the request."""
        return obj.unit.unit

    def get_building_name(self, obj: MaintenanceRequest) -> str:
        """Return the building of the request."""
        return getattr(obj.unit.building, "name", "") or obj.unit.building_name or ""

    def get_caretaker_name(self, obj: MaintenanceRequest) -> str:
        """Return the caretaker that looks after the unit."""
        return getattr(obj.assigned_caretaker, "name", "") or ""


class RenterVerificationSerializer(serializers.ModelSerializer):
    """The police verification of the renter."""

    status_label = serializers.CharField(source="get_status_display", read_only=True)
    renter_name = serializers.CharField(source="renter.name", read_only=True)
    unit_label = serializers.CharField(source="unit.unit", read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()

    class Meta:
        model = PoliceVerification
        fields = [
            "id",
            "status",
            "status_label",
            "renter_name",
            "unit_label",
            "file",
            "file_name",
            "submitted_at",
            "verified_at",
            "reviewed_at",
            "reviewed_by_name",
            "review_notes",
            "rejection_reason",
        ]
        read_only_fields = [
            "status",
            "submitted_at",
            "verified_at",
            "reviewed_at",
            "reviewed_by_name",
            "file_name",
            "review_notes",
            "rejection_reason",
        ]

    def get_reviewed_by_name(self, obj: PoliceVerification) -> str:
        """Return who reviewed the document, without the account details."""
        reviewer = obj.reviewed_by
        if reviewer is None:
            return ""
        return getattr(reviewer, "full_name", "") or getattr(reviewer, "username", "")

    def get_file_name(self, obj: PoliceVerification) -> str:
        """Return the name of the uploaded document."""
        if not obj.file:
            return ""
        return obj.file.name.rsplit("/", 1)[-1]


class RenterAgreementSerializer(serializers.ModelSerializer):
    """The agreement of the renter, with the state of the workflow."""

    status_label = serializers.CharField(source="get_status_display", read_only=True)
    signature_progress = serializers.IntegerField(read_only=True)
    document_url = serializers.SerializerMethodField()
    unit_label = serializers.CharField(source="unit.unit", read_only=True)
    building_name = serializers.CharField(source="unit.building.name", read_only=True)
    owner_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = RentAgreementDraft
        fields = [
            "id",
            "status",
            "status_label",
            "signature_progress",
            "document_url",
            "agreement_number",
            "unit_label",
            "building_name",
            "owner_name",
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
            "owner_signed",
            "renter_signed",
            "owner_signed_at",
            "renter_signed_at",
            "document_generated_at",
        ]

    def get_document_url(self, obj: RentAgreementDraft) -> str:
        """Return the absolute path of the generated document."""
        if not obj.file:
            return ""
        request = self.context.get("request")
        if request is not None:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url
