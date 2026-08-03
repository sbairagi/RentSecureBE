from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import (
    DownloadTaxFilesView,
    TaxSubmissionToCAViewSet,
    ca_leads_list,
    get_matched_ca,
    request_ca_callback,
    update_lead_status,
)

router = DefaultRouter()
router.register(r"tax-submissions", TaxSubmissionToCAViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "tax-summary/download/",
        DownloadTaxFilesView.as_view(),
        name="download-tax-files",
    ),
    path("ca/match/", get_matched_ca, name="get-matched-ca"),
    path("ca/callback-request/", request_ca_callback, name="ca-callback-request"),
    path("ca/leads/", ca_leads_list, name="ca-leads-list"),
    path(
        "ca/leads/<int:lead_id>/update/", update_lead_status, name="update-lead-status"
    ),
]
