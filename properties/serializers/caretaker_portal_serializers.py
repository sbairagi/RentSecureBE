"""The serializers of the caretaker portal.

The caretaker works with the properties of the owner. The payloads carry
only what a caretaker needs on the ground — the property, the tenant contact
and the maintenance job. Owner financials never appear here.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from rentsecure_be.type_compat import override

from ..models import CareTaker, CareTakerAssignment, MaintenanceRequest, Renter


def short_address(obj: Any) -> str:
    """Return the address of a building or a home without the postal code."""
    parts = [
        getattr(obj, "address_line", "") or "",
        getattr(obj, "city", "") or "",
    ]
    return ", ".join(part for part in parts if part)


def full_address(obj: Any) -> str:
    """Return the address of a building or a home as one line."""
    base = short_address(obj)
    postal_code = getattr(obj, "postal_code", "") or ""
    if base and postal_code:
        return f"{base} {postal_code}"
    return base or postal_code


def street_label(address_line: str) -> str:
    """Return the street of an address without the house number.

    "5 Baner Road" becomes "Baner Road" — the way a caretaker names the
    place on the ground.
    """
    value = (address_line or "").strip()
    if not value:
        return ""
    street = value.split(",", 1)[0].strip()
    head, _, tail = street.partition(" ")
    if head.isdigit() and tail:
        return tail
    return street


class CareTakerBuildingSerializer(serializers.Serializer):
    """A building the caretaker looks after."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    address = serializers.SerializerMethodField()
    address_line = serializers.CharField(read_only=True)
    city = serializers.CharField(read_only=True)
    state = serializers.CharField(read_only=True)
    postal_code = serializers.CharField(read_only=True)
    society_contact_name = serializers.CharField(read_only=True)
    society_contact_phone = serializers.CharField(read_only=True)
    unit_count = serializers.IntegerField(read_only=True)
    tenant_count = serializers.IntegerField(read_only=True)
    open_requests = serializers.IntegerField(read_only=True)
    type = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    owner_phone = serializers.SerializerMethodField()

    @override
    def get_address(self, obj: Any) -> str:
        """Return the address of the building."""
        return full_address(obj)

    @override
    def get_owner_name(self, obj: Any) -> str:
        """Return the owner of the building."""
        owner = getattr(obj, "owner", None)
        return getattr(owner, "full_name", "") or getattr(owner, "username", "") or ""

    @override
    def get_owner_phone(self, obj: Any) -> str:
        """Return the phone of the owner of the building."""
        owner = getattr(obj, "owner", None)
        return getattr(owner, "phone", "") or ""

    @override
    def get_type(self, obj: Any) -> str:
        """Return the kind of the property."""
        return "building"


class CareTakerUnitSerializer(serializers.Serializer):
    """A single home the caretaker looks after."""

    id = serializers.IntegerField(read_only=True)
    unit = serializers.CharField(read_only=True)
    building = serializers.CharField(read_only=True)
    address = serializers.SerializerMethodField()
    address_line = serializers.CharField(read_only=True)
    city = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    tenant_name = serializers.CharField(read_only=True, allow_null=True)
    tenant_phone = serializers.CharField(read_only=True, allow_null=True)
    open_requests = serializers.IntegerField(read_only=True)
    type = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    owner_phone = serializers.SerializerMethodField()

    @override
    def get_address(self, obj: Any) -> str:
        """Return the address of the home."""
        return full_address(obj)

    @override
    def get_owner_name(self, obj: Any) -> str:
        """Return the owner of the home."""
        owner = getattr(obj, "owner", None)
        return getattr(owner, "full_name", "") or getattr(owner, "username", "") or ""

    @override
    def get_owner_phone(self, obj: Any) -> str:
        """Return the phone of the owner of the home."""
        owner = getattr(obj, "owner", None)
        return getattr(owner, "phone", "") or ""

    @override
    def get_type(self, obj: Any) -> str:
        """Return the kind of the property."""
        return "standalone home"

    @override
    def get_label(self, obj: Any) -> str:
        """Return the name the caretaker uses for the home."""
        unit = getattr(obj, "unit", "") or ""
        street = street_label(getattr(obj, "address_line", "") or "")
        if street and street.lower() != unit.lower():
            return f"{unit} · {street}"
        return unit


