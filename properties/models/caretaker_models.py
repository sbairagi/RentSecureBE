"""
Caretaker Management Models

Handles caretaker/facility manager information for properties.
Caretakers are responsible for day-to-day maintenance and management.
"""

# Django Imports
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from simple_history.models import HistoricalRecords

# Local Imports
from .unit_models import Unit


# Phone number validator for consistent format
phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)


class Caretaker(models.Model):
    """
    Represents a caretaker/facility manager assigned to a unit.

    Caretakers handle day-to-day operations, maintenance coordination,
    and communication between owners and renters.

    Attributes:
        unit (Unit): Unit managed by this caretaker
        name (str): Full name
        phone (str): Primary contact number
        whatsapp_number (str): WhatsApp contact (for quick messaging)
        emergency_contact_*: Emergency contact information
        id_proof: Government ID document
        start_date: When caretaker started
    """

    id = models.AutoField(primary_key=True)
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name='caretakers',
        db_index=True,
        help_text="Unit managed by this caretaker"
    )

    # Personal Information
    name = models.CharField(
        max_length=100,
        help_text="Caretaker's full name"
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=15,
        db_index=True,
        help_text="Primary phone number (+country_code format)"
    )
    alternate_phone = models.CharField(
        validators=[phone_regex],
        max_length=15,
        blank=True,
        null=True,
        help_text="Alternate phone number (optional)"
    )
    whatsapp_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text="WhatsApp number for quick communication"
    )
    caretaker_image = models.ImageField(
        upload_to='caretaker_image/',
        blank=True,
        null=True,
        help_text="Photo of caretaker for identification"
    )

    # Emergency Contact
    emergency_contact_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Name of emergency contact person"
    )
    emergency_contact_number = models.CharField(
        validators=[phone_regex],
        max_length=15,
        blank=True,
        null=True,
        help_text="Emergency contact phone number"
    )

    # Documents
    id_proof = models.FileField(
        upload_to='id_proof/caretaker/',
        help_text="Government ID proof (Aadhaar, PAN, etc.)"
    )

    # Address Information
    address_line = models.CharField(
        max_length=255,
        help_text="Residential address"
    )
    landmark = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Nearby landmark"
    )
    city = models.CharField(
        max_length=100,
        help_text="City",
        db_index=True
    )
    state = models.CharField(
        max_length=100,
        help_text="State/Province"
    )
    country = models.CharField(
        max_length=100,
        help_text="Country"
    )
    postal_code = models.CharField(
        max_length=20,
        help_text="ZIP or postal code"
    )

    # Employment Details
    start_date = models.DateField(
        blank=True,
        null=True,
        db_index=True,
        help_text="When caretaker started"
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        help_text="When caretaker ended (null if active)"
    )

    # Additional Information
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about caretaker"
    )

    # Tracking
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    class Meta:
        unique_together = ('unit', 'phone')
        verbose_name = "Caretaker"
        verbose_name_plural = "Caretakers"
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['unit', 'start_date']),
        ]

    def clean(self):
        """Validate date range: end_date cannot be before start_date."""
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")

    def __str__(self):
        """Return caretaker name with unit."""
        return f"{self.name} - {self.unit}"

    @property
    def is_active(self):
        """Check if caretaker is currently active."""
        return self.end_date is None or self.end_date >= __import__('datetime').date.today()
