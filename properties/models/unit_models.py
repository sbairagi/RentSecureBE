# Python Imports

# Django Imports
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast, override

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from simple_history.models import HistoricalRecords

# Local Imports
from core.models import User

if TYPE_CHECKING:
    from django.core.files.uploadedfile import UploadedFile

    from properties.models.renter_models import Renter


# Phone number validator for consistent format
phone_regex = RegexValidator(
    regex=r"^\+?1?\d{9,15}$",
    message=(
        "Phone number must be entered in the format: '+999999999'. "
        "Up to 15 digits allowed."
    ),
)


class Unit(models.Model):
    """
    Represents a single rental unit/property within a Building.

    A Unit is the core entity where tenants live and rent is collected.
    Each unit belongs to exactly one building and can have multiple
    renters over time (sequential tenancy).

    Attributes:
        owner (User): Property owner
        building (Building): Parent building
        unit (str): Unit identifier (e.g., '101', 'Flat A')
        unit_type (str): Category (flat, house, commercial, etc.)
        status (str): 'vacant' or 'occupied'
        rent_due_reminder (bool): Enable automated reminders
    """

    class UnitType(models.TextChoices):
        """Supported unit/property types."""

        LAND = "land", "Land"
        FLAT = "flat", "Flat/Apartment"
        COMMERCIAL_SHOP = "commercial_shop", "Commercial Shop"
        HOUSE = "house", "House"
        VILLA = "villa", "Villa"
        OFFICE = "office", "Office"
        PAYING_GUEST = "paying_guest", "Paying Guest / PG"

    class VacancyStatus(models.TextChoices):
        """Unit occupancy status."""

        VACANT = "vacant", "Vacant"
        OCCUPIED = "occupied", "Occupied"

    @override
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        legacy_rent_amount = None
        legacy_security_deposit = None
        if not args:
            legacy_unit_number = kwargs.pop("unit_number", None)
            legacy_rent_amount = kwargs.pop("rent_amount", None)
            legacy_security_deposit = kwargs.pop("security_deposit", None)
            kwargs.pop("floor", None)

            building = kwargs.get("building")
            if legacy_unit_number is not None and "unit" not in kwargs:
                kwargs["unit"] = legacy_unit_number
            if legacy_unit_number is not None and "status" not in kwargs:
                kwargs["status"] = "VACANT"
            if building is not None:
                kwargs.setdefault("owner", building.owner)
                kwargs.setdefault("address_line", building.address_line)
                kwargs.setdefault("city", building.city)
                kwargs.setdefault("state", building.state)
                kwargs.setdefault("country", building.country)
                kwargs.setdefault("postal_code", building.postal_code)
            kwargs.setdefault("unit_type", self.UnitType.FLAT)

        super().__init__(*args, **kwargs)
        self._legacy_rent_amount = legacy_rent_amount
        self._legacy_security_deposit = legacy_security_deposit

    # Identification
    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="units",
        db_index=True,
        help_text="Property owner",
    )
    building = models.ForeignKey(
        "properties.Building",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        related_name="units",
        help_text="Parent building (optional for standalone units)",
    )
    unit = models.CharField(
        max_length=100, help_text="Unit identifier (e.g., '101', 'Flat A', 'Shop 5')"
    )
    building_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Display name of building (cached for performance)",
    )

    # Property Details
    unit_type = models.CharField(
        max_length=50, choices=UnitType.choices, help_text="Type of property"
    )
    address_line = models.CharField(max_length=255, help_text="Street address")
    landmark = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Nearby landmark for easy identification",
    )
    city = models.CharField(max_length=100, help_text="City", db_index=True)
    state = models.CharField(max_length=100, help_text="State/Province")
    country = models.CharField(max_length=100, help_text="Country")
    postal_code = models.CharField(max_length=20, help_text="ZIP or postal code")
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        help_text="Latitude coordinate (-90 to 90)",
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        help_text="Longitude coordinate (-180 to 180)",
    )

    # Status & Configuration
    status = models.CharField(
        max_length=20,
        choices=VacancyStatus.choices,
        default=VacancyStatus.VACANT,
        help_text="Current occupancy status",
    )
    is_vacant = models.BooleanField(
        default=True, help_text="Denormalized: True if status=='vacant'"
    )
    is_verified = models.BooleanField(
        default=False, help_text="Whether property details have been verified"
    )
    is_archived = models.BooleanField(
        default=False, help_text="Soft-delete: archived units are hidden from listings"
    )

    last_vacated_at = models.DateField(
        null=True,
        blank=True,
        help_text="Date when the unit became vacant because no active renter remained",
    )

    # Notification Settings
    rent_due_reminder = models.BooleanField(
        default=True, help_text="Enable automated rent due reminders"
    )
    agreement_expiry_reminder = models.BooleanField(
        default=True, help_text="Enable automated agreement expiry reminders"
    )

    # Additional Information
    maintenance_notes = models.TextField(
        blank=True, null=True, help_text="Internal notes about maintenance or issues"
    )
    notes = models.TextField(
        blank=True, null=True, help_text="Additional notes about the unit"
    )

    # Tracking
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    class Meta:
        unique_together = ("owner", "unit", "building", "address_line")
        indexes = [
            models.Index(fields=["city", "owner"]),
            models.Index(fields=["owner", "is_archived"]),
        ]
        verbose_name = "Unit"
        verbose_name_plural = "Units"
        ordering = ["-created_at"]

    @override
    def clean(self) -> None:
        """Validate geographic coordinates if provided."""
        if self.latitude and not -90 <= self.latitude <= 90:
            raise ValidationError("Latitude must be between -90 and 90.")
        if self.longitude and not -180 <= self.longitude <= 180:
            raise ValidationError("Longitude must be between -180 and 180.")

    @override
    def __str__(self) -> str:
        """Return unit identifier with location."""
        return f"{self.unit} - {self.city}, {self.state}"

    @property
    def name(self) -> str:
        """Return unit display name."""
        return self.building_name or self.unit

    @property
    def unit_number(self) -> str:
        """Backward-compatible alias used by older tests and integrations."""
        return self.unit

    @unit_number.setter
    def unit_number(self, value: str) -> None:
        self.unit = value

    @property
    def title(self) -> str:
        return self.name

    @property
    def rent_amount(self) -> Decimal:
        return (
            self._legacy_rent_amount
            if self._legacy_rent_amount is not None
            else Decimal("0")
        )

    @rent_amount.setter
    def rent_amount(self, value: Decimal) -> None:
        self._legacy_rent_amount = value

    @property
    def security_deposit(self) -> Decimal:
        return (
            self._legacy_security_deposit
            if self._legacy_security_deposit is not None
            else Decimal("0")
        )

    @security_deposit.setter
    def security_deposit(self, value: Decimal) -> None:
        self._legacy_security_deposit = value

    @property
    def current_renter(self) -> "Renter | None":
        """Get the currently active renter (if any)."""
        return self.renters.filter(status="active").first()

    @property
    def total_renters(self) -> int:
        """Return count of all renters who have rented this unit."""
        return self.renters.count()


