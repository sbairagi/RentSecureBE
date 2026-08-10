"""Tests for owner dashboard endpoint."""

from datetime import timedelta
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from django.test import override_settings

from core.models import PlanFeatureLimit, UserSubscription
from properties.models import Building, Renter, RentRecord, Unit


@pytest.mark.django_db
class TestOwnerDashboard:
    def test_owner_dashboard_returns_200(self, owner, subscription):
        with override_settings(
            ROOT_URLCONF="properties.tests.test_property_views_urls"
        ):
            client = APIClient()
            client.force_authenticate(user=owner)
            response = client.get("/owner/dashboard/")
        assert response.status_code == 200
        data = response.data
        assert "stats" in data
        assert "analytics" in data
        assert "recent" in data
        assert "pending_tasks" in data
        assert "notifications" in data
        assert "subscription" in data
        assert "plan_limits" in data
        assert "feature_usage" in data
        assert "payouts" in data

    def test_owner_dashboard_includes_subscription_expired(self, owner, plan_free):
        _expired_subscription = UserSubscription.objects.create(
            user=owner,
            plan=plan_free,
            start_date=owner.date_joined.date(),
            end_date=owner.date_joined.date() - timedelta(days=1),
            is_active=False,
        )
        with override_settings(
            ROOT_URLCONF="properties.tests.test_property_views_urls"
        ):
            client = APIClient()
            client.force_authenticate(user=owner)
            response = client.get("/owner/dashboard/")
        assert response.status_code == 200
        assert response.data["subscription"]["is_subscription_expired"] is True

    def test_owner_dashboard_includes_active_subscription_not_expired(
        self, owner, subscription
    ):
        with override_settings(
            ROOT_URLCONF="properties.tests.test_property_views_urls"
        ):
            client = APIClient()
            client.force_authenticate(user=owner)
            response = client.get("/owner/dashboard/")
        assert response.status_code == 200
        assert response.data["subscription"]["is_subscription_expired"] is False

    def test_owner_dashboard_includes_plan_limits(self, owner, subscription, plan_pro):
        PlanFeatureLimit.objects.create(
            plan=plan_pro, feature_key="max_buildings", value="10"
        )
        PlanFeatureLimit.objects.create(
            plan=plan_pro, feature_key="max_units", value="50"
        )
        with override_settings(
            ROOT_URLCONF="properties.tests.test_property_views_urls"
        ):
            client = APIClient()
            client.force_authenticate(user=owner)
            response = client.get("/owner/dashboard/")
        assert response.status_code == 200
        plan_limits = response.data["plan_limits"]
        assert len(plan_limits) == 2
        feature_keys = {limit["feature_key"] for limit in plan_limits}
        assert "max_buildings" in feature_keys
        assert "max_units" in feature_keys

    def test_owner_dashboard_excludes_other_owner_data(self, owner, subscription):
        other = owner.__class__.objects.create_user(
            username="other_owner_dash",
            password="p",
            full_name="Other Owner",
            phone="+19999999999",
        )
        Building.objects.create(
            owner=other,
            name="Other Building",
            address_line="1",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        Unit.objects.create(
            owner=other,
            building=None,
            unit="Other Unit",
            unit_type="flat",
            address_line="1",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        with override_settings(
            ROOT_URLCONF="properties.tests.test_property_views_urls"
        ):
            client = APIClient()
            client.force_authenticate(user=other)
            response = client.get("/owner/dashboard/")
        assert response.status_code == 200
        assert response.data["stats"]["total_buildings"] == 1
        assert response.data["stats"]["total_units"] == 1

    def test_owner_dashboard_anonymous_returns_401(self):
        with override_settings(
            ROOT_URLCONF="properties.tests.test_property_views_urls"
        ):
            client = APIClient()
            response = client.get("/owner/dashboard/")
        assert response.status_code == 401

    def test_owner_dashboard_stats_counts(self, owner, subscription, building, unit):
        with override_settings(
            ROOT_URLCONF="properties.tests.test_property_views_urls"
        ):
            client = APIClient()
            client.force_authenticate(user=owner)
            response = client.get("/owner/dashboard/")
        assert response.status_code == 200
        stats = response.data["stats"]
        assert stats["total_buildings"] == 1
        assert stats["total_units"] == 1

    def test_owner_dashboard_recent_payments(self, owner, subscription, building, unit):
        renter = Renter.objects.create(
            unit=unit,
            name="Test Renter",
            phone="+911234567890",
            email="renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=owner.date_joined.date(),
        )
        RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="paid",
            due_date=owner.date_joined.date(),
        )
        with override_settings(
            ROOT_URLCONF="properties.tests.test_property_views_urls"
        ):
            client = APIClient()
            client.force_authenticate(user=owner)
            response = client.get("/owner/dashboard/")
        assert response.status_code == 200
        recent = response.data["recent"]
        assert len(recent["rent_payments"]) == 1
        assert recent["rent_payments"][0]["amount"] == 10000.0

    def test_owner_dashboard_payouts(self, owner, subscription, building, unit):
        renter = Renter.objects.create(
            unit=unit,
            name="Test Renter",
            phone="+911234567890",
            email="renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=owner.date_joined.date(),
        )
        RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PAID",
            due_date=owner.date_joined.date(),
            payout_status="SUCCESS",
        )
        with override_settings(
            ROOT_URLCONF="properties.tests.test_property_views_urls"
        ):
            client = APIClient()
            client.force_authenticate(user=owner)
            response = client.get("/owner/dashboard/")
        assert response.status_code == 200
        payouts = response.data["payouts"]
        assert payouts["success"] == 1

    def test_owner_dashboard_pending_tasks(self, owner, subscription, building, unit):
        renter = Renter.objects.create(
            unit=unit,
            name="Test Renter",
            phone="+911234567890",
            email="renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=owner.date_joined.date(),
        )
        RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PENDING",
            due_date=owner.date_joined.date(),
        )
        with override_settings(
            ROOT_URLCONF="properties.tests.test_property_views_urls"
        ):
            client = APIClient()
            client.force_authenticate(user=owner)
            response = client.get("/owner/dashboard/")
        assert response.status_code == 200
        tasks = response.data["pending_tasks"]
        assert tasks["pending_verification"] == 1

    def test_owner_dashboard_renter_status_counts(
        self, owner, subscription, building, unit
    ):
        Renter.objects.create(
            unit=unit,
            name="Notice Renter",
            phone="+911234567890",
            email="renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=owner.date_joined.date(),
            status=Renter.RenterStatus.NOTICE_PERIOD,
        )
        Renter.objects.create(
            unit=unit,
            name="Revoked Renter",
            phone="+911234567891",
            email="revoked@test.com",
            rent_amount=Decimal("10000"),
            start_date=owner.date_joined.date(),
            status=Renter.RenterStatus.REVOKED,
        )
        Renter.objects.create(
            unit=unit,
            name="Deactivated Renter",
            phone="+911234567892",
            email="deactivated@test.com",
            rent_amount=Decimal("10000"),
            start_date=owner.date_joined.date(),
            status=Renter.RenterStatus.DEACTIVATED,
        )
        with override_settings(
            ROOT_URLCONF="properties.tests.test_property_views_urls"
        ):
            client = APIClient()
            client.force_authenticate(user=owner)
            response = client.get("/owner/dashboard/")
        assert response.status_code == 200
        stats = response.data["stats"]
        assert stats["notice_period_renters"] == 1
        assert stats["revoked_renters"] == 1
        assert stats["deactivated_renters"] == 1

    def test_owner_dashboard_rent_expected_and_collected(
        self, owner, subscription, building, unit
    ):
        renter = Renter.objects.create(
            unit=unit,
            name="Test Renter",
            phone="+911234567890",
            email="renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=owner.date_joined.date(),
        )
        RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status=RentRecord.Status.PAID,
            due_date=owner.date_joined.date(),
        )
        with override_settings(
            ROOT_URLCONF="properties.tests.test_property_views_urls"
        ):
            client = APIClient()
            client.force_authenticate(user=owner)
            response = client.get("/owner/dashboard/")
        assert response.status_code == 200
        stats = response.data["stats"]
        assert stats["rent_expected"] == 10000.0
        assert stats["rent_collected"] == 10000.0
        assert stats["rent_pending"] == 0.0

    def test_owner_dashboard_rent_overdue_and_late_fees(
        self, owner, subscription, building, unit
    ):
        renter = Renter.objects.create(
            unit=unit,
            name="Test Renter",
            phone="+911234567890",
            email="renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=owner.date_joined.date(),
        )
        RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status=RentRecord.Status.OVERDUE,
            due_date=owner.date_joined.date() - timedelta(days=5),
            late_fee=Decimal("500"),
        )
        with override_settings(
            ROOT_URLCONF="properties.tests.test_property_views_urls"
        ):
            client = APIClient()
            client.force_authenticate(user=owner)
            response = client.get("/owner/dashboard/")
        assert response.status_code == 200
        stats = response.data["stats"]
        assert stats["rent_overdue"] == 10000.0
        assert stats["overdue_renters_count"] == 1
        assert stats["late_fees_total"] == 500.0

    def test_owner_dashboard_payment_status_breakdown(
        self, owner, subscription, building, unit
    ):
        renter = Renter.objects.create(
            unit=unit,
            name="Test Renter",
            phone="+911234567890",
            email="renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=owner.date_joined.date(),
        )
        RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status=RentRecord.Status.PAID,
            due_date=owner.date_joined.date(),
        )
        RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status=RentRecord.Status.PENDING,
            due_date=owner.date_joined.date() + timedelta(days=5),
        )
        with override_settings(
            ROOT_URLCONF="properties.tests.test_property_views_urls"
        ):
            client = APIClient()
            client.force_authenticate(user=owner)
            response = client.get("/owner/dashboard/")
        assert response.status_code == 200
        stats = response.data["stats"]
        assert stats["payment_status_breakdown"]["paid"] == 1
        assert stats["payment_status_breakdown"]["pending"] == 1

    def test_owner_dashboard_collection_rate(self, owner, subscription, building, unit):
        renter = Renter.objects.create(
            unit=unit,
            name="Test Renter",
            phone="+911234567890",
            email="renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=owner.date_joined.date(),
        )
        RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status=RentRecord.Status.PAID,
            due_date=owner.date_joined.date(),
        )
        RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status=RentRecord.Status.PENDING,
            due_date=owner.date_joined.date() + timedelta(days=5),
        )
        with override_settings(
            ROOT_URLCONF="properties.tests.test_property_views_urls"
        ):
            client = APIClient()
            client.force_authenticate(user=owner)
            response = client.get("/owner/dashboard/")
        assert response.status_code == 200
        stats = response.data["stats"]
        assert stats["collection_rate"] == 50.0
        assert stats["current_month"] is not None

    def test_owner_dashboard_empty_dataset(self, owner, subscription):
        with override_settings(
            ROOT_URLCONF="properties.tests.test_property_views_urls"
        ):
            client = APIClient()
            client.force_authenticate(user=owner)
            response = client.get("/owner/dashboard/")
        assert response.status_code == 200
        stats = response.data["stats"]
        assert stats["total_buildings"] == 0
        assert stats["rent_expected"] == 0.0
        assert stats["collection_rate"] == 0.0
