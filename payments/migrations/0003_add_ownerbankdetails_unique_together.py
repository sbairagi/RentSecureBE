from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0002_ownerbankdetails_created_at_and_more"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="ownerbankdetails",
            unique_together={("owner", "bank_account_number")},
        ),
    ]
