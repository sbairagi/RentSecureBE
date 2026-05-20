from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (UnitViewSet, CaretakerViewSet, RenterViewSet, RentRecordViewSet, 
                    RentAgreementDraftViewSet, BuildingViewSet,
                    UnitImageViewSet, UnitDocumentViewSet, owner_rent_records, retry_payout_api,
                    download_rent_invoice, get_latest_due_rent, rent_history, owner_rent_overview,
                    owner_dashboard_summary, leegality_webhook, ExtraChargeViewSet)

router = DefaultRouter()
# Active end-point
router.register(r'buildings', BuildingViewSet, basename='buildings')
router.register(r'units', UnitViewSet, basename='units')
router.register(r'caretakers', CaretakerViewSet, basename='caretakers')
router.register(r'renters', RenterViewSet, basename='renters')
router.register(r'rent-records', RentRecordViewSet, basename='rent-records')
router.register(r'extra-charges', ExtraChargeViewSet, basename='extra-charges')

# De-prioritized for now do not touch bellow end-point
router.register(r'unit-images', UnitImageViewSet, basename='unit-images')
router.register(r'rent-agreements', RentAgreementDraftViewSet, basename='rent-agreements')
router.register(r'unit-all-documents', UnitDocumentViewSet, basename='unit-all-documents')

urlpatterns = [
    path('', include(router.urls)),
    path('owner/rent-records/', owner_rent_records),
    path('rent-records/<int:rent_id>/invoice/', download_rent_invoice),
    path('renter/rent-due/', get_latest_due_rent),
    path('renter/rent-history/', rent_history),
    path('owner/rents/', owner_rent_overview),
    path('owner/dashboard-summary/', owner_dashboard_summary),
    path('owner/retry_payout_api/<int:rent_id>/', retry_payout_api),
    path('leegality/webhook/', leegality_webhook)
]


