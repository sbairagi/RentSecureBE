"""Tests for the sign in routes: the one time code, the e-mail link and the
logout of every device."""

from datetime import date, timedelta
from unittest.mock import patch

from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from core.models import OTP, EmailSignInLink

User = get_user_model()

API_PREFIX = "/api"


class SignInSessionTest(TestCase):
    """Every sign in route hands the same session to the three apps."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="renter@securenest.in",
            email="renter@securenest.in",
            password="securenest123",
            full_name="Riya Kapoor",
            phone="+919845099887",
        )
        self.user.groups.add(Group.objects.get_or_create(name="renter")[0])

    def test_password_login_answers_with_the_session(self):
        response = self.client.post(
            f"{API_PREFIX}/auth/login/",
            {"email": "renter@securenest.in", "password": "securenest123"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["role"], "renter")
        self.assertEqual(response.data["user"]["full_name"], "Riya Kapoor")
        self.assertEqual(response.data["user"]["phone"], "+919845099887")

    def test_one_time_code_answers_with_the_same_session(self):
        OTP.objects.create(
            phone_number="+919845099887", code="246810", referral_code=""
        )

        response = self.client.post(
            f"{API_PREFIX}/auth/renter/verify-otp/",
            {"phone": "+919845099887", "otp": "246810"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["role"], "renter")
        self.assertEqual(response.data["user"]["full_name"], "Riya Kapoor")

    def test_an_account_that_signs_in_with_a_code_has_no_password(self):
        OTP.objects.create(
            phone_number="+915555555555", code="135790", referral_code=""
        )

        self.client.post(
            f"{API_PREFIX}/auth/renter/verify-otp/",
            {"phone": "+915555555555", "otp": "135790"},
            content_type="application/json",
        )

        created = User.objects.get(phone="+915555555555")
        self.assertFalse(created.has_usable_password())

    @patch("core.views.send_otp")
    def test_the_resend_wait_counts_the_real_seconds(self, mocked_send):
        OTP.objects.create(
            phone_number="+916666666666",
            code="111111",
            referral_code="",
        )
        OTP.objects.filter(phone_number="+916666666666").update(
            created_at=timezone.now() - timedelta(seconds=90)
        )

        response = self.client.post(
            f"{API_PREFIX}/auth/send-otp/",
            {"phone": "+916666666666"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

    def test_logging_out_of_every_device_keeps_the_password(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(f"{API_PREFIX}/auth/logout-all/")

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.has_usable_password())
        self.assertTrue(self.user.check_password("securenest123"))


class CaretakerVerifyOTPTest(TestCase):
    """A caretaker signs in with the number the owner registered."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username="owner@securenest.in",
            email="owner@securenest.in",
            password="securenest123",
            full_name="Arjun Mehta",
        )
        self.caretaker_user = User.objects.create_user(
            username="caretaker@securenest.in",
            email="caretaker@securenest.in",
            password="securenest123",
            full_name="Kavita Rao",
            phone="+919876543210",
        )
        self._caretaker_record()

    def _caretaker_record(self):
        from properties.models import Caretaker

        caretaker, _ = Caretaker.objects.get_or_create(
            owner=self.owner,
            name="Kavita Rao",
            defaults={
                "user": self.caretaker_user,
                "phone": "+919876543210",
                "email": "caretaker@securenest.in",
                "joining_date": date.today(),
            },
        )
        caretaker.user = self.caretaker_user
        caretaker.save(update_fields=["user"])

    def test_the_caretaker_signs_in_with_the_code(self):
        OTP.objects.create(
            phone_number="+919876543210", code="246810", referral_code=""
        )

        response = self.client.post(
            f"{API_PREFIX}/auth/caretaker/verify-otp/",
            {"phone": "+919876543210", "otp": "246810"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["role"], "caretaker")
        self.assertEqual(response.data["user"]["full_name"], "Kavita Rao")

    def test_an_unknown_number_is_refused(self):
        response = self.client.post(
            f"{API_PREFIX}/auth/caretaker/verify-otp/",
            {"phone": "+917777777777", "otp": "246810"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn("No caretaker", response.data["error"])
        self.assertFalse(User.objects.filter(phone="+917777777777").exists())

    def test_an_account_without_a_caretaker_record_is_refused(self):
        User.objects.create_user(
            username="someone@securenest.in",
            email="someone@securenest.in",
            password="securenest123",
            full_name="Someone",
            phone="+918888888888",
        )
        OTP.objects.create(
            phone_number="+918888888888", code="246810", referral_code=""
        )

        response = self.client.post(
            f"{API_PREFIX}/auth/caretaker/verify-otp/",
            {"phone": "+918888888888", "otp": "246810"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn("not a caretaker", response.data["error"])


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class EmailSignInLinkTest(TestCase):
    """The renter signs in with a link that lands in the inbox."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="renter@securenest.in",
            email="renter@securenest.in",
            password="securenest123",
            full_name="Riya Kapoor",
        )
        self.user.groups.add(Group.objects.get_or_create(name="renter")[0])

    def _send(self, email="renter@securenest.in", role="renter"):
        return self.client.post(
            f"{API_PREFIX}/auth/email-link/",
            {"email": email, "role": role},
            content_type="application/json",
        )

    @override_settings(
        DEBUG=True, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
    )
    def test_the_link_lands_on_the_renter_app(self):
        response = self._send()

        self.assertEqual(response.status_code, 200)
        link = EmailSignInLink.objects.get(email=self.user.email)
        self.assertEqual(link.role, "renter")
        self.assertFalse(link.used_at)
        self.assertIn("/renter?email_token=", response.data["debug_link"])

    def test_the_link_hands_the_session(self):
        self._send()
        token = EmailSignInLink.objects.get(email=self.user.email).token

        response = self.client.post(
            f"{API_PREFIX}/auth/email-link/verify/",
            {"token": token},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["access"])
        self.assertEqual(response.data["user"]["role"], "renter")
        self.assertEqual(response.data["user"]["full_name"], "Riya Kapoor")

    def test_the_link_works_only_once(self):
        self._send()
        token = EmailSignInLink.objects.get(email=self.user.email).token
        self.client.post(
            f"{API_PREFIX}/auth/email-link/verify/",
            {"token": token},
            content_type="application/json",
        )

        second = self.client.post(
            f"{API_PREFIX}/auth/email-link/verify/",
            {"token": token},
            content_type="application/json",
        )

        self.assertEqual(second.status_code, 400)
        self.assertIn("no longer valid", second.data["error"])

    def test_an_expired_link_is_refused(self):
        self._send()
        link = EmailSignInLink.objects.get(email=self.user.email)
        link.expires_at = timezone.now() - timedelta(minutes=1)
        link.save(update_fields=["expires_at"])

        response = self.client.post(
            f"{API_PREFIX}/auth/email-link/verify/",
            {"token": link.token},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("no longer valid", response.data["error"])

    def test_a_new_link_replaces_the_old_one(self):
        self._send()
        first = EmailSignInLink.objects.get(email=self.user.email).token
        self._send()
        second = EmailSignInLink.objects.get(email=self.user.email).token

        self.assertNotEqual(first, second)
        self.assertEqual(EmailSignInLink.objects.count(), 1)

    def test_an_unknown_address_gets_the_same_answer(self):
        response = self._send(email="nobody@securenest.in")

        self.assertEqual(response.status_code, 200)
        self.assertIn("on its way", response.data["message"])
        self.assertFalse(EmailSignInLink.objects.exists())

    def test_an_invalid_address_is_refused(self):
        response = self._send(email="not-an-address")

        self.assertEqual(response.status_code, 400)
        self.assertIn("valid e-mail", response.data["error"])

    @override_settings(DEBUG=False)
    def test_the_link_is_not_given_away_when_the_server_is_not_in_debug(self):
        response = self._send()

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("debug_link", response.data)
