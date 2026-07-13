"""
URL configuration for documents/views tests.

This module exposes ``urlpatterns`` and is referenced by
``ROOT_URLCONF = "documents.tests.test_urls"`` in tests that resolve
HTTP routes through Django's URL router.
"""

from rest_framework.routers import DefaultRouter

from django.test import TestCase, override_settings
from django.urls import include, path, resolve

from documents.views import (
    GenerateRentAgreementPdfViewSet,
    GenerateRentReceiptPdfViewSet,
    GenerateUnitDossierPdfViewSet,
)

router = DefaultRouter()
router.register(
    r"rent_agreement", GenerateRentAgreementPdfViewSet, basename="rent-agreement-pdf"
)
router.register(
    r"properties", GenerateUnitDossierPdfViewSet, basename="unit-dossier-pdf"
)
router.register(
    r"rent_receipt", GenerateRentReceiptPdfViewSet, basename="rent-receipt-pdf"
)

urlpatterns = [
    path("documents/", include(router.urls)),
]


class TestDocumentRoutes(TestCase):
    """Verify that document URL routes resolve correctly."""

    def test_rent_agreement_route_resolves(self):
        with override_settings(ROOT_URLCONF="documents.tests.test_routes"):
            resolver = resolve(
                "/documents/rent_agreement/1/generate-rent-agreement-pdf/"
            )
            self.assertEqual(resolver.func.cls, GenerateRentAgreementPdfViewSet)

    def test_unit_dossier_route_resolves(self):
        with override_settings(ROOT_URLCONF="documents.tests.test_routes"):
            resolver = resolve("/documents/properties/1/generate-dossier-pdf/")
            self.assertEqual(resolver.func.cls, GenerateUnitDossierPdfViewSet)

    def test_rent_receipt_route_resolves(self):
        with override_settings(ROOT_URLCONF="documents.tests.test_routes"):
            resolver = resolve("/documents/rent_receipt/")
            self.assertEqual(resolver.func.cls, GenerateRentReceiptPdfViewSet)
