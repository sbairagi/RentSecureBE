from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0005_ca_dashboard_updates"),
    ]

    operations = [
        migrations.RenameField(
            model_name="caconnectionrequest",
            old_name="ca",
            new_name="ca_partner",
        ),
    ]
