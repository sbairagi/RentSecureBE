from django.contrib import admin
from django.urls import path
from django.utils.html import format_html

from .models import Notification, WhatsAppLog


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "is_read", "created_at")
    search_fields = ("user__username", "title")
    list_filter = ("is_read",)


@admin.register(WhatsAppLog)
class WhatsAppLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "phone",
        "status",
        "retry_count",
        "message_type",
        "timestamp",
        "retry_button",
    )
    list_filter = ("status", "message_type")
    search_fields = ("phone", "message_content", "user__username")
    actions = ["retry_whatsapp_messages"]
    readonly_fields = ("timestamp",)

    def retry_button(self, obj):
        if obj.status == WhatsAppLog.FAILED and obj.retry_count < 3:
            return format_html(
                '<a class="button" href="/admin/notification/whatsapplog/{}/'
                'retry/">Retry Now</a>',
                obj.pk,
            )
        return "-"

    retry_button.short_description = "Manual Retry"

    def retry_whatsapp_messages(self, request, queryset):
        from notification.services.whatsapp_service import (
            send_whatsapp_audio,
            send_whatsapp_message,
        )

        retried = 0
        for log in queryset.filter(status=WhatsAppLog.FAILED, retry_count__lt=3):
            try:
                if log.message_type == WhatsAppLog.TEXT:
                    success = send_whatsapp_message(
                        log.phone,
                        log.message_content,
                        user=log.user,
                        rent_record=log.rent_record,
                        retry_count=log.retry_count + 1,
                    )
                elif log.message_type == WhatsAppLog.AUDIO:
                    if not log.media_url:
                        continue
                    success = send_whatsapp_audio(
                        log.phone,
                        log.media_url,
                        user=log.user,
                        rent_record=log.rent_record,
                        retry_count=log.retry_count + 1,
                    )
                else:
                    continue

                log.retry_count += 1
                if success:
                    log.status = WhatsAppLog.SENT
                else:
                    log.status = (
                        WhatsAppLog.PERMANENT_FAILED
                        if log.retry_count >= 3
                        else WhatsAppLog.FAILED
                    )
                log.save()
                retried += 1
            except Exception:
                log.retry_count += 1
                log.status = (
                    WhatsAppLog.PERMANENT_FAILED
                    if log.retry_count >= 3
                    else WhatsAppLog.FAILED
                )
                log.save()

        self.message_user(request, f"Retried {retried} message(s).")

    retry_whatsapp_messages.short_description = "Retry selected failed WhatsApp msgs"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:log_id>/retry/",
                self.admin_site.admin_view(self.retry_message_view),
                name="retry_whatsapp_message",
            ),
        ]
        return custom_urls + urls

    def retry_message_view(self, request, log_id):
        from django.contrib import messages
        from django.shortcuts import get_object_or_404, redirect

        from notification.services.whatsapp_service import (
            send_whatsapp_audio,
            send_whatsapp_message,
        )

        log = get_object_or_404(WhatsAppLog, pk=log_id)

        if log.status != WhatsAppLog.FAILED or log.retry_count >= 3:
            messages.warning(request, "Retry not allowed.")
            return redirect("/admin/notification/whatsapplog/")

        try:
            if log.message_type == WhatsAppLog.TEXT:
                success = send_whatsapp_message(
                    log.phone,
                    log.message_content,
                    user=log.user,
                    rent_record=log.rent_record,
                    retry_count=log.retry_count + 1,
                )
            elif log.message_type == WhatsAppLog.AUDIO:
                if not log.media_url:
                    messages.warning(request, "Missing media_url for audio log.")
                    return redirect("/admin/notification/whatsapplog/")
                success = send_whatsapp_audio(
                    log.phone,
                    log.media_url,
                    user=log.user,
                    rent_record=log.rent_record,
                    retry_count=log.retry_count + 1,
                )
            else:
                messages.warning(request, "Unsupported message type.")
                return redirect("/admin/notification/whatsapplog/")

            log.retry_count += 1
            log.last_retry_at = log.timestamp
            if success:
                log.status = WhatsAppLog.SENT
                messages.success(request, "Retry successful!")
            else:
                log.status = (
                    WhatsAppLog.PERMANENT_FAILED
                    if log.retry_count >= 3
                    else WhatsAppLog.FAILED
                )
                messages.error(request, "Retry failed.")
            log.save()
        except Exception as exc:
            log.retry_count += 1
            log.status = (
                WhatsAppLog.PERMANENT_FAILED
                if log.retry_count >= 3
                else WhatsAppLog.FAILED
            )
            log.save()
            messages.error(request, f"Retry error: {exc}")

        return redirect("/admin/notification/whatsapplog/")
