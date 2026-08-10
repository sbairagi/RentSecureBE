from django.conf import settings
from django.db import models


class Notification(models.Model):
    RENT_DUE = "rent_due"
    RENT_PAYMENT_SUCCESS = "payment_success"
    RENT_PAYMENT_FAILED = "payment_failed"
    AGREEMENT_EXPIRING = "agreement_expiry"
    AGREEMENT_SIGNED = "agreement_signed"
    MAINTENANCE_CREATED = "maintenance_created"
    MAINTENANCE_UPDATED = "maintenance_update"
    VISITOR_REQUEST = "visitor_request"
    VISITOR_APPROVED = "visitor_approved"
    SUBSCRIPTION_EXPIRING = "subscription_expiry"
    SUBSCRIPTION_EXPIRED = "subscription_expired"
    DOCUMENT_SHARED = "document_shared"
    SYSTEM_ALERT = "system_announcement"
    PAYOUT_SUCCESS = "payout_success"
    PAYOUT_FAILED = "payout_failed"
    RENTER_STATUS_CHANGE = "renter_status_change"
    ITR_REMINDER = "itr_reminder"
    TAX_REMINDER = "tax_reminder"
    EXTRA_CHARGE_REMINDER = "extra_charge_reminder"

    NOTIFICATION_TYPE_CHOICES = (
        (RENT_DUE, "Rent Due"),
        (RENT_PAYMENT_SUCCESS, "Payment Success"),
        (RENT_PAYMENT_FAILED, "Payment Failed"),
        (AGREEMENT_EXPIRING, "Agreement Expiring"),
        (AGREEMENT_SIGNED, "Agreement Signed"),
        (MAINTENANCE_CREATED, "Maintenance Created"),
        (MAINTENANCE_UPDATED, "Maintenance Updated"),
        (VISITOR_REQUEST, "Visitor Request"),
        (VISITOR_APPROVED, "Visitor Approved"),
        (SUBSCRIPTION_EXPIRING, "Subscription Expiring"),
        (SUBSCRIPTION_EXPIRED, "Subscription Expired"),
        (DOCUMENT_SHARED, "Document Shared"),
        (SYSTEM_ALERT, "System Alert"),
        (PAYOUT_SUCCESS, "Payout Success"),
        (PAYOUT_FAILED, "Payout Failed"),
        (RENTER_STATUS_CHANGE, "Renter Status Change"),
        (ITR_REMINDER, "ITR Reminder"),
        (TAX_REMINDER, "Tax Reminder"),
        (EXTRA_CHARGE_REMINDER, "Extra Charge Reminder"),
    )

    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"
    PRIORITY_URGENT = "urgent"

    PRIORITY_CHOICES = (
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High"),
        (PRIORITY_URGENT, "Urgent"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50, choices=NOTIFICATION_TYPE_CHOICES, default=SYSTEM_ALERT
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    resource_type = models.CharField(max_length=50, blank=True)
    resource_id = models.CharField(max_length=50, blank=True)
    data = models.JSONField(default=dict, blank=True)
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM
    )
    channels = models.JSONField(default=list, blank=True)
    action_url = models.CharField(max_length=500, blank=True)
    action_label = models.CharField(max_length=100, blank=True)
    image_url = models.URLField(blank=True)
    archived = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_read", "created_at"]),
            models.Index(fields=["user", "notification_type"]),
            models.Index(fields=["user", "resource_type", "resource_id"]),
        ]
        ordering = ["-created_at"]


class DeviceToken(models.Model):
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"
    PLATFORM_CHOICES = (
        (IOS, "iOS"),
        (ANDROID, "Android"),
        (WEB, "Web"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="device_tokens"
    )
    token = models.CharField(max_length=255)
    device_id = models.CharField(max_length=255, blank=True)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    fcm_token = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "token")
        indexes = [models.Index(fields=["user", "active"])]

    def __str__(self) -> str:
        return f"{self.user} — {self.platform} — {self.token[:8]}..."


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
