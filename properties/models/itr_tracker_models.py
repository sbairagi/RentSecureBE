from __future__ import annotations

from django.conf import settings
from django.db import models


class ITRTracker(models.Model):
    class CAReviewStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        REVIEWED = "REVIEWED", "Reviewed"
        READY = "READY", "Ready for Filing"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="itr_tracker",
    )
    fy_start = models.DateField(
        help_text="Financial year start date, e.g., 2024-04-01",
        null=True,
        blank=True,
    )
    fy_end = models.DateField(
        help_text="Financial year end date, e.g., 2025-03-31",
        null=True,
        blank=True,
    )
    total_rent_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)
    ca_review_status = models.CharField(
        max_length=20,
        choices=CAReviewStatus.choices,
        default=CAReviewStatus.PENDING,
    )

    class Meta:
        ordering = ["-fy_start"]
        verbose_name = "ITR Tracker"
        verbose_name_plural = "ITR Trackers"
