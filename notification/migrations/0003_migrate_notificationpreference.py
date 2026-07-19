from django.db import migrations


def migrate_notification_preferences(apps, schema_editor) -> None:
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT OR IGNORE INTO notification_notificationpreference
                (id, owner_id, rent_alerts_whatsapp, rent_alerts_email,
                 monthly_summary_email, monthly_summary_whatsapp,
                 payout_alerts_whatsapp, payout_alerts_email)
            SELECT
                id, owner_id, rent_alerts_whatsapp, rent_alerts_email,
                monthly_summary_email, monthly_summary_whatsapp,
                payout_alerts_whatsapp, payout_alerts_email
            FROM core_notificationpreference
            """)


def reverse_migrate_notification_preferences(apps, schema_editor) -> None:
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM notification_notificationpreference
            WHERE owner_id IN (SELECT owner_id FROM core_notificationpreference)
            """)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("notification", "0002_add_notificationpreference"),
    ]

    operations = [
        migrations.RunPython(
            migrate_notification_preferences,
            reverse_migrate_notification_preferences,
        ),
    ]
