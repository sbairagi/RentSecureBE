from typing import Any

from django.urls import include, path

from visitors.views.visitor_views import VisitorPublicVerifyView, VisitorViewSet

router: Any = None
try:
    from rest_framework.routers import DefaultRouter

    router = DefaultRouter()
    router.register(r"visitors", VisitorViewSet, basename="visitors")
except ImportError:
    pass

urlpatterns = [
    path("", include(router.urls)),
    path(
        "visitors/verify/",
        VisitorPublicVerifyView.as_view({"post": "verify_qr_public"}),
    ),
]
