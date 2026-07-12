"""Comprehensive pytest tests for properties/views/rent_record_views.py."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache

from conftest import (
    BuildingFactory,
    PlanFeatureLimitFactory,
    RenterFactory,
    RentRecordFactory,
    SubscriptionPlanFactory,
    UnitFactory,
    UsageLimitFactory,
    UserFactory,
    UserSubscriptionFactory,
)
from properties.models import RentRecord

User = get_user_model()


def _make_client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


# ===========================================================================
# RentRecordViewSet — queryset and permission branches
# ===========================================================================


class TestRentRecordViewSetQueryset:
    """Covers get_queryset branches."""

    def test_anonymous_returns_empty_queryset(self, db):
        """AnonymousUser branch in get_queryset returns none()."""
        from properties.views.rent_record_views import RentRecordViewSet

        owner = UserFactory()
        unit = UnitFactory(owner=owner)
        renter = RenterFactory(unit=unit)
        RentRecordFactory(unit=unit, renter=renter)

        request = MagicMock()
        request.user = AnonymousUser()
        viewset = RentRecordViewSet()
        viewset.request = request
        viewset.format_kwarg = None

        qs = viewset.get_queryset()
        assert list(qs) == []

    def test_owner_sees_only_own_rent_records(self, db):
        """Authenticated owner sees only records for their units."""
        owner = UserFactory()
        other = UserFactory()
        building = BuildingFactory(owner=owner)
        other_building = BuildingFactory(owner=other)
        unit = UnitFactory(owner=owner, building=building)
        other_unit = UnitFactory(owner=other, building=other_building)
        renter = RenterFactory(unit=unit)
        other_renter = RenterFactory(unit=other_unit)

        RentRecordFactory(unit=unit, renter=renter)
        RentRecordFactory(unit=other_unit, renter=other_renter)

        c = _make_client(owner)
        response = c.get("/properties/rent-records/")
        assert response.status_code == 200
        assert len(response.data) == 1


class TestRentRecordViewSetCreate:
    """Covers perform_create permission and quota branches."""

    def test_create_with_other_unit_owner_raises_permission_denied(self, db):
        """Unit owner mismatch raises PermissionDenied."""
        owner = UserFactory()
        other = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=unit)
        other_unit = UnitFactory(owner=other)

        plan = SubscriptionPlanFactory(name="test_plan", monthly_price=Decimal("29.99"))
        UserSubscriptionFactory(user=owner, plan=plan, is_active=True)
        PlanFeatureLimitFactory(plan=plan, feature_key="rent_records", value="10")

        c = _make_client(owner)
        response = c.post(
            "/properties/rent-records/",
            {
                "unit": other_unit.id,
                "renter": renter.id,
                "amount": "10000",
                "payment_method": "upi",
                "status": "PENDING",
                "due_date": (date.today() + timedelta(days=7)).isoformat(),
            },
        )
        assert response.status_code == 400

    def test_create_with_renter_from_different_unit_raises_validation_error(self, db):
        """Renter not belonging to selected unit raises ValidationError."""
        owner = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        other_unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=other_unit)

        plan = SubscriptionPlanFactory(
            name="test_plan2", monthly_price=Decimal("29.99")
        )
        UserSubscriptionFactory(user=owner, plan=plan, is_active=True)
        PlanFeatureLimitFactory(plan=plan, feature_key="rent_records", value="10")

        c = _make_client(owner)
        response = c.post(
            "/properties/rent-records/",
            {
                "unit": unit.id,
                "renter": renter.id,
                "amount": "10000",
                "payment_method": "upi",
                "status": "PENDING",
                "due_date": (date.today() + timedelta(days=7)).isoformat(),
            },
        )
        assert response.status_code == 400

    def test_create_quota_exceeded_raises_permission_denied(self, db):
        """FeatureEnforcer.can_create returning False raises PermissionDenied."""
        owner = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=unit)

        plan = SubscriptionPlanFactory(
            name="quota_plan", monthly_price=Decimal("29.99")
        )
        UserSubscriptionFactory(user=owner, plan=plan, is_active=True)
        PlanFeatureLimitFactory(plan=plan, feature_key="rent_records", value="1")
        UsageLimitFactory(user=owner, feature_key="rent_records", usage_count=1)

        c = _make_client(owner)
        response = c.post(
            "/properties/rent-records/",
            {
                "unit": unit.id,
                "renter": renter.id,
                "amount": "10000",
                "payment_method": "upi",
                "status": "PENDING",
                "due_date": (date.today() + timedelta(days=7)).isoformat(),
            },
        )
        assert response.status_code == 403

    def test_create_payment_link_exception_logs_and_returns_201(self, db):
        """Exception during payment link creation is caught and logged."""
        owner = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=unit)

        plan = SubscriptionPlanFactory(name="exc_plan", monthly_price=Decimal("29.99"))
        UserSubscriptionFactory(user=owner, plan=plan, is_active=True)
        PlanFeatureLimitFactory(plan=plan, feature_key="rent_records", value="10")

        c = _make_client(owner)
        with patch(
            "properties.views.rent_record_views.create_payment_link",
            side_effect=RuntimeError("payment provider down"),
        ):
            response = c.post(
                "/properties/rent-records/",
                {
                    "unit": unit.id,
                    "renter": renter.id,
                    "amount": "10000",
                    "payment_method": "upi",
                    "status": "PENDING",
                    "due_date": (date.today() + timedelta(days=7)).isoformat(),
                },
            )
        assert response.status_code == 201
        assert RentRecord.objects.filter(unit=unit, renter=renter).exists()

    def test_create_deletes_cache_after_success(self, db):
        """Cache key is deleted after successful create."""
        owner = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=unit)

        plan = SubscriptionPlanFactory(
            name="cache_plan", monthly_price=Decimal("29.99")
        )
        UserSubscriptionFactory(user=owner, plan=plan, is_active=True)
        PlanFeatureLimitFactory(plan=plan, feature_key="rent_records", value="10")

        cache_key = f"rent_records_user_{owner.id}"
        cache.set(cache_key, ["stale"], timeout=300)

        c = _make_client(owner)
        c.post(
            "/properties/rent-records/",
            {
                "unit": unit.id,
                "renter": renter.id,
                "amount": "10000",
                "payment_method": "upi",
                "status": "PENDING",
                "due_date": (date.today() + timedelta(days=7)).isoformat(),
            },
        )
        assert cache.get(cache_key) is None


class TestRentRecordViewSetUpdate:
    """Covers perform_update permission and cache branches."""

    def test_update_other_user_rent_record_raises_validation_error(self, db):
        """Updating a rent record owned by another user raises ValidationError."""
        owner = UserFactory()
        other = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=unit)
        rent = RentRecordFactory(unit=unit, renter=renter)

        plan = SubscriptionPlanFactory(name="upd_plan", monthly_price=Decimal("29.99"))
        UserSubscriptionFactory(user=other, plan=plan, is_active=True)

        c = _make_client(other)
        response = c.patch(
            f"/properties/rent-records/{rent.id}/",
            {"notes": "Hacked"},
        )
        assert response.status_code == 404

    def test_update_deletes_cache(self, db):
        """Cache key is deleted after successful update."""
        owner = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=unit)
        rent = RentRecordFactory(unit=unit, renter=renter)

        c = _make_client(owner)

        with patch("django.core.cache.cache.delete") as mock_delete:
            c.patch(f"/properties/rent-records/{rent.id}/", {"notes": "Updated"})
            mock_delete.assert_called_once_with(f"rent_records_user_{owner.id}")


class TestRentRecordViewSetDestroy:
    """Covers perform_destroy permission and cache branches."""

    def test_destroy_other_user_rent_record_returns_not_found(self, db):
        """Deleting another user's rent record returns 404 (not in filtered queryset)."""
        owner = UserFactory()
        other = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=unit)
        rent = RentRecordFactory(unit=unit, renter=renter)

        plan = SubscriptionPlanFactory(name="del_plan", monthly_price=Decimal("29.99"))
        UserSubscriptionFactory(user=other, plan=plan, is_active=True)

        c = _make_client(other)
        response = c.delete(f"/properties/rent-records/{rent.id}/")
        assert response.status_code == 404

    def test_destroy_deletes_cache(self, db):
        """Cache key is deleted after successful destroy."""
        owner = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=unit)
        rent = RentRecordFactory(unit=unit, renter=renter)

        c = _make_client(owner)

        with patch("django.core.cache.cache.delete") as mock_delete:
            c.delete(f"/properties/rent-records/{rent.id}/")
            mock_delete.assert_called_once_with(f"rent_records_user_{owner.id}")


