from __future__ import annotations

import logging
from typing import Any

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError

from rentsecure_be.type_compat import override
from visitors.models import Visitor, VisitorHistory

logger = logging.getLogger(__name__)


class VisitorSerializer(serializers.ModelSerializer):
    """Serializer for Visitor model — full detail."""

    renter_name = serializers.CharField(source="renter.name", read_only=True)
    renter_phone = serializers.CharField(source="renter.phone", read_only=True)
    unit_identifier = serializers.CharField(source="unit.unit", read_only=True)
    building_name = serializers.CharField(source="building.name", read_only=True)
    approved_by_name = serializers.CharField(
        source="approved_by.full_name", read_only=True
    )
    verified_by_name = serializers.CharField(
        source="verified_by.full_name", read_only=True
    )
    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True
    )
    photo_url = serializers.SerializerMethodField()
    can_check_in = serializers.ReadOnlyField()
    can_check_out = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    is_otp_expired = serializers.ReadOnlyField()
    is_qr_expired = serializers.ReadOnlyField()

    class Meta:
        model = Visitor
        fields = "__all__"
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "qr_token",
            "qr_generated_at",
            "qr_expires_at",
            "qr_used_count",
            "qr_verified",
            "qr_verified_at",
            "otp_code",
            "otp_generated_at",
            "otp_expires_at",
            "otp_verified",
            "otp_verified_at",
            "otp_attempts",
            "check_in_time",
            "check_out_time",
            "visit_duration_minutes",
        ]

    def get_photo_url(self, obj: Visitor) -> str | None:
        if obj.photo:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None

    @override
    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        request = self.context.get("request")
        user = request.user if request else None

        unit = data.get("unit")
        if unit and hasattr(unit, "owner") and user and unit.owner != user:
            raise PermissionDenied("You do not own the selected unit.")

        building = data.get("building")
        if building and hasattr(building, "owner") and user and building.owner != user:
            raise PermissionDenied("You do not own the selected building.")

        renter = data.get("renter")
        if renter and unit and renter.unit_id != unit.id:
            raise ValidationError(
                {"renter": "Renter must be associated with the selected unit."}
            )

        expected_arrival = data.get("expected_arrival")
        expected_departure = data.get("expected_departure")
        if expected_arrival and expected_departure:
            if expected_departure <= expected_arrival:
                raise ValidationError(
                    {"expected_departure": "Departure must be after arrival."}
                )

        phone = data.get("phone_number")
        if phone:
            import re

            if not re.match(r"^\+?1?\d{9,15}$", phone):
                raise ValidationError(
                    {"phone_number": "Phone must be in format: +999999999"}
                )

        return data


class VisitorCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a visitor request."""

    class Meta:
        model = Visitor
        fields = [
            "visitor_name",
            "phone_number",
            "email",
            "photo",
            "purpose",
            "building",
            "unit",
            "renter",
            "visit_date",
            "expected_arrival",
            "expected_departure",
            "number_of_visitors",
            "vehicle_number",
            "notes",
        ]

    @override
    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        request = self.context.get("request")
        user = request.user if request else None

        unit = data.get("unit")
        if unit and hasattr(unit, "owner") and user and unit.owner != user:
            raise PermissionDenied("You do not own the selected unit.")

        building = data.get("building")
        if building and hasattr(building, "owner") and user and building.owner != user:
            raise PermissionDenied("You do not own the selected building.")

        renter = data.get("renter")
        if renter and unit and renter.unit_id != unit.id:
            raise ValidationError(
                {"renter": "Renter must be associated with the selected unit."}
            )

        expected_arrival = data.get("expected_arrival")
        expected_departure = data.get("expected_departure")
        if expected_arrival and expected_departure:
            if expected_departure <= expected_arrival:
                raise ValidationError(
                    {"expected_departure": "Departure must be after arrival."}
                )

        return data

    @override
    def create(self, validated_data: dict[str, Any]) -> Visitor:
        request = self.context.get("request")
        validated_data["created_by"] = request.user if request else None
        validated_data.setdefault("status", Visitor.Status.REQUESTED)
        return super().create(validated_data)


class VisitorApprovalSerializer(serializers.Serializer):
    """Serializer for approving/rejecting a visitor."""

    action = serializers.ChoiceField(choices=["approve", "reject"])
    reason = serializers.CharField(required=False, default="")
    notes = serializers.CharField(required=False, default="")


class VisitorCheckInSerializer(serializers.Serializer):
    """Serializer for checking in a visitor."""

    vehicle_details = serializers.CharField(required=False, default="", max_length=100)
    qr_token = serializers.CharField(required=False, default="")
    otp_code = serializers.CharField(required=False, default="")


class VisitorCheckOutSerializer(serializers.Serializer):
    """Serializer for checking out a visitor."""


class VisitorQRGenerateSerializer(serializers.Serializer):
    """Serializer for QR generation request."""


class VisitorOTPGenerateSerializer(serializers.Serializer):
    """Serializer for OTP generation request."""


class VisitorOTPVerifySerializer(serializers.Serializer):
    """Serializer for OTP verification request."""

    otp_code = serializers.CharField(max_length=6, min_length=6)


class VisitorHistorySerializer(serializers.ModelSerializer):
    """Serializer for visitor history entries."""

    performed_by_name = serializers.CharField(
        source="performed_by.full_name", read_only=True, default=None
    )
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = VisitorHistory
        fields = [
            "id",
            "visitor",
            "action",
            "action_display",
            "description",
            "performed_by",
            "performed_by_name",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields


class VisitorStatsSerializer(serializers.Serializer):
    """Serializer for visitor statistics."""

    total = serializers.IntegerField()
    pending_approval = serializers.IntegerField()
    approved = serializers.IntegerField()
    checked_in = serializers.IntegerField()
    checked_out = serializers.IntegerField()
    rejected = serializers.IntegerField()
    expired = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    blocked = serializers.IntegerField()
    today = serializers.IntegerField()
    this_week = serializers.IntegerField()