class UnitVacancy(models.Model):
    """
    Tracks why a unit became vacant and when.

    Helps property managers understand vacancy patterns
    and make better decisions about unit maintenance and rental.
    """

    class Reason(models.TextChoices):
        """Reasons for unit vacancy."""

        RENOVATION = "renovation", "Under Renovation"
        CLEANING = "cleaning", "Cleaning/Maintenance"
        BETWEEN_RENTERS = "between_renters", "Between Renters"
        LONG_TERM_VACANCY = "long_term_vacancy", "Long-Term Vacancy"
        OTHER = "other", "Other Reason"

    unit = models.OneToOneField(
        "properties.Unit", on_delete=models.CASCADE, help_text="Unit that became vacant"
    )
    reason = models.CharField(
        max_length=100, choices=Reason.choices, help_text="Reason for vacancy"
    )
    noted_on = models.DateField(
        auto_now_add=True, help_text="Date vacancy was recorded"
    )

    class Meta:
        verbose_name = "Unit Vacancy"
        verbose_name_plural = "Unit Vacancies"
        ordering = ["-noted_on"]

    @override
    def __str__(self) -> str:
        return f"{self.unit} - {self.get_reason_display()}"


class UnitDocument(models.Model):
    """
    Stores documents related to a unit or renter.

    Examples: property papers, inspection reports, repair invoices, etc.
    """

    unit = models.ForeignKey(
        "properties.Unit",
        on_delete=models.CASCADE,
        db_index=True,
        related_name="documents",
        help_text="Unit this document belongs to",
    )
    renter = models.ForeignKey(
        "properties.Renter",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        related_name="documents",
        help_text="Associated renter (optional)",
    )
    document = models.FileField(
        upload_to="unit_documents/", help_text="Uploaded document file"
    )
    file_hash = models.CharField(
        max_length=64,
        editable=False,
        db_index=True,
        help_text="SHA256 hash for deduplication",
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True, help_text="When document was uploaded"
    )

    class Meta:
        verbose_name = "Unit Document"
        verbose_name_plural = "Unit Documents"
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["unit", "uploaded_at"]),
        ]

    @override
    def clean(self) -> None:
        """Validate and hash document to prevent duplicates."""
        if self.document:
            from properties.utils import generate_file_hash

            hash_value = generate_file_hash(
                cast("UploadedFile", self.document)  # type: ignore[arg-type]
            )
            self.file_hash = hash_value

            existing = UnitDocument.objects.filter(
                file_hash=hash_value, unit=self.unit
            ).exclude(pk=self.pk)

            if existing.exists():
                raise ValidationError("This document already exists for this unit.")

    @override
    def __str__(self) -> str:
        return f"{self.unit} - {self.document.name}"


class UnitImage(models.Model):
    """
    Stores images of a unit for listing and documentation.

    Multiple images can be uploaded per unit to show different
    angles, rooms, amenities, etc.
    """

    unit = models.ForeignKey(
        "properties.Unit",
        on_delete=models.CASCADE,
        db_index=True,
        related_name="images",
        help_text="Unit these images belong to",
    )
    renter = models.ForeignKey(
        "properties.Renter",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        related_name="images",
        help_text="Associated renter (optional - for condition check-in/out photos)",
    )
    image = models.ImageField(upload_to="unit_images/", help_text="Unit image/photo")
    image_hash = models.CharField(
        max_length=64,
        editable=False,
        db_index=True,
        help_text="SHA256 hash for deduplication",
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True, help_text="When image was uploaded"
    )

    class Meta:
        verbose_name = "Unit Image"
        verbose_name_plural = "Unit Images"
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["unit", "uploaded_at"]),
        ]

    @override
    def clean(self) -> None:
        """Validate and hash image to prevent duplicate uploads."""
        if self.image:
            from properties.utils import generate_file_hash

            hash_value = generate_file_hash(
                cast("UploadedFile", self.image)  # type: ignore[arg-type]
            )
            self.image_hash = hash_value

            existing = UnitImage.objects.filter(
                image_hash=hash_value, unit=self.unit
            ).exclude(pk=self.pk)

            if existing.exists():
                raise ValidationError("This image already exists for this unit.")

    @override
    def __str__(self) -> str:
        return f"{self.unit} - Image"
