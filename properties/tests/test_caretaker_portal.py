"""Tests for the caretaker portal and for the caretaker assignments.

A caretaker works for one owner and looks after the buildings and the
standalone units the owner assigned to them. These tests cover the owner
side (hiring, assigning) and the caretaker side (today, properties,
maintenance, tenants).
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import PlanFeatureLimit, SubscriptionPlan, UserSubscription
from properties.models import (
    Building,
    CareTaker,
    CareTakerAssignment,
    MaintenanceRequest,
    Renter,
    Unit,
)

User = get_user_model()


@pytest.fixture
def owner(db):
    return User.objects.create_user(
        username="ct_owner",
        password="p",
        full_name="Owner One",
        phone="+911111111111",
    )


@pytest.fixture
def other_owner(db):
    return User.objects.create_user(
        username="ct_other_owner",
        password="p",
        full_name="Owner Two",
        phone="+922222222222",
    )


@pytest.fixture
def plan(db):
    return SubscriptionPlan.objects.create(
        name="ct_plan",
        monthly_price=Decimal("29.99"),
        yearly_price=Decimal("299.99"),
    )


@pytest.fixture
def subscription(db, owner, plan):
    UserSubscription.objects.create(user=owner, plan=plan, is_active=True)
    PlanFeatureLimit.objects.create(plan=plan, feature_key="max_caretakers", value="10")
    return plan


@pytest.fixture
def building(db, owner):
    return Building.objects.create(
        owner=owner,
        name="Sunrise Complex",
        address_line="1 Main St",
        city="Pune",
        state="MH",
        country="IN",
        postal_code="411001",
    )


@pytest.fixture
def other_building(db, other_owner):
    return Building.objects.create(
        owner=other_owner,
        name="Neighbour Tower",
        address_line="2 Main St",
        city="Pune",
        state="MH",
        country="IN",
        postal_code="411002",
    )


@pytest.fixture
def unit(db, owner, building):
    return Unit.objects.create(
        owner=owner,
        building=building,
        unit="A101",
        unit_type="flat",
        address_line="1 Main St",
        city="Pune",
        state="MH",
        country="IN",
        postal_code="411001",
    )


@pytest.fixture
def standalone_unit(db, owner):
    return Unit.objects.create(
        owner=owner,
        building=None,
        unit="Villa 5",
        unit_type="villa",
        address_line="5 Lane St",
        city="Pune",
        state="MH",
        country="IN",
        postal_code="411003",
    )


@pytest.fixture
def caretaker_user(db):
    return User.objects.create_user(
        username="ct_worker",
        password="p",
        full_name="Caretaker Kumar",
        phone="+933333333333",
    )


@pytest.fixture
def caretaker(db, owner, caretaker_user, unit):
    return CareTaker.objects.create(
        owner=owner,
        unit=unit,
        user=caretaker_user,
        name="Caretaker Kumar",
        phone="+933333333333",
        joining_date=date.today(),
    )


@pytest.fixture
def owner_client(owner):
    client = APIClient()
    client.force_authenticate(user=owner)
    return client


@pytest.fixture
def caretaker_client(caretaker_user):
    client = APIClient()
    client.force_authenticate(user=caretaker_user)
    return client


# ---------------------------------------------------------------------------
# The owner manages the team
# ---------------------------------------------------------------------------


class TestCaretakerTeam:
    def test_owner_sees_only_own_caretakers(self, owner_client, caretaker, owner):
        response = owner_client.get("/properties/caretakers/")
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_caretaker_belongs_to_the_owner(self, caretaker, owner):
        assert caretaker.owner_id == owner.id

    def test_owner_hires_a_caretaker(self, owner_client, subscription, unit):
        response = owner_client.post(
            "/properties/caretakers/",
            {
                "name": "New Caretaker",
                "phone": "+944444444444",
                "email": "new@caretaker.test",
                "joining_date": "2026-01-01",
                "unit": unit.id,
            },
            format="json",
        )
        assert response.status_code == 201
        created = CareTaker.objects.get(name="New Caretaker")
        assert created.owner_id == owner_client.handler._force_user.id

    def test_owner_hires_a_caretaker_without_home_unit(
        self, owner_client, subscription
    ):
        response = owner_client.post(
            "/properties/caretakers/",
            {
                "name": "Roaming Caretaker",
                "phone": "+955555555555",
                "joining_date": "2026-01-01",
            },
            format="json",
        )
        assert response.status_code == 201
        assert CareTaker.objects.filter(name="Roaming Caretaker").exists()

    def test_deactivate_ends_the_assignments(self, owner_client, caretaker, building):
        owner_client.post(
            f"/properties/caretakers/{caretaker.id}/assignments/",
            {"building": building.id},
            format="json",
        )
        response = owner_client.post(
            f"/properties/caretakers/{caretaker.id}/deactivate/"
        )
        assert response.status_code == 200
        caretaker.refresh_from_db()
        assert caretaker.is_active is False
        assert caretaker.assignments.filter(is_active=True).count() == 0

    def test_the_quota_counts_the_active_team(
        self, owner_client, caretaker, subscription
    ):
        owner_client.post(
            "/properties/caretakers/",
            {
                "name": "Second Caretaker",
                "phone": "+955555555555",
                "joining_date": "2026-01-01",
            },
            format="json",
        )
        from core.models import UsageLimit

        usage = UsageLimit.objects.get(
            user=owner_client.handler._force_user, feature_key="max_caretakers"
        )
        assert usage.usage_count == 2

        owner_client.post(f"/properties/caretakers/{caretaker.id}/deactivate/")
        usage.refresh_from_db()
        assert usage.usage_count == 1

    def test_other_owner_cannot_hire_for_this_owner(
        self, owner_client, other_owner, unit
    ):
        response = owner_client.post(
            "/properties/caretakers/",
            {
                "name": "Spy",
                "phone": "+966666666666",
                "joining_date": "2026-01-01",
                "unit": unit.id,
            },
            format="json",
        )
        assert response.status_code == 201
        created = CareTaker.objects.get(name="Spy")
        assert created.owner_id != other_owner.id


# ---------------------------------------------------------------------------
# The owner assigns the properties
# ---------------------------------------------------------------------------


class TestCaretakerAssignments:
    def test_assign_a_building(self, owner_client, caretaker, building):
        response = owner_client.post(
            f"/properties/caretakers/{caretaker.id}/assignments/",
            {"building": building.id},
            format="json",
        )
        assert response.status_code == 201
        assert CareTakerAssignment.objects.filter(
            caretaker=caretaker, building=building
        ).exists()

    def test_assign_a_single_unit(self, owner_client, caretaker, standalone_unit):
        response = owner_client.post(
            f"/properties/caretakers/{caretaker.id}/assignments/",
            {"unit": standalone_unit.id},
            format="json",
        )
        assert response.status_code == 201
        assert CareTakerAssignment.objects.filter(
            caretaker=caretaker, unit=standalone_unit
        ).exists()

    def test_cannot_assign_both_building_and_unit(
        self, owner_client, caretaker, building, unit
    ):
        response = owner_client.post(
            f"/properties/caretakers/{caretaker.id}/assignments/",
            {"building": building.id, "unit": unit.id},
            format="json",
        )
        assert response.status_code == 400

    def test_cannot_assign_a_property_of_another_owner(
        self, owner_client, caretaker, other_building
    ):
        response = owner_client.post(
            f"/properties/caretakers/{caretaker.id}/assignments/",
            {"building": other_building.id},
            format="json",
        )
        assert response.status_code == 403

    def test_cannot_assign_the_same_building_twice(
        self, owner_client, caretaker, building
    ):
        owner_client.post(
            f"/properties/caretakers/{caretaker.id}/assignments/",
            {"building": building.id},
            format="json",
        )
        response = owner_client.post(
            f"/properties/caretakers/{caretaker.id}/assignments/",
            {"building": building.id},
            format="json",
        )
        assert response.status_code == 400

    def test_list_the_assignments(self, owner_client, caretaker, building):
        owner_client.post(
            f"/properties/caretakers/{caretaker.id}/assignments/",
            {"building": building.id},
            format="json",
        )
        response = owner_client.get(
            f"/properties/caretakers/{caretaker.id}/assignments/"
        )
        assert response.status_code == 200
        assert len(response.data["data"]) == 1

    def test_remove_an_assignment(self, owner_client, caretaker, building):
        created = owner_client.post(
            f"/properties/caretakers/{caretaker.id}/assignments/",
            {"building": building.id},
            format="json",
        )
        assignment_id = created.data["id"]
        response = owner_client.delete(
            f"/properties/caretakers/{caretaker.id}/assignments/{assignment_id}/"
        )
        assert response.status_code == 204
        assignment = CareTakerAssignment.objects.get(pk=assignment_id)
        assert assignment.is_active is False

    def test_assignable_properties_of_the_owner(
        self, owner_client, caretaker, building, other_building
    ):
        response = owner_client.get("/properties/caretakers/assignable-properties/")
        assert response.status_code == 200
        building_ids = [item["id"] for item in response.data["data"]["buildings"]]
        assert building.id in building_ids
        assert other_building.id not in building_ids

    def test_the_caretaker_carries_the_properties(
        self, owner_client, caretaker, building, unit
    ):
        owner_client.post(
            f"/properties/caretakers/{caretaker.id}/assignments/",
            {"building": building.id},
            format="json",
        )
        response = owner_client.get(f"/properties/caretakers/{caretaker.id}/")
        assert response.status_code == 200
        assert response.data["assignment_count"] == 1
        assert response.data["property_count"] == 1


# ---------------------------------------------------------------------------
# The caretaker works in the portal
# ---------------------------------------------------------------------------


class TestCaretakerPortal:
    def test_a_user_without_a_caretaker_profile_is_refused(self, db):
        plain = User.objects.create_user(
            username="plain_user", password="p", full_name="Plain", phone="+9777777"
        )
        client = APIClient()
        client.force_authenticate(user=plain)
        response = client.get("/properties/caretaker/today/")
        assert response.status_code == 404

    def test_today_shows_the_work(self, caretaker_client, caretaker, unit, owner):
        request = MaintenanceRequest.objects.create(
            owner=owner,
            unit=unit,
            title="Tap leaking",
            description="The tap drips",
            priority=MaintenanceRequest.Priority.URGENT,
        )
        response = caretaker_client.get("/properties/caretaker/today/")
        assert response.status_code == 200
        data = response.data["data"]
        assert data["counts"]["open"] == 1
        assert data["counts"]["urgent"] == 1
        assert data["todo"][0]["id"] == request.id

    def test_today_counts_the_properties(self, caretaker_client, caretaker, unit):
        response = caretaker_client.get("/properties/caretaker/today/")
        assert response.status_code == 200
        assert response.data["data"]["counts"]["units"] == 1

    def test_properties_of_the_caretaker(self, caretaker_client, caretaker, unit):
        response = caretaker_client.get("/properties/caretaker/properties/")
        assert response.status_code == 200
        unit_ids = [item["id"] for item in response.data["data"]["units"]]
        assert unit.id in unit_ids

    def test_a_building_assignment_covers_every_unit(
        self, caretaker_client, caretaker, building, unit
    ):
        CareTakerAssignment.objects.create(caretaker=caretaker, building=building)
        response = caretaker_client.get("/properties/caretaker/properties/")
        assert response.status_code == 200
        unit_ids = [item["id"] for item in response.data["data"]["units"]]
        assert unit.id in unit_ids

    def test_another_owner_property_stays_hidden(
        self, caretaker_client, caretaker, other_owner, other_building
    ):
        other_unit = Unit.objects.create(
            owner=other_owner,
            building=other_building,
            unit="B202",
            unit_type="flat",
            address_line="2 Main St",
            city="Pune",
            state="MH",
            country="IN",
            postal_code="411002",
        )
        response = caretaker_client.get("/properties/caretaker/properties/")
        assert response.status_code == 200
        unit_ids = [item["id"] for item in response.data["data"]["units"]]
        assert other_unit.id not in unit_ids

    def test_maintenance_of_the_scope(self, caretaker_client, caretaker, unit, owner):
        request = MaintenanceRequest.objects.create(
            owner=owner, unit=unit, title="Broken window", priority="high"
        )
        response = caretaker_client.get("/properties/caretaker/maintenance/")
        assert response.status_code == 200
        ids = [item["id"] for item in response.data["data"]]
        assert request.id in ids

    def test_maintenance_of_a_home_outside_the_scope_is_hidden(
        self, caretaker_client, caretaker, other_owner, other_building
    ):
        other_unit = Unit.objects.create(
            owner=other_owner,
            building=other_building,
            unit="B203",
            unit_type="flat",
            address_line="2 Main St",
            city="Pune",
            state="MH",
            country="IN",
            postal_code="411002",
        )
        request = MaintenanceRequest.objects.create(
            owner=other_owner, unit=other_unit, title="Not my job"
        )
        response = caretaker_client.get("/properties/caretaker/maintenance/")
        assert response.status_code == 200
        ids = [item["id"] for item in response.data["data"]]
        assert request.id not in ids

    def test_the_caretaker_moves_a_job_forward(
        self, caretaker_client, caretaker, unit, owner
    ):
        request = MaintenanceRequest.objects.create(
            owner=owner, unit=unit, title="Fan not working"
        )
        response = caretaker_client.patch(
            f"/properties/caretaker/maintenance/{request.id}/",
            {"status": "in_progress"},
            format="json",
        )
        assert response.status_code == 200
        request.refresh_from_db()
        assert request.status == MaintenanceRequest.Status.IN_PROGRESS
        assert request.assigned_caretaker_id == caretaker.id

    def test_the_caretaker_adds_a_note(self, caretaker_client, caretaker, unit, owner):
        request = MaintenanceRequest.objects.create(
            owner=owner, unit=unit, title="Painted wall"
        )
        response = caretaker_client.patch(
            f"/properties/caretaker/maintenance/{request.id}/",
            {"notes": "Painter visited"},
            format="json",
        )
        assert response.status_code == 200
        request.refresh_from_db()
        assert "Painter visited" in request.description

    def test_the_caretaker_cannot_take_the_job_of_another_caretaker(
        self, caretaker_client, caretaker, unit, owner
    ):
        other_caretaker = CareTaker.objects.create(
            owner=owner,
            name="Other Caretaker",
            phone="+988888888888",
            joining_date=date.today(),
        )
        request = MaintenanceRequest.objects.create(
            owner=owner, unit=unit, title="Shared job"
        )
        response = caretaker_client.patch(
            f"/properties/caretaker/maintenance/{request.id}/",
            {"assigned_caretaker": other_caretaker.id},
            format="json",
        )
        assert response.status_code == 400

    def test_the_caretaker_sees_the_tenants(self, caretaker_client, caretaker, unit):
        renter = Renter.objects.create(
            unit=unit,
            name="Tenant One",
            phone="+999999999999",
            email="tenant@test.com",
            rent_amount=Decimal("15000"),
            start_date=timezone.now().date() - timedelta(days=30),
        )
        response = caretaker_client.get("/properties/caretaker/tenants/")
        assert response.status_code == 200
        data = response.data["data"]
        assert data[0]["id"] == renter.id
        assert data[0]["phone"] == "+999999999999"
        assert "rent_amount" not in data[0]

    def test_the_dashboard(self, caretaker_client, caretaker, unit):
        response = caretaker_client.get("/properties/caretaker/dashboard/")
        assert response.status_code == 200
        assert response.data["data"]["units"] == 1