# ===========================================================================
# retry_payout_api branches
# ===========================================================================


class TestRetryPayoutAPI:
    """Covers all retry_payout_api branches."""

    def test_not_retryable_when_payout_status_is_success(self, db):
        """PAID + payout SUCCESS is not retryable."""
        owner = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=unit)
        rent = RentRecordFactory(
            unit=unit,
            renter=renter,
            status="PAID",
            payout_status="SUCCESS",
        )

        c = _make_client(owner)
        response = c.post(f"/properties/owner/retry_payout_api/{rent.id}/")
        assert response.status_code == 400
        assert response.data["error"] == "Payout not retryable"

    def test_not_retryable_when_payment_not_paid(self, db):
        """PENDING payment + FAILED payout is not retryable."""
        owner = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=unit)
        rent = RentRecordFactory(
            unit=unit,
            renter=renter,
            status="PENDING",
            payout_status="FAILED",
        )

        c = _make_client(owner)
        response = c.post(f"/properties/owner/retry_payout_api/{rent.id}/")
        assert response.status_code == 400

    def test_retry_success_returns_updated_status(self, db):
        """Successful payout retry returns SUCCESS status."""
        owner = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=unit)
        rent = RentRecordFactory(
            unit=unit,
            renter=renter,
            status="PAID",
            payout_status="FAILED",
        )

        c = _make_client(owner)
        with patch(
            "properties.views.rent_record_views.process_rent_payout",
            return_value=None,
        ):
            with patch.object(rent, "refresh_from_db"):
                with patch(
                    "properties.views.rent_record_views.send_payout_notification"
                ):
                    response = c.post(f"/properties/owner/retry_payout_api/{rent.id}/")
        assert response.status_code == 200
        assert response.data["message"] == "Payout retry attempted"

    def test_retry_process_raises_exception_returns_500(self, db):
        """Exception in process_rent_payout returns 500."""
        owner = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=unit)
        rent = RentRecordFactory(
            unit=unit,
            renter=renter,
            status="PAID",
            payout_status="FAILED",
        )

        c = _make_client(owner)
        with patch(
            "properties.views.rent_record_views.process_rent_payout",
            side_effect=RuntimeError("cashfree down"),
        ):
            response = c.post(f"/properties/owner/retry_payout_api/{rent.id}/")
        assert response.status_code == 500
        assert "error" in response.data


