"""
URL configuration for documents/views tests.

This module exposes ``urlpatterns`` and is referenced by
``ROOT_URLCONF = "documents.tests.test_views"`` in tests that resolve
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

# These values let Django find valid error-handler callables when
# Http404 (or other exceptions) propagate through the test client while
# ROOT_URLCONF is temporarily pointed at this module.
handler404 = "django.views.defaults.page_not_found"
handler500 = "django.views.defaults.server_error"

urlpatterns = [
    path("documents/", include(router.urls)),
]
