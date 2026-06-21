"""
Property Tax Record model for tracking property tax payments and due dates.
"""

from typing import TYPE_CHECKING

from django.db import models

from rentsecure_be.type_compat import override

if TYPE_CHECKING:
    pass


class PropertyTaxRecord(models.Model):
    """Tracks property tax payments and due dates."""

    property = models.ForeignKey(
        "properties.Building", on_delete=models.CASCADE, related_name="tax_records"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @override
    def __str__(self) -> str:
        return f"{self.property.name} - ₹{self.amount} due {self.due_date}"
