from django.db import migrations


def copy_owner_bank_details(apps, schema_editor) -> None:
    OwnerBankDetails = apps.get_model("core", "OwnerBankDetails")
    PaymentOwnerBankDetails = apps.get_model("payments", "OwnerBankDetails")
    for record in OwnerBankDetails.objects.all():
        PaymentOwnerBankDetails.objects.get_or_create(
            owner_id=record.owner_id,
            defaults={
                "bank_account_number": record.bank_account_number,
                "ifsc_code": record.ifsc_code,
                "account_holder_name": record.account_holder_name,
                "beneficiary_id": record.beneficiary_id,
                "bank_account_verified": record.bank_account_verified,
            },
        )


def reverse_copy(apps, schema_editor) -> None:
    PaymentOwnerBankDetails = apps.get_model("payments", "OwnerBankDetails")
    PaymentOwnerBankDetails.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0001_initial"),
        ("core", "0002_alter_ownerbankdetails_beneficiary_id"),
    ]

    operations = [
        migrations.RunPython(copy_owner_bank_details, reverse_copy),
    ]
