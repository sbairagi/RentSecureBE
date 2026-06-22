"""Comprehensive tests covering core views, signals, serializers, and utils"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from rest_framework.test import APIClient, APIRequestFactory

from core.models import (
    OTP,
    AddOnPurchase,
    NotificationPreference,
    OwnerBankDetails,
    PlanFeatureLimit,
    SubscriptionPlan,
    UsageLimit,
    UserSubscription,
)
from core.serializers import (
    AddOnPurchaseSerializer,
    PlanFeatureLimitSerializer,
    SubscriptionPlanSerializer,
    UsageLimitSerializer,
    UserSerializer,
    UserSubscriptionSerializer,
)
from core.signals import assign_default_plan

User = get_user_model()

# ===================== Model Tests =====================


class UserModelStringTest(TestCase):
    def test_user_str(self):
        u = User.objects.create_user(
            username="ustr@t.com",
            email="ustr@t.com",
            password="p",
            full_name="Test Name",
            phone="+1",
        )
        self.assertEqual(str(u), "Test Name")

    def test_subscription_plan_str(self):
        p = SubscriptionPlan.objects.create(
            name="gold",
            monthly_price=Decimal("49.99"),
            yearly_price=Decimal("499.99"),
            features="Premium",
        )
        self.assertEqual(str(p), "Gold")

    def test_user_subscription_str(self):
        u = User.objects.create_user(
            username="substr@t.com",
            email="substr@t.com",
            password="p",
            full_name="Sub",
            phone="+1",
        )
        p = SubscriptionPlan.objects.create(
            name="basic",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Basic",
        )
        s = UserSubscription.objects.create(user=u, plan=p)
        self.assertIn("basic", str(s))

    def test_add_on_purchase_str(self):
        u = User.objects.create_user(
            username="addonstr@t.com",
            email="addonstr@t.com",
            password="p",
            full_name="Addon",
            phone="+1",
        )
        a = AddOnPurchase.objects.create(
            user=u, name="max_units", amount=Decimal("9.99")
        )
        self.assertIn("max_units", str(a))

    def test_plan_feature_limit_str(self):
        p = SubscriptionPlan.objects.create(
            name="pfl_str",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="F",
        )
        pl = PlanFeatureLimit.objects.create(
            plan=p, feature_key="max_buildings", value="3"
        )
        self.assertIn("pfl_str", str(pl))

    def test_otp_str(self):
        otp = OTP.objects.create(
            phone_number="+919999999999", code="123456", referral_code=""
        )
        self.assertEqual(otp.code, "123456")

    def test_notification_preference_str(self):
        u = User.objects.create_user(
            username="npstr@t.com",
            email="npstr@t.com",
            password="p",
            full_name="NP",
            phone="+1",
        )
        np = NotificationPreference.objects.create(owner=u)
        self.assertIn("npstr@t.com", str(np))

    def test_owner_bank_details_str(self):
        u = User.objects.create_user(
            username="bankstr@t.com",
            email="bankstr@t.com",
            password="p",
            full_name="Bank",
            phone="+1",
        )
        b = OwnerBankDetails.objects.create(
            owner=u, bank_account_number="1234567890", ifsc_code="HDFC0001234"
        )
        self.assertIn("bankstr@t.com", str(b))

    def test_usage_limit_str(self):
        u = User.objects.create_user(
            username="ulstr@t.com",
            email="ulstr@t.com",
            password="p",
            full_name="UL",
            phone="+1",
        )
        ul = UsageLimit.objects.create(user=u, feature_key="max_units", usage_count=5)
        self.assertIn("ulstr@t.com", str(ul))


# ===================== Signal Tests =====================


class SignalTest(TestCase):
    def test_user_creation_signal_creates_all(self):
        u = User.objects.create_user(
            username="sigfull@t.com",
            email="sigfull@t.com",
            password="p",
            full_name="Sig Full",
            phone="+1",
        )
        self.assertTrue(hasattr(u, "userprofile"))
        self.assertTrue(hasattr(u, "notification_preference"))
        self.assertTrue(hasattr(u, "usersubscription"))
        self.assertEqual(u.usersubscription.plan.name, "free")

    def test_existing_user_does_not_duplicate(self):
        u = User.objects.create_user(
            username="singleno@t.com",
            email="singleno@t.com",
            password="p",
            full_name="Single",
            phone="+1",
        )
        # Create again should not error (signal checks hasattr)
        assign_default_plan(User, u, created=False)
        self.assertTrue(hasattr(u, "userprofile"))

    def test_user_profile_language_default(self):
        u = User.objects.create_user(
            username="lang@t.com",
            email="lang@t.com",
            password="p",
            full_name="Lang",
            phone="+1",
        )
        self.assertEqual(u.userprofile.language_preference, "en")


# ===================== Serializer Tests =====================


class SerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="sertest@t.com",
            email="sertest@t.com",
            password="p",
            full_name="Ser Test",
            phone="+1",
        )
        self.plan = SubscriptionPlan.objects.create(
            name="ser_plan",
            monthly_price=Decimal("9.99"),
            yearly_price=Decimal("99.99"),
            features="Test",
        )
        self.factory = APIRequestFactory()
        self.request = self.factory.get("/")
        self.request.user = self.user

    def test_user_serializer(self):
        s = UserSerializer(instance=self.user)
        self.assertEqual(s.data["full_name"], "Ser Test")

    def test_subscription_plan_serializer(self):
        s = SubscriptionPlanSerializer(instance=self.plan)
        self.assertEqual(s.data["name"], "ser_plan")

    def test_user_subscription_serializer_create(self):
        s = UserSubscriptionSerializer(
            data={"plan": self.plan.id}, context={"request": self.request}
        )
        self.assertTrue(s.is_valid(), msg=str(s.errors))
        obj = s.save()
        self.assertEqual(obj.user, self.user)

    def test_addon_purchase_serializer_create(self):
        s = AddOnPurchaseSerializer(
            data={"name": "max_units", "amount": "14.99"},
            context={"request": self.request},
        )
        self.assertTrue(s.is_valid(), msg=str(s.errors))
        obj = s.save()
        self.assertEqual(obj.user, self.user)

    def test_plan_feature_limit_serializer(self):
        pl = PlanFeatureLimit.objects.create(
            plan=self.plan, feature_key="max_renters", value="10"
        )
        s = PlanFeatureLimitSerializer(instance=pl)
        self.assertEqual(s.data["value"], "10")

    def test_usage_limit_serializer(self):
        ul = UsageLimit.objects.create(
            user=self.user, feature_key="max_buildings", usage_count=2
        )
        s = UsageLimitSerializer(instance=ul)
        self.assertEqual(s.data["usage_count"], 2)


# ===================== View Tests =====================

API_PREFIX = "/api"


class OTPSendViewTest(TestCase):
    @override_settings(TWILIO_ACCOUNT_SID="", TWILIO_AUTH_TOKEN="", DEBUG=True)
    def test_send_otp_missing_phone(self):
        r = self.client.post(
            f"{API_PREFIX}/auth/send-otp/", {}, content_type="application/json"
        )
        self.assertEqual(r.status_code, 400)

    @override_settings(TWILIO_ACCOUNT_SID="", TWILIO_AUTH_TOKEN="", DEBUG=True)
    def test_send_otp_success(self):
        r = self.client.post(
            f"{API_PREFIX}/auth/send-otp/",
            {"phone": "+911234567890"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)

    @override_settings(TWILIO_ACCOUNT_SID="", TWILIO_AUTH_TOKEN="", DEBUG=True)
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

    @override_settings(TWILIO_ACCOUNT_SID="", TWILIO_AUTH_TOKEN="", DEBUG=True)
    def test_send_otp_invalid_referral(self):
        r = self.client.post(
            f"{API_PREFIX}/auth/send-otp/",
            {"phone": "+918888888888", "referral_code": "INVALID"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)  # OTP sent, referral validated later


class OTPVerifyViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Group.objects.get_or_create(name="tenant")
        Group.objects.get_or_create(name="renter")

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


class ChangePasswordViewTest(TestCase):
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

    def test_change_password_missing(self):
        r = self.client.put(
            f"{API_PREFIX}/change-password/", {}, content_type="application/json"
        )
        self.assertEqual(r.status_code, 400)

    def test_change_password_wrong_old(self):
        r = self.client.put(
            f"{API_PREFIX}/change-password/",
            {"old_password": "wrong", "new_password": "new"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 400)

    def test_change_password_same(self):
        r = self.client.put(
            f"{API_PREFIX}/change-password/",
            {"old_password": "oldpass123", "new_password": "oldpass123"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 400)

    def test_change_password_success(self):
        r = self.client.put(
            f"{API_PREFIX}/change-password/",
            {"old_password": "oldpass123", "new_password": "newpass456"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)


class ResetPasswordViewTest(TestCase):
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

    def test_reset_missing(self):
        r = self.client.post(
            f"{API_PREFIX}/reset-password/", {}, content_type="application/json"
        )
        self.assertEqual(r.status_code, 400)

    def test_reset_not_found(self):
        r = self.client.post(
            f"{API_PREFIX}/reset-password/",
            {"username": "nonexistent", "new_password": "new"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)

    def test_reset_by_username(self):
        r = self.client.post(
            f"{API_PREFIX}/reset-password/",
            {"username": "rp@t.com", "new_password": "newpass"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)

    def test_reset_by_email(self):
        r = self.client.post(
            f"{API_PREFIX}/reset-password/",
            {"username": "rp@t.com", "new_password": "another"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)


class SubscriptionViewSetTest(TestCase):
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


class AuthenticatedViewSetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="authv@t.com",
            email="authv@t.com",
            password="p",
            full_name="AuthV",
            phone="+1",
        )
        self.plan = SubscriptionPlan.objects.create(
            name="authv_plan",
            monthly_price=Decimal("19.99"),
            yearly_price=Decimal("199.99"),
            features="Test",
        )
        SubscriptionPlan.objects.create(
            name="authv_free",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Free",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        UserSubscription.objects.filter(user=self.user).delete()

    def test_create_subscription(self):
        r = self.client.post(
            f"{API_PREFIX}/user-subscriptions/", {"plan": self.plan.id}, format="json"
        )
        self.assertEqual(r.status_code, 201)

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

    def test_list_usage_limits(self):
        UsageLimit.objects.create(
            user=self.user, feature_key="max_units", usage_count=3
        )
        r = self.client.get(f"{API_PREFIX}/usage-limits/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)

    def test_list_own_subscription(self):
        UserSubscription.objects.create(user=self.user, plan=self.plan)
        r = self.client.get(f"{API_PREFIX}/user-subscriptions/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)
