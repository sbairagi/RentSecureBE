from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ( GenerateUnitDossierPdfViewSet, GenerateRentAgreementPdfViewSet, 
                    GenerateRentReceiptPdfViewSet)

router = DefaultRouter()
router.register(r'rent_receipt', GenerateRentReceiptPdfViewSet, basename='rent-receipt-pdf')
router.register(r'properties', GenerateUnitDossierPdfViewSet, basename='unit-dossier-pdf')
router.register(r'rent_agreement', GenerateRentAgreementPdfViewSet, basename='rent-agreement-pdf')


urlpatterns = [
    path('file_generater/', include(router.urls)),
]
