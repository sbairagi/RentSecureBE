"""
Property Tax Record model for tracking property tax payments and due dates.
"""

from django.db import models

from rentsecure_be.type_compat import override


class PropertyTaxRecord(models.Model):
    """Tracks property tax payments and due dates."""

    property = models.ForeignKey(
        "properties.Building",
        on_delete=models.CASCADE,
        related_name="tax_records",
        db_index=True,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField(db_index=True)
    paid = models.BooleanField(default=False, db_index=True)
    paid_date = models.DateField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["property", "paid", "due_date"]),
        ]

    @override
    def __str__(self) -> str:
        return f"{self.property.name} - ₹{self.amount} due {self.due_date}"
