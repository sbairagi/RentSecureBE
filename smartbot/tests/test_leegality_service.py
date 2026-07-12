"""Comprehensive tests for smartbot/services/leegality_service.py."""

from unittest.mock import MagicMock, mock_open, patch

from faker import Faker

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from properties.models import Building, Renter, Unit
from smartbot.services.leegality_service import (
    check_signature_status,
    initiate_signature,
)

fake = Faker()
User = get_user_model()


class LeegalityServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="leegality_owner",
            password="pass123",
            email="owner@example.com",
            full_name="Test Owner",
            phone="+919999999999",
        )
        self.building = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user,
        )
        self.unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="101",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT,
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Test Renter",
            email="renter@example.com",
            phone="+919876543210",
            start_date="2025-01-01",
            end_date="2026-01-01",
            rent_amount=10000,
            is_active=True,
            status=Renter.RenterStatus.ACTIVE,
        )
        self.file_path = "/tmp/test_agreement.pdf"
        self.signature_request_id = "sig_req_123"

    @override_settings(
        LEEGALITY_API_KEY="test-api-key",
        LEEGALITY_ORG_ID="test-org-id",
        LEEGALITY_WORKFLOW_ID="test-workflow-id",
    )
    @patch("smartbot.services.leegality_service.requests.post")
    def test_initiate_signature_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"documentId": "doc_123", "status": "SENT"}
        mock_post.return_value = mock_response

        m = mock_open(read_data=b"PDF content")
        with patch("builtins.open", m):
            result = initiate_signature(self.renter, self.file_path)

        self.assertEqual(result, {"documentId": "doc_123", "status": "SENT"})
        mock_post.assert_called_once()
        called_args, called_kwargs = mock_post.call_args
        self.assertEqual(called_args[0], "https://api.leegality.com/v3/document/upload")
        self.assertIn("X-API-KEY", called_kwargs["headers"])
        self.assertEqual(called_kwargs["headers"]["X-API-KEY"], "test-api-key")
        self.assertEqual(called_kwargs["headers"]["X-ORG-ID"], "test-org-id")
        self.assertIn("data", called_kwargs)
        parsed_data = __import__("json").loads(called_kwargs["data"]["data"])
        self.assertEqual(parsed_data["recipients"][0]["name"], "Test Renter")
        self.assertEqual(parsed_data["recipients"][0]["email"], "renter@example.com")
        self.assertEqual(parsed_data["recipients"][0]["phone"], "+919876543210")
        self.assertEqual(parsed_data["recipients"][0]["workflowId"], "test-workflow-id")
        self.assertTrue(parsed_data["sendNow"])

    @override_settings(
        LEEGALITY_API_KEY="test-api-key",
        LEEGALITY_ORG_ID="test-org-id",
        LEEGALITY_WORKFLOW_ID="test-workflow-id",
    )
    @patch("smartbot.services.leegality_service.requests.post")
    def test_initiate_signature_renter_attributes_used(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"documentId": "doc_456"}
        mock_post.return_value = mock_response

        renter = Renter.objects.create(
            unit=self.unit,
            name="Jane Doe",
            email="jane@example.com",
            phone="+919111111111",
            start_date="2025-01-01",
            end_date="2026-01-01",
            rent_amount=10000,
            is_active=True,
            status=Renter.RenterStatus.ACTIVE,
        )

        m = mock_open(read_data=b"PDF content")
        with patch("builtins.open", m):
            result = initiate_signature(renter, self.file_path)

        called_kwargs = mock_post.call_args.kwargs
        parsed_data = __import__("json").loads(called_kwargs["data"]["data"])
        recipient = parsed_data["recipients"][0]
        self.assertEqual(recipient["name"], "Jane Doe")
        self.assertEqual(recipient["email"], "jane@example.com")
        self.assertEqual(recipient["phone"], "+919111111111")
        self.assertEqual(result, {"documentId": "doc_456"})

    @override_settings(
        LEEGALITY_API_KEY="test-api-key",
        LEEGALITY_ORG_ID="test-org-id",
    )
    @patch("smartbot.services.leegality_service.requests.get")
    def test_check_signature_status_success_with_status_key(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "SIGNED", "documentId": "doc_123"}
        mock_get.return_value = mock_response

        result = check_signature_status(self.signature_request_id)

        self.assertEqual(result, "SIGNED")
        mock_get.assert_called_once_with(
            f"https://api.leegality.com/v3/document/{self.signature_request_id}",
            headers={
                "X-API-KEY": "test-api-key",
                "X-ORG-ID": "test-org-id",
            },
            timeout=10,
        )
        mock_response.raise_for_status.assert_called_once()

    @override_settings(
        LEEGALITY_API_KEY="test-api-key",
        LEEGALITY_ORG_ID="test-org-id",
    )
    @patch("smartbot.services.leegality_service.requests.get")
    def test_check_signature_status_success_with_document_status_key(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "documentStatus": "COMPLETED",
            "documentId": "doc_456",
        }
        mock_get.return_value = mock_response

        result = check_signature_status(self.signature_request_id)

        self.assertEqual(result, "COMPLETED")
        mock_response.raise_for_status.assert_called_once()

    @override_settings(
        LEEGALITY_API_KEY="test-api-key",
        LEEGALITY_ORG_ID="test-org-id",
    )
    @patch("smartbot.services.leegality_service.requests.get")
    def test_check_signature_status_prefers_status_over_document_status(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "SIGNED",
            "documentStatus": "COMPLETED",
        }
        mock_get.return_value = mock_response

        result = check_signature_status(self.signature_request_id)

        self.assertEqual(result, "SIGNED")

    @override_settings(
        LEEGALITY_API_KEY="test-api-key",
        LEEGALITY_ORG_ID="test-org-id",
    )
    @patch("smartbot.services.leegality_service.requests.get")
    def test_check_signature_status_returns_none_when_no_status(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"documentId": "doc_789"}
        mock_get.return_value = mock_response

        result = check_signature_status(self.signature_request_id)

        self.assertIsNone(result)

    @override_settings(
        LEEGALITY_API_KEY="test-api-key",
        LEEGALITY_ORG_ID="test-org-id",
    )
    @patch("smartbot.services.leegality_service.requests.get")
    def test_check_signature_status_returns_none_for_empty_status(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": None, "documentStatus": None}
        mock_get.return_value = mock_response

        result = check_signature_status(self.signature_request_id)

        self.assertIsNone(result)

    @override_settings(
        LEEGALITY_API_KEY="test-api-key",
        LEEGALITY_ORG_ID="test-org-id",
    )
    @patch("smartbot.services.leegality_service.requests.get")
    def test_check_signature_status_returns_empty_string_for_empty_status(
        self, mock_get
    ):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "", "documentStatus": ""}
        mock_get.return_value = mock_response

        result = check_signature_status(self.signature_request_id)

        self.assertEqual(result, "")

    @override_settings(
        LEEGALITY_API_KEY="test-api-key",
        LEEGALITY_ORG_ID="test-org-id",
    )
    @patch("smartbot.services.leegality_service.requests.get")
    def test_check_signature_status_http_error_raises(self, mock_get):
        import requests as req

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = req.exceptions.HTTPError(
            "404 Not Found"
        )
        mock_get.return_value = mock_response

        with self.assertRaises(req.exceptions.HTTPError):
            check_signature_status(self.signature_request_id)

    @override_settings(
        LEEGALITY_API_KEY="test-api-key",
        LEEGALITY_ORG_ID="test-org-id",
    )
    @patch("smartbot.services.leegality_service.requests.get")
    def test_check_signature_status_converts_numeric_status_to_string(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": 2}
        mock_get.return_value = mock_response

        result = check_signature_status(self.signature_request_id)

        self.assertEqual(result, "2")
