"""
Property Tax Record model for tracking property tax payments and due dates.
"""

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from properties.models.building_models import Building


class PropertyTaxRecord(models.Model):
    """Tracks property tax payments and due dates."""

    property: "Building" = models.ForeignKey(
        "properties.Building", on_delete=models.CASCADE, related_name="tax_records"
    )
    amount: float = models.DecimalField(max_digits=12, decimal_places=2)
    due_date: "models.DateField" = models.DateField()
    paid: bool = models.BooleanField(default=False)
    paid_date: "models.DateField | None" = models.DateField(null=True, blank=True)
    created_at: "models.DateTimeField" = models.DateTimeField(auto_now_add=True)
    updated_at: "models.DateTimeField" = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.property.name} - ₹{self.amount} due {self.due_date}"
