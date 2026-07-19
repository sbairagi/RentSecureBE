import importlib

from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import TestCase

from notification.models import NotificationPreference


class TestNotificationPreferenceMigration(TestCase):
    def test_migrates_all_rows(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="migration_test_user",
            email="test@example.com",
            password="testpass123",
        )
        from core.models import NotificationPreference as CoreNotificationPreference

        NotificationPreference.objects.filter(owner=user).delete()
        CoreNotificationPreference.objects.create(
            owner=user,
            rent_alerts_whatsapp=True,
            rent_alerts_email=False,
            monthly_summary_email=True,
            monthly_summary_whatsapp=False,
            payout_alerts_whatsapp=True,
            payout_alerts_email=False,
        )

        core_count = CoreNotificationPreference.objects.count()
        self.assertEqual(core_count, 1)

        migration_module = importlib.import_module(
            "notification.migrations.0003_migrate_notificationpreference"
        )
        migration_module.migrate_notification_preferences(apps, None)

        notification_count = NotificationPreference.objects.count()
        self.assertEqual(notification_count, core_count)

    def test_reverse_migration_restores_data(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="reverse_test",
            email="reverse@example.com",
            password="testpass123",
        )
        from core.models import NotificationPreference as CoreNotificationPreference

        NotificationPreference.objects.filter(owner=user).delete()
        CoreNotificationPreference.objects.create(
            owner=user,
            rent_alerts_whatsapp=True,
            rent_alerts_email=True,
            monthly_summary_email=True,
            monthly_summary_whatsapp=True,
            payout_alerts_whatsapp=True,
            payout_alerts_email=True,
        )

        migration_module = importlib.import_module(
            "notification.migrations.0003_migrate_notificationpreference"
        )
        migration_module.migrate_notification_preferences(apps, None)
        self.assertEqual(NotificationPreference.objects.count(), 1)

        migration_module.reverse_migrate_notification_preferences(apps, None)
        self.assertEqual(NotificationPreference.objects.count(), 0)
        self.assertEqual(CoreNotificationPreference.objects.count(), 1)

    def test_migration_on_empty_database(self):
        self.assertEqual(NotificationPreference.objects.count(), 0)
        migration_module = importlib.import_module(
            "notification.migrations.0003_migrate_notificationpreference"
        )
        migration_module.migrate_notification_preferences(apps, None)
        self.assertEqual(NotificationPreference.objects.count(), 0)

    def test_preference_fields_preserved(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="fields_test",
            email="fields@example.com",
            password="testpass123",
        )
        from core.models import NotificationPreference as CoreNotificationPreference

        NotificationPreference.objects.filter(owner=user).delete()
        core_pref = CoreNotificationPreference.objects.create(
            owner=user,
            rent_alerts_whatsapp=False,
            rent_alerts_email=True,
            monthly_summary_email=False,
            monthly_summary_whatsapp=True,
            payout_alerts_whatsapp=False,
            payout_alerts_email=True,
        )

        migration_module = importlib.import_module(
            "notification.migrations.0003_migrate_notificationpreference"
        )
        migration_module.migrate_notification_preferences(apps, None)

        notification_pref = NotificationPreference.objects.get(owner=user)
        self.assertEqual(
            notification_pref.rent_alerts_whatsapp, core_pref.rent_alerts_whatsapp
        )
        self.assertEqual(
            notification_pref.rent_alerts_email, core_pref.rent_alerts_email
        )
        self.assertEqual(
            notification_pref.monthly_summary_email, core_pref.monthly_summary_email
        )
        self.assertEqual(
            notification_pref.monthly_summary_whatsapp,
            core_pref.monthly_summary_whatsapp,
        )
        self.assertEqual(
            notification_pref.payout_alerts_whatsapp, core_pref.payout_alerts_whatsapp
        )
        self.assertEqual(
            notification_pref.payout_alerts_email, core_pref.payout_alerts_email
        )

    def test_migration_preserves_user_links(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="user_link_test",
            email="userlink@example.com",
            password="testpass123",
        )
        from core.models import NotificationPreference as CoreNotificationPreference

        NotificationPreference.objects.filter(owner=user).delete()
        CoreNotificationPreference.objects.create(owner=user)

        migration_module = importlib.import_module(
            "notification.migrations.0003_migrate_notificationpreference"
        )
        migration_module.migrate_notification_preferences(apps, None)

        notification_pref = NotificationPreference.objects.get(owner=user)
        self.assertEqual(notification_pref.owner_id, user.id)
        self.assertEqual(notification_pref.owner, user)
