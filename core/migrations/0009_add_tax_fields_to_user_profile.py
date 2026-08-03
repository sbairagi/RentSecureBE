from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_add_income_fields_to_user_profile"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="elss_investment",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Annual ELSS/PPF/LIC investment claimed under Section 80C",
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="has_health_insurance",
            field=models.BooleanField(
                default=False,
                help_text="Whether the user has active health insurance for Section 80D",
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="home_loan_interest",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Annual home loan interest paid for Section 24(b) deduction",
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="receives_hra",
            field=models.BooleanField(
                default=False,
                help_text="Whether the user receives House Rent Allowance (HRA)",
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="rent_paid",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Annual rent paid for Section 80GG deduction",
            ),
        ),
    ]
