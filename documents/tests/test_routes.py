"""
URL configuration for documents/views tests.

This module exposes ``urlpatterns`` and is referenced by
``ROOT_URLCONF = "documents.tests.test_urls"`` in tests that resolve
HTTP routes through Django's URL router.
"""

from rest_framework.routers import DefaultRouter

from django.urls import include, path

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
