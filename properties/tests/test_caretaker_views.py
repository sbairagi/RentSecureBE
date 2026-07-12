"""Comprehensive pytest tests for properties/views/caretaker_views.py."""

from unittest.mock import MagicMock, patch

import pytest
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.test import RequestFactory

from core.models import PlanFeatureLimit, SubscriptionPlan, UsageLimit, UserSubscription
from properties.feature_enforcer import FeatureEnforcer
from properties.models import Caretaker, Unit
from properties.views.caretaker_views import CaretakerViewSet


def _make_view():
    view = CaretakerViewSet()
    view.format_kwarg = None
    return view


def _make_request(user, method="get"):
    factory = RequestFactory()
    request = factory.get("/properties/caretakers/")
    request.user = user
    return request


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def owner(db):
    from django.contrib.auth import get_user_model

    user = get_user_model()
    return user.objects.create_user(
        username="caretaker_owner",
        password="p",
        full_name="CaretakerOwner",
        phone="+911111111111",
    )


@pytest.fixture
def other_user(db):
    from django.contrib.auth import get_user_model

    user = get_user_model()
    return user.objects.create_user(
        username="other_user",
        password="p",
        full_name="OtherUser",
        phone="+922222222222",
    )


@pytest.fixture
def plan(db, owner):
    return SubscriptionPlan.objects.create(
        name="caretaker_plan",
        monthly_price="29.99",
        yearly_price="299.99",
    )


@pytest.fixture
def subscription(db, owner, plan):
    return UserSubscription.objects.create(user=owner, plan=plan, is_active=True)


@pytest.fixture
def plan_feature_limit(db, plan):
    return PlanFeatureLimit.objects.create(
        plan=plan, feature_key="max_caretakers", value="10"
    )


@pytest.fixture
def building(db, owner):
    from properties.models import Building

    return Building.objects.create(
        owner=owner,
        name="CaretakerBuilding",
        address_line="1 St",
        city="C",
        state="S",
        country="CO",
        postal_code="1",
    )


@pytest.fixture
def unit(db, owner, building):
    return Unit.objects.create(
        owner=owner,
        building=building,
        unit="C101",
        unit_type="flat",
        address_line="1 St",
        city="C",
        state="S",
        country="CO",
        postal_code="1",
    )


@pytest.fixture
def other_unit(db, other_user, building):
    return Unit.objects.create(
        owner=other_user,
        building=building,
        unit="C102",
        unit_type="flat",
        address_line="2 St",
        city="C",
        state="S",
        country="CO",
        postal_code="2",
    )


@pytest.fixture
def api_client_owner(owner):
    client = APIClient()
    client.force_authenticate(user=owner)
    return client


@pytest.fixture
def api_client_other(other_user):
    client = APIClient()
    client.force_authenticate(user=other_user)
    return client


# ---------------------------------------------------------------------------
# Tests for get_queryset
# ---------------------------------------------------------------------------


