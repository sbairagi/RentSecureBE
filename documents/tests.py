"""Tests for documents app"""

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from documents.utils import generate_unit_history_pdf
from documents.views import (
    GenerateRentAgreementPdfViewSet,
    GenerateUnitDossierPdfViewSet,
    download_unit_history,
)

User = get_user_model()


class GenerateRentAgreementPdfViewSetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="doc_user",
            email="doc@test.com",
            password="p",
            full_name="Doc User",
            phone="+1",
        )

    @patch("documents.views.render_to_string")
    @patch("weasyprint.HTML")
    def test_generate_rent_agreement_pdf_not_found(self, mock_html, mock_render):
        viewset = GenerateRentAgreementPdfViewSet()
        viewset.request = MagicMock()
        viewset.request.user = self.user
        viewset.kwargs = {"pk": 999}
        response = viewset.generate_rent_agreement_pdf(request=viewset.request, pk=999)
        self.assertEqual(response.status_code, 404)

    @patch("documents.views.Renter")
    @patch("documents.views.render_to_string")
    @patch("weasyprint.HTML")
    def test_generate_rent_agreement_pdf_success(
        self, mock_html, mock_render, mock_renter
    ):
        mock_renter_instance = MagicMock()
        mock_renter_instance.unit.owner = MagicMock()
        mock_renter.objects.select_related.return_value.get.return_value = (
            mock_renter_instance
        )
        mock_render.return_value = "<html></html>"
        mock_html_instance = MagicMock()
        mock_html_instance.write_pdf.return_value = b"PDF content"
        mock_html.return_value = mock_html_instance
        viewset = GenerateRentAgreementPdfViewSet()
        viewset.request = MagicMock()
        viewset.request.user = self.user
        viewset.kwargs = {"pk": 1}
        response = viewset.generate_rent_agreement_pdf(request=viewset.request, pk=1)
        self.assertEqual(response.status_code, 200)


class GenerateUnitHistoryPdfTest(TestCase):
    @patch("documents.utils.render_to_string")
    @patch("weasyprint.HTML")
    @patch("documents.utils.PdfWriter")
    def test_generate_unit_history_pdf(self, _mock_writer, mock_html, mock_render):
        mock_unit = MagicMock()
        mock_unit.renters.all.return_value = []
        mock_render.return_value = "<html></html>"
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance
        result = generate_unit_history_pdf(mock_unit)
        self.assertIsNotNone(result)


class GenerateUnitDossierPdfViewSetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dossier_user",
            email="du@test.com",
            password="p",
            full_name="Dossier User",
            phone="+1",
        )

    @patch("documents.views.render_to_string")
    @patch("weasyprint.HTML")
    def test_generate_dossier_pdf_success(self, mock_html, mock_render):
        mock_render.return_value = "<html></html>"
        mock_html_instance = MagicMock()
        mock_html_instance.write_pdf.return_value = b"PDF content"
        mock_html.return_value = mock_html_instance
        viewset = GenerateUnitDossierPdfViewSet()
        viewset.request = MagicMock()
        viewset.request.user = self.user
        viewset.kwargs = {"pk": 1}
        with patch("documents.views.get_object_or_404") as mock_get:
            mock_unit = MagicMock()
            mock_unit.caretakers.all.return_value = []
            mock_unit.renters.all.return_value = []
            mock_unit.tax_records.all.return_value = []
            mock_get.return_value = mock_unit
            response = viewset.generate_dossier_pdf(request=viewset.request, pk=1)
            self.assertEqual(response.status_code, 200)


class DownloadUnitHistoryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="hist_user",
            email="hu@test.com",
            password="p",
            full_name="Hist User",
            phone="+1",
        )

    @patch("documents.views.generate_unit_history_pdf")
    def test_download_unit_history_success(self, mock_gen):
        mock_gen.return_value = b"PDF content"
        mock_unit = MagicMock()
        with patch("documents.views.Unit") as mock_unit_cls:
            mock_unit_cls.objects.get.return_value = mock_unit
            from django.http import HttpRequest

            request = HttpRequest()
            request.user = self.user
            response = download_unit_history(request, unit_id=1)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "application/pdf")
