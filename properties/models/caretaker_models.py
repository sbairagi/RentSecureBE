from simple_history.models import HistoricalRecords  # type: ignore[import-untyped]

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from rentsecure_be.type_compat import override

# Reuse the shared phone regex if available; otherwise define a local one.
phone_regex = RegexValidator(
    regex=r"^\+?1?\d{9,15}$",
    message=(
        "Phone number must be entered in the format: '+999999999'. "
        "Up to 15 digits allowed."
    ),
)


class CareTaker(models.Model):
    """
    Caretaker/manager assigned to a unit/property.
    """

    unit = models.ForeignKey(
        "properties.Unit",
        on_delete=models.CASCADE,
        related_name="caretakers",
        db_index=True,
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="caretaker_profile",
    )
    name = models.CharField(max_length=100, help_text="Caretaker full name")
    email = models.EmailField(default="", blank=True)
    phone = models.CharField(
        validators=[phone_regex], max_length=15, help_text="Primary phone"
    )
    alternate_phone = models.CharField(
        validators=[phone_regex], max_length=15, blank=True, help_text="Alternate phone"
    )
    address = models.TextField(blank=True)
    joining_date = models.DateField(help_text="Date of joining", db_index=True)
    leaving_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, help_text="Currently active?")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    class Meta:
        unique_together = ("unit", "phone")
        ordering = ["-joining_date"]
        verbose_name = "Caretaker"
        verbose_name_plural = "Caretakers"

    @override
    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        if self.leaving_date and self.leaving_date < self.joining_date:
            raise ValidationError("Leaving date cannot be earlier than joining date.")

    @override
    def __str__(self) -> str:
        return f"{self.name} ({self.unit})"


class CareTakerAssignmentLog(models.Model):
    caretaker = models.ForeignKey(CareTaker, on_delete=models.CASCADE, db_index=True)
    action = models.CharField(max_length=20, help_text="assigned / unassigned")
    action_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-action_date"]