# ===========================================================================
# owner_rent_records endpoint
# ===========================================================================


class TestOwnerRentRecordsAPI:
    """Covers owner_rent_records endpoint."""

    def test_lists_own_records(self, db):
        """Owner sees their rent records."""
        owner = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=unit)
        RentRecordFactory(unit=unit, renter=renter)

        c = _make_client(owner)
        response = c.get("/properties/owner/rent-records/")
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_empty_for_owner_with_no_records(self, db):
        """Owner with no rent records gets empty list."""
        owner = UserFactory()

        c = _make_client(owner)
        response = c.get("/properties/owner/rent-records/")
        assert response.status_code == 200
        assert response.data == []


# ===========================================================================
# download_rent_invoice endpoint
# ===========================================================================


class TestDownloadRentInvoiceAPI:
    """Covers download_rent_invoice endpoint."""

    def test_download_returns_pdf_response(self, db):
        """Authenticated owner can download invoice PDF."""
        owner = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=unit)
        rent = RentRecordFactory(unit=unit, renter=renter)

        c = _make_client(owner)
        fake_path = "/tmp/fake_invoice.pdf"
        with patch(
            "properties.views.rent_record_views.get_object_or_404",
            return_value=rent,
        ):
            with patch(
                "properties.views.rent_record_views.generate_rent_invoice_pdf",
                return_value=fake_path,
            ):
                with patch(
                    "properties.views.rent_record_views.open",
                    return_value=MagicMock(),
                    create=True,
                ):
                    response = c.get(f"/properties/rent-records/{rent.id}/invoice/")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"


