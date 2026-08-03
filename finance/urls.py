from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import (
    DownloadTaxFilesView,
    TaxSubmissionToCAViewSet,
    get_matched_ca,
    request_ca_callback,
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
]
