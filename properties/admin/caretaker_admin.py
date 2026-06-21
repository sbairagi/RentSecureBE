from django.contrib import admin

from ..models import Caretaker


@admin.register(Caretaker)
class CaretakerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "unit",
        "name",
        "email",
        "phone",
        "alternate_phone",
        "address",
        "joining_date",
        "leaving_date",
        "is_active",
        "notes",
        "created_at",
        "updated_at",
    )
    search_fields = ("name", "phone")
    list_filter = ("joining_date", "leaving_date", "is_active")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Basic Info",
            {"fields": ("unit", "name", "email", "phone", "alternate_phone")},
        ),
        (
            "Address",
            {"fields": ("address",)},
        ),
        ("Dates", {"fields": ("joining_date", "leaving_date", "is_active")}),
        ("Notes", {"fields": ("notes",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
