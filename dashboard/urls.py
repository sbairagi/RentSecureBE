# dashboard/urls.py

from django.urls import path

from . import views

urlpatterns = [
    path("agreements/", views.agreement_status_view, name="agreement_status"),
    path(
        "retry-signature/<int:rent_id>/", views.retry_signature, name="retry_signature"
    ),
]
