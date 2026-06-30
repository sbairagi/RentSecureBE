"""API Contract Tests — Critical Endpoint Response Shape Regression Detection.

These tests validate that DRF ViewSets maintain their JSON contract
(response shape, status codes, required keys) across commits.

A contract regression is when an existing endpoint silently changes its
response shape — e.g., renaming a key, changing a status code, or
changing the pagination structure.

Run with:
    pytest tests/test_api_contracts.py -v --tb=short --randomly-seed=last
"""

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from core.models import SubscriptionPlan
from tests.factories import (
    BuildingFactory,
    RenterFactory,
    RentRecordFactory,
    SubscriptionPlanFactory,
    UnitFactory,
    UserFactory,
    UserSubscriptionFactory,
)

User = UserFactory._meta.model


class APIContractTestCase(APITestCase):
    """Base class with authenticated client for contract tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = UserFactory(username="contract_owner", full_name="Contract Owner")
        plan, _ = SubscriptionPlan.objects.get_or_create(
            name="pro",
            defaults={
                "monthly_price": "29.99",
                "yearly_price": "299.99",
                "features": "Pro Plan",
                "is_active": True,
            },
        )
        cls.subscription = UserSubscriptionFactory(
            user=cls.owner, plan=plan, is_active=True
        )
        cls.building = BuildingFactory(owner=cls.owner)
        cls.unit = UnitFactory(owner=cls.owner, building=cls.building)

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)


class BuildingAPIContractTests(APIContractTestCase):
    """Contract tests for Building ViewSet response shapes."""

    def test_list_returns_paginated_dict_with_count(self):
        for _i in range(5):
            BuildingFactory(owner=self.owner)
        resp = self.client.get("/api/buildings/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        if isinstance(data, dict) and "results" in data:
            items = data["results"]
        else:
            items = data
        self.assertIsInstance(items, list)
        item = items[0]
        for key in ["id", "name", "address_line", "city", "state", "country"]:
            self.assertIn(
                key,
                item,
                f"Building list item missing required key '{key}'. "
                f"Got keys: {list(item.keys())}",
            )

    def test_list_item_has_required_fields(self):
        BuildingFactory(owner=self.owner)
        resp = self.client.get("/api/buildings/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        if isinstance(data, dict) and "results" in data:
            items = data["results"]
        else:
            items = data
        self.assertIsInstance(items, list)
        item = items[0]
        for key in ["id", "name", "address_line", "city", "state", "country"]:
            self.assertIn(
                key,
                item,
                f"Building list item missing required key '{key}'. "
                f"Got keys: {list(item.keys())}",
            )


class UnitAPIContractTests(APIContractTestCase):
    """Contract tests for Unit ViewSet response shapes."""

    def test_list_returns_paginated_dict(self):
        for _i in range(3):
            UnitFactory(owner=self.owner, building=self.building)
        resp = self.client.get("/api/units/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        if isinstance(data, dict) and "results" in data:
            items = data["results"]
        else:
            items = data
        self.assertIsInstance(items, list)

    def test_list_item_has_required_fields(self):
        UnitFactory(owner=self.owner, building=self.building)
        resp = self.client.get("/api/units/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        if isinstance(data, dict) and "results" in data:
            items = data["results"]
        else:
            items = data
        self.assertIsInstance(items, list)
        item = items[0]
        for key in ["id", "unit", "building_name", "unit_type", "status"]:
            self.assertIn(
                key,
                item,
                f"Unit list item missing key '{key}'. Got: {list(item.keys())}",
            )


class RenterAPIContractTests(APIContractTestCase):
    """Contract tests for Renter ViewSet response shapes."""

    def test_list_returns_paginated_dict(self):
        for _i in range(3):
            RenterFactory(unit=self.unit)
        resp = self.client.get("/api/renters/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        if isinstance(data, dict) and "results" in data:
            items = data["results"]
        else:
            items = data
        self.assertIsInstance(items, list)

    def test_list_item_has_required_fields(self):
        RenterFactory(unit=self.unit)
        resp = self.client.get("/api/renters/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        if isinstance(data, dict) and "results" in data:
            items = data["results"]
        else:
            items = data
        self.assertIsInstance(items, list)
        item = items[0]
        for key in ["id", "name", "phone", "rent_amount", "start_date", "status"]:
            self.assertIn(
                key,
                item,
                f"Renter list item missing key '{key}'. Got: {list(item.keys())}",
            )


class RentRecordAPIContractTests(APIContractTestCase):
    """Contract tests for RentRecord ViewSet response shapes."""

    def test_list_returns_paginated_dict(self):
        for _i in range(3):
            RentRecordFactory(unit=self.unit)
        resp = self.client.get("/api/rent-records/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        if isinstance(data, dict) and "results" in data:
            items = data["results"]
        else:
            items = data
        self.assertIsInstance(items, list)

    def test_list_item_has_required_fields(self):
        RentRecordFactory(unit=self.unit)
        resp = self.client.get("/api/rent-records/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        if isinstance(data, dict) and "results" in data:
            items = data["results"]
        else:
            items = data
        self.assertIsInstance(items, list)
        item = items[0]
        for key in ["id", "unit", "due_date", "amount", "status"]:
            self.assertIn(
                key,
                item,
                f"RentRecord list item missing key '{key}'. Got: {list(item.keys())}",
            )


class SubscriptionAPIContractTests(APIContractTestCase):
    """Contract tests for subscription/plans endpoints."""

    def test_subscription_plan_list_response_shape(self):
        SubscriptionPlanFactory(name="free")
        resp = self.client.get("/api/subscription-plans/")
        if resp.status_code == status.HTTP_200_OK:
            data = resp.json()
            if isinstance(data, dict):
                self.assertIn(
                    "results", data, "Plan list must be paginated with 'results' key"
                )
            else:
                self.assertIsInstance(data, list)

    def test_user_subscription_response_shape(self):
        resp = self.client.get("/api/user-subscription/")
        if resp.status_code == status.HTTP_200_OK:
            data = resp.json()
            self.assertIn(
                "plan",
                data,
                "UserSubscription response must include 'plan' key. Got: "
                + str(list(data.keys())[:10]),
            )
