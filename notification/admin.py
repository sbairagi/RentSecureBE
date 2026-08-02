from django.contrib import admin

from .models import Notification, WhatsAppLog


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "is_read", "created_at")
    search_fields = ("user__username", "title")
    list_filter = ("is_read",)


@admin.register(WhatsAppLog)
class WhatsAppLogAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "message_type", "status", "timestamp")
    search_fields = ("phone", "message_content", "user__username")
    list_filter = ("message_type", "status", "timestamp")
    readonly_fields = ("timestamp",)
