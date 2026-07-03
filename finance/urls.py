from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import DownloadTaxFilesView, TaxSubmissionToCAViewSet

router = DefaultRouter()
# router.register(r'ca-profiles', CAProfileViewSet)
router.register(r"tax-submissions", TaxSubmissionToCAViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "tax-summary/download/",
        DownloadTaxFilesView.as_view(),
        name="download-tax-files",
    ),
]
