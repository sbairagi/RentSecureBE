"""Tests for core app signals"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import UserProfile
from notification.models import NotificationPreference

User = get_user_model()


class UserSignalTest(TestCase):
    def test_user_creation_creates_profile(self):
        user = User.objects.create_user(
            username="sig1@t.com",
            email="sig1@t.com",
            password="p",
            full_name="Sig User",
            phone="+1",
        )
        self.assertTrue(hasattr(user, "userprofile"))
        self.assertIsInstance(user.userprofile, UserProfile)

    def test_user_creation_creates_notification_preference(self):
        user = User.objects.create_user(
            username="sig2@t.com",
            email="sig2@t.com",
            password="p",
            full_name="Sig User 2",
            phone="+2",
        )
        self.assertTrue(hasattr(user, "notification_preferences"))
        self.assertIsInstance(user.notification_preferences, NotificationPreference)

    def test_user_creation_assigns_free_plan(self):
        user = User.objects.create_user(
            username="sig3@t.com",
            email="sig3@t.com",
            password="p",
            full_name="Sig User 3",
            phone="+3",
        )
        self.assertTrue(hasattr(user, "usersubscription"))
        self.assertEqual(user.usersubscription.plan.name, "free")

    def test_user_profile_defaults(self):
        user = User.objects.create_user(
            username="sig4@t.com",
            email="sig4@t.com",
            password="p",
            full_name="Sig User 4",
            phone="+4",
        )
        profile = user.userprofile
        self.assertEqual(profile.language_preference, "en")
        self.assertTrue(profile.whatsapp_opt_in)

    def test_notification_preference_defaults(self):
        user = User.objects.create_user(
            username="sig5@t.com",
            email="sig5@t.com",
            password="p",
            full_name="Sig User 5",
            phone="+5",
        )
        prefs = user.notification_preferences
        self.assertTrue(prefs.rent_alerts_whatsapp)
        self.assertTrue(prefs.rent_alerts_email)
        self.assertTrue(prefs.monthly_summary_email)
        self.assertFalse(prefs.monthly_summary_whatsapp)
        self.assertTrue(prefs.payout_alerts_whatsapp)
        self.assertFalse(prefs.payout_alerts_email)
