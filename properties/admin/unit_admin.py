from django.contrib import admin

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


class RenterInline(admin.TabularInline):
    model = Renter
    extra = 1


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
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
    readonly_fields = ("created_at", "updated_at")
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
            {"fields": ("id_proof",)},
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
