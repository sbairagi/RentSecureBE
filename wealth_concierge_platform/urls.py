from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (PropertyViewSet, CaretakerViewSet, RenterViewSet, RentRecordViewSet, 
                    PropertyTaxRecordViewSet, GeneratePropertyDossierPdfViewSet, 
                    GenerateRentAgreementPdfViewSet, GenerateRentReceiptPdfViewSet)

router = DefaultRouter()
router.register(r'properties', PropertyViewSet)
router.register(r'caretakers', CaretakerViewSet)
router.register(r'renters', RenterViewSet)
router.register(r'rent-records', RentRecordViewSet)
router.register(r'property-tax-records', PropertyTaxRecordViewSet, basename='property-tax-record')
router.register(r'rent_receipt', GenerateRentReceiptPdfViewSet, basename='rent-receipt-pdf')
router.register(r'properties', GeneratePropertyDossierPdfViewSet, basename='property-dossier-pdf')
router.register(r'rent_agreement', GenerateRentAgreementPdfViewSet, basename='rent-agreement-pdf')

urlpatterns = [
    path('', include(router.urls)),
]


