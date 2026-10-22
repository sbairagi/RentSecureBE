from django.contrib import admin

from ..models import (
    CareTaker,
    CareTakerActivity,
    CareTakerAssignment,
    CareTakerAssignmentLog,
)


@admin.register(CareTaker)
class CareTakerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner",
        "name",
        "unit",
        "email",
        "phone",
        "alternate_phone",
        "joining_date",
        "leaving_date",
        "is_active",
    )
    search_fields = ("name", "phone", "email")
    list_filter = ("joining_date", "leaving_date", "is_active", "owner")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("owner", "unit", "user")
    fieldsets = (
        (
            "Who they work for",
            {"fields": ("owner", "unit", "user")},
        ),
        (
            "Basic Info",
            {"fields": ("name", "email", "phone", "alternate_phone")},
        ),
        (
            "Address",
            {"fields": ("address",)},
        ),
        ("Dates", {"fields": ("joining_date", "leaving_date", "is_active")}),
        ("Notes", {"fields": ("notes",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(CareTakerAssignment)
class CareTakerAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "caretaker",
        "scope_type",
        "scope_label",
        "assigned_by",
        "assigned_at",
        "unassigned_at",
        "is_active",
    )
    search_fields = ("caretaker__name", "notes")
    list_filter = ("is_active", "assigned_at")
    autocomplete_fields = ("caretaker", "building", "unit", "assigned_by")


@admin.register(CareTakerAssignmentLog)
class CareTakerAssignmentLogAdmin(admin.ModelAdmin):
    list_display = ("id", "caretaker", "action", "action_date", "notes")
    search_fields = ("caretaker__name", "notes")
    list_filter = ("action", "action_date")


@admin.register(CareTakerActivity)
class CareTakerActivityAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner",
        "caretaker",
        "action",
        "summary",
        "created_at",
    )
    search_fields = ("caretaker__name", "summary", "detail")
    list_filter = ("action", "created_at")
    readonly_fields = ("created_at", "maintenance_request", "actor")
    autocomplete_fields = ("caretaker", "owner")
