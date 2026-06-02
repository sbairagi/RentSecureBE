from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BuildingViewSet,
    CaretakerViewSet,
    ExtraChargeViewSet,
    RentAgreementDraftViewSet,
    RenterViewSet,
    RentRecordViewSet,
    UnitDocumentViewSet,
    UnitImageViewSet,
    UnitViewSet,
    download_rent_invoice,
    get_latest_due_rent,
    leegality_webhook,
    owner_dashboard_summary,
    owner_rent_overview,
    owner_rent_records,
    rent_history,
    retry_payout_api,
)

router = DefaultRouter()
# Active end-point
router.register(r"buildings", BuildingViewSet, basename="buildings")
router.register(r"units", UnitViewSet, basename="units")
router.register(r"caretakers", CaretakerViewSet, basename="caretakers")
router.register(r"renters", RenterViewSet, basename="renters")
router.register(r"rent-records", RentRecordViewSet, basename="rent-records")
router.register(r"extra-charges", ExtraChargeViewSet, basename="extra-charges")

# De-prioritized for now do not touch bellow end-point
router.register(r"unit-images", UnitImageViewSet, basename="unit-images")
router.register(
    r"rent-agreements", RentAgreementDraftViewSet, basename="rent-agreements"
)
router.register(
    r"rent-agreement-drafts",
    RentAgreementDraftViewSet,
    basename="rent-agreement-drafts",
)
router.register(
    r"unit-all-documents", UnitDocumentViewSet, basename="unit-all-documents"
)

urlpatterns = [
    path("", include(router.urls)),
    path("owner/rent-records/", owner_rent_records),
    path("rent-records/<int:rent_id>/invoice/", download_rent_invoice),
    path("renter/rent-due/", get_latest_due_rent),
    path("renter/rent-history/", rent_history),
    path("owner/rents/", owner_rent_overview),
    path("owner/dashboard-summary/", owner_dashboard_summary),
    path("owner/retry_payout_api/<int:rent_id>/", retry_payout_api),
    path("leegality/webhook/", leegality_webhook),
]
