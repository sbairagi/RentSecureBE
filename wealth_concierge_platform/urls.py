from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (PropertyViewSet, CaretakerViewSet, RenterViewSet, RentRecordViewSet, 
                    PropertyTaxRecordViewSet, GeneratePropertyDossierPdfViewSet, 
                    GenerateRentAgreementPdfViewSet, GenerateRentReceiptPdfViewSet,
                    PropertyTaxRecordViewSet, SubscriptionPlanViewSet, UserSubscriptionViewSet,
                    AddOnPurchaseViewSet, PlanFeatureLimitViewSet, UsageLimitViewSet,
                    RentAgreementDraftViewSet, PDFExportRecordViewSet,
                    PropertyImageViewSet, PropertyDocumentViewSet)

router = DefaultRouter()
router.register(r'properties', PropertyViewSet)
router.register(r'caretakers', CaretakerViewSet)
router.register(r'renters', RenterViewSet)
router.register(r'rent-records', RentRecordViewSet)
router.register(r'property-tax-records', PropertyTaxRecordViewSet, basename='property-tax-record')
router.register(r'rent_receipt', GenerateRentReceiptPdfViewSet, basename='rent-receipt-pdf')
router.register(r'properties', GeneratePropertyDossierPdfViewSet, basename='property-dossier-pdf')
router.register(r'rent_agreement', GenerateRentAgreementPdfViewSet, basename='rent-agreement-pdf')
router.register(r'property-tax-records', PropertyTaxRecordViewSet)
router.register(r'subscription-plans', SubscriptionPlanViewSet)
router.register(r'user-subscriptions', UserSubscriptionViewSet)
router.register(r'addon-purchases', AddOnPurchaseViewSet)
router.register(r'plan-feature-limits', PlanFeatureLimitViewSet)
router.register(r'usage-limits', UsageLimitViewSet)
router.register(r'rent-agreements', RentAgreementDraftViewSet)
router.register(r'pdf-exports', PDFExportRecordViewSet)
router.register(r'property-images', PropertyImageViewSet)
router.register(r'property-documents', PropertyDocumentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path("notifications/", include("wealth_concierge_platform.management.urls")),
]