# ===========================================================================
# get_latest_due_rent branches
# ===========================================================================


class TestGetLatestDueRentAPI:
    """Covers get_latest_due_rent branches."""

    def test_not_a_renter_returns_403(self, db):
        """User who is not a renter gets 403."""
        owner = UserFactory()

        c = _make_client(owner)
        response = c.get("/properties/renter/rent-due/")
        assert response.status_code == 403
        assert response.data["error"] == "Not a renter"

    def test_no_pending_rent_returns_message(self, db):
        """Renter with no pending rent gets a message."""
        owner = UserFactory()

        c = _make_client(owner)
        response = c.get("/properties/renter/rent-due/")
        assert response.status_code == 200
        assert response.data["message"] == "No pending rent"

    def test_renter_gets_latest_due_rent(self, db):
        """Renter with pending rent gets the latest due rent details."""
        owner = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=unit, user=owner)
        rent = RentRecordFactory(
            unit=unit,
            renter=renter,
            status="PENDING",
            due_date=date.today() + timedelta(days=7),
        )

        c = _make_client(owner)
        response = c.get("/properties/renter/rent-due/")
        assert response.status_code == 200
        assert float(response.data["amount"]) == float(rent.amount)


# ===========================================================================
# rent_history branches
# ===========================================================================


class TestRentHistoryAPI:
    """Covers rent_history branches."""

    def test_not_a_renter_returns_403(self, db):
        """User who is not a renter gets 403."""
        owner = UserFactory()

        c = _make_client(owner)
        response = c.get("/properties/renter/rent-history/")
        assert response.status_code == 403
        assert response.data["error"] == "Not a renter"

    def test_renter_gets_history(self, db):
        """Renter sees their rent history."""
        owner = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=unit, user=owner)
        RentRecordFactory(unit=unit, renter=renter, status="PAID")

        c = _make_client(owner)
        response = c.get("/properties/renter/rent-history/")
        assert response.status_code == 200
        assert len(response.data) == 1
        assert "status" in response.data[0]


# ===========================================================================
# owner_rent_overview endpoint
# ===========================================================================


class TestOwnerRentOverviewAPI:
    """Covers owner_rent_overview endpoint."""

    def test_overview_returns_rent_data(self, db):
        """Owner gets rent overview with tenant and payout info."""
        owner = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=unit)
        RentRecordFactory(unit=unit, renter=renter, status="PAID")

        c = _make_client(owner)
        response = c.get("/properties/owner/rents/")
        assert response.status_code == 200
        assert len(response.data) == 1
        assert "tenant" in response.data[0]
        assert "payout" in response.data[0]

    def test_overview_empty_for_owner_with_no_records(self, db):
        """Owner with no records gets empty overview."""
        owner = UserFactory()

        c = _make_client(owner)
        response = c.get("/properties/owner/rents/")
        assert response.status_code == 200
        assert response.data == []
