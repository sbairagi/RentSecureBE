"""
E2E Flow: Authentication

Tests the complete authentication lifecycle:
- OTP send/verify
- Login
- Token refresh
- Logout
- Session expiry
- Unauthorized access
- Multi-role authentication
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone

from core.models import OTP, SubscriptionPlan, UserSubscription
from tests.test_e2e_flows import OWNER_USERNAME, RENTER_USERNAME, E2EAPIClientMixin

User = get_user_model()
API_PREFIX = "/api"


class AuthenticationE2EFlowTests(E2EAPIClientMixin, APITestCase):
    """End-to-end authentication flow tests."""

    def setUp(self):
        self.client = APIClient()
        self.owner = self._create_owner_with_subscription(OWNER_USERNAME)
        self.renter_user = self._create_renter_user(RENTER_USERNAME)
        self._ensure_group(self.renter_user, "renter")
        self.unauthenticated_client = APIClient()

    # ------------------------------------------------------------------
    # OTP Flow
    # ------------------------------------------------------------------

    @override_settings(DEBUG=True)
    def test_send_otp_owner_flow(self):
        response = self.client.post(
            f"{API_PREFIX}/auth/send-otp/",
            {"phone": "+911234567890"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

    @override_settings(DEBUG=True)
    def test_verify_otp_owner_flow(self):
        _otp = OTP.objects.create(
            phone_number="+911234567891", code="123456", referral_code=""
        )
        response = self.client.post(
            f"{API_PREFIX}/auth/owner/verify-otp/",
            {"phone": "+911234567891", "otp": "123456"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)
        access_token = response.data["access"]
        self.assertTrue(access_token)

    @override_settings(DEBUG=True)
    def test_verify_otp_renter_flow(self):
        _otp = OTP.objects.create(
            phone_number="+911234567892", code="654321", referral_code=""
        )
        response = self.client.post(
            f"{API_PREFIX}/auth/renter/verify-otp/",
            {"phone": "+911234567892", "otp": "654321"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("user", response.data)

    def test_verify_otp_invalid_otp(self):
        response = self.client.post(
            f"{API_PREFIX}/auth/owner/verify-otp/",
            {"phone": "+911234567893", "otp": "000000"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_otp_missing_phone(self):
        response = self.client.post(f"{API_PREFIX}/auth/send-otp/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # Login Flow
    # ------------------------------------------------------------------

    def test_login_with_credentials(self):
        response = self.client.post(
            f"{API_PREFIX}/auth/login/",
            {"email": self.owner.email, "password": "TestPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid_credentials(self):
        response = self.client.post(
            f"{API_PREFIX}/auth/login/",
            {"email": self.owner.email, "password": "WrongPass"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_fields(self):
        response = self.client.post(f"{API_PREFIX}/auth/login/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # Protected endpoint access
    # ------------------------------------------------------------------

    def test_protected_endpoint_with_valid_token(self):
        token = self._get_access_token(self.owner)
        response = self._get_json(f"{API_PREFIX}/auth/profile/", token=token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["username"], self.owner.username)

    def test_protected_endpoint_without_token(self):
        response = self.client.get(f"{API_PREFIX}/auth/profile/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_with_invalid_token(self):
        response = self.client.get(
            f"{API_PREFIX}/auth/profile/",
            HTTP_AUTHORIZATION="Bearer invalidtoken12345",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ------------------------------------------------------------------
    # Token Refresh Flow
    # ------------------------------------------------------------------

    def test_token_refresh_flow(self):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(self.owner)
        response = self.client.post(
            f"{API_PREFIX}/token/refresh/",
            {"refresh": str(refresh)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_token_refresh_invalid_token(self):
        response = self.client.post(
            f"{API_PREFIX}/token/refresh/",
            {"refresh": "invalid-refresh-token"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ------------------------------------------------------------------
    # Logout Flow
    # ------------------------------------------------------------------

    def test_logout_blacklists_token(self):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(self.owner)
        token = str(refresh.access_token)
        response = self._post_json(
            f"{API_PREFIX}/auth/logout/",
            {"refresh": str(refresh)},
            token=token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Try using the refresh token again — should be blacklisted
        response2 = self.client.post(
            f"{API_PREFIX}/token/refresh/",
            {"refresh": str(refresh)},
            format="json",
        )
        self.assertEqual(response2.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_all_devices(self):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(self.owner)
        token = str(refresh.access_token)
        response = self._post_json(
            f"{API_PREFIX}/auth/logout-all/",
            token=token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Password change
    # ------------------------------------------------------------------

    def test_change_password_flow(self):
        token = self._get_access_token(self.owner)
        response = self._post_json(
            f"{API_PREFIX}/change-password/",
            {"old_password": "TestPass123!", "new_password": "NewPass456!"},
            token=token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.check_password("NewPass456!"))

    def test_change_password_wrong_old_password(self):
        token = self._get_access_token(self.owner)
        response = self._post_json(
            f"{API_PREFIX}/change-password/",
            {"old_password": "WrongOldPass", "new_password": "NewPass456!"},
            token=token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # Profile
    # ------------------------------------------------------------------

    def test_get_profile(self):
        token = self._get_access_token(self.owner)
        response = self._get_json(f"{API_PREFIX}/auth/profile/", token=token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["username"], self.owner.username)

    def test_update_profile(self):
        token = self._get_access_token(self.owner)
        response = self._patch_json(
            f"{API_PREFIX}/auth/profile/",
            {"full_name": "Updated E2E Owner"},
            token=token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.full_name, "Updated E2E Owner")

    # ------------------------------------------------------------------
    # Unauthorized access
    # ------------------------------------------------------------------

    def test_unauthenticated_access_denied(self):
        endpoints = [
            f"{API_PREFIX}/auth/profile/",
            f"{API_PREFIX}/buildings/",
            f"{API_PREFIX}/renters/",
            f"{API_PREFIX}/notifications/get/",
        ]
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                self.assertEqual(
                    response.status_code,
                    status.HTTP_401_UNAUTHORIZED,
                    msg=f"Expected 401 for {endpoint}",
                )

    # ------------------------------------------------------------------
    # Bootstrap endpoint
    # ------------------------------------------------------------------

    def test_bootstrap_authenticated(self):
        token = self._get_access_token(self.owner)
        response = self._get_json(f"{API_PREFIX}/auth/bootstrap/", token=token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)

    def test_bootstrap_unauthenticated(self):
        response = self.client.get(f"{API_PREFIX}/auth/bootstrap/")
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_200_OK],
        )


class MultiRoleAuthenticationTests(APITestCase):
    """Test authentication behavior across different roles."""

    def test_owner_can_access_owner_endpoints(self):
        owner = User.objects.create_user(
            username="role_owner", password="TestPass123!", email="role_owner@test.com"
        )
        plan, _ = SubscriptionPlan.objects.get_or_create(
            name="pro",
            defaults={
                "monthly_price": Decimal("29.99"),
                "yearly_price": Decimal("299.99"),
                "features": "Pro",
                "is_active": True,
            },
        )
        UserSubscription.objects.create(
            user=owner,
            plan=plan,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365),
            is_active=True,
        )
        token = str(
            __import__("rest_framework_simplejwt.tokens", fromlist=["RefreshToken"])
            .RefreshToken.for_user(owner)
            .access_token
        )
        response = self.client.get(
            f"{API_PREFIX}/owner/dashboard-summary/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_renter_cannot_access_owner_endpoints(self):
        renter_user = User.objects.create_user(
            username="role_renter",
            password="TestPass123!",
            email="role_renter@test.com",
        )
        token = str(
            __import__("rest_framework_simplejwt.tokens", fromlist=["RefreshToken"])
            .RefreshToken.for_user(renter_user)
            .access_token
        )
        response = self.client.get(
            f"{API_PREFIX}/owner/dashboard-summary/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED],
        )
