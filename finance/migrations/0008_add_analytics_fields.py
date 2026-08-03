from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0007_remove_message_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="caconnectionrequest",
            name="contacted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="caconnectionrequest",
            name="converted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
