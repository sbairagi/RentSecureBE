from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0010_add_ca_matching_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="AppVersion",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "min_supported_version",
                    models.CharField(
                        default="1.0.0",
                        help_text="Minimum supported version; users below this must force-update.",
                        max_length=20,
                    ),
                ),
                (
                    "latest_version",
                    models.CharField(
                        default="1.0.0",
                        help_text="Latest released version.",
                        max_length=20,
                    ),
                ),
                (
                    "is_force_update",
                    models.BooleanField(
                        default=False,
                        help_text="If True, all users must update regardless of version.",
                    ),
                ),
                (
                    "store_url",
                    models.URLField(
                        blank=True,
                        help_text="URL to the app store page for forced updates.",
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "App Version",
                "verbose_name_plural": "App Version",
            },
        ),
        migrations.CreateModel(
            name="MaintenanceMode",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "is_active",
                    models.BooleanField(
                        default=False,
                        help_text="Enable or disable maintenance mode.",
                    ),
                ),
                (
                    "message",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="Message displayed to users during maintenance.",
                    ),
                ),
                (
                    "scheduled_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Optional: when maintenance is scheduled to start.",
                        null=True,
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Maintenance Mode",
                "verbose_name_plural": "Maintenance Mode",
            },
        ),
    ]
