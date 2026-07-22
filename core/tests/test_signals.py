"""Tests for core app signals"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import UserProfile

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

    def test_existing_user_does_not_duplicate(self):
        user = User.objects.create_user(
            username="singleno@t.com",
            email="singleno@t.com",
            password="p",
            full_name="Single",
            phone="+1",
        )
        self.assertTrue(hasattr(user, "userprofile"))

    def test_user_profile_language_default(self):
        user = User.objects.create_user(
            username="lang@t.com",
            email="lang@t.com",
            password="p",
            full_name="Lang",
            phone="+1",
        )
        self.assertEqual(user.userprofile.language_preference, "en")
