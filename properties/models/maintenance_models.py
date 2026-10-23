from django.conf import settings
from django.db import models


class MaintenanceRequest(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In progress"
        WAITING = "waiting", "Waiting"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    class Category(models.TextChoices):
        PLUMBING = "plumbing", "Plumbing"
        ELECTRICAL = "electrical", "Electrical"
        HVAC = "hvac", "Heating / cooling"
        APPLIANCE = "appliance", "Appliance"
        STRUCTURAL = "structural", "Structural"
        PEST_CONTROL = "pest_control", "Pest control"
        CLEANING = "cleaning", "Cleaning"
        SAFETY = "safety", "Safety"
        OTHER = "other", "Other"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="maintenance_requests",
        db_index=True,
    )
    unit = models.ForeignKey(
        "properties.Unit",
        on_delete=models.CASCADE,
        related_name="maintenance_requests",
        db_index=True,
    )
    renter = models.ForeignKey(
        "properties.Renter",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="maintenance_requests",
        db_index=True,
    )
    assigned_caretaker = models.ForeignKey(
        "properties.CareTaker",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="maintenance_requests",
        db_index=True,
    )
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=24, choices=Category.choices, default=Category.OTHER
    )
    priority = models.CharField(
        max_length=12, choices=Priority.choices, default=Priority.MEDIUM, db_index=True
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.OPEN, db_index=True
    )
    reported_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-reported_at"]
        indexes = [
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["owner", "reported_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_status_display()})"
