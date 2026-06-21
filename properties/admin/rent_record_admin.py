from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from simple_history.admin import SimpleHistoryAdmin

from ..models import RentRecord


@admin.register(RentRecord)
class RentRecordAdmin(SimpleHistoryAdmin):  # type: ignore[misc]
    list_display = (
        "id",
        "renter",
        "unit",
        "amount_paid",
        "paid_on",
        "payment_method",
        "status",
        "late_fee",
        "discount",
        "notes",
        "created_at",
        "updated_at",
    )
    search_fields = ("renter__name",)
    list_filter = ("status", "payment_method", "paid_on")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Rent Info",
            {
                "fields": (
                    "renter",
                    "unit",
                    "amount",
                    "payment_method",
                    "paid_on",
                    "due_date",
                    "status",
                    "late_fee",
                    "discount",
                )
            },
        ),
        ("Additional Info", {"fields": ("notes", "transaction_id")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
    actions = ["mark_as_paid"]

    def mark_as_paid(
        self, request: HttpRequest, queryset: QuerySet[RentRecord]
    ) -> None:
        updated_count = queryset.update(status=RentRecord.Status.PAID)
        self.message_user(request, f"{updated_count} rent record(s) marked as Paid.")

    mark_as_paid.short_description = "Mark selected rent records as Paid"  # type: ignore[attr-defined]
