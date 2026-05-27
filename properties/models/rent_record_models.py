from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from simple_history.models import HistoricalRecords

from core.models import User

from .renter_models import Renter
from .unit_models import Unit


class RentRecord(models.Model):
    class PaymentMode(models.TextChoices):
        CASH = 'cash', 'Cash'
        CHEQUE = 'cheque', 'Cheque'
        ONLINE = 'online', 'Online Transfer'
        OTHER = 'other', 'Other'

    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        FAILED = 'FAILED', 'Failed'

    def __init__(self, *args, **kwargs):
        if not args:
            amount = kwargs.pop('amount', None)
            due_date = kwargs.pop('due_date', None)
            month = kwargs.pop('month', None)
            year = kwargs.pop('year', None)

            renter = kwargs.get('renter')
            if renter is not None:
                kwargs.setdefault('unit', renter.unit)
                kwargs.setdefault('owner', renter.unit.owner)
            if amount is not None and 'amount_paid' not in kwargs:
                kwargs['amount_paid'] = amount
            if due_date is not None:
                kwargs.setdefault('rent_due_date', due_date)
                kwargs.setdefault('date_paid', due_date)
            if month is not None and year is not None and 'rent_month' not in kwargs:
                kwargs['rent_month'] = date(int(year), int(month), 1)
            if 'rent_month' in kwargs:
                kwargs.setdefault('date_paid', kwargs['rent_month'])

        super().__init__(*args, **kwargs)

    id = models.AutoField(primary_key=True)
    renter = models.ForeignKey(Renter, on_delete=models.CASCADE, related_name='rent_records', db_index=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='rent_records_unit')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rent_records_owner', db_index=True)
    rent_month = models.DateField(help_text="Use first day of the month, e.g. 2025-05-01", db_index=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount paid for rent")
    date_paid = models.DateField(help_text="Date when payment was made")
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, help_text="Payment status")
    payment_mode = models.CharField(max_length=20, choices=PaymentMode.choices, blank=True, null=True, help_text="Mode of payment")
    remarks = models.TextField(blank=True, null=True, help_text="Additional remarks or notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    payout_status = models.CharField(max_length=20, default="PENDING")
    payout_reference = models.CharField(max_length=100, null=True, blank=True)
    payout_retry_count = models.IntegerField(default=0)
    last_retry_on = models.DateTimeField(null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_status = models.CharField(max_length=20, default="PENDING")
    payout_retries = models.IntegerField(default=0)
    last_payout_retry = models.DateTimeField(null=True, blank=True)
    grace_days = models.PositiveIntegerField(default=3)
    late_fee = models.DecimalField(max_digits=8, decimal_places=2, default=100.00)
    adjustment_reason = models.TextField(blank=True, null=True)
    rent_due_date = models.DateField(default=date.today)
    payment_link = models.URLField(null=True, blank=True)
    rent_due_day = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)
    invoice_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    invoice_pdf = models.FileField(upload_to="rent_invoices/", null=True, blank=True)

    class Meta:
        unique_together = ('renter', 'rent_month')
        ordering = ['-rent_month']

    def clean(self):
        if self.amount_paid < 0:
            raise ValidationError("Amount paid cannot be negative.")

        if self.date_paid < self.rent_month:
            raise ValidationError("Date paid cannot be before rent month.")

        if self.renter.unit != self.unit:
            raise ValidationError("Renter does not belong to the selected unit.")

    @property
    def amount(self):
        return self.amount_paid

    @property
    def payment_date(self):
        return self.date_paid

    @property
    def due_date(self):
        return self.rent_due_date

    @property
    def month(self):
        return self.rent_month.month

    @property
    def year(self):
        return self.rent_month.year

    def __str__(self):
        return (
            f"{self.renter.name} - {self.rent_month.strftime('%B %Y')} "
            f"- {self.amount_paid}"
        )
