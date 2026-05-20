from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch, MagicMock

from .models import Building, Unit, Renter, RentAgreementDraft
from rentsecure_be.services.leegality_service import send_agreement_for_signature

User = get_user_model()


class LeegalityServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner1", password="pass123", email="owner@example.com")
        self.building = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user
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
            unit_type=Unit.UnitType.FLAT
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Alice",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1)
        )
        self.draft_file = ContentFile(b"PDF content", name="draft.pdf")
        self.agreement = RentAgreementDraft.objects.create(
            user=self.user,
            renter=self.renter,
            unit=self.unit,
            file=self.draft_file
        )

    @override_settings(
        LEEGALITY_API_KEY="test-api-key",
        LEEGALITY_ORG_ID="test-org-id",
        LEEGALITY_TEMPLATE_ID="test-template-id"
    )
    @patch('rentsecure_be.services.leegality_service.requests.post')
    def test_send_agreement_for_signature_updates_leegality_id(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"document_id": "doc_123"}
        mock_post.return_value = mock_response

        response = send_agreement_for_signature(
            self.agreement,
            owner_email="owner@example.com",
            renter_email="renter@example.com"
        )

        self.assertEqual(response["document_id"], "doc_123")
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.leegality_document_id, "doc_123")

        mock_post.assert_called_once()
        called_args, called_kwargs = mock_post.call_args
        self.assertEqual(called_args[0], "https://sandbox.leegality.com/api/v3/document")
        payload = called_kwargs["json"]
        self.assertEqual(payload["template_id"], "test-template-id")
        self.assertEqual(payload["participants"][0]["email"], "owner@example.com")
        self.assertEqual(payload["participants"][1]["email"], "renter@example.com")
        self.assertEqual(payload["participants"][1]["identifier"], "RENTER")

    @override_settings(
        LEEGALITY_API_KEY="test-api-key",
        LEEGALITY_ORG_ID="test-org-id",
        LEEGALITY_TEMPLATE_ID=""
    )
    def test_send_agreement_for_signature_raises_when_template_id_missing(self):
        with self.assertRaises(ValueError):
            send_agreement_for_signature(
                self.agreement,
                owner_email="owner@example.com",
                renter_email="renter@example.com"
            )


class LeegalityWebhookTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner1", password="pass123", email="owner@example.com")
        self.building = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user
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
            unit_type=Unit.UnitType.FLAT
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Alice",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1)
        )
        self.agreement = RentAgreementDraft.objects.create(
            user=self.user,
            renter=self.renter,
            unit=self.unit,
            file=ContentFile(b"PDF content", name="draft.pdf"),
            leegality_document_id="doc_abc"
        )
        self.client = APIClient()

    def test_leegality_webhook_marks_owner_signed(self):
        response = self.client.post(
            '/api/leegality/webhook/',
            {
                'document_id': 'doc_abc',
                'status': 'SIGNED',
                'participant': 'OWNER'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.agreement.refresh_from_db()
        self.assertTrue(self.agreement.owner_signed)
        self.assertFalse(self.agreement.renter_signed)

    def test_leegality_webhook_marks_renter_signed(self):
        response = self.client.post(
            '/api/leegality/webhook/',
            {
                'document_id': 'doc_abc',
                'status': 'SIGNED',
                'participant': 'RENTER'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.agreement.refresh_from_db()
        self.assertFalse(self.agreement.owner_signed)
        self.assertTrue(self.agreement.renter_signed)

    def test_leegality_webhook_marks_both_signed_for_unknown_participant(self):
        response = self.client.post(
            '/api/leegality/webhook/',
            {
                'document_id': 'doc_abc',
                'status': 'SIGNED',
                'participant': 'OTHER'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.agreement.refresh_from_db()
        self.assertTrue(self.agreement.owner_signed)
        self.assertTrue(self.agreement.renter_signed)

    def test_leegality_webhook_rejects_get_method(self):
        response = self.client.get('/api/leegality/webhook/')
        self.assertEqual(response.status_code, 405)
