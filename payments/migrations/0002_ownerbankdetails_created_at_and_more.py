from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="ownerbankdetails",
            name="created_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="ownerbankdetails",
            name="updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
