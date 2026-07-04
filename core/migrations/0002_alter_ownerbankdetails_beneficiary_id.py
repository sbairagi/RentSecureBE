from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ownerbankdetails",
            name="beneficiary_id",
            field=models.CharField(
                blank=True, default=None, max_length=100, unique=True
            ),
            preserve_default=False,
        ),
    ]
