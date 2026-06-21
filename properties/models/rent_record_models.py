import builtins
from datetime import date
from typing import Any, override

from django.core.exceptions import ValidationError
from django.db import models

from .unit_models import Unit


class RentRecord(models.Model):
    """
    Tracks individual rent payments for a unit.

    Each record links a renter to a payment event so that property
    owners can maintain a complete audit trail of rent collection.
    """

    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Cash"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        UPI = "upi", "UPI"
        CHEQUE = "cheque", "Cheque"
        CARD = "card", "Card"
        ONLINE = "online", "Online Payment"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"
        CANCELLED = "cancelled", "Cancelled"

    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name="rent_records",
        db_index=True,
        help_text="Unit this rent record belongs to",
    )
    renter = models.ForeignKey(
        "properties.Renter",
        on_delete=models.SET_NULL,
        null=True,
        related_name="rent_records",
        help_text="Renter who made the payment",
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Rent amount paid"
    )
    payment_method = models.CharField(
        max_length=50,
        choices=PaymentMethod.choices,
        help_text="Mode of payment used",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text="Payment status",
    )
    paid_on = models.DateField(
        null=True, blank=True, help_text="Date when payment was made"
    )
    due_date = models.DateField(help_text="Rent due date", db_index=True)
    late_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text="Late fee applied"
    )
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text="Any discount given"
    )
    notes = models.TextField(blank=True, null=True)
    transaction_id = models.CharField(
        max_length=100, blank=True, null=True, help_text="Payment gateway / bank ref"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("unit", "due_date")
        ordering = ["-due_date"]
        verbose_name = "Rent Record"
        verbose_name_plural = "Rent Records"

    @builtins.property
    def owner(self) -> Any:
        """Backward-compatible alias for ``self.unit.owner``."""
        return self.unit.owner

    @builtins.property
    def payment_status(self) -> str:
        """Backward-compatible alias for ``self.status``."""
        return self.status

    @builtins.property
    def rent_due_date(self) -> date:
        """Backward-compatible alias for ``self.due_date``."""
        return self.due_date

    @builtins.property
    def amount_paid(self) -> Any:
        """Backward-compatible alias for ``self.amount``."""
        return self.amount

    @builtins.property
    def payout_status(self) -> str:
        """Derived payout status used by legacy views."""
        return "PENDING"

    @override
    def clean(self) -> None:
        if self.paid_on is not None and self.due_date is not None:
            if self.paid_on < self.due_date:
                pass  # Early payment is allowed

        if self.amount < 0:
            raise ValidationError("Rent amount cannot be negative.")

    @override
    def __str__(self) -> str:
        return f"{self.unit} - {self.due_date} - {self.status}"
