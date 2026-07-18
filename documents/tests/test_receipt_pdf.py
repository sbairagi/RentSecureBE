"""Tests for documents views - GenerateRentReceiptPdfViewSet."""

from unittest.mock import MagicMock, patch

from rest_framework.test import APIRequestFactory, force_authenticate

from django.contrib.auth import get_user_model
from django.test import TestCase

from documents.views import GenerateRentReceiptPdfViewSet

User = get_user_model()


class GenerateRentReceiptPdfViewSetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="receipt_user",
            email="receipt@test.com",
            password="p",
            full_name="Receipt User",
            phone="+1",
        )

    def _make_request(self, pk=None, user=None):
        request = self.factory.get(f"/api/document/rent_receipt/{pk or 1}/pdf_receipt/")
        if user is not None:
            force_authenticate(request, user=user)
        return request

    @patch("documents.views.render_to_string")
    @patch("weasyprint.HTML")
    def test_pdf_receipt_success(self, mock_html, mock_render):
        mock_render.return_value = "<html></html>"
        mock_html_instance = MagicMock()
        mock_html_instance.write_pdf.return_value = b"PDF content"
        mock_html.return_value = mock_html_instance
        request = self._make_request(pk=1, user=self.user)
        view = GenerateRentReceiptPdfViewSet.as_view({"get": "pdf_receipt"})
        mock_rent = MagicMock()
        mock_rent.id = 1
        with patch.object(
            GenerateRentReceiptPdfViewSet, "get_object", return_value=mock_rent
        ):
            response = view(request, pk=1)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "application/pdf")
