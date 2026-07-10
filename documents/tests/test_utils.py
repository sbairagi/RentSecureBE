"""Tests for documents/utils.py — PDF generation and merging utilities."""

import os
import tempfile
from unittest.mock import MagicMock, patch

from django.test import TestCase

from documents.utils import (
    _build_pdf_context,
    _collect_agreement_paths,
    _get_tax_records,
    _merge_pdfs,
    _read_pdf_if_exists,
)


class ReadPdfIfExistsTests(TestCase):
    def test_returns_empty_for_none_path(self):
        self.assertEqual(_read_pdf_if_exists(None), b"")

    def test_returns_empty_for_missing_file(self):
        self.assertEqual(_read_pdf_if_exists("/nonexistent/path.pdf"), b"")

    def test_returns_bytes_for_existing_file(self):
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        with open(path, "wb") as f:
            f.write(b"%PDF-1.4 fake pdf content")
        try:
            result = _read_pdf_if_exists(path)
            self.assertEqual(result, b"%PDF-1.4 fake pdf content")
        finally:
            os.unlink(path)


class GetTaxRecordsTests(TestCase):
    def test_returns_empty_when_no_related(self):
        class FakeUnit:
            pass

        self.assertEqual(_get_tax_records(FakeUnit()), [])

    def test_returns_queryset_when_unittaxrecord_set_exists(self):
        qs = MagicMock()
        unit = MagicMock()
        unit.unittaxrecord_set.all.return_value = qs
        result = _get_tax_records(unit)
        self.assertEqual(result, qs)

    def test_returns_queryset_when_tax_records_related_name_exists(self):
        qs = MagicMock()
        unit = MagicMock()
        del unit.unittaxrecord_set
        unit.tax_records = qs
        result = _get_tax_records(unit)
        self.assertEqual(result, qs)


class BuildPdfContextTests(TestCase):
    def test_builds_context_with_unit_data(self):
        unit = MagicMock()
        unit.owner = MagicMock()
        unit.caretakers.all.return_value = []
        unit.renters.all.return_value = []
        context = _build_pdf_context(unit)
        self.assertIn("unit", context)
        self.assertIn("owner", context)
        self.assertIn("caretakers", context)
        self.assertIn("renters", context)
        self.assertIn("tax_records", context)


class CollectAgreementPathsTests(TestCase):
    def test_returns_empty_when_no_renters(self):
        unit = MagicMock()
        unit.renters.all.return_value = []
        result = _collect_agreement_paths(unit)
        self.assertEqual(result, [])

    def test_returns_paths_for_signed_drafts(self):
        renter = MagicMock()
        unit = MagicMock()
        unit.renters.all.return_value = [renter]
        draft = MagicMock()
        draft.file.path = "/tmp/draft.pdf"
        draft.file.__bool__ = lambda self: True
        draft.file.has_path = True
        with patch("documents.utils.RentAgreementDraft.objects.filter") as mock_filter:
            mock_filter.return_value = [draft]
            with patch("os.path.exists", return_value=True):
                result = _collect_agreement_paths(unit)
        self.assertIn("/tmp/draft.pdf", result)


class MergePdfsTests(TestCase):
    def test_merge_pdfs_returns_bytes(self):
        from pypdf import PdfWriter

        fd1, pdf1 = tempfile.mkstemp(suffix=".pdf")
        os.close(fd1)
        fd2, pdf2 = tempfile.mkstemp(suffix=".pdf")
        os.close(fd2)
        writer = PdfWriter()
        writer.add_blank_page(100, 100)
        with open(pdf1, "wb") as f:
            writer.write(f)
        writer2 = PdfWriter()
        writer2.add_blank_page(100, 100)
        with open(pdf2, "wb") as f:
            writer2.write(f)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                result = _merge_pdfs(pdf1, [pdf2], tmpdir)
                self.assertIsInstance(result, bytes)
                self.assertTrue(len(result) > 0)
        finally:
            os.unlink(pdf1)
            os.unlink(pdf2)
