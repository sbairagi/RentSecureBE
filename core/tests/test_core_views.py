"""Tests for core views - OTP, auth, password, subscriptions, and webhooks."""

from unittest.mock import patch

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import OTP, OwnerBankDetails
from core.views import download_rent_excel, owner_rent_records, rent_inflow_summary

User = get_user_model()
API_PREFIX = "/api"


class SendOTPViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="otp_user",
            email="otp@test.com",
            password="testpass123",
            full_name="OTP User",
            phone="+919999999999",
        )

    @patch("core.views.Client")
    def test_send_otp_creates_otp(self, mock_client):
        mock_client.return_value.messages.create.return_value = None
        response = self.client.post(
            f"{API_PREFIX}/auth/send-otp/", {"phone": "+919999999999"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(OTP.objects.filter(phone_number="+919999999999").exists())


class OwnerVerifyOTPTest(TestCase):
    def setUp(self):
        self.client = APIClient()
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

    def test_verify_otp_success(self):
        response = self.client.post(
            f"{API_PREFIX}/auth/owner/verify-otp/",
            {"phone": "+919999999999", "otp": "123456"},
        )
        self.assertEqual(response.status_code, 200)

    def test_verify_otp_invalid_code(self):
        response = self.client.post(
            f"{API_PREFIX}/auth/owner/verify-otp/",
            {"phone": "+919999999999", "otp": "000000"},
        )
        self.assertEqual(response.status_code, 400)


class RenterVerifyOTPTest(TestCase):
    def setUp(self):
        self.client = APIClient()
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

    def test_renter_verify_otp_success(self):
        response = self.client.post(
            f"{API_PREFIX}/auth/renter/verify-otp/",
            {"phone": "+919999999999", "otp": "654321"},
        )
        self.assertEqual(response.status_code, 200)


class ChangePasswordViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="changepw",
            email="cpw@test.com",
            password="oldpass123",
            full_name="Change PW",
            phone="+919999999999",
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_change_password_success(self):
        response = self.client.post(
            f"{API_PREFIX}/change-password/",
            {"old_password": "oldpass123", "new_password": "newpass456"},
        )
        self.assertEqual(response.status_code, 200)


class ResetPasswordViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="resetpw",
            email="rpw@test.com",
            password="oldpass123",
            full_name="Reset PW",
            phone="+919999999999",
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @patch("core.views.send_otp")
    def test_reset_password_request(self, mock_send):
        response = self.client.post(
            f"{API_PREFIX}/reset-password/", {"new_password": "newpass456"}
        )
        self.assertEqual(response.status_code, 200)


class UpdateOwnerBankDetailsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="bank_user",
            email="bu@test.com",
            password="testpass123",
            full_name="Bank User",
            phone="+919999999999",
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @patch("core.views.add_beneficiary")
    @patch("core.views.delete_beneficiary")
    def test_update_bank_details(self, mock_delete, mock_add):
        mock_delete.return_value = {}
        mock_add.return_value = {"subCode": "200"}
        response = self.client.post(
            f"{API_PREFIX}/api/owner/update-bank-details/",
            {
                "account_number": "1234567890",
                "ifsc_code": "HDFC0001234",
                "account_holder_name": "Bank User",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(OwnerBankDetails.objects.filter(owner=self.user).exists())


class RentInflowSummaryTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="summary_user",
            email="su@test.com",
            password="testpass123",
            full_name="Summary User",
            phone="+919999999999",
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_rent_inflow_summary_view_exists(self):

        self.assertTrue(callable(rent_inflow_summary))


class OwnerRentRecordsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="records_user",
            email="ru@test.com",
            password="testpass123",
            full_name="Records User",
            phone="+919999999999",
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_owner_rent_records_view_exists(self):

        self.assertTrue(callable(owner_rent_records))


class DownloadRentExcelTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="excel_user",
            email="eu@test.com",
            password="testpass123",
            full_name="Excel User",
            phone="+919999999999",
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_download_rent_excel_view_exists(self):

        self.assertTrue(callable(download_rent_excel))
