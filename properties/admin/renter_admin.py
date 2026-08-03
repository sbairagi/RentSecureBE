from simple_history.admin import SimpleHistoryAdmin  # type: ignore[import-untyped]

from django.contrib import admin
from django.utils.html import format_html

from ..models import Renter


@admin.register(Renter)
class RenterAdmin(SimpleHistoryAdmin):  # type: ignore[misc]
    list_display = (
        "id",
        "unit",
        "name",
        "phone",
        "alternate_phone",
        "whatsapp_number",
        "emergency_contact_name",
        "emergency_contact_number",
        "renter_image_thumbnail",
        "rent_amount",
        "start_date",
        "end_date",
        "is_active",
        "status",
        "missed_rents",
        "notes",
        "created_at",
        "updated_at",
    )
    search_fields = ("name", "phone")
    list_filter = ("status", "is_active")
    readonly_fields = ("created_at", "updated_at", "renter_image_thumbnail")
    fieldsets = (
        (
            "Basic Info",
            {"fields": ("unit", "name", "phone", "alternate_phone", "whatsapp_number")},
        ),
        (
            "Emergency Contact",
            {"fields": ("emergency_contact_name", "emergency_contact_number")},
        ),
        (
            "Documents",
            {
                "fields": (
                    "renter_image",
                    "renter_image_thumbnail",
                    "id_proof",
                    "rent_agreement",
                )
            },
        ),
        (
            "Rental Details",
            {
                "fields": (
                    "rent_amount",
                    "start_date",
                    "end_date",
                    "is_active",
                    "status",
                )
            },
        ),
        ("Additional Info", {"fields": ("notes",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
    actions = ["mark_active", "mark_notice_period", "mark_revoked", "mark_deactivated"]

    def renter_image_thumbnail(self, obj: Renter) -> str:
        if obj.renter_image:
            return format_html(
                '<img src="{}" style="height: 50px;"/>', obj.renter_image.url
            )
        return "-"

    renter_image_thumbnail.short_description = (  # type: ignore[attr-defined]
        "Renter Image Preview"
    )

    @admin.action(description="Mark selected renters as Active")
    def mark_active(self, request, queryset):
        queryset.update(status=Renter.RenterStatus.ACTIVE)

    @admin.action(description="Mark selected renters as Notice Period")
    def mark_notice_period(self, request, queryset):
        queryset.update(status=Renter.RenterStatus.NOTICE_PERIOD)

    @admin.action(description="Mark selected renters as Revoked")
    def mark_revoked(self, request, queryset):
        queryset.update(status=Renter.RenterStatus.REVOKED)

    @admin.action(description="Mark selected renters as Deactivated")
    def mark_deactivated(self, request, queryset):
        queryset.update(status=Renter.RenterStatus.DEACTIVATED)
