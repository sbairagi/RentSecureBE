"""Backfill the persisted ``amount_paid`` column on rent records.

Before this migration ``amount_paid`` was a property that always returned
``amount``, so a partially paid month could not be represented.  The column
now stores the money actually received, which is what the reporting and the
ledger need.

Rules:

* ``paid`` records  -> the total billed (``amount + late_fee - discount``),
  except when the payout already went out, where the transferred amount
  (``amount``) is kept so the gateway transfer stays reconcilable.
* every other record -> ``0`` (nothing was received).
"""

from decimal import Decimal

from django.db import migrations


def backfill_amount_paid(apps, schema_editor):
    RentRecord = apps.get_model("properties", "RentRecord")
    for record in RentRecord.objects.filter(status__iexact="paid").iterator():
        billed = (
            (record.amount or Decimal("0"))
            + (record.late_fee or Decimal("0"))
            - (record.discount or Decimal("0"))
        )
        if billed < 0:
            billed = record.amount or Decimal("0")
        if record.payout_status == "SUCCESS":
            billed = record.amount or Decimal("0")
        if record.amount_paid != billed:
            record.amount_paid = billed
            record.save(update_fields=["amount_paid"])


def noop_reverse(apps, schema_editor):
    """The column is reset by the schema migration when reversed."""


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0014_historicalrentrecord_amount_paid_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_amount_paid, noop_reverse),
    ]
