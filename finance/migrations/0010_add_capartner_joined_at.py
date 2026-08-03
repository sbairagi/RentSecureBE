from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0009_alter_caconnectionrequest_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="capartner",
            name="joined_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
