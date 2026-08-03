from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("finance", "0002_alter_taxsubmissiontoca_message"),
    ]

    operations = [
        migrations.CreateModel(
            name="CAPartner",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("phone", models.CharField(max_length=15)),
                (
                    "email",
                    models.EmailField(max_length=254),
                ),
                ("firm_name", models.CharField(max_length=255)),
                ("city", models.CharField(db_index=True, max_length=100)),
                ("experience_years", models.PositiveIntegerField()),
                (
                    "specialization",
                    models.CharField(
                        choices=[
                            ("ITR_FILING", "ITR Filing"),
                            ("NRI_TAX", "NRI Tax Help"),
                            ("INVESTMENT_TAX", "Investment Advice"),
                        ],
                        db_index=True,
                        max_length=255,
                    ),
                ),
                (
                    "available",
                    models.BooleanField(db_index=True, default=True),
                ),
                ("rating", models.FloatField(default=0.0)),
                ("price_range", models.CharField(max_length=50)),
            ],
            options={
                "ordering": ["-rating", "name"],
            },
        ),
    ]
