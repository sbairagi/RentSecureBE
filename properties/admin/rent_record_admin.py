from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from ..models import RentRecord


@admin.register(RentRecord)
class RentRecordAdmin(SimpleHistoryAdmin):
    list_display = (
        "id",
        "renter",
        "unit",
        "rent_month",
        "amount_paid",
        "date_paid",
        "payment_mode",
        "remarks",
        "created_at",
        "updated_at",
        "grace_days",
        "late_fee",
    )
    search_fields = ("renter__name",)
    list_filter = ("rent_month",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Rent Info",
            {
                "fields": (
                    "renter",
                    "unit",
                    "rent_month",
                    "amount_paid",
                    "date_paid",
                    "payment_mode",
                )
            },
        ),
        ("Additional Info", {"fields": ("remarks",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
    actions = ["mark_as_paid"]

    def mark_as_paid(self, request, queryset):
        updated_count = queryset.update(remarks="Paid")
        self.message_user(request, f"{updated_count} rent record(s) marked as Paid.")

    mark_as_paid.short_description = "Mark selected rent records as Paid"
