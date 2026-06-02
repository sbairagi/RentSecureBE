from django.contrib import admin
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin

from ..models import (
    Caretaker,
    RentAgreementDraft,
    Renter,
    Unit,
    UnitDocument,
    UnitImage,
)


class CaretakerInline(admin.TabularInline):
    model = Caretaker
    extra = 1
    readonly_fields = ("caretaker_image_thumbnail",)

    def caretaker_image_thumbnail(self, obj):
        if obj.caretaker_image:
            return format_html(
                '<img src="{}" style="height: 50px;"/>', obj.caretaker_image.url
            )
        return "-"

    caretaker_image_thumbnail.short_description = "Caretaker Image"


class RenterInline(admin.TabularInline):
    model = Renter
    extra = 1
    readonly_fields = ("renter_image_thumbnail",)

    def renter_image_thumbnail(self, obj):
        if obj.renter_image:
            return format_html(
                '<img src="{}" style="height: 50px;"/>', obj.renter_image.url
            )
        return "-"

    renter_image_thumbnail.short_description = "Renter Image"


@admin.register(Unit)
class UnitAdmin(SimpleHistoryAdmin):
    list_display = (
        "id",
        "building_name",
        "unit",
        "owner",
        "address_line",
        "landmark",
        "city",
        "state",
        "country",
        "postal_code",
        "unit_type",
        "unit_image_thumbnail",
        "is_vacant",
        "is_verified",
        "maintenance_notes",
        "rent_due_reminder",
        "agreement_expiry_reminder",
        "latitude",
        "longitude",
        "notes",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "building__name",
        "building_name",
        "unit",
        "city",
        "owner__username",
    )
    list_filter = ("unit_type", "is_vacant", "is_verified")
    readonly_fields = ("created_at", "updated_at", "unit_image_thumbnail")
    inlines = [CaretakerInline, RenterInline]
    fieldsets = (
        ("Basic Info", {"fields": ("owner", "building_name", "unit", "unit_type")}),
        (
            "Address",
            {
                "fields": (
                    "address_line",
                    "landmark",
                    "city",
                    "state",
                    "country",
                    "postal_code",
                )
            },
        ),
        (
            "Documents & Images",
            {"fields": ("unit_image", "unit_image_thumbnail", "id_proof")},
        ),
        (
            "Status & Reminders",
            {
                "fields": (
                    "is_vacant",
                    "is_verified",
                    "rent_due_reminder",
                    "agreement_expiry_reminder",
                )
            },
        ),
        ("Location", {"fields": ("latitude", "longitude")}),
        ("Additional Notes", {"fields": ("maintenance_notes", "notes")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def unit_image_thumbnail(self, obj):
        if obj.unit_image:
            return format_html(
                '<img src="{}" style="height: 50px;"/>', obj.unit_image.url
            )
        return "-"

    unit_image_thumbnail.short_description = "Unit Image Preview"


@admin.register(UnitImage)
class UnitImageAdmin(admin.ModelAdmin):
    list_display = ("unit", "image", "uploaded_at")
    search_fields = ("unit__unit",)


@admin.register(UnitDocument)
class UnitDocumentAdmin(admin.ModelAdmin):
    list_display = ("unit", "document", "uploaded_at")
    search_fields = ("unit__unit",)


@admin.register(RentAgreementDraft)
class RentAgreementDraftAdmin(admin.ModelAdmin):
    list_display = ("user", "renter", "generated_at")
    search_fields = ("user__username", "renter__name")
