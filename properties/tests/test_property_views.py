"""Tests for properties/views/property_views.py — full branch coverage."""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

from core.models import UserSubscription
from properties.models import Renter, RentRecord

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ---------------------------------------------------------------------------
# my_rent_records
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestMyRentRecords:
    def test_owner_gets_own_rent_records(
        self, settings, owner, subscription, building, unit
    ):
        settings.ROOT_URLCONF = "properties.tests.test_property_views_urls"
        renter = Renter.objects.create(
            unit=unit,
            name="Test Renter",
            phone="+911234567890",
            email="renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PENDING",
            due_date=date.today(),
        )
        client = _auth_client(owner)
        response = client.get("/my-rent-records/")
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_non_owner_gets_empty(self, settings, owner, subscription, building, unit):
        settings.ROOT_URLCONF = "properties.tests.test_property_views_urls"
        other = User.objects.create_user(
            username="myrr_other", password="p", full_name="Other", phone="+19999999999"
        )
        UserSubscription.objects.create(
            user=other, plan=subscription.plan, is_active=True
        )
        renter = Renter.objects.create(
            unit=unit,
            name="Test Renter",
            phone="+911234567890",
            email="renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PENDING",
            due_date=date.today(),
        )
        client = _auth_client(other)
        response = client.get("/my-rent-records/")
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_anonymous_returns_401_from_view_body(self, settings):
        settings.ROOT_URLCONF = "properties.tests.test_property_views_urls"
        with patch(
            "rest_framework.permissions.IsAuthenticated.has_permission",
            return_value=True,
        ):
            client = APIClient()
            response = client.get("/my-rent-records/")
        assert response.status_code == 401
        assert response.data == {"error": "Unauthorized"}


# ---------------------------------------------------------------------------
# update_late_fee_policy
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestUpdateLateFeePolicy:
    def test_owner_updates_late_fee(
        self, settings, owner, subscription, building, unit
    ):
        settings.ROOT_URLCONF = "properties.tests.test_property_views_urls"
        renter = Renter.objects.create(
            unit=unit,
            name="LF Renter",
            phone="+911234567890",
            email="lf@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        rent = RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("1000"),
            payment_method="upi",
            status="PENDING",
            due_date=date.today(),
            late_fee=Decimal("0"),
        )
        client = _auth_client(owner)
        response = client.patch(
            f"/update-late-fee/{rent.id}/",
            {"late_fee_amount": "500"},
            format="json",
        )
        assert response.status_code == 200
        rent.refresh_from_db()
        assert rent.late_fee == Decimal("500")

    def test_anonymous_returns_401_from_view_body(
        self, settings, owner, subscription, building, unit
    ):
        settings.ROOT_URLCONF = "properties.tests.test_property_views_urls"
        renter = Renter.objects.create(
            unit=unit,
            name="LF Renter",
            phone="+911234567890",
            email="lf@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        rent = RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("1000"),
            payment_method="upi",
            status="PENDING",
            due_date=date.today(),
            late_fee=Decimal("0"),
        )
        with patch(
            "rest_framework.permissions.IsAuthenticated.has_permission",
            return_value=True,
        ):
            client = APIClient()
            response = client.patch(
                f"/update-late-fee/{rent.id}/",
                {"late_fee_amount": "100"},
                format="json",
            )
        assert response.status_code == 401
        assert response.data == {"error": "Unauthorized"}


