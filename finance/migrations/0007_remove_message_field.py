from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0006_rename_ca_to_ca_partner"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="caconnectionrequest",
            name="message",
        ),
    ]
