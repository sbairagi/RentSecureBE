# Add missing db_index on MaintenanceRequest foreign keys.
# SQLite-only deployment (no Redis, no PostgreSQL) on 2 vRAM Ubuntu server.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0022_alter_building_is_archived_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="maintenancerequest",
            name="assigned_caretaker",
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="maintenance_requests",
                to="properties.caretaker",
            ),
        ),
        migrations.AlterField(
            model_name="maintenancerequest",
            name="renter",
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="maintenance_requests",
                to="properties.renter",
            ),
        ),
        migrations.AlterField(
            model_name="maintenancerequest",
            name="unit",
            field=models.ForeignKey(
                db_index=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="maintenance_requests",
                to="properties.unit",
            ),
        ),
    ]
