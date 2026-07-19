from django.db import migrations


def copy_owner_bank_details(apps, schema_editor) -> None:
    from django.db import connection

    connection_ctx = (
        schema_editor.connection if schema_editor is not None else connection
    )

    with connection_ctx.cursor() as cursor:
        cursor.execute("""
            INSERT OR IGNORE INTO payment_ownerbankdetails
                (owner_id, bank_account_number, ifsc_code,
                 account_holder_name, beneficiary_id,
                 bank_account_verified, created_at, updated_at)
            SELECT
                owner_id, bank_account_number, ifsc_code,
                account_holder_name, beneficiary_id,
                bank_account_verified, created_at, updated_at
            FROM core_ownerbankdetails
            """)


def reverse_copy(apps, schema_editor) -> None:
    PaymentOwnerBankDetails = apps.get_model("payments", "OwnerBankDetails")
    CoreOwnerBankDetails = apps.get_model("core", "OwnerBankDetails")
    core_owner_ids = list(
        CoreOwnerBankDetails.objects.values_list("owner_id", flat=True)
    )
    PaymentOwnerBankDetails.objects.filter(owner_id__in=core_owner_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0003_add_ownerbankdetails_unique_together"),
        ("core", "0004_add_ownerbankdetails_timestamps"),
    ]

    operations = [
        migrations.RunPython(copy_owner_bank_details, reverse_copy),
    ]
