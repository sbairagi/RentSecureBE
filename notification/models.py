from django.conf import settings
from django.db import models


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class DeviceToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    platform = models.CharField(max_length=20, default="expo")  # or 'fcm'


class WhatsAppLog(models.Model):
    TEXT = "text"
    AUDIO = "audio"
    MESSAGE_TYPES = (
        (TEXT, "Text"),
        (AUDIO, "Audio"),
    )
    SENT = "SENT"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    PERMANENT_FAILED = "PERMANENT_FAILED"
    STATUS_CHOICES = (
        (SENT, "Sent"),
        (FAILED, "Failed"),
        (RETRYING, "Retrying"),
        (PERMANENT_FAILED, "Permanent Failed"),
    )

    rent_record = models.ForeignKey(
        "properties.RentRecord",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="whatsapp_logs",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="whatsapp_logs",
        null=True,
        blank=True,
    )
    phone = models.CharField(max_length=20)
    message_type = models.CharField(choices=MESSAGE_TYPES, max_length=10)
    message_content = models.TextField()
    media_url = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=SENT)
    retry_count = models.IntegerField(default=0)
    last_retry_at = models.DateTimeField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"{self.message_type} to {self.phone} at {self.timestamp}"
