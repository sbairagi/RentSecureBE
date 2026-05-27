"""Tests for documents app"""
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase

from documents.views import GenerateRentAgreementPdfViewSet, GenerateUnitDossierPdfViewSet
from documents.utils import generate_unit_history_pdf

User = get_user_model()


class GenerateRentAgreementPdfViewSetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='doc_user', email='doc@test.com',
            password='p', full_name='Doc User', phone='+1'
        )

    @patch('documents.views.render_to_string')
    @patch('documents.views.HTML')
    def test_generate_rent_agreement_pdf_not_found(self, mock_html, mock_render):
        viewset = GenerateRentAgreementPdfViewSet()
        viewset.request = MagicMock()
        viewset.request.user = self.user
        viewset.kwargs = {'pk': 999}
        response = viewset.generate_rent_agreement_pdf(request=viewset.request, pk=999)
        self.assertEqual(response.status_code, 404)

    @patch('documents.views.Renter')
    @patch('documents.views.render_to_string')
    @patch('documents.views.HTML')
    def test_generate_rent_agreement_pdf_success(self, mock_html, mock_render, mock_renter):
        mock_renter_instance = MagicMock()
        mock_renter_instance.unit.owner = MagicMock()
        mock_renter.objects.select_related.return_value.get.return_value = mock_renter_instance
        mock_render.return_value = '<html></html>'
        mock_html_instance = MagicMock()
        mock_html_instance.write_pdf.return_value = b'PDF content'
        mock_html.return_value = mock_html_instance
        viewset = GenerateRentAgreementPdfViewSet()
        viewset.request = MagicMock()
        viewset.request.user = self.user
        viewset.kwargs = {'pk': 1}
        response = viewset.generate_rent_agreement_pdf(request=viewset.request, pk=1)
        self.assertEqual(response.status_code, 200)


class GenerateUnitHistoryPdfTest(TestCase):
    @patch('documents.utils.render_to_string')
    @patch('documents.utils.HTML')
    @patch('documents.utils.PdfMerger')
    def test_generate_unit_history_pdf(self, mock_merger, mock_html, mock_render):
        mock_unit = MagicMock()
        mock_unit.renters.all.return_value = []
        mock_render.return_value = '<html></html>'
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance
        result = generate_unit_history_pdf(mock_unit)
        self.assertIsNotNone(result)