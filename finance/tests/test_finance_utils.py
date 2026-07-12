"""Comprehensive tests for finance/utils.py targeting uncovered branches.

Coverage target: >= 95%.
Uncovered lines in finance/utils.py:
  - 47  : RuntimeError when ``wb.active`` is None
  - 61–64: renter is None / hasattr(p, "renter") falsy branch emits "—"
  - 127 : falsy value in ``extra_docs`` is skipped
  - 130–131: doc path exists on disk but is None / missing file — skipped
"""

import os
import tempfile
import zipfile
from unittest.mock import MagicMock, patch

from django.core.files import File
from django.test import TestCase

from core.models import SubscriptionPlan, UserSubscription
from finance.utils import create_tax_zip, generate_tax_excel, generate_tax_pdf
from properties.models import Building, Renter, Unit


def _make_unit_without_renter(owner):
    """Create a Unit with no renter attached (vacant)."""
    Unit.objects.filter(owner=owner, unit="TEST-UN").delete()
    return Unit.objects.create(
        owner=owner,
        unit="TEST-UN",
        unit_type=Unit.UnitType.FLAT,
        address_line="Nowhere St",
        city="City",
        state="ST",
        country="IN",
        postal_code="000000",
        status=Unit.VacancyStatus.VACANT,
        is_vacant=True,
    )


def _make_unit_with_renter(user, renter_name="Renter One"):
    """Create an owner → unit with an attached Renter."""
    building = Building.objects.create(
        owner=user,
        name="Finance Test Building",
        address_line="Finance St",
        city="City",
        state="ST",
        country="IN",
        postal_code="000000",
    )
    unit = Unit.objects.create(
        owner=user,
        building=building,
        unit="TEST-RENT-UN",
        address_line="Finance St",
        city="City",
        state="ST",
        country="IN",
        postal_code="000000",
    )
    Renter.objects.create(
        unit=unit,
        name=renter_name,
        phone="+10000000001",
        email="renter@test.com",
        start_date="2024-01-01",
        status=Renter.RenterStatus.ACTIVE,
    )
    return unit


