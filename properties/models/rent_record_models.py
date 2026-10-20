from decimal import Decimal
from typing import Any

from simple_history.models import HistoricalRecords  # type: ignore[import-untyped]

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from rentsecure_be.type_compat import override

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
        db_index=True,
        help_text="Renter who made the payment",
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Rent amount billed"
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Amount received so far (parts included)",
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
        db_index=True,
    )
    paid_on = models.DateField(
        null=True, blank=True, help_text="Date when payment was made", db_index=True
    )
    due_date = models.DateField(help_text="Rent due date", db_index=True)
    late_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text="Late fee applied"
    )
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text="Any discount given"
    )
    notes = models.TextField(blank=True)
    transaction_id = models.CharField(
        max_length=100, blank=True, help_text="Payment gateway / bank ref"
    )
    payout_status = models.CharField(
        max_length=20,
        default="PENDING",
        help_text="Payout transfer status",
        db_index=True,
    )
    payout_reference = models.CharField(
        max_length=100, blank=True, help_text="Payout gateway reference"
    )
    payment_link = models.CharField(
        max_length=500, blank=True, help_text="Payment gateway link"
    )
    invoice_pdf = models.FileField(
        upload_to="invoices/",
        blank=True,
        null=True,
        help_text="Generated rent receipt PDF",
    )
    razorpay_order_id = models.CharField(
        max_length=100, blank=True, help_text="Razorpay order reference"
    )
    payout_retries = models.PositiveIntegerField(
        default=0, help_text="Number of payout retry attempts"
    )
    last_payout_retry = models.DateTimeField(
        blank=True, null=True, help_text="Timestamp of last payout retry"
    )
    payout_retry_count = models.PositiveIntegerField(
        default=0, help_text="Cumulative payout retry count"
    )
    adjustment_reason = models.TextField(
        blank=True, help_text="Reason for late fee or adjustment"
    )
    cancel_reason = models.TextField(
        blank=True, help_text="Why the record was cancelled"
    )
    cancelled_at = models.DateTimeField(
        null=True, blank=True, help_text="When the record was cancelled"
    )
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cancelled_rent_records",
        help_text="Who cancelled the record",
    )
    receipt_sent_at = models.DateTimeField(
        null=True, blank=True, help_text="When the receipt was last sent"
    )
    last_reminded_at = models.DateTimeField(
        null=True, blank=True, help_text="When a reminder was last sent"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("unit", "due_date")
        ordering = ["-due_date"]
        verbose_name = "Rent Record"
        verbose_name_plural = "Rent Records"
        indexes = [
            models.Index(fields=["unit", "status", "due_date"]),
            models.Index(fields=["unit", "payout_status"]),
        ]

    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    @property
    def payment_status(self) -> str:
        return self.status

    @payment_status.setter
    def payment_status(self, value: str) -> None:
        self.status = value

    @property
    def date_paid(self) -> Any:
        return self.paid_on

    @date_paid.setter
    def date_paid(self, value: Any) -> None:
        self.paid_on = value

    @property
    def rent_due_date(self) -> Any:
        return self.due_date

    @rent_due_date.setter
    def rent_due_date(self, value: Any) -> None:
        self.due_date = value

    @property
    def total_due(self) -> Decimal:
        """Total billed for the month: rent + late fee - discount.

        The bill never turns negative — a month that owes the renter money is
        not a thing the ledger can show.
        """
        total = (
            (self.amount or Decimal("0"))
            + (self.late_fee or Decimal("0"))
            - (self.discount or Decimal("0"))
        )
        return max(Decimal("0"), total)

    @property
    def balance(self) -> Decimal:
        """What is still owed on this record."""
        return max(Decimal("0"), self.total_due - (self.amount_paid or Decimal("0")))

    @property
    def is_partially_paid(self) -> bool:
        """True when money came in but the month is not settled yet."""
        return (
            self.amount_paid or Decimal("0")
        ) > 0 and self.status != self.Status.PAID

    @property
    def allow_partial_payments(self) -> bool:
        """Whether the unit of this record allows part payments."""
        return bool(getattr(self.unit, "allow_partial_payments", False))

    @override
    def clean(self) -> None:
        if self.paid_on is not None and self.due_date is not None:
            if self.paid_on < self.due_date:
                pass  # Early payment is allowed

        if self.amount < 0:
            raise ValidationError("Rent amount cannot be negative.")

        if self.amount_paid < 0:
            raise ValidationError("Amount paid cannot be negative.")

    @override
    def __str__(self) -> str:
        return f"{self.unit} - {self.due_date} - {self.status}"


class RentRecordPart(models.Model):
    """One part payment received against a monthly rent record.

    A rent record stays a single row per unit per month; every instalment
    is a child row so the ledger can show the progress, the receipt can
    name the part it belongs to, and the audit trail keeps each amount,
    date, mode and reference.
    """

    rent_record = models.ForeignKey(
        RentRecord,
        on_delete=models.CASCADE,
        related_name="parts",
        help_text="Monthly record this part belongs to",
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Amount received in this part"
    )
    paid_on = models.DateField(help_text="Date the part was received", db_index=True)
    payment_method = models.CharField(
        max_length=50,
        choices=RentRecord.PaymentMethod.choices,
        default=RentRecord.PaymentMethod.CASH,
        help_text="Mode of payment used for this part",
    )
    transaction_id = models.CharField(
        max_length=100, blank=True, help_text="Payment gateway / bank ref"
    )
    note = models.TextField(blank=True, help_text="Note for this part")
    receipt_no = models.CharField(
        max_length=120, blank=True, help_text="Receipt file name for this part"
    )
    receipt_pdf = models.FileField(
        upload_to="invoices/parts/",
        blank=True,
        null=True,
        help_text="Generated part receipt PDF",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="rent_record_parts",
        help_text="Who recorded this part",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["paid_on", "id"]
        verbose_name = "Rent Record Part"
        verbose_name_plural = "Rent Record Parts"

    @override
    def __str__(self) -> str:
        return f"{self.rent_record} - {self.paid_on} - {self.amount}"


class RentRecordAction(models.Model):
    """One action a user took on a rent record.

    The audit trail of ``django-simple-history`` records what the **data**
    looks like after a change.  This records what the **user did** — the
    reminder that was sent, the receipt that was delivered, the month that
    was cancelled and why.  An action is kept even when it changed nothing
    (a receipt that could not be delivered is still something the owner
    did), and it is kept even when it failed.

    Both trails are shown together in the history of a record, newest
    first.
    """

    class Kind(models.TextChoices):
        CREATED = "created", "Created"
        EDITED = "edited", "Edited"
        CANCELLED = "cancelled", "Cancelled"
        RECEIPT_SENT = "receipt_sent", "Receipt sent"
        REMINDER_SENT = "reminder_sent", "Reminder sent"

    class Outcome(models.TextChoices):
        RECORDED = "recorded", "Recorded"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    rent_record = models.ForeignKey(
        RentRecord,
        on_delete=models.CASCADE,
        related_name="actions",
        help_text="The record this action was taken on",
    )
    kind = models.CharField(
        max_length=32,
        choices=Kind.choices,
        help_text="What the user did",
    )
    summary = models.CharField(
        max_length=200,
        blank=True,
        help_text="One line that says what happened",
    )
    detail = models.TextField(
        blank=True,
        help_text="The numbers and the words behind the action",
    )
    outcome = models.CharField(
        max_length=16,
        choices=Outcome.choices,
        default=Outcome.RECORDED,
        help_text="How the action ended",
    )
    history_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="The audit entry this action explains — it is not listed twice",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="rent_record_actions",
        help_text="Who took the action",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Rent Record Action"
        verbose_name_plural = "Rent Record Actions"
        indexes = [models.Index(fields=["rent_record", "created_at"])]

    @override
    def __str__(self) -> str:
        return (
            f"{self.rent_record} - {self.get_kind_display()} "
            f"- {self.created_at:%Y-%m-%d %H:%M}"
        )
