from django.contrib import admin
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin

from ..models import Caretaker


@admin.register(Caretaker)
class CaretakerAdmin(SimpleHistoryAdmin):
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
    readonly_fields = ("created_at", "updated_at", "caretaker_image_thumbnail")
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

    def caretaker_image_thumbnail(self, obj):
        if obj.caretaker_image:
            return format_html(
                '<img src="{}" style="height: 50px;"/>', obj.caretaker_image.url
            )
        return "-"

    caretaker_image_thumbnail.short_description = "Caretaker Image Preview"