class FinanceUtilsComprehensiveTest(TestCase):
    """Covers the previously uncovered branches."""

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------

    def setUp(self):
        from django.contrib.auth import get_user_model

        user = get_user_model()
        self.user = user.objects.create_user(
            username="cov_fin_util",
            email="cov@test.com",
            password="p",
            full_name="Coverage Finance",
            phone="+110000000000",
        )
        plan = SubscriptionPlan.objects.create(
            name="pro",
            monthly_price=29,
            yearly_price=290,
            features="all",
            is_active=True,
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)

    # ------------------------------------------------------------------
    # Line 47 – RuntimeError when wb.active is None
    # ------------------------------------------------------------------

    @patch("finance.utils.Workbook")
    def test_generate_tax_excel_workbook_raises_runtime_error(self, mock_workbook):
        mock_wb = MagicMock()
        mock_wb.active = None  # simulate failure
        mock_workbook.return_value = mock_wb

        with self.assertRaises(RuntimeError) as ctx:
            generate_tax_excel(self.user, [], "2024-25")
        self.assertIn("Failed to create active worksheet", str(ctx.exception))

    # ------------------------------------------------------------------
    # Line 47 – happy path workbook active is truthy (coverage of the
    # ``if ws is not None`` True-branch continuation)
    # ------------------------------------------------------------------

    @patch("finance.utils.Workbook")
    def test_generate_tax_excel_workbook_active_truthy(self, mock_workbook):
        mock_wb = MagicMock()
        # active must be truthy for normal flow
        mock_wb.active = MagicMock()
        mock_workbook.return_value = mock_wb

        building = Building.objects.create(
            owner=self.user,
            name="Finance Test Bldg",
            address_line="Finance St",
            city="City",
            state="ST",
            country="IN",
            postal_code="000000",
        )
        unit = Unit.objects.create(
            owner=self.user,
            building=building,
            unit="TEST-UNIT-1",
            address_line="Finance St",
            city="City",
            state="ST",
            country="IN",
            postal_code="000000",
        )

        path = generate_tax_excel(self.user, [unit], "2024-25")
        self.assertTrue(path.endswith(".xlsx"))
        self.assertTrue(os.path.exists(path))
        os.unlink(path)

    # ------------------------------------------------------------------
    # Lines 61–64 – unit has NO renter (or attribute absent) => "—"
    # ------------------------------------------------------------------

    @patch("finance.utils.Workbook")
    def test_generate_tax_excel_vacant_unit_yields_em_dash(self, mock_workbook):
        mock_wb = MagicMock()
        mock_wb.active = MagicMock()
        mock_workbook.return_value = mock_wb

        unit = _make_unit_without_renter(self.user)

        path = generate_tax_excel(self.user, [unit], "2024-25")
        # ws.append must have been called with the em-dash placeholder
        append_calls = mock_wb.active.append.call_args_list
        data_row = append_calls[-1][0][0]  # last row appended
        self.assertEqual(data_row[2], "—")
        if os.path.exists(path):
            os.unlink(path)

    # ------------------------------------------------------------------
    # Line 127 – falsy doc in extra_docs is skipped via continue
    # ------------------------------------------------------------------

    def test_create_tax_zip_skips_falsy_doc(self):
        fd1, excel_path = tempfile.mkstemp(suffix=".xlsx")
        os.close(fd1)
        fd2, pdf_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd2)

        # Mix a None and a False among real docs — both must be skipped
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as extra:
            extra.write(b"extra data")
            extra_path = extra.name

        extra_docs = [None, extra_path, False]
        result = create_tax_zip(self.user, excel_path, pdf_path, extra_docs)

        self.assertTrue(os.path.exists(result))
        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()
            self.assertIn(os.path.basename(excel_path), names)
            self.assertIn(os.path.basename(pdf_path), names)
            self.assertIn(os.path.basename(extra_path), names)

        os.unlink(extra_path)
        os.unlink(excel_path)
        os.unlink(pdf_path)
        os.unlink(result)

    # ------------------------------------------------------------------
    # Lines 127–131 – doc path that does NOT exist on disk is skipped
    # ------------------------------------------------------------------

    def test_create_tax_zip_skips_nonexistent_doc_path(self):
        fd1, excel_path = tempfile.mkstemp(suffix=".xlsx")
        os.close(fd1)
        fd2, pdf_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd2)

        nonexistent = "/tmp/this_file_does_not_exist_xyz_999.txt"
        self.assertFalse(os.path.exists(nonexistent))

        extra_docs = [nonexistent]
        result = create_tax_zip(self.user, excel_path, pdf_path, extra_docs)

        self.assertTrue(os.path.exists(result))
        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()
            # nonexistent file must NOT appear
            self.assertNotIn(os.path.basename(nonexistent), names)
            # excel/pdf must still be there
            self.assertIn(os.path.basename(excel_path), names)
            self.assertIn(os.path.basename(pdf_path), names)

        os.unlink(excel_path)
        os.unlink(pdf_path)
        os.unlink(result)

    # ------------------------------------------------------------------
    # Line 131 – Django File object with existing path is included
    # ------------------------------------------------------------------

    def test_create_tax_zip_includes_django_file_with_path(self):
        fd1, excel_path = tempfile.mkstemp(suffix=".xlsx")
        os.close(fd1)
        fd2, pdf_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd2)

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as extra_file:
            extra_file.write(b"django file contents")
            extra_path = extra_file.name

        # Django File wraps a file descriptor; manually set ``path`` so
        # ``getattr(doc, "path", doc)`` returns the filesystem path.
        django_file = File(open(extra_path, "rb"), name=os.path.basename(extra_path))
        # Attach path directly because FieldFile/path may not be auto-set
        django_file.path = extra_path  # type: ignore[attr-defined]
        extra_docs = [django_file]
        try:
            result = create_tax_zip(self.user, excel_path, pdf_path, extra_docs)

            self.assertTrue(os.path.exists(result))
            with zipfile.ZipFile(result) as zf:
                self.assertIn(os.path.basename(extra_path), zf.namelist())
        finally:
            django_file.close()
            os.unlink(extra_path)
            os.unlink(excel_path)
            os.unlink(pdf_path)
            os.unlink(result)

    # ------------------------------------------------------------------
    # Empty extra_docs — zip should still be created correctly
    # ------------------------------------------------------------------

    def test_create_tax_zip_empty_extra_docs(self):
        fd1, excel_path = tempfile.mkstemp(suffix=".xlsx")
        os.close(fd1)
        fd2, pdf_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd2)

        result = create_tax_zip(self.user, excel_path, pdf_path, [])
        self.assertTrue(os.path.exists(result))
        with zipfile.ZipFile(result) as zf:
            self.assertEqual(
                sorted(zf.namelist()),
                sorted([os.path.basename(excel_path), os.path.basename(pdf_path)]),
            )

        os.unlink(excel_path)
        os.unlink(pdf_path)
        os.unlink(result)

    # ------------------------------------------------------------------
    # generate_tax_excel with list of units (not just QuerySet)
    # ------------------------------------------------------------------

    @patch("finance.utils.Workbook")
    def test_generate_tax_excel_accepts_list_units(self, mock_workbook):
        mock_wb = MagicMock()
        mock_wb.active = MagicMock()
        mock_workbook.return_value = mock_wb

        building = Building.objects.create(
            owner=self.user,
            name="Finance Test Bldg2",
            address_line="Finance St",
            city="City",
            state="ST",
            country="IN",
            postal_code="000000",
        )
        units = [
            Unit.objects.create(
                owner=self.user,
                building=building,
                unit=f"TEST-LIST-{i}",
                address_line="Finance St",
                city="City",
                state="ST",
                country="IN",
                postal_code="000000",
            )
            for i in range(2)
        ]
        units.append(_make_unit_without_renter(self.user))

        path = generate_tax_excel(self.user, units, "2024-25")
        # 3 data rows + 1 header
        self.assertEqual(mock_wb.active.append.call_count, 4)
        if os.path.exists(path):
            os.unlink(path)

    # ------------------------------------------------------------------
    # generate_tax_pdf happy path
    # ------------------------------------------------------------------

    @patch("finance.utils.render_to_string")
    @patch("finance.utils.HTML")
    def test_generate_tax_pdf_returns_pdf_path(self, mock_html_cls, mock_render):
        mock_render.return_value = "<html>tax</html>"
        mock_html_inst = MagicMock()
        mock_html_cls.return_value = mock_html_inst

        path = generate_tax_pdf(self.user, [], "2024-25")
        self.assertTrue(path.endswith(".pdf"))
        mock_html_inst.write_pdf.assert_called_once()
        if os.path.exists(path):
            os.unlink(path)

    # ------------------------------------------------------------------
    # generate_tax_excel – renter attribute present but renter is None
    # (testing getattr default branch)
    # ------------------------------------------------------------------

    @patch("finance.utils.Workbook")
    def test_generate_tax_excel_renter_none_yields_em_dash(self, mock_workbook):
        mock_wb = MagicMock()
        mock_wb.active = MagicMock()
        mock_workbook.return_value = mock_wb

        _make_unit_without_renter(self.user)

        # Delete FK-related "renter" property to simulate
        # hasattr returning True but getattr returning None
        # (Only the reverse FK case matters here — for a real DB unit
        # with no Renter the hasattr check passes via related manager
        # but renter attr itself is a descriptor, not None.  For coverage
        # we use a plain namespace object.)
        class FakeUnit:
            title = "Fake Unit"
            address_line = "Fake Street"
            renter = None

            def rent_income_for_fy(*a, **k):
                return 0

            def tax_paid_for_fy(*a, **k):
                return 0

            def net_income_for_fy(*a, **k):
                return 0

        path = generate_tax_excel(self.user, [FakeUnit()], "2024-25")
        data_row = mock_wb.active.append.call_args_list[-1][0][0]
        self.assertEqual(data_row[2], "—")
        if os.path.exists(path):
            os.unlink(path)
