"""URLconf for property_views tests."""

from django.urls import path

from properties.views.property_views import (
    my_rent_records,
    revoke_rent_agreement,
    unit_analytics,
    update_late_fee_policy,
)

urlpatterns = [
    path("my-rent-records/", my_rent_records, name="my-rent-records"),
    path(
        "update-late-fee/<int:property_id>/",
        update_late_fee_policy,
        name="update-late-fee",
    ),
    path(
        "revoke-agreement/<int:renter_id>/",
        revoke_rent_agreement,
        name="revoke-agreement",
    ),
    path("unit-analytics/", unit_analytics, name="unit-analytics"),
]