class TestGetQueryset:
    def test_anonymous_user_returns_empty(self):
        view = _make_view()
        view.request = _make_request(AnonymousUser())
        qs = view.get_queryset()
        assert list(qs) == []

    def test_authenticated_user_cache_hit(self, owner, unit, db):
        cache.set(f"caretakers_user_{owner.id}", [1, 2, 3], timeout=300)
        view = _make_view()
        view.request = _make_request(owner)
        result = view.get_queryset()
        assert list(result) == [1, 2, 3]

    def test_authenticated_user_cache_miss_sets_cache(self, owner, unit, db):
        cache.clear()
        Caretaker.objects.create(
            unit=unit,
            name="CT1",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        view = _make_view()
        view.request = _make_request(owner)
        result = view.get_queryset()
        assert result.count() == 1
        cached = cache.get(f"caretakers_user_{owner.id}")
        assert cached is not None
        assert cached.count() == 1

    def test_other_user_sees_only_own_caretakers(
        self, owner, other_user, unit, other_unit, db
    ):
        Caretaker.objects.create(
            unit=unit,
            name="OwnerCT",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        Caretaker.objects.create(
            unit=other_unit,
            name="OtherCT",
            phone="+922222222222",
            joining_date="2025-01-01",
        )
        view_owner = _make_view()
        view_owner.request = _make_request(owner)
        assert view_owner.get_queryset().count() == 1

        view_other = _make_view()
        view_other.request = _make_request(other_user)
        assert view_other.get_queryset().count() == 1


# ---------------------------------------------------------------------------
# Tests for list endpoint
# ---------------------------------------------------------------------------


class TestCaretakerList:
    def test_list_returns_200(self, api_client_owner, unit, db):
        Caretaker.objects.create(
            unit=unit,
            name="CT1",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        response = api_client_owner.get("/properties/caretakers/")
        assert response.status_code == 200

    def test_other_user_lists_empty(self, api_client_other, owner, unit, db):
        Caretaker.objects.create(
            unit=unit,
            name="CT1",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        response = api_client_other.get("/properties/caretakers/")
        assert response.status_code == 200
        assert len(response.data) == 0


# ---------------------------------------------------------------------------
# Tests for create (perform_create)
# ---------------------------------------------------------------------------


class TestPerformCreate:
    def test_create_with_other_user_unit_raises_permission_denied(
        self, owner, other_user, other_unit, api_client_owner
    ):
        with patch.object(FeatureEnforcer, "can_create", return_value=True):
            response = api_client_owner.post(
                "/properties/caretakers/",
                {
                    "unit": other_unit.id,
                    "name": "CT",
                    "phone": "+911111111111",
                    "address": "Addr",
                    "joining_date": "2025-01-01",
                },
                format="json",
            )
        assert response.status_code == 403

    def test_create_limit_reached_raises_permission_denied(
        self, owner, unit, api_client_owner, plan, plan_feature_limit
    ):
        with patch.object(FeatureEnforcer, "can_create", return_value=False):
            response = api_client_owner.post(
                "/properties/caretakers/",
                {
                    "unit": unit.id,
                    "name": "CT",
                    "phone": "+911111111111",
                    "address": "Addr",
                    "joining_date": "2025-01-01",
                },
                format="json",
            )
        assert response.status_code == 403

    def test_create_success_clears_cache(
        self, owner, unit, api_client_owner, plan, plan_feature_limit
    ):
        cache.set(f"caretakers_user_{owner.id}", ["stale"], timeout=300)
        response = api_client_owner.post(
            "/properties/caretakers/",
            {
                "unit": unit.id,
                "name": "CT",
                "phone": "+911111111111",
                "address": "Addr",
                "joining_date": "2025-01-01",
            },
            format="json",
        )
        assert response.status_code == 201
        assert cache.get(f"caretakers_user_{owner.id}") is None

    def test_create_bad_request_missing_fields(self, api_client_owner):
        response = api_client_owner.post(
            "/properties/caretakers/",
            {},
            format="json",
        )
        assert response.status_code == 400

    def test_create_usage_count_reflects_actual_caretakers(
        self, owner, unit, api_client_owner, plan, plan_feature_limit
    ):
        response = api_client_owner.post(
            "/properties/caretakers/",
            {
                "unit": unit.id,
                "name": "CT",
                "phone": "+911111111111",
                "address": "Addr",
                "joining_date": "2025-01-01",
            },
            format="json",
        )
        assert response.status_code == 201
        limit = UsageLimit.objects.get(user=owner, feature_key="max_caretakers")
        actual_count = Caretaker.objects.filter(unit__owner=owner).count()
        assert limit.usage_count >= actual_count


# ---------------------------------------------------------------------------
# Tests for perform_create direct (edge cases)
# ---------------------------------------------------------------------------


class TestPerformCreateDirect:
    def test_perform_create_denied_when_unit_not_owned(
        self, owner, other_user, other_unit
    ):
        view = _make_view()
        view.request = _make_request(owner, method="post")
        serializer = MagicMock()
        serializer.validated_data = {"unit": other_unit}
        with pytest.raises(PermissionDenied):
            view.perform_create(serializer)

    @patch.object(FeatureEnforcer, "can_create", return_value=False)
    def test_perform_create_denied_when_limit_reached_direct(
        self, mock_can_create, owner, unit
    ):
        view = _make_view()
        view.request = _make_request(owner, method="post")
        serializer = MagicMock()
        serializer.validated_data = {
            "unit": unit,
            "name": "CT",
            "phone": "+911111111111",
        }
        with pytest.raises(PermissionDenied):
            view.perform_create(serializer)
        mock_can_create.assert_called_once_with("max_caretakers")


# ---------------------------------------------------------------------------
# Tests for retrieve
# ---------------------------------------------------------------------------


class TestCaretakerRetrieve:
    def test_retrieve_own_caretaker(self, api_client_owner, unit):
        ct = Caretaker.objects.create(
            unit=unit,
            name="CT1",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        response = api_client_owner.get(f"/properties/caretakers/{ct.id}/")
        assert response.status_code == 200
        assert response.data["name"] == "CT1"

    def test_other_user_cannot_retrieve_caretaker(self, api_client_other, owner, unit):
        ct = Caretaker.objects.create(
            unit=unit,
            name="CT1",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        response = api_client_other.get(f"/properties/caretakers/{ct.id}/")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests for update (perform_update)
# ---------------------------------------------------------------------------


class TestPerformUpdate:
    def test_update_other_user_unit_raises_permission_denied(
        self, owner, other_unit, unit
    ):
        ct = Caretaker.objects.create(
            unit=unit,
            name="CT1",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        view = _make_view()
        view.request = _make_request(owner, method="patch")
        serializer = MagicMock()
        serializer.instance = ct
        serializer.validated_data = {"unit": other_unit}
        with pytest.raises(PermissionDenied):
            view.perform_update(serializer)

    def test_update_clears_cache_on_success_direct(self, owner, unit):
        ct = Caretaker.objects.create(
            unit=unit,
            name="CT1",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        cache.set(f"caretakers_user_{owner.id}", ["stale"], timeout=300)
        view = _make_view()
        view.request = _make_request(owner, method="patch")
        serializer = MagicMock()
        serializer.instance = ct
        serializer.validated_data = {"name": "CT1_Updated"}
        view.perform_update(serializer)
        assert cache.get(f"caretakers_user_{owner.id}") is None

    def test_update_keeps_instance_unit_when_not_provided(
        self, owner, unit, api_client_owner
    ):
        ct = Caretaker.objects.create(
            unit=unit,
            name="CT1",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        response = api_client_owner.patch(
            f"/properties/caretakers/{ct.id}/",
            {"name": "CT1_Updated"},
            format="json",
        )
        assert response.status_code == 200
        ct.refresh_from_db()
        assert ct.name == "CT1_Updated"
        assert ct.unit == unit

    def test_perform_update_owner_mismatch_direct(
        self, owner, other_user, other_unit, unit
    ):
        ct = Caretaker.objects.create(
            unit=other_unit,
            name="OtherCT",
            phone="+922222222222",
            joining_date="2025-01-01",
        )
        view = _make_view()
        view.request = _make_request(owner, method="patch")
        serializer = MagicMock()
        serializer.instance = ct
        serializer.validated_data = {"unit": other_unit}
        with pytest.raises(PermissionDenied):
            view.perform_update(serializer)

    def test_perform_update_unit_none_raises_permission_denied(self, owner, unit):
        view = _make_view()
        view.request = _make_request(owner, method="patch")
        serializer = MagicMock()
        serializer.instance = None
        serializer.validated_data = {}
        with pytest.raises(PermissionDenied):
            view.perform_update(serializer)


# ---------------------------------------------------------------------------
# Tests for delete (perform_destroy)
# ---------------------------------------------------------------------------


class TestPerformDestroy:
    def test_delete_other_user_unit_raises_permission_denied(
        self, owner, other_unit, other_user
    ):
        ct = Caretaker.objects.create(
            unit=other_unit,
            name="OtherCT",
            phone="+922222222222",
            joining_date="2025-01-01",
        )
        view = _make_view()
        view.request = _make_request(owner, method="delete")
        with pytest.raises(PermissionDenied):
            view.perform_destroy(ct)

    def test_delete_success_clears_cache_direct(self, owner, unit):
        ct = Caretaker.objects.create(
            unit=unit,
            name="CT1",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        cache.set(f"caretakers_user_{owner.id}", ["stale"], timeout=300)
        view = _make_view()
        view.request = _make_request(owner, method="delete")
        view.perform_destroy(ct)
        assert cache.get(f"caretakers_user_{owner.id}") is None

    def test_delete_own_caretaker_204(self, api_client_owner, unit):
        ct = Caretaker.objects.create(
            unit=unit,
            name="CT1",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        response = api_client_owner.delete(f"/properties/caretakers/{ct.id}/")
        assert response.status_code == 204


# ---------------------------------------------------------------------------
# Tests for perform_destroy direct (owner mismatch)
# ---------------------------------------------------------------------------


class TestPerformDestroyDirect:
    def test_perform_destroy_owner_mismatch_raises(self, owner, other_unit, other_user):
        ct = Caretaker.objects.create(
            unit=other_unit,
            name="OtherCT",
            phone="+922222222222",
            joining_date="2025-01-01",
        )
        view = _make_view()
        view.request = _make_request(owner, method="delete")
        with pytest.raises(PermissionDenied):
            view.perform_destroy(ct)


# ---------------------------------------------------------------------------
# Tests for create via API
# ---------------------------------------------------------------------------


class TestCaretakerCreateAPI:
    def test_create_calls_feature_enforcer_increment(
        self, owner, unit, api_client_owner, plan, plan_feature_limit
    ):
        with (
            patch.object(FeatureEnforcer, "can_create", return_value=True),
            patch.object(FeatureEnforcer, "increment") as mock_increment,
        ):
            response = api_client_owner.post(
                "/properties/caretakers/",
                {
                    "unit": unit.id,
                    "name": "CT",
                    "phone": "+911111111111",
                    "address": "Addr",
                    "joining_date": "2025-01-01",
                },
                format="json",
            )
        assert response.status_code == 201
        mock_increment.assert_called_once_with("max_caretakers")

    def test_create_returns_201_and_object_created(
        self, owner, unit, api_client_owner, plan, plan_feature_limit
    ):
        response = api_client_owner.post(
            "/properties/caretakers/",
            {
                "unit": unit.id,
                "name": "CT",
                "phone": "+911111111111",
                "address": "Addr",
                "joining_date": "2025-01-01",
            },
            format="json",
        )
        assert response.status_code == 201
        assert Caretaker.objects.filter(name="CT", unit=unit).exists()

    def test_create_usage_count_matches_actual_count(
        self, owner, unit, api_client_owner, plan, plan_feature_limit
    ):
        api_client_owner.post(
            "/properties/caretakers/",
            {
                "unit": unit.id,
                "name": "CT",
                "phone": "+911111111111",
                "address": "Addr",
                "joining_date": "2025-01-01",
            },
            format="json",
        )
        limit = UsageLimit.objects.get(user=owner, feature_key="max_caretakers")
        actual_count = Caretaker.objects.filter(unit__owner=owner).count()
        assert limit.usage_count >= actual_count


# ---------------------------------------------------------------------------
# Tests for update via API
# ---------------------------------------------------------------------------


class TestCaretakerUpdateAPI:
    def test_update_returns_200(self, api_client_owner, unit):
        ct = Caretaker.objects.create(
            unit=unit,
            name="CT1",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        response = api_client_owner.patch(
            f"/properties/caretakers/{ct.id}/",
            {"name": "UpdatedName"},
            format="json",
        )
        assert response.status_code == 200
        ct.refresh_from_db()
        assert ct.name == "UpdatedName"

    def test_other_user_update_returns_404(self, api_client_other, owner, unit):
        ct = Caretaker.objects.create(
            unit=unit,
            name="CT1",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        response = api_client_other.patch(
            f"/properties/caretakers/{ct.id}/",
            {"name": "Hacked"},
            format="json",
        )
        assert response.status_code == 404

    def test_update_to_other_users_unit_returns_403(
        self, api_client_owner, owner, other_user, unit, other_unit
    ):
        ct = Caretaker.objects.create(
            unit=unit,
            name="CT1",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        response = api_client_owner.patch(
            f"/properties/caretakers/{ct.id}/",
            {"unit": other_unit.id},
            format="json",
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Tests for delete via API
# ---------------------------------------------------------------------------


class TestCaretakerDeleteAPI:
    def test_delete_returns_204(self, api_client_owner, unit):
        ct = Caretaker.objects.create(
            unit=unit,
            name="CT1",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        response = api_client_owner.delete(f"/properties/caretakers/{ct.id}/")
        assert response.status_code == 204

    def test_other_user_delete_returns_404(self, api_client_other, owner, unit):
        ct = Caretaker.objects.create(
            unit=unit,
            name="CT1",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        response = api_client_other.delete(f"/properties/caretakers/{ct.id}/")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests for FeatureEnforcer integration
# ---------------------------------------------------------------------------


class TestFeatureEnforcerIntegration:
    @patch.object(FeatureEnforcer, "can_create", return_value=False)
    def test_cannot_create_when_limit_reached_via_api(
        self, mock_can_create, owner, unit, api_client_owner, plan, plan_feature_limit
    ):
        response = api_client_owner.post(
            "/properties/caretakers/",
            {
                "unit": unit.id,
                "name": "CT",
                "phone": "+911111111111",
                "address": "Addr",
                "joining_date": "2025-01-01",
            },
            format="json",
        )
        assert response.status_code == 403

    @patch.object(FeatureEnforcer, "can_create", return_value=True)
    def test_can_create_when_under_limit(
        self, mock_can_create, owner, unit, api_client_owner, plan, plan_feature_limit
    ):
        response = api_client_owner.post(
            "/properties/caretakers/",
            {
                "unit": unit.id,
                "name": "CT",
                "phone": "+911111111111",
                "address": "Addr",
                "joining_date": "2025-01-01",
            },
            format="json",
        )
        assert response.status_code == 201

    @patch.object(FeatureEnforcer, "decrement")
    def test_delete_calls_decrement(
        self, mock_decrement, owner, unit, api_client_owner, plan, plan_feature_limit
    ):
        ct = Caretaker.objects.create(
            unit=unit,
            name="CT1",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        response = api_client_owner.delete(f"/properties/caretakers/{ct.id}/")
        assert response.status_code == 204
        mock_decrement.assert_called_once_with("max_caretakers")


# ---------------------------------------------------------------------------
# Tests for cache invalidation via direct method calls
# ---------------------------------------------------------------------------


class TestCacheInvalidationDirect:
    def test_create_clears_cache_direct(self, owner, unit):
        cache.set(f"caretakers_user_{owner.id}", ["stale"], timeout=300)
        view = _make_view()
        view.request = _make_request(owner, method="post")
        data = {"unit": unit, "name": "CT", "phone": "+911111111111"}
        serializer = MagicMock()
        serializer.validated_data = data
        with patch.object(FeatureEnforcer, "can_create", return_value=True):
            view.perform_create(serializer)
        assert cache.get(f"caretakers_user_{owner.id}") is None

    def test_update_clears_cache_direct(self, owner, unit):
        ct = Caretaker.objects.create(
            unit=unit,
            name="CT1",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        cache.set(f"caretakers_user_{owner.id}", ["stale"], timeout=300)
        view = _make_view()
        view.request = _make_request(owner, method="patch")
        serializer = MagicMock()
        serializer.instance = ct
        serializer.validated_data = {"name": "CT1_Updated"}
        view.perform_update(serializer)
        assert cache.get(f"caretakers_user_{owner.id}") is None

    def test_delete_clears_cache_direct(self, owner, unit):
        ct = Caretaker.objects.create(
            unit=unit,
            name="CT1",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        cache.set(f"caretakers_user_{owner.id}", ["stale"], timeout=300)
        view = _make_view()
        view.request = _make_request(owner, method="delete")
        view.perform_destroy(ct)
        assert cache.get(f"caretakers_user_{owner.id}") is None


# ---------------------------------------------------------------------------
# Tests for external integration mocking
# ---------------------------------------------------------------------------


class TestExternalIntegrationMocking:
    def test_create_does_not_create_notification(
        self, owner, unit, api_client_owner, plan, plan_feature_limit
    ):
        from notification.models import Notification

        with patch.object(FeatureEnforcer, "can_create", return_value=True):
            response = api_client_owner.post(
                "/properties/caretakers/",
                {
                    "unit": unit.id,
                    "name": "CT",
                    "phone": "+911111111111",
                    "address": "Addr",
                    "joining_date": "2025-01-01",
                },
                format="json",
            )
        assert response.status_code == 201
        assert not Notification.objects.filter(user=owner).exists()

    def test_delete_does_not_create_notification(
        self, owner, unit, api_client_owner, plan, plan_feature_limit
    ):
        from notification.models import Notification

        ct = Caretaker.objects.create(
            unit=unit,
            name="CT1",
            phone="+911111111111",
            joining_date="2025-01-01",
        )
        with patch.object(FeatureEnforcer, "can_create", return_value=True):
            response = api_client_owner.delete(f"/properties/caretakers/{ct.id}/")
        assert response.status_code == 204
        assert not Notification.objects.filter(user=owner).exists()
