from __future__ import annotations

from django.conf import settings
from django.db import models


class ITRCAContactRequest(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_index=True,
        help_text="Owner who submitted the request",
    )
    phone = models.CharField(max_length=15, help_text="Contact phone number")
    email = models.EmailField(help_text="Contact email address")
    pan_number = models.CharField(max_length=10, help_text="PAN number")
    message = models.TextField(
        blank=True, null=True, help_text="Optional message from the owner"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "ITR CA Contact Request"
        verbose_name_plural = "ITR CA Contact Requests"
