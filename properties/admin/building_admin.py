from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from ..models import Building


@admin.register(Building)
class BuildingAdmin(SimpleHistoryAdmin):
    list_display = (
        "id",
        "name",
        "address_line",
        "city",
        "state",
        "country",
        "postal_code",
        "owner",
        "created_at",
    )
    search_fields = (
        "name",
        "address_line",
        "city",
        "state",
        "country",
        "owner__username",
    )
    list_filter = ("city", "state", "country")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
