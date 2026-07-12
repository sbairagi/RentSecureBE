from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.routers import DefaultRouter  # noqa: E402
from rest_framework.test import APIClient

from django.http import Http404, HttpRequest
from django.test import override_settings

# ---------------------------------------------------------------------------
# URL patterns for direct HTTP endpoint tests.
# NOTE: this is consumed as ROOT_URLCONF by @override_settings below.
# It must NOT import anything that would itself import Django URLs setup
# in a way that reaches this module again (no circular imports).
# ---------------------------------------------------------------------------
from django.urls import include, path  # noqa: E402

from conftest import RenterFactory, RentRecordPaidFactory, UnitFactory
from documents.views import (
    GenerateRentAgreementPdfViewSet,
    GenerateRentReceiptPdfViewSet,
    GenerateUnitDossierPdfViewSet,
    download_unit_history,
)

_router = DefaultRouter()
_router.register(
    r"rent_agreement", GenerateRentAgreementPdfViewSet, basename="rent-agreement-pdf"
)
_router.register(
    r"properties", GenerateUnitDossierPdfViewSet, basename="unit-dossier-pdf"
)
_router.register(
    r"rent_receipt", GenerateRentReceiptPdfViewSet, basename="rent-receipt-pdf"
)
# Provide error handler stubs so Django's handler resolver does not raise
# AttributeError when respond to 404s raised inside test_client calls
# while ROOT_URLCONF is temporarily pointed here.
handler404 = "django.views.defaults.page_not_found"  # noqa: F841
handler500 = "django.views.defaults.server_error"  # noqa: F841

urlpatterns = [
    path("documents/", include(_router.urls)),
]


def _doc_url(viewset: str, pk: int, action: str) -> str:
    return f"/documents/{viewset}/{pk}/{action}/"


def _render_context(mock_render):
    call_args = mock_render.call_args
    if call_args is None:
        return {}
    pos_args = call_args.args
    if len(pos_args) >= 2:
        return pos_args[1]
    return call_args.kwargs.get("context", {})


def _http(method):
    """Apply ROOT_URLCONF override so the test client can resolve /documents/ ... URLs."""
    import functools

    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        from django.urls import clear_url_caches  # noqa: PLC0415

        clear_url_caches()
        with override_settings(ROOT_URLCONF="documents.tests.test_views"):
            return method(*args, **kwargs)

    wrapper.__wrapped__ = method
    return wrapper


