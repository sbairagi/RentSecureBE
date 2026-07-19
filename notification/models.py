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


class NotificationPreference(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    rent_alerts_whatsapp = models.BooleanField(default=True)
    rent_alerts_email = models.BooleanField(default=True)
    monthly_summary_email = models.BooleanField(default=True)
    monthly_summary_whatsapp = models.BooleanField(default=False)
    payout_alerts_whatsapp = models.BooleanField(default=True)
    payout_alerts_email = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Notification Preferences for {self.owner.email or self.owner.username}"

    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"