class CareTakerHomeSerializer(serializers.Serializer):
    """One home of the scope of the caretaker.

    A home of a building the caretaker looks after is a home of the scope, so
    the caretaker sees the tenant of every flat of the building — not only the
    one that was assigned to them.
    """

    id = serializers.IntegerField(read_only=True)
    unit = serializers.CharField(read_only=True)
    building = serializers.CharField(read_only=True)
    building_name = serializers.SerializerMethodField()
    building_id = serializers.IntegerField(read_only=True)
    address = serializers.SerializerMethodField()
    home_label = serializers.SerializerMethodField()
    tenant_name = serializers.CharField(read_only=True, allow_null=True)
    tenant_phone = serializers.CharField(read_only=True, allow_null=True)
    status = serializers.CharField(read_only=True)
    open_requests = serializers.IntegerField(read_only=True)
    last_update = serializers.CharField(read_only=True)
    scope = serializers.CharField(read_only=True)

    @override
    def get_address(self, obj: Any) -> str:
        """Return the address of the home."""
        return full_address(obj)

    @override
    def get_building_name(self, obj: Any) -> str:
        """Return the name of the building the home belongs to."""
        building = getattr(obj, "building", None)
        return getattr(building, "name", "") or ""

    @override
    def get_home_label(self, obj: Any) -> str:
        """Return the short kind of the home — flat, villa, house."""
        raw = getattr(obj, "unit_type", "") or ""
        labels = {
            "land": "Land",
            "flat": "Flat",
            "commercial_shop": "Shop",
            "house": "House",
            "villa": "Villa",
            "office": "Office",
            "paying_guest": "Paying guest",
        }
        return labels.get(str(raw).lower(), "Home")


class CareTakerProfileSerializer(serializers.ModelSerializer):
    """The caretaker himself — the screen of the profile."""

    owner_name = serializers.SerializerMethodField()
    owner_phone = serializers.SerializerMethodField()

    class Meta:
        model = CareTaker
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "alternate_phone",
            "preferred_language",
            "joining_date",
            "address",
            "is_active",
            "owner_name",
            "owner_phone",
        ]
        read_only_fields = fields

    @override
    def get_owner_name(self, obj: CareTaker) -> str:
        """Return the name of the owner the caretaker works for."""
        return getattr(obj.owner, "full_name", "") or getattr(obj.owner, "username", "")

    @override
    def get_owner_phone(self, obj: CareTaker) -> str:
        """Return the phone of the owner the caretaker works for."""
        return getattr(obj.owner, "phone", "") or ""


class CareTakerMaintenanceSerializer(serializers.ModelSerializer):
    """A maintenance job of the caretaker."""

    unit_label = serializers.SerializerMethodField()
    building_name = serializers.CharField(read_only=True)
    priority_label = serializers.CharField(read_only=True)
    status_label = serializers.CharField(read_only=True)
    category_label = serializers.CharField(read_only=True)
    tenant_name = serializers.CharField(read_only=True, allow_null=True)
    tenant_phone = serializers.CharField(read_only=True, allow_null=True)
    assigned_caretaker_name = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

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
            "assigned_caretaker_name",
            "is_mine",
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

    @override
    def get_assigned_caretaker_name(self, obj: MaintenanceRequest) -> str:
        """Return the caretaker that took the job."""
        return getattr(obj.assigned_caretaker, "name", "") or ""

    @override
    def get_is_mine(self, obj: MaintenanceRequest) -> bool:
        """Return whether the job is in the hands of the caretaker."""
        caretaker_id = self.context.get("caretaker_id")
        return bool(caretaker_id) and obj.assigned_caretaker_id == caretaker_id


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


class CareTakerProfileUpdateSerializer(serializers.ModelSerializer):
    """The changes the caretaker may make to his own profile."""

    class Meta:
        model = CareTaker
        fields = [
            "name",
            "email",
            "phone",
            "alternate_phone",
            "preferred_language",
        ]
        extra_kwargs = {
            "name": {"required": False},
            "email": {"required": False},
            "phone": {"required": False},
            "alternate_phone": {"required": False},
            "preferred_language": {"required": False},
        }


class CareTakerAssignmentSummarySerializer(serializers.ModelSerializer):
    """The scope of the caretaker, as shown in the portal."""

    scope_type = serializers.CharField(read_only=True)
    scope_label = serializers.CharField(read_only=True)
    address = serializers.SerializerMethodField()
    property_type = serializers.SerializerMethodField()

    class Meta:
        model = CareTakerAssignment
        fields = [
            "id",
            "building",
            "unit",
            "scope_type",
            "scope_label",
            "property_type",
            "address",
            "assigned_at",
            "is_active",
        ]
        read_only_fields = fields

    @override
    def get_address(self, obj: CareTakerAssignment) -> str:
        """Return the address of the assigned property."""
        if obj.building_id:
            return short_address(obj.building)
        if obj.unit_id:
            return short_address(obj.unit)
        return ""

    @override
    def get_property_type(self, obj: CareTakerAssignment) -> str:
        """Return the kind of the assigned property."""
        return "building" if obj.building_id else "standalone home"
