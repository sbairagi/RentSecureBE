from django.conf import settings
from django.db import models

from rentsecure_be.type_compat import override


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
