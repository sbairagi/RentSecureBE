from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0009_add_tax_fields_to_user_profile"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="is_nri",
            field=models.BooleanField(
                default=False,
                help_text="Whether the user is a Non-Resident Indian",
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="city",
            field=models.CharField(
                blank=True,
                help_text="City for CA matchmaking",
                max_length=100,
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="total_investment_income",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Total investment income for CA specialization matching",
            ),
        ),
    ]
