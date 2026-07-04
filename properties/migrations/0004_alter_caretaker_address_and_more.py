import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0003_rentagreementdraft_history"),
    ]

    operations = [
        migrations.AlterField(
            model_name="caretaker",
            name="address",
            field=models.TextField(blank=True, default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="caretaker",
            name="alternate_phone",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Alternate phone",
                max_length=15,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
                        regex="^\\+?1?\\d{9,15}$",
                    )
                ],
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="caretaker",
            name="notes",
            field=models.TextField(blank=True, default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="caretakerassignmentlog",
            name="notes",
            field=models.TextField(blank=True, default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalcaretaker",
            name="address",
            field=models.TextField(blank=True, default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalcaretaker",
            name="alternate_phone",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Alternate phone",
                max_length=15,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
                        regex="^\\+?1?\\d{9,15}$",
                    )
                ],
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalcaretaker",
            name="notes",
            field=models.TextField(blank=True, default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalrentagreementdraft",
            name="leegality_document_id",
            field=models.CharField(blank=True, default=None, max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalrenter",
            name="alternate_phone",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Alternate phone number",
                max_length=15,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
                        regex="^\\+?1?\\d{9,15}$",
                    )
                ],
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalrenter",
            name="emergency_contact_name",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Emergency contact name",
                max_length=100,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalrenter",
            name="emergency_contact_number",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Emergency contact number",
                max_length=15,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
                        regex="^\\+?1?\\d{9,15}$",
                    )
                ],
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalrenter",
            name="final_invoice_path",
            field=models.CharField(blank=True, default=None, max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalrenter",
            name="flagged_reason",
            field=models.TextField(blank=True, default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalrenter",
            name="notes",
            field=models.TextField(
                blank=True, default=None, help_text="Additional notes"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalrenter",
            name="onboarding_token",
            field=models.CharField(
                blank=True,
                db_index=True,
                default=None,
                help_text="Secure token for onboarding link",
                max_length=255,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalrenter",
            name="revocation_reason",
            field=models.TextField(blank=True, default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalrenter",
            name="whatsapp_number",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="For WhatsApp messages",
                max_length=15,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalrentrecord",
            name="adjustment_reason",
            field=models.TextField(
                blank=True, default=None, help_text="Reason for late fee or adjustment"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalrentrecord",
            name="notes",
            field=models.TextField(blank=True, default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalrentrecord",
            name="payment_link",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Payment gateway link",
                max_length=500,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalrentrecord",
            name="payout_reference",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Payout gateway reference",
                max_length=100,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalrentrecord",
            name="razorpay_order_id",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Razorpay order reference",
                max_length=100,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalrentrecord",
            name="transaction_id",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Payment gateway / bank ref",
                max_length=100,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalunit",
            name="building_name",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Display name of building (cached for performance)",
                max_length=100,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalunit",
            name="landmark",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Nearby landmark for easy identification",
                max_length=255,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalunit",
            name="maintenance_notes",
            field=models.TextField(
                blank=True,
                default=None,
                help_text="Internal notes about maintenance or issues",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalunit",
            name="notes",
            field=models.TextField(
                blank=True, default=None, help_text="Additional notes about the unit"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="rentagreementdraft",
            name="leegality_document_id",
            field=models.CharField(blank=True, default=None, max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="renter",
            name="alternate_phone",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Alternate phone number",
                max_length=15,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
                        regex="^\\+?1?\\d{9,15}$",
                    )
                ],
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="renter",
            name="emergency_contact_name",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Emergency contact name",
                max_length=100,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="renter",
            name="emergency_contact_number",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Emergency contact number",
                max_length=15,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
                        regex="^\\+?1?\\d{9,15}$",
                    )
                ],
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="renter",
            name="final_invoice_path",
            field=models.CharField(blank=True, default=None, max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="renter",
            name="flagged_reason",
            field=models.TextField(blank=True, default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="renter",
            name="notes",
            field=models.TextField(
                blank=True, default=None, help_text="Additional notes"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="renter",
            name="onboarding_token",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Secure token for onboarding link",
                max_length=255,
                unique=True,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="renter",
            name="revocation_reason",
            field=models.TextField(blank=True, default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="renter",
            name="whatsapp_number",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="For WhatsApp messages",
                max_length=15,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="rentrecord",
            name="adjustment_reason",
            field=models.TextField(
                blank=True, default=None, help_text="Reason for late fee or adjustment"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="rentrecord",
            name="notes",
            field=models.TextField(blank=True, default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="rentrecord",
            name="payment_link",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Payment gateway link",
                max_length=500,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="rentrecord",
            name="payout_reference",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Payout gateway reference",
                max_length=100,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="rentrecord",
            name="razorpay_order_id",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Razorpay order reference",
                max_length=100,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="rentrecord",
            name="transaction_id",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Payment gateway / bank ref",
                max_length=100,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="unit",
            name="building_name",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Display name of building (cached for performance)",
                max_length=100,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="unit",
            name="landmark",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Nearby landmark for easy identification",
                max_length=255,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="unit",
            name="maintenance_notes",
            field=models.TextField(
                blank=True,
                default=None,
                help_text="Internal notes about maintenance or issues",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="unit",
            name="notes",
            field=models.TextField(
                blank=True, default=None, help_text="Additional notes about the unit"
            ),
            preserve_default=False,
        ),
    ]
