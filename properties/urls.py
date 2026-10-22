from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import (
    BuildingViewSet,
    CareTakerViewSet,
    ExtraChargeViewSet,
    MaintenanceRequestViewSet,
    OpsAgreementViewSet,
    OpsPoliceVerificationViewSet,
    PoliceVerificationViewSet,
    RentAgreementDraftViewSet,
    RenterAppointmentViewSet,
    RenterViewSet,
    RentRecordViewSet,
    UnitDocumentViewSet,
    UnitImageViewSet,
    UnitViewSet,
    caretaker_dashboard,
    caretaker_maintenance,
    caretaker_maintenance_detail,
    caretaker_profile,
    caretaker_properties,
    caretaker_tenants,
    caretaker_today,
    contact_ca,
    download_owner_rent_report,
    download_rent_invoice,
    extract_form16_data,
    get_itr_deduction_suggestions,
    get_latest_due_rent,
    income_summary,
    itr_tracker_summary,
    leegality_webhook,
    owner_dashboard,
    owner_dashboard_summary,
    owner_rent_overview,
    owner_rent_records,
    owner_reports,
    rent_history,
    rent_whatsapp_logs,
    renter_agreement,
    renter_agreements,
    renter_dashboard,
    renter_documents,
    renter_extra_charges,
    renter_home,
    renter_listings,
    renter_maintenance,
    renter_profile,
    renter_rent_payment,
    renter_rent_receipt,
    renter_rent_record_detail,
    renter_rent_records,
    renter_sign_agreement,
    renter_verification,
    resend_rent_confirmation,
    retry_payout_api,
)

router = DefaultRouter()
# Active end-point
router.register(r"buildings", BuildingViewSet, basename="buildings")
router.register(r"maintenance", MaintenanceRequestViewSet, basename="maintenance")
router.register(r"units", UnitViewSet, basename="units")
router.register(r"caretakers", CareTakerViewSet, basename="caretakers")
router.register(r"renters", RenterViewSet, basename="renters")
router.register(r"rent-records", RentRecordViewSet, basename="rent-records")
router.register(r"extra-charges", ExtraChargeViewSet, basename="extra-charges")
router.register(
    r"police-verifications", PoliceVerificationViewSet, basename="police-verifications"
)

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

# The renter portal — the renter browses homes, books a viewing and signs.
router.register(
    r"renter/appointments",
    RenterAppointmentViewSet,
    basename="renter-appointments",
)

# The RentSecure Ops desk — the internal trust and operations team.
router.register(
    r"ops/police-verifications",
    OpsPoliceVerificationViewSet,
    basename="ops-police-verifications",
)
router.register(r"ops/agreements", OpsAgreementViewSet, basename="ops-agreements")

urlpatterns = [
    path("", include(router.urls)),
    path("owner/rent-records/", owner_rent_records),
    path("rent-records/<int:rent_id>/invoice/", download_rent_invoice),
    path(
        "rent-records/<int:rent_id>/resend-confirmation/",
        resend_rent_confirmation,
    ),
    path("caretaker/dashboard/", caretaker_dashboard),
    path("caretaker/today/", caretaker_today),
    path("caretaker/properties/", caretaker_properties),
    path("caretaker/maintenance/", caretaker_maintenance),
    path("caretaker/maintenance/<int:pk>/", caretaker_maintenance_detail),
    path("caretaker/tenants/", caretaker_tenants),
    path("caretaker/profile/", caretaker_profile),
    path("renter/rent-due/", get_latest_due_rent),
    path("renter/rent-history/", rent_history),
    path("renter/profile/", renter_profile),
    path("renter/home/", renter_home),
    path("renter/rent-records/", renter_rent_records),
    path("renter/rent-records/<int:rent_id>/", renter_rent_record_detail),
    path(
        "renter/rent-records/<int:rent_id>/payments/",
        renter_rent_payment,
    ),
    path(
        "renter/rent-records/<int:rent_id>/receipt/",
        renter_rent_receipt,
    ),
    path("renter/agreement/", renter_agreement),
    path("renter/documents/", renter_documents),
    path("renter/extra-charges/", renter_extra_charges),
    path("renter/dashboard/", renter_dashboard),
    path("renter/listings/", renter_listings),
    path("renter/agreements/", renter_agreements),
    path("renter/agreement/sign/", renter_sign_agreement),
    path("renter/maintenance/", renter_maintenance),
    path("renter/verification/", renter_verification),
    path("owner/rents/", owner_rent_overview),
    path("owner/dashboard/", owner_dashboard),
    path("owner/dashboard-summary/", owner_dashboard_summary),
    path("owner/reports/", owner_reports),
    path("owner/rent-report/", download_owner_rent_report),
    path("owner/income-summary/", income_summary),
    path("owner/retry_payout_api/<int:rent_id>/", retry_payout_api),
    path(
        "rent-records/<int:rent_id>/whatsapp-logs/",
        rent_whatsapp_logs,
    ),
    path("leegality/webhook/", leegality_webhook),
    path("itr/contact-ca/", contact_ca),
    path("itr/tracker/", itr_tracker_summary),
    path("itr/deduction-suggestions/", get_itr_deduction_suggestions),
    path("itr/extract-form16/", extract_form16_data),
]
