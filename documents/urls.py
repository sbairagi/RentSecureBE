from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import (
    GenerateRentAgreementPdfViewSet,
    GenerateRentReceiptPdfViewSet,
    GenerateUnitDossierPdfViewSet,
)

router = DefaultRouter()
router.register(
    r"rent_receipt", GenerateRentReceiptPdfViewSet, basename="rent-receipt-pdf"
)
router.register(
    r"properties", GenerateUnitDossierPdfViewSet, basename="unit-dossier-pdf"
)
router.register(
    r"rent_agreement", GenerateRentAgreementPdfViewSet, basename="rent-agreement-pdf"
)


urlpatterns = [
    path("document/", include(router.urls)),
]
