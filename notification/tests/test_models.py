from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from notification.models import NotificationPreference


class TestNotificationPreferenceModel(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            username="notification_pref_test_user",
            email="pref@example.com",
            password="testpass123",
        )

    def test_notification_preference_matches_original_schema(self):
        expected_fields = {
            "id",
            "owner",
            "rent_alerts_whatsapp",
            "rent_alerts_email",
            "monthly_summary_email",
            "monthly_summary_whatsapp",
            "payout_alerts_whatsapp",
            "payout_alerts_email",
        }
        actual_fields = {f.name for f in NotificationPreference._meta.get_fields()}
        self.assertEqual(actual_fields, expected_fields)

    def test_unique_together_owner(self):
        NotificationPreference.objects.filter(owner=self.user).delete()
        NotificationPreference.objects.create(owner=self.user)
        with self.assertRaises(IntegrityError):
            NotificationPreference.objects.create(owner=self.user)

    def test_user_foreign_key_uses_auth_user_model_string(self):
        owner_field = NotificationPreference._meta.get_field("owner")
        self.assertEqual(owner_field.remote_field.model, self.user_model)

    def test_db_table_is_notification_notificationpreference(self):
        self.assertEqual(
            NotificationPreference._meta.db_table, "notification_notificationpreference"
        )

    def test_default_values(self):
        pref = NotificationPreference.objects.get(owner=self.user)
        self.assertTrue(pref.rent_alerts_whatsapp)
        self.assertTrue(pref.rent_alerts_email)
        self.assertTrue(pref.monthly_summary_email)
        self.assertFalse(pref.monthly_summary_whatsapp)
        self.assertTrue(pref.payout_alerts_whatsapp)
        self.assertFalse(pref.payout_alerts_email)