# ---------------------------------------------------------------------------
# GenerateRentAgreementPdfViewSet tests
# ---------------------------------------------------------------------------
class TestGenerateRentAgreementPdfViewSet:
    pytestmark = pytest.mark.django_db

    def _make_renter(self, owner, unit):
        return RenterFactory(unit=unit)

    @_http
    def test_unauthenticated_returns_401(self, owner, unit: UnitFactory):
        renter = self._make_renter(owner, unit)
        client = APIClient()
        resp = client.get(
            _doc_url("rent_agreement", renter.id, "generate-rent-agreement-pdf")
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    @_http
    def test_renter_not_found_returns_404(self, owner, unit: UnitFactory):
        self._make_renter(owner, unit)
        client = APIClient()
        client.force_authenticate(user=owner)
        resp = client.get(
            _doc_url("rent_agreement", 99999, "generate-rent-agreement-pdf")
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert resp.json()["detail"] == "Renter not found."

    @_http
    def test_success_returns_pdf(self, owner, unit: UnitFactory):
        renter = self._make_renter(owner, unit)
        with patch("weasyprint.HTML") as mock_html_cls:
            with patch("documents.views.render_to_string") as mock_render:
                mock_render.return_value = "<html><body>Agreement</body></html>"
                mock_html_inst = MagicMock()
                mock_html_inst.write_pdf.return_value = b"%PDF-1.4 content"
                mock_html_cls.return_value = mock_html_inst

                client = APIClient()
                client.force_authenticate(user=owner)
                resp = client.get(
                    _doc_url("rent_agreement", renter.id, "generate-rent-agreement-pdf")
                )

        assert resp.status_code == status.HTTP_200_OK
        assert resp["Content-Type"] == "application/pdf"
        assert (
            resp["Content-Disposition"]
            == f"inline; filename=rent_agreement_{renter.id}.pdf"
        )

    @_http
    def test_success_render_context_includes_renter_unit_owner(
        self, owner, unit: UnitFactory
    ):
        renter = self._make_renter(owner, unit)
        with patch("weasyprint.HTML") as mock_html_cls:
            with patch("documents.views.render_to_string") as mock_render:
                mock_render.return_value = "<html></html>"
                mock_html_inst = MagicMock()
                mock_html_inst.write_pdf.return_value = b"PDF"
                mock_html_cls.return_value = mock_html_inst

                client = APIClient()
                client.force_authenticate(user=owner)
                client.get(
                    _doc_url("rent_agreement", renter.id, "generate-rent-agreement-pdf")
                )

                context = _render_context(mock_render)
                assert context["renter"] == renter
                assert context["unit"] == renter.unit
                assert context["owner"] == renter.unit.owner
                assert "today_date" in context


# ---------------------------------------------------------------------------
# GenerateUnitDossierPdfViewSet tests
# ---------------------------------------------------------------------------
class TestGenerateUnitDossierPdfViewSet:
    pytestmark = pytest.mark.django_db

    @_http
    def test_unauthenticated_returns_401(self, unit: UnitFactory):
        client = APIClient()
        resp = client.get(_doc_url("properties", unit.id, "generate-dossier-pdf"))
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    @_http
    def test_unit_not_found_returns_404(self, owner):
        client = APIClient()
        client.force_authenticate(user=owner)

        with patch(
            "documents.views.get_object_or_404",
            side_effect=Http404,
        ):
            resp = client.get(_doc_url("properties", 99999, "generate-dossier-pdf"))
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    @_http
    def test_taxes_none_when_unit_has_no_tax_records_attribute(
        self, owner, unit: UnitFactory
    ):
        mock_unit = MagicMock()
        mock_unit.caretakers.all.return_value = []
        mock_unit.renters.all.return_value = []

        original_getattr = getattr

        def _strict_getattr(obj, name, *default):
            if name == "tax_records":
                return None
            return original_getattr(obj, name, *default)

        with patch("builtins.getattr", _strict_getattr):
            with patch(
                "documents.views.get_object_or_404",
                return_value=mock_unit,
            ):
                with patch(
                    "documents.views.render_to_string",
                    return_value="<html></html>",
                ):
                    with patch("weasyprint.HTML") as mock_html_cls:
                        mock_html_inst = MagicMock()
                        mock_html_inst.write_pdf.return_value = b"%PDF"
                        mock_html_cls.return_value = mock_html_inst

                        client = APIClient()
                        client.force_authenticate(user=owner)
                        resp = client.get(
                            _doc_url("properties", unit.id, "generate-dossier-pdf")
                        )

        assert resp.status_code == status.HTTP_200_OK
        assert resp["Content-Type"] == "application/pdf"

    @_http
    def test_taxes_honored_when_tax_records_attribute_present(
        self, owner, unit: UnitFactory, building
    ):
        from properties.models import PropertyTaxRecord  # noqa: PLC0415

        taxes_qs = [
            PropertyTaxRecord.objects.create(
                property=building,
                amount="5000",
                due_date="2025-03-31",
                paid=False,
            ),
            PropertyTaxRecord.objects.create(
                property=building,
                amount="6000",
                due_date="2024-03-31",
                paid=True,
            ),
        ]
        mock_tax_records = MagicMock()
        mock_tax_records.all.return_value = taxes_qs

        unit_obj = MagicMock()
        unit_obj.caretakers.all.return_value = []
        unit_obj.renters.all.return_value = []
        unit_obj.tax_records = mock_tax_records

        with patch("documents.views.get_object_or_404", return_value=unit_obj):
            with patch(
                "documents.views.render_to_string", return_value="<html></html>"
            ):
                with patch("weasyprint.HTML") as mock_html_cls:
                    mock_inst = MagicMock()
                    mock_inst.write_pdf.return_value = b"%PDF"
                    mock_html_cls.return_value = mock_inst

                    client = APIClient()
                    client.force_authenticate(user=owner)
                    resp = client.get(
                        _doc_url("properties", unit.id, "generate-dossier-pdf")
                    )

        assert resp.status_code == status.HTTP_200_OK
        assert resp["Content-Type"] == "application/pdf"

    @_http
    def test_pdf_generation_exception_returns_500(self, owner, unit: UnitFactory):
        with patch("documents.views.render_to_string", return_value="<html></html>"):
            with patch("weasyprint.HTML") as mock_html_cls:
                mock_html_inst = MagicMock()
                mock_html_inst.write_pdf.side_effect = RuntimeError(
                    "PDF engine crashed"
                )
                mock_html_cls.return_value = mock_html_inst

                mock_unit = MagicMock()
                mock_unit.caretakers.all.return_value = []
                mock_unit.renters.all.return_value = []

                with patch("documents.views.get_object_or_404", return_value=mock_unit):
                    client = APIClient()
                    client.force_authenticate(user=owner)
                    resp = client.get(
                        _doc_url("properties", unit.id, "generate-dossier-pdf")
                    )

        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        body = resp.json()
        assert body["error"] == "Failed to generate PDF"
        assert "PDF engine crashed" in body["details"]

    @_http
    def test_success_returns_dossier_pdf(self, owner, unit: UnitFactory):
        with patch("documents.views.render_to_string", return_value="<html></html>"):
            with patch("weasyprint.HTML") as mock_html_cls:
                mock_html_inst = MagicMock()
                mock_html_inst.write_pdf.return_value = b"%PDF-1.4 dossier"
                mock_html_cls.return_value = mock_html_inst

                mock_unit = MagicMock()
                mock_unit.caretakers.all.return_value = []
                mock_unit.renters.all.return_value = []

                with patch("documents.views.get_object_or_404", return_value=mock_unit):
                    client = APIClient()
                    client.force_authenticate(user=owner)
                    resp = client.get(
                        _doc_url("properties", unit.id, "generate-dossier-pdf")
                    )

        assert resp.status_code == status.HTTP_200_OK
        assert resp["Content-Type"] == "application/pdf"
        assert (
            resp["Content-Disposition"]
            == f"attachment; filename=unit_dossier_{unit.id}.pdf"
        )


# ---------------------------------------------------------------------------
# GenerateRentReceiptPdfViewSet tests
# ---------------------------------------------------------------------------
class TestGenerateRentReceiptPdfViewSet:
    pytestmark = pytest.mark.django_db

    @staticmethod
    def _make_rent_record(unit: UnitFactory) -> RentRecordPaidFactory:
        renter = RenterFactory(unit=unit)
        return RentRecordPaidFactory(unit=unit, renter=renter)

    @_http
    def test_unauthenticated_returns_401(self, unit: UnitFactory):
        rent_record = self._make_rent_record(unit)
        client = APIClient()
        resp = client.get(_doc_url("rent_receipt", rent_record.id, "pdf_receipt"))
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    @_http
    def test_rent_record_not_found_returns_404(self, owner):
        client = APIClient()
        client.force_authenticate(user=owner)

        with patch.object(
            GenerateRentReceiptPdfViewSet,
            "get_object",
            side_effect=NotFound("Rent record not found."),
        ):
            resp = client.get(_doc_url("rent_receipt", 99999, "pdf_receipt"))

        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert resp.json()["error"] == "Rent record not found."

    @_http
    def test_success_returns_receipt_pdf(
        self,
        owner,
        unit: UnitFactory,
    ):
        rent_record = self._make_rent_record(unit)
        with patch("documents.views.render_to_string", return_value="<html></html>"):
            with patch("weasyprint.HTML") as mock_html_cls:
                mock_html_inst = MagicMock()
                mock_html_inst.write_pdf.return_value = b"%PDF-1.4 receipt"
                mock_html_cls.return_value = mock_html_inst

                client = APIClient()
                client.force_authenticate(user=owner)
                resp = client.get(
                    _doc_url("rent_receipt", rent_record.id, "pdf_receipt")
                )

        assert resp.status_code == status.HTTP_200_OK
        assert resp["Content-Type"] == "application/pdf"
        assert (
            resp["Content-Disposition"]
            == f"attachment; filename=rent_receipt_{rent_record.id}.pdf"
        )

    @_http
    def test_success_template_receives_rent_record(
        self,
        owner,
        unit: UnitFactory,
    ):
        rent_record = self._make_rent_record(unit)
        with patch("documents.views.render_to_string") as mock_render:
            with patch("weasyprint.HTML") as mock_html_cls:
                mock_html_inst = MagicMock()
                mock_html_inst.write_pdf.return_value = b"PDF"
                mock_html_cls.return_value = mock_html_inst

                client = APIClient()
                client.force_authenticate(user=owner)
                client.get(_doc_url("rent_receipt", rent_record.id, "pdf_receipt"))

                context = _render_context(mock_render)
                assert context["rent_record"] == rent_record


# ---------------------------------------------------------------------------
# download_unit_history function tests
# ---------------------------------------------------------------------------
class TestDownloadUnitHistory:
    pytestmark = pytest.mark.django_db

    def test_unit_not_found_for_owner_raises_does_not_exist(self, owner):
        from properties.models import Unit  # noqa: PLC0415

        request = HttpRequest()
        request.user = owner

        with patch("documents.views.Unit") as mock_unit_cls:
            mock_unit_cls.objects.get.side_effect = Unit.DoesNotExist(
                "Unit matching query does not exist."
            )
            with pytest.raises(Unit.DoesNotExist):
                download_unit_history(request, unit_id=99999)

    @patch("documents.views.generate_unit_history_pdf")
    def test_success_returns_history_pdf(self, mock_gen, owner, unit: UnitFactory):
        mock_gen.return_value = b"%PDF-1.4 history"

        request = HttpRequest()
        request.user = owner

        with patch("documents.views.Unit") as mock_unit_cls:
            mock_unit_instance = MagicMock()
            mock_unit_cls.objects.get.return_value = mock_unit_instance

            response = download_unit_history(request, unit_id=unit.id)

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/pdf"
        assert (
            response["Content-Disposition"]
            == f'attachment; filename="unit_{unit.id}_history.pdf"'
        )
        mock_gen.assert_called_once_with(mock_unit_instance)
