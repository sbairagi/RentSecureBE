"""Comprehensive pytest tests for core views targeting coverage without cross-app violations."""

from decimal import Decimal

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model

from core.models import (
    OTP,
    AddOnPurchase,
    SubscriptionPlan,
    UsageLimit,
    UserSubscription,
)

User = get_user_model()
API_PREFIX = "/api"
PROPS_PREFIX = "/api/properties"


def _auth_client(user):
    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


# ===================================================================
# OTP Views
# ===================================================================


class TestSendOTPView:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(
            username="otp_user",
            email="otp@test.com",
            password="testpass123",
            full_name="OTP User",
            phone="+919999999999",
        )
        self.client = APIClient()

    def test_missing_phone_returns_400(self):
        response = self.client.post(
            f"{API_PREFIX}/auth/send-otp/", {}, content_type="application/json"
        )
        assert response.status_code == 400

    def test_success_returns_200(self):
        response = self.client.post(
            f"{API_PREFIX}/auth/send-otp/",
            {"phone": "+919999999999"},
            content_type="application/json",
        )
        assert response.status_code == 200


class TestOwnerVerifyOTP:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(
            username="owner_verify",
            email="ov@test.com",
            password="testpass123",
            full_name="Owner Verify",
            phone="+919999999999",
        )
        self.otp = OTP.objects.create(
            phone_number="+919999999999",
            code="123456",
            referral_code="",
        )
        self.client = APIClient()

    def test_invalid_code_returns_400(self):
        response = self.client.post(
            f"{API_PREFIX}/auth/owner/verify-otp/",
            {"phone": "+919999999999", "otp": "000000"},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_success_returns_200(self):
        response = self.client.post(
            f"{API_PREFIX}/auth/owner/verify-otp/",
            {"phone": "+919999999999", "otp": "123456"},
            content_type="application/json",
        )
        assert response.status_code == 200


class TestRenterVerifyOTP:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(
            username="renter_verify",
            email="rv@test.com",
            password="testpass123",
            full_name="Renter Verify",
            phone="+919999999999",
        )
        self.otp = OTP.objects.create(
            phone_number="+919999999999",
            code="654321",
            referral_code="",
        )
        self.client = APIClient()

    def test_success_returns_200(self):
        response = self.client.post(
            f"{API_PREFIX}/auth/renter/verify-otp/",
            {"phone": "+919999999999", "otp": "654321"},
            content_type="application/json",
        )
        assert response.status_code == 200


# ===================================================================
# ChangePasswordView
# ===================================================================


class TestChangePasswordView:
    @pytest.fixture(autouse=True)
    def setup(self, user):
        self.user = user
        self.client = _auth_client(user)

    def test_missing_fields_returns_400(self):
        response = self.client.post(
            f"{API_PREFIX}/change-password/",
            {},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_wrong_old_password_returns_400(self):
        response = self.client.post(
            f"{API_PREFIX}/change-password/",
            {"old_password": "wrongpass", "new_password": "newpass123"},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_same_password_returns_400(self):
        self.user.set_password("samepass")
        self.user.save()
        response = self.client.post(
            f"{API_PREFIX}/change-password/",
            {"old_password": "samepass", "new_password": "samepass"},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_success_returns_200(self):
        self.user.set_password("oldpass123")
        self.user.save()
        response = self.client.post(
            f"{API_PREFIX}/change-password/",
            {"old_password": "oldpass123", "new_password": "newpass456"},
            content_type="application/json",
        )
        assert response.status_code == 200
        self.user.refresh_from_db()
        assert self.user.check_password("newpass456")


# ===================================================================
# ResetPasswordView
# ===================================================================


class TestResetPasswordView:
    @pytest.fixture(autouse=True)
    def setup(self, user):
        self.user = user
        self.client = _auth_client(user)

    def test_missing_new_password_returns_400(self):
        response = self.client.post(
            f"{API_PREFIX}/reset-password/", {}, content_type="application/json"
        )
        assert response.status_code == 400

    def test_success_returns_200(self):
        response = self.client.post(
            f"{API_PREFIX}/reset-password/",
            {"new_password": "resetpass123"},
            content_type="application/json",
        )
        assert response.status_code == 200
        self.user.refresh_from_db()
        assert self.user.check_password("resetpass123")


# ===================================================================
# SubscriptionPlanViewSet
# ===================================================================


class TestSubscriptionPlanViewSet:
    def test_list_plans(self, db):
        SubscriptionPlan.objects.all().delete()
        SubscriptionPlan.objects.create(
            name="test_plan",
            monthly_price=Decimal("9.99"),
            yearly_price=Decimal("99.99"),
            features="Test",
        )
        client = APIClient()
        response = client.get(f"{API_PREFIX}/subscription-plans/")
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_retrieve_plan(self, db):
        plan = SubscriptionPlan.objects.create(
            name="retrieve_plan",
            monthly_price=Decimal("19.99"),
            yearly_price=Decimal("199.99"),
            features="Retrieve",
        )
        client = APIClient()
        response = client.get(f"{API_PREFIX}/subscription-plans/{plan.id}/")
        assert response.status_code == 200
        assert response.data["name"] == "retrieve_plan"


# ===================================================================
# UserSubscriptionViewSet
# ===================================================================


class TestUserSubscriptionViewSet:
    def test_anonymous_returns_401(self, db):
        client = APIClient()
        response = client.get(f"{API_PREFIX}/user-subscriptions/")
        assert response.status_code == 401

    def test_list_own_subscriptions(self, user, plan_pro):
        UserSubscription.objects.create(user=user, plan=plan_pro, is_active=True)
        client = _auth_client(user)
        response = client.get(f"{API_PREFIX}/user-subscriptions/")
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_create_subscription(self, user, plan_pro):
        client = _auth_client(user)
        response = client.post(
            f"{API_PREFIX}/user-subscriptions/",
            {"plan": plan_pro.id},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["user"] == user.id

    def test_update_own_subscription(self, user, plan_pro, plan_free):
        sub = UserSubscription.objects.create(user=user, plan=plan_pro, is_active=True)
        client = _auth_client(user)
        response = client.patch(
            f"{API_PREFIX}/user-subscriptions/{sub.id}/",
            {"is_active": False},
            format="json",
        )
        assert response.status_code == 200

    def test_delete_own_subscription(self, user, plan_pro):
        sub = UserSubscription.objects.create(user=user, plan=plan_pro, is_active=True)
        client = _auth_client(user)
        response = client.delete(f"{API_PREFIX}/user-subscriptions/{sub.id}/")
        assert response.status_code == 204


# ===================================================================
# AddOnPurchaseViewSet
# ===================================================================


class TestAddOnPurchaseViewSet:
    def test_anonymous_returns_401(self, db):
        client = APIClient()
        response = client.get(f"{API_PREFIX}/addon-purchases/")
        assert response.status_code == 401

    def test_list_own_purchases(self, user):
        AddOnPurchase.objects.create(
            user=user, name="max_buildings", amount=Decimal("29.99")
        )
        client = _auth_client(user)
        response = client.get(f"{API_PREFIX}/addon-purchases/")
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_create_addon(self, user):
        client = _auth_client(user)
        response = client.post(
            f"{API_PREFIX}/addon-purchases/",
            {"name": "max_units", "amount": "49.99"},
            format="json",
        )
        assert response.status_code == 201

    def test_update_own_purchase(self, user):
        purchase = AddOnPurchase.objects.create(
            user=user, name="max_buildings", amount=Decimal("29.99")
        )
        client = _auth_client(user)
        response = client.patch(
            f"{API_PREFIX}/addon-purchases/{purchase.id}/",
            {"amount": "39.99"},
            format="json",
        )
        assert response.status_code == 200

    def test_delete_own_purchase(self, user):
        purchase = AddOnPurchase.objects.create(
            user=user, name="max_buildings", amount=Decimal("29.99")
        )
        client = _auth_client(user)
        response = client.delete(f"{API_PREFIX}/addon-purchases/{purchase.id}/")
        assert response.status_code == 204


# ===================================================================
# UsageLimitViewSet
# ===================================================================


class TestUsageLimitViewSet:
    def test_anonymous_returns_401(self, db):
        client = APIClient()
        response = client.get(f"{API_PREFIX}/usage-limits/")
        assert response.status_code == 401

    def test_list_own_limits(self, user):
        UsageLimit.objects.create(user=user, feature_key="max_units", usage_count=3)
        client = _auth_client(user)
        response = client.get(f"{API_PREFIX}/usage-limits/")
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["usage_count"] == 3
