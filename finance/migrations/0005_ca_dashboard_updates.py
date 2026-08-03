from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("finance", "0004_ca_connection_request"),
    ]

    operations = [
        migrations.AddField(
            model_name="capartner",
            name="user",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="ca_partner_profile",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="caconnectionrequest",
            name="ca",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="finance.capartner",
            ),
        ),
        migrations.AddField(
            model_name="caconnectionrequest",
            name="notes",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="caconnectionrequest",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pending"),
                    ("CONTACTED", "Contacted"),
                    ("CLOSED", "Closed"),
                ],
                default="PENDING",
                max_length=20,
            ),
        ),
        migrations.RenameField(
            model_name="caconnectionrequest",
            old_name="created_at",
            new_name="requested_at",
        ),
    ]
