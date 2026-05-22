from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from .renter_models import Renter
from .unit_models import Unit


class ExtraCharge(models.Model):
    class Status(models.TextChoices):
        DUE = 'DUE', 'Due'
        PAID = 'PAID', 'Paid'
        MISSED = 'MISSED', 'Missed'

    renter = models.ForeignKey(
        Renter,
        on_delete=models.CASCADE,
        related_name='extra_charges',
        db_index=True,
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name='extra_charges',
        db_index=True,
    )
    name = models.CharField(max_length=50, help_text='Charge name, e.g. Electricity or Maintenance')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DUE,
        help_text='Current payment status for this extra charge',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    class Meta:
        ordering = ['due_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"{self.name} for {self.renter.name} due {self.due_date}"

    @property
    def is_paid(self):
        return self.status == self.Status.PAID
