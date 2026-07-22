from django.contrib import admin

from core.events.inbox.models import InboxEvent
from shared.type_compat import override


@admin.register(InboxEvent)
class InboxEventAdmin(admin.ModelAdmin):
    list_display = (
        "event_id",
        "aggregate_type",
        "aggregate_id",
        "event_type",
        "status",
        "retry_count",
        "next_retry_at",
        "processed_at",
        "received_at",
        "created_at",
    )
    search_fields = ("event_id", "aggregate_id", "aggregate_type", "event_type")
    list_filter = ("status", "event_type", "created_at")
    readonly_fields = (
        "id",
        "event_id",
        "aggregate_type",
        "aggregate_id",
        "event_type",
        "payload",
        "headers",
        "status",
        "received_at",
        "processed_at",
        "retry_count",
        "max_retry",
        "next_retry_at",
        "last_error",
        "created_at",
        "updated_at",
    )
    actions = None

    @override
    def has_add_permission(self, request: object) -> bool:
        return False

    @override
    def has_change_permission(self, request: object, obj: object | None = None) -> bool:
        return False

    @override
    def has_delete_permission(self, request: object, obj: object | None = None) -> bool:
        return False


__all__ = ["InboxEventAdmin"]
