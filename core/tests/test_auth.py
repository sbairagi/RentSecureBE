"""Tests for core auth views"""

from decimal import Decimal

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from core.models import (
    OTP,
    AddOnPurchase,
    SubscriptionPlan,
    UsageLimit,
    UserSubscription,
)

User = get_user_model()

API_PREFIX = "/api"


class SendOTPTest(TestCase):
    def test_send_otp_missing_phone(self):
        r = self.client.post(
            f"{API_PREFIX}/auth/send-otp/", {}, content_type="application/json"
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("error", r.data)

    @override_settings(DEBUG=True)
    def test_send_otp_success(self):
        r = self.client.post(
            f"{API_PREFIX}/auth/send-otp/",
            {"phone": "+911234567890"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("message", r.data)

    @override_settings(DEBUG=True)
    def test_send_otp_rate_limit(self):
        self.client.post(
            f"{API_PREFIX}/auth/send-otp/",
            {"phone": "+919999999999"},
            content_type="application/json",
        )
        r = self.client.post(
            f"{API_PREFIX}/auth/send-otp/",
            {"phone": "+919999999999"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 429)


class VerifyOTPTest(TestCase):
    def test_verify_missing_fields(self):
        r = self.client.post(
            f"{API_PREFIX}/auth/owner/verify-otp/", {}, content_type="application/json"
        )
        self.assertEqual(r.status_code, 400)

    def test_verify_invalid_otp(self):
        r = self.client.post(
            f"{API_PREFIX}/auth/owner/verify-otp/",
            {"phone": "+9111111111", "otp": "000000"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 400)

    def test_verify_valid_otp(self):
        OTP.objects.create(phone_number="+9122222222", code="123456", referral_code="")
        r = self.client.post(
            f"{API_PREFIX}/auth/owner/verify-otp/",
            {"phone": "+9122222222", "otp": "123456"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("access", r.data)

    def test_renter_verify_valid_otp(self):
        OTP.objects.create(phone_number="+9133333333", code="654321", referral_code="")
        r = self.client.post(
            f"{API_PREFIX}/auth/renter/verify-otp/",
            {"phone": "+9133333333", "otp": "654321"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("access", r.data)


class ChangePasswordTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="cp@t.com",
            email="cp@t.com",
            password="oldpass123",
            full_name="CP",
            phone="+1",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_change_password_missing_fields(self):
        r = self.client.post(
            f"{API_PREFIX}/change-password/", {}, content_type="application/json"
        )
        self.assertEqual(r.status_code, 400)

    def test_change_password_wrong_old(self):
        r = self.client.post(
            f"{API_PREFIX}/change-password/",
            {"old_password": "wrong", "new_password": "newpass"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 400)

    def test_change_password_same(self):
        r = self.client.post(
            f"{API_PREFIX}/change-password/",
            {"old_password": "oldpass123", "new_password": "oldpass123"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 400)

    def test_change_password_success(self):
        r = self.client.post(
            f"{API_PREFIX}/change-password/",
            {"old_password": "oldpass123", "new_password": "newpass456"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)


class ResetPasswordTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="rp@t.com",
            email="rp@t.com",
            password="oldpass",
            full_name="RP",
            phone="+1",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_reset_missing_fields(self):
        r = self.client.post(
            f"{API_PREFIX}/reset-password/", {}, content_type="application/json"
        )
        self.assertEqual(r.status_code, 400)

    def test_reset_user_not_found(self):
        r = self.client.post(
            f"{API_PREFIX}/reset-password/",
            {"username": "nonexistent", "new_password": "newpass"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)

    def test_reset_by_username(self):
        r = self.client.post(
            f"{API_PREFIX}/reset-password/",
            {"username": "rp@t.com", "new_password": "brandnew"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)

    def test_reset_by_email(self):
        r = self.client.post(
            f"{API_PREFIX}/reset-password/",
            {"username": "rp@t.com", "new_password": "anothernew"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)


class SubscriptionPlanViewSetTest(TestCase):
    def setUp(self):
        SubscriptionPlan.objects.all().delete()
        self.plan = SubscriptionPlan.objects.create(
            name="test_plan",
            monthly_price=Decimal("9.99"),
            yearly_price=Decimal("99.99"),
            features="Test",
        )

    def test_list_plans(self):
        r = self.client.get(f"{API_PREFIX}/subscription-plans/")
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(len(r.data), 1)

    def test_retrieve_plan(self):
        r = self.client.get(f"{API_PREFIX}/subscription-plans/{self.plan.id}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["name"], "test_plan")


class UserSubscriptionViewSetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="usv@t.com",
            email="usv@t.com",
            password="p",
            full_name="USV",
            phone="+1",
        )
        self.plan = SubscriptionPlan.objects.create(
            name="usv_plan",
            monthly_price=Decimal("19.99"),
            yearly_price=Decimal("199.99"),
            features="Test",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_subscription(self):
        r = self.client.post(
            f"{API_PREFIX}/user-subscriptions/", {"plan": self.plan.id}, format="json"
        )
        self.assertEqual(r.status_code, 201)

    def test_list_own_subscription(self):
        UserSubscription.objects.create(user=self.user, plan=self.plan)
        r = self.client.get(f"{API_PREFIX}/user-subscriptions/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)


class AddOnPurchaseViewSetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="aop@t.com",
            email="aop@t.com",
            password="p",
            full_name="AOP",
            phone="+1",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_addon(self):
        r = self.client.post(
            f"{API_PREFIX}/addon-purchases/",
            {"name": "max_units", "amount": "49.99"},
            format="json",
        )
        self.assertEqual(r.status_code, 201)

    def test_list_addons(self):
        AddOnPurchase.objects.create(
            user=self.user, name="max_buildings", amount=Decimal("29.99")
        )
        r = self.client.get(f"{API_PREFIX}/addon-purchases/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)


class UsageLimitViewSetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ulv@t.com",
            email="ulv@t.com",
            password="p",
            full_name="ULV",
            phone="+1",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.ul = UsageLimit.objects.create(
            user=self.user, feature_key="max_units", usage_count=3
        )

    def test_list_usage_limits(self):
        r = self.client.get(f"{API_PREFIX}/usage-limits/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)
        self.assertEqual(r.data[0]["usage_count"], 3)


class TokenRefreshTest(TestCase):
    def test_token_refresh(self):
        user = User.objects.create_user(
            username="tr@t.com",
            email="tr@t.com",
            password="p",
            full_name="TR",
            phone="+1",
        )
        refresh = RefreshToken.for_user(user)
        r = self.client.post(
            f"{API_PREFIX}/api/token/refresh/", {"refresh": str(refresh)}, format="json"
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("access", r.data)
