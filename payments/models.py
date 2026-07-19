import warnings
from typing import Any

from django.conf import settings
from django.db import models

from shared.fields import EncryptedCharField
from shared.type_compat import override


class OwnerBankDetails(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payment_bank_details",
    )
    bank_account_number = EncryptedCharField(max_length=30)
    ifsc_code = EncryptedCharField(max_length=20)
    account_holder_name = models.CharField(max_length=100, blank=True, default="")
    beneficiary_id = models.CharField(max_length=100, unique=True, blank=True)
    bank_account_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=None, blank=True, null=True)
    updated_at = models.DateTimeField(default=None, blank=True, null=True)

    class Meta:
        db_table = "payment_ownerbankdetails"
        verbose_name = "Owner Bank Details"
        verbose_name_plural = "Owner Bank Details"
        unique_together = ("owner", "bank_account_number")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if "owner" in kwargs:
            warnings.warn(
                "payments.models.OwnerBankDetails is the canonical model. "
                "core.models.OwnerBankDetails is deprecated.",
                DeprecationWarning,
                stacklevel=2,
            )
        super().__init__(*args, **kwargs)

    @override
    def __str__(self) -> str:
        return f"{self.owner.username} - {self.bank_account_number}"


class WebhookEvent(models.Model):
    class Provider(models.TextChoices):
        CASHFREE = "CASHFREE", "Cashfree"
        RAZORPAY = "RAZORPAY", "Razorpay"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSED = "PROCESSED", "Processed"
        FAILED = "FAILED", "Failed"

    event_id = models.CharField(max_length=255, unique=True)
    provider = models.CharField(max_length=20, choices=Provider.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payment_webhookevent"
        verbose_name = "Webhook Event"
        verbose_name_plural = "Webhook Events"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.provider} - {self.event_id} ({self.status})"
