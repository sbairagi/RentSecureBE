# Django Imports
from django.db import models

# Local Imports
from core.models import User


class Building(models.Model):
    """
    Represents a physical building/property managed by a user.

    A Building is the top-level entity in the property management hierarchy.
    It can contain multiple Units. All rental and financial operations trace
    back to the Building through its Units.

    Attributes:
        name (str): Building identifier or display name
        address_line (str): Street address
        city (str): City name
        state (str): State/Province name
        country (str): Country name
        postal_code (str): ZIP/Postal code
        owner (User): Property owner who manages this building
        is_archived (bool): Soft-delete flag
        created_at (datetime): Auto-set creation timestamp
    """

    # Building Information
    name = models.CharField(
        max_length=255,
        help_text="Building name or identifier (e.g., 'Sunshine Complex', 'Tower A')",
    )
    address_line = models.CharField(
        max_length=255, help_text="Street address of the building"
    )
    city = models.CharField(
        max_length=100, help_text="City where building is located", db_index=True
    )
    state = models.CharField(max_length=100, help_text="State or province")
    country = models.CharField(max_length=100, help_text="Country name")
    postal_code = models.CharField(max_length=10, help_text="ZIP or postal code")

    # Owner & Status
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="buildings",
        help_text="Owner of this building",
        db_index=True,
    )
    is_archived = models.BooleanField(
        default=False,
        help_text="Soft-delete: archived buildings are excluded from queries",
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this building was added to the system",
    )

    class Meta:
        unique_together = ("name", "address_line", "city", "owner")
        indexes = [
            models.Index(fields=["owner", "is_archived"]),
            models.Index(fields=["city", "owner"]),
        ]
        verbose_name = "Building"
        verbose_name_plural = "Buildings"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return building identifier with city."""
        return f"{self.name} ({self.city}, {self.state})"

    @property
    def units_count(self) -> int:
        """Return total count of units in this building."""
        return self.units.count()

    @property
    def occupied_units_count(self) -> int:
        """Return count of currently occupied units."""
        return self.units.filter(is_vacant=False).count()
