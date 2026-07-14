"""Tests for properties/views/building_views.py — cover missed branches (29->33, 34-38, 57, 66)."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient, APIRequestFactory, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model

from core.models import PlanFeatureLimit, SubscriptionPlan, UserSubscription
from properties.models import Building
from properties.views.building_views import BuildingViewSet

User = get_user_model()


def _jwt_client(user):
    client = APIClient()
    token = RefreshToken.for_user(user).access_token
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def _drf_request(method, path, user):
    factory = APIRequestFactory()
    token = RefreshToken.for_user(user).access_token
    req = getattr(factory, method.lower())(path, HTTP_AUTHORIZATION=f"Bearer {token}")
    req.user = user
    return req


class TestBuildingViewSetCacheHitAndExpiredGrace(APITestCase):
    """Cover get_queryset branches: 29->33 and 34-38."""

    def setUp(self):
        super().setUp()
        self.owner = User.objects.create_user(
            username="cbh_owner", password="p", full_name="CBHOwner", phone="+1"
        )

    def test_cache_hit_active_subscription_returns_all(self):
        """Line 29 False branch (cache hit), line 33 False → line 40."""
        pro_plan = SubscriptionPlan.objects.create(
            name="cbh_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        PlanFeatureLimit.objects.create(
            plan=pro_plan, feature_key="max_buildings", value="10"
        )
        UserSubscription.objects.create(user=self.owner, plan=pro_plan, is_active=True)
        Building.objects.create(
            owner=self.owner,
            name="CB1",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        Building.objects.create(
            owner=self.owner,
            name="CB2",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )

        view = BuildingViewSet.as_view({"get": "list"})

        # First request → cache miss (line 29 True branch taken)
        r1 = view(_drf_request("GET", "/properties/buildings/", self.owner))
        assert r1.status_code == 200
        assert len(r1.data) == 2

        # Second request → cache hit (line 29 False branch taken)
        r2 = view(_drf_request("GET", "/properties/buildings/", self.owner))
        assert r2.status_code == 200
        assert len(r2.data) == 2

    def test_expired_past_grace_unlimited_returns_active_buildings(self):
        """Lines 33 True, 36 True, 37 → return active_buildings (unlimited)."""
        free_plan = SubscriptionPlan.objects.create(
            name="cbh_free",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Free",
        )
        PlanFeatureLimit.objects.create(
            plan=free_plan, feature_key="max_buildings", value="unlimited"
        )
        UserSubscription.objects.create(user=self.owner, plan=free_plan, is_active=True)
        active = Building.objects.create(
            owner=self.owner,
            name="ActiveB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
            is_archived=False,
        )
        archived = Building.objects.create(
            owner=self.owner,
            name="ArchivedB",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
            is_archived=True,
        )

        view = BuildingViewSet.as_view({"get": "list"})

        with patch(
            "properties.services.building_service.FeatureEnforcer"
        ) as mock_enforcer:
            mock_instance = mock_enforcer.return_value
            mock_instance.is_expired.return_value = True
            mock_instance.is_past_grace_period.return_value = True
            mock_instance.get_free_plan_limit.return_value = "unlimited"

            r = view(_drf_request("GET", "/properties/buildings/", self.owner))
            assert r.status_code == 200
            ids = [b["id"] for b in r.data]
            assert active.id in ids
            assert archived.id not in ids

    def test_expired_past_grace_numeric_limit_slices_active_buildings(self):
        """Lines 33 True, 36 False, 38 → return active_buildings[:free_limit]."""
        free_plan = SubscriptionPlan.objects.create(
            name="cbh_free2",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Free",
        )
        PlanFeatureLimit.objects.create(
            plan=free_plan, feature_key="max_buildings", value="1"
        )
        UserSubscription.objects.create(user=self.owner, plan=free_plan, is_active=True)
        Building.objects.create(
            owner=self.owner,
            name="A",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
            is_archived=False,
        )
        Building.objects.create(
            owner=self.owner,
            name="B",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
            is_archived=False,
        )
        Building.objects.create(
            owner=self.owner,
            name="ArchC",
            address_line="3 St",
            city="C",
            state="S",
            country="CO",
            postal_code="3",
            is_archived=True,
        )

        view = BuildingViewSet.as_view({"get": "list"})

        with patch(
            "properties.services.building_service.FeatureEnforcer"
        ) as mock_enforcer:
            mock_instance = mock_enforcer.return_value
            mock_instance.is_expired.return_value = True
            mock_instance.is_past_grace_period.return_value = True
            mock_instance.get_free_plan_limit.return_value = 1

            r = view(_drf_request("GET", "/properties/buildings/", self.owner))
            assert r.status_code == 200
            assert len(r.data) == 1


class TestBuildingViewSetPerformUpdateDenied(APITestCase):
    """Cover line 57: perform_update with wrong owner."""

    def setUp(self):
        super().setUp()
        self.owner = User.objects.create_user(
            username="pu_owner", password="p", full_name="PUOwner", phone="+1"
        )
        self.other = User.objects.create_user(
            username="pu_other", password="p", full_name="PUOther", phone="+2"
        )
        plan = SubscriptionPlan.objects.create(
            name="pu_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=self.other, plan=plan, is_active=True)

    def test_perform_update_owner_mismatch_raises_permission_denied(self):
        """Line 57 True → PermissionDenied."""
        target = Building.objects.create(
            owner=self.owner,
            name="TargetB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

        view = BuildingViewSet()
        view.request = MagicMock()
        view.request.user = self.other

        mock_serializer = MagicMock()
        mock_serializer.instance = target

        with pytest.raises(PermissionDenied) as exc_info:
            view.perform_update(mock_serializer)
        assert "permission" in str(exc_info.value).lower()


class TestBuildingViewSetPerformDestroyDenied(APITestCase):
    """Cover line 66: perform_destroy with wrong owner."""

    def setUp(self):
        super().setUp()
        self.owner = User.objects.create_user(
            username="pd_owner", password="p", full_name="PDOwner", phone="+1"
        )
        self.other = User.objects.create_user(
            username="pd_other", password="p", full_name="PDOther", phone="+2"
        )
        plan = SubscriptionPlan.objects.create(
            name="pd_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=self.other, plan=plan, is_active=True)

    def test_perform_destroy_owner_mismatch_raises_permission_denied(self):
        """Line 66 True → PermissionDenied."""
        target = Building.objects.create(
            owner=self.owner,
            name="TargetB2",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

        view = BuildingViewSet()
        view.request = MagicMock()
        view.request.user = self.other

        with pytest.raises(PermissionDenied) as exc_info:
            view.perform_destroy(target)
        assert "permission" in str(exc_info.value).lower()
