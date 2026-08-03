from django.conf import settings
from django.db import models

from rentsecure_be.type_compat import override


class CAPartner(models.Model):
    """Verified Chartered Accountant available for user matchmaking."""

    SPECIALIZATION_CHOICES = [
        ("ITR_FILING", "ITR Filing"),
        ("NRI_TAX", "NRI Tax Help"),
        ("INVESTMENT_TAX", "Investment Advice"),
    ]

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    firm_name = models.CharField(max_length=255)
    city = models.CharField(max_length=100, db_index=True)
    experience_years = models.PositiveIntegerField()
    specialization = models.CharField(
        max_length=255,
        choices=SPECIALIZATION_CHOICES,
        db_index=True,
    )
    available = models.BooleanField(default=True, db_index=True)
    rating = models.FloatField(default=0.0)
    price_range = models.CharField(max_length=50)

    class Meta:
        ordering = ["-rating", "name"]

    @override
    def __str__(self) -> str:
        return f"{self.name} ({self.get_specialization_display()})"


class CAConnectionRequest(models.Model):
    """Stores a user's request to be connected with a matched CA."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ca_connection_requests",
    )
    ca = models.ForeignKey(CAPartner, on_delete=models.SET_NULL, null=True)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @override
    def __str__(self) -> str:
        return f"Connection request from {self.user} to {self.ca}"


class CAProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    firm_name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    phone = models.CharField(max_length=15)
    verified = models.BooleanField(default=False)

    @override
    def __str__(self) -> str:
        return f"{self.firm_name} ({'Verified' if self.verified else 'Unverified'})"


class TaxSubmissionToCA(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tax_submissions_to_ca",
    )
    ca = models.ForeignKey(CAProfile, on_delete=models.SET_NULL, null=True, blank=True)
    financial_year = models.CharField(max_length=9, help_text="e.g., 2024-25")
    sent_to_email = models.EmailField()
    sent_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField(blank=True)

    @override
    def __str__(self) -> str:
        return f"Sent to {self.sent_to_email} on {self.sent_at.strftime('%Y-%m-%d')}"
