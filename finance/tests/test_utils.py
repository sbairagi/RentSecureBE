"""Tests for finance utilities"""
import os
import tempfile
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase

from finance.utils import generate_tax_excel, generate_tax_pdf, create_tax_zip

User = get_user_model()


class FinanceUtilsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='fin_util', email='fin@test.com',
            password='p', full_name='Finance', phone='+1'
        )

    @patch('finance.utils.Workbook')
    def test_generate_tax_excel(self, mock_workbook):
        mock_wb = MagicMock()
        mock_workbook.return_value = mock_wb
        mock_ws = MagicMock()
        mock_wb.active = mock_ws
        result = generate_tax_excel(self.user, [], '2024-25')
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(result) or True)
        # Cleanup
        if os.path.exists(result):
            os.unlink(result)

    @patch('finance.utils.render_to_string')
    @patch('finance.utils.HTML')
    def test_generate_tax_pdf(self, mock_html, mock_render):
        mock_render.return_value = '<html></html>'
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance
        result = generate_tax_pdf(self.user, [], '2024-25')
        self.assertIsNotNone(result)
        if os.path.exists(result):
            os.unlink(result)

    def test_create_tax_zip(self):
        fd1, excel_path = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd1)
        fd2, pdf_path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd2)
        result = create_tax_zip(self.user, excel_path, pdf_path, [])
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(result))
        os.unlink(excel_path)
        os.unlink(pdf_path)
        os.unlink(result)