# ---------------------------------------------------------------------------
# revoke_rent_agreement
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestRevokeRentAgreement:
    def test_owner_revokes_agreement(
        self, settings, owner, subscription, building, unit
    ):
        settings.ROOT_URLCONF = "properties.tests.test_property_views_urls"
        renter = Renter.objects.create(
            unit=unit,
            name="Rev Renter",
            phone="+911234567890",
            email="rev@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        client = _auth_client(owner)
        with (
            patch("properties.views.property_views.send_whatsapp_message") as mock_send,
            patch("properties.views.property_views.update_unit_status") as mock_status,
        ):
            response = client.post(
                f"/revoke-agreement/{renter.id}/",
                {"reason": "Owner request"},
                format="json",
            )
        assert response.status_code == 200
        assert response.data["success"] is True
        renter.refresh_from_db()
        assert renter.is_agreement_revoked is True
        assert renter.revocation_reason == "Owner request"
        mock_send.assert_called_once()
        mock_status.assert_called_once_with(unit)

    def test_revoke_with_active_agreement_sets_none(
        self, monkeypatch, settings, owner, subscription, building, unit
    ):
        settings.ROOT_URLCONF = "properties.tests.test_property_views_urls"
        renter = Renter.objects.create(
            unit=unit,
            name="Rev Renter",
            phone="+911234567890",
            email="rev@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        monkeypatch.setattr(Renter, "active_agreement", object(), raising=False)
        client = _auth_client(owner)
        with (
            patch("properties.views.property_views.send_whatsapp_message") as mock_send,
            patch("properties.views.property_views.update_unit_status") as mock_status,
        ):
            response = client.post(
                f"/revoke-agreement/{renter.id}/",
                {"reason": "Owner request"},
                format="json",
            )
        assert response.status_code == 200
        renter.refresh_from_db()
        assert renter.is_agreement_revoked is True
        mock_send.assert_called_once()
        mock_status.assert_called_once_with(unit)

    def test_anonymous_returns_401_from_view_body(
        self, settings, owner, subscription, building, unit
    ):
        settings.ROOT_URLCONF = "properties.tests.test_property_views_urls"
        renter = Renter.objects.create(
            unit=unit,
            name="Rev Renter",
            phone="+911234567890",
            email="rev@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        with patch(
            "rest_framework.permissions.IsAuthenticated.has_permission",
            return_value=True,
        ):
            client = APIClient()
            response = client.post(
                f"/revoke-agreement/{renter.id}/",
                {"reason": "Owner request"},
                format="json",
            )
        assert response.status_code == 401
        assert response.data == {"error": "Unauthorized"}


# ---------------------------------------------------------------------------
# unit_analytics
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestUnitAnalytics:
    def test_owner_analytics_returns_data(
        self, settings, owner, subscription, building, unit
    ):
        settings.ROOT_URLCONF = "properties.tests.test_property_views_urls"
        client = _auth_client(owner)
        with patch(
            "properties.views.property_views.get_owner_analytics"
        ) as mock_analytics:
            mock_analytics.return_value = {
                "owner_id": owner.id,
                "total_buildings": 1,
                "buildings": [],
                "aggregate": {
                    "total_units": 1,
                    "occupied": 1,
                    "vacant": 0,
                    "overall_occupancy_rate": 100.0,
                },
            }
            response = client.get("/unit-analytics/")
        assert response.status_code == 200
        assert response.data["owner_id"] == owner.id

    def test_owner_analytics_by_building(
        self, settings, owner, subscription, building, unit
    ):
        settings.ROOT_URLCONF = "properties.tests.test_property_views_urls"
        client = _auth_client(owner)
        with patch(
            "properties.services.unit_service.get_building_analytics"
        ) as mock_building:
            mock_building.return_value = {
                "building_id": building.id,
                "building_name": building.name,
                "total_units": 1,
                "occupied_units": 1,
                "vacant_units": 0,
                "occupancy_rate": 100.0,
            }
            response = client.get(f"/unit-analytics/?building_id={building.id}")
        assert response.status_code == 200
        assert response.data["data"]["building_id"] == building.id

    def test_anonymous_returns_401_from_view_body(self, settings):
        settings.ROOT_URLCONF = "properties.tests.test_property_views_urls"
        with patch(
            "rest_framework.permissions.IsAuthenticated.has_permission",
            return_value=True,
        ):
            client = APIClient()
            response = client.get("/unit-analytics/")
        assert response.status_code == 401
        assert response.data == {"error": "Unauthorized"}
