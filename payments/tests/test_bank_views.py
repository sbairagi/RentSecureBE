"""Tests for payment bank views."""

from decimal import Decimal
from unittest.mock import patch

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import OwnerBankDetails
from payments.views.bank_views import create_rent_payment
from properties.models import Renter, RentRecord


def _auth_client(user):
    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


class TestCreateRentPayment:
    def test_invalid_method_returns_405(self):
        from django.test import RequestFactory

        factory = RequestFactory()
        req = factory.get("/test")
        response = create_rent_payment(req)
        assert response.status_code == 405

    def test_rent_not_found_returns_404(self):
        from django.test import RequestFactory

        factory = RequestFactory()
        req = factory.post(
            "/test",
            data=b'{"rent_id": "9999"}',
            content_type="application/json",
        )
        req._body = b'{"rent_id": "9999"}'
        response = create_rent_payment(req)
        assert response.status_code == 404

    @patch("payments.adapters.razorpay.client")
    def test_success_creates_order(self, mock_client, owner, building, unit):
        import json

        from django.test import RequestFactory

        renter = Renter.objects.create(
            unit=unit,
            name="Test Renter",
            phone="+919876543210",
            email="renter@test.com",
            rent_amount=10000,
            start_date="2025-01-01",
        )
        mock_client.order.create.return_value = {
            "id": "order_123",
            "amount": 100000,
            "currency": "INR",
        }

        rent = RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PENDING",
            due_date="2025-01-05",
        )
        factory = RequestFactory()
        req = factory.post(
            "/test",
            data=json.dumps({"rent_id": str(rent.id)}),
            content_type="application/json",
        )
        req._body = json.dumps({"rent_id": str(rent.id)}).encode()
        response = create_rent_payment(req)
        assert response.status_code == 200
        content = json.loads(response.content)
        assert content["order_id"] == "order_123"
        rent.refresh_from_db()
        assert rent.razorpay_order_id == "order_123"


class TestUpdateOwnerBankDetails:
    def test_missing_fields_returns_400(self, user):
        client = _auth_client(user)
        response = client.post(
            "/api/owner/update-bank-details/",
            {},
            format="json",
        )
        assert response.status_code == 400

    @patch("payments.services.bank_details_service.add_beneficiary")
    @patch("payments.services.payment_service.PaymentService.delete_beneficiary")
    def test_existing_bank_with_beneficiary_deletes_first(
        self, mock_delete, mock_add, user
    ):
        OwnerBankDetails.objects.create(
            owner=user,
            bank_account_number="1234567890",
            ifsc_code="HDFC0001234",
            account_holder_name="Test User",
            beneficiary_id="BENE_OLD",
        )
        mock_delete.return_value = {}
        mock_add.return_value = {"subCode": "200"}
        client = _auth_client(user)
        response = client.post(
            "/api/owner/update-bank-details/",
            {
                "account_number": "9999999999",
                "ifsc_code": "HDFC0009999",
                "account_holder_name": "Test User",
            },
            format="json",
        )
        assert response.status_code == 200
        mock_delete.assert_called_once_with("BENE_OLD")

    @patch("payments.services.bank_details_service.add_beneficiary")
    def test_new_bank_creates_details(self, mock_add, user):
        mock_add.return_value = {"subCode": "200"}
        client = _auth_client(user)
        response = client.post(
            "/api/owner/update-bank-details/",
            {
                "account_number": "1234567890",
                "ifsc_code": "HDFC0001234",
                "account_holder_name": "Test User",
            },
            format="json",
        )
        assert response.status_code == 200
        assert OwnerBankDetails.objects.filter(owner=user).exists()

    @patch("payments.services.bank_details_service.add_beneficiary")
    def test_bank_registration_failure_returns_400(self, mock_add, user):
        mock_add.return_value = {"subCode": "400", "message": "Invalid bank"}
        client = _auth_client(user)
        response = client.post(
            "/api/owner/update-bank-details/",
            {
                "account_number": "1234567890",
                "ifsc_code": "HDFC0001234",
                "account_holder_name": "Test User",
            },
            format="json",
        )
        assert response.status_code == 400
        assert "error" in response.data
