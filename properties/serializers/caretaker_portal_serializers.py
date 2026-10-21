"""The serializers of the caretaker portal.

The caretaker works with the properties of the owner. The payloads carry
only what a caretaker needs on the ground — the property, the tenant contact
and the maintenance job. Owner financials never appear here.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from rentsecure_be.type_compat import override

from ..models import CareTakerAssignment, MaintenanceRequest, Renter


class CareTakerBuildingSerializer(serializers.Serializer):
    """A building the caretaker looks after."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    address_line = serializers.CharField(read_only=True)
    city = serializers.CharField(read_only=True)
    unit_count = serializers.IntegerField(read_only=True)
    tenant_count = serializers.IntegerField(read_only=True)
    open_requests = serializers.IntegerField(read_only=True)


class CareTakerUnitSerializer(serializers.Serializer):
    """A single home the caretaker looks after."""

    id = serializers.IntegerField(read_only=True)
    unit = serializers.CharField(read_only=True)
    building = serializers.CharField(read_only=True)
    address_line = serializers.CharField(read_only=True)
    city = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    tenant_name = serializers.CharField(read_only=True, allow_null=True)
    open_requests = serializers.IntegerField(read_only=True)


class CareTakerMaintenanceSerializer(serializers.ModelSerializer):
    """A maintenance job of the caretaker."""

    unit_label = serializers.SerializerMethodField()
    building_name = serializers.CharField(read_only=True)
    priority_label = serializers.CharField(read_only=True)
    status_label = serializers.CharField(read_only=True)
    category_label = serializers.CharField(read_only=True)
    tenant_name = serializers.CharField(read_only=True, allow_null=True)
    tenant_phone = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = MaintenanceRequest
        fields = [
            "id",
            "title",
            "description",
            "category",
            "category_label",
            "priority",
            "priority_label",
            "status",
            "status_label",
            "unit",
            "unit_label",
            "building_name",
            "tenant_name",
            "tenant_phone",
            "assigned_caretaker",
            "reported_at",
            "updated_at",
            "resolved_at",
        ]
        read_only_fields = [
            "id",
            "title",
            "description",
            "category",
            "priority",
            "unit",
            "reported_at",
            "updated_at",
            "resolved_at",
        ]

    @override
    def get_unit_label(self, obj: MaintenanceRequest) -> str:
        unit = obj.unit
        return getattr(unit, "unit", "") or "Unit"

    @override
    def to_representation(self, instance: MaintenanceRequest) -> dict[str, Any]:
        data = super().to_representation(instance)
        unit = instance.unit
        building = getattr(unit, "building", None)
        renter = instance.renter
        data["building_name"] = getattr(building, "name", "") or ""
        data["tenant_name"] = getattr(renter, "name", None)
        data["tenant_phone"] = getattr(renter, "phone", None)
        return data


class CareTakerMaintenanceUpdateSerializer(serializers.Serializer):
    """The only changes a caretaker may make to a maintenance job."""

    status = serializers.ChoiceField(
        choices=MaintenanceRequest.Status.choices, required=False
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    assigned_caretaker = serializers.IntegerField(required=False, allow_null=True)


class CareTakerTenantSerializer(serializers.ModelSerializer):
    """The contact details of a tenant of an assigned home."""

    unit_label = serializers.SerializerMethodField()
    building_name = serializers.CharField(read_only=True)
    status_label = serializers.CharField(read_only=True)

    class Meta:
        model = Renter
        fields = [
            "id",
            "name",
            "phone",
            "whatsapp_number",
            "alternate_phone",
            "email",
            "unit",
            "unit_label",
            "building_name",
            "status",
            "status_label",
            "start_date",
            "end_date",
            "emergency_contact_name",
            "emergency_contact_number",
        ]
        read_only_fields = fields

    @override
    def get_unit_label(self, obj: Renter) -> str:
        return getattr(obj.unit, "unit", "") or "Unit"

    @override
    def to_representation(self, instance: Renter) -> dict[str, Any]:
        data = super().to_representation(instance)
        building = getattr(instance.unit, "building", None)
        data["building_name"] = getattr(building, "name", "") or ""
        return data


class CareTakerAssignmentSummarySerializer(serializers.ModelSerializer):
    """The scope of the caretaker, as shown in the portal."""

    scope_type = serializers.CharField(read_only=True)
    scope_label = serializers.CharField(read_only=True)

    class Meta:
        model = CareTakerAssignment
        fields = [
            "id",
            "building",
            "unit",
            "scope_type",
            "scope_label",
            "assigned_at",
            "is_active",
        ]
        read_only_fields = fields
