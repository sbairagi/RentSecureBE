from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="taxsubmissiontoca",
            name="message",
            field=models.TextField(blank=True, default=None),
            preserve_default=False,
        ),
    ]
