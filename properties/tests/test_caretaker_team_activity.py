"""Tests for the trail of the team — what the owner reads.

Every action of a caretaker (taking a job, moving a request forward, leaving
a note) writes one row of ``CareTakerActivity``, and the owner reads those
rows in the *What my team did* panel of the caretaker screen.
"""

from datetime import date

import pytest
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

from properties.models import (
    Building,
    CareTaker,
    CareTakerActivity,
    MaintenanceRequest,
    Unit,
)

User = get_user_model()


@pytest.fixture
def owner(db):
    return User.objects.create_user(
        username="ta_owner",
        password="p",
        full_name="Owner One",
        phone="+911111111111",
    )


@pytest.fixture
def other_owner(db):
    return User.objects.create_user(
        username="ta_other_owner",
        password="p",
        full_name="Owner Two",
        phone="+922222222222",
    )


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
def caretaker_user(db):
    return User.objects.create_user(
        username="ta_worker",
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
def request_row(db, owner, unit):
    return MaintenanceRequest.objects.create(
        owner=owner,
        unit=unit,
        title="Leaking tap",
        description="The kitchen tap keeps dripping.",
        category=MaintenanceRequest.Category.PLUMBING,
        priority=MaintenanceRequest.Priority.MEDIUM,
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


def move(caretaker_client, request_row, **payload):
    """Move a maintenance request forward as the caretaker."""
    return caretaker_client.patch(
        f"/api/caretaker/maintenance/{request_row.id}/", payload, format="json"
    )


class TestTheTrailIsWritten:
    def test_taking_the_job_leaves_a_trail(
        self, caretaker_client, caretaker, request_row
    ):
        response = move(caretaker_client, request_row, status="in_progress")
        assert response.status_code == 200

        activity = CareTakerActivity.objects.get(
            action=CareTakerActivity.Action.TOOK_JOB
        )
        assert activity.caretaker_id == caretaker.id
        assert activity.owner_id == caretaker.owner_id
        assert "Leaking tap" in activity.summary

    def test_the_status_change_is_recorded(
        self, caretaker_client, caretaker, request_row
    ):
        move(caretaker_client, request_row, status="in_progress")
        move(caretaker_client, request_row, status="resolved")

        activity = CareTakerActivity.objects.filter(
            action=CareTakerActivity.Action.STATUS_CHANGE
        ).first()
        assert activity is not None
        assert activity.from_status == "in_progress"
        assert activity.to_status == "resolved"
        assert "In progress" in activity.summary
        assert "Resolved" in activity.summary

    def test_the_note_is_recorded(self, caretaker_client, caretaker, request_row):
        move(caretaker_client, request_row, notes="Plumber booked for Friday")

        activity = CareTakerActivity.objects.filter(
            action=CareTakerActivity.Action.NOTE
        ).get()
        assert activity.detail == "Plumber booked for Friday"
        assert "Leaking tap" in activity.summary

    def test_a_status_that_does_not_change_writes_no_status_entry(
        self, caretaker_client, caretaker, request_row
    ):
        response = move(caretaker_client, request_row, status="open")
        assert response.status_code == 200
        assert not CareTakerActivity.objects.filter(
            action=CareTakerActivity.Action.STATUS_CHANGE
        ).exists()
        # The job was taken, so that is the only entry.
        assert CareTakerActivity.objects.count() == 1

    def test_the_trail_is_not_written_by_the_owner(self, owner_client, request_row):
        """Only the caretaker acts — the owner does not write the trail."""
        assert CareTakerActivity.objects.count() == 0


class TestTheOwnerReadsTheTrail:
    def test_the_owner_sees_what_the_team_did(
        self, owner_client, caretaker, caretaker_client, request_row
    ):
        move(caretaker_client, request_row, status="in_progress")

        response = owner_client.get("/api/caretakers/team-activity/")
        assert response.status_code == 200
        data = response.data["data"]
        assert data["count"] == 2
        entry = data["results"][0]
        assert entry["caretaker"]["name"] == "Caretaker Kumar"
        assert entry["action"] == "status_change"
        assert entry["action_label"] == "Changed the status"
        assert entry["request_title"] == "Leaking tap"
        assert entry["property_label"] == "Sunrise Complex · A101"
        assert entry["from_status_label"] == "Open"
        assert entry["to_status_label"] == "In progress"
        assert entry["created_at"]

    def test_the_trail_is_newest_first(
        self, owner_client, caretaker, caretaker_client, request_row
    ):
        move(caretaker_client, request_row, status="in_progress")
        move(caretaker_client, request_row, status="resolved")

        response = owner_client.get("/api/caretakers/team-activity/")
        actions = [entry["action"] for entry in response.data["data"]["results"]]
        assert actions[0] == "status_change"
        assert "took_job" in actions

    def test_the_trail_of_another_owner_stays_hidden(
        self, other_owner, caretaker, caretaker_client, request_row
    ):
        move(caretaker_client, request_row, status="in_progress")

        response = other_owner_client(other_owner).get("/api/caretakers/team-activity/")
        assert response.status_code == 200
        assert response.data["data"]["count"] == 0
        assert response.data["data"]["results"] == []

    def test_the_trail_can_be_narrowed_to_one_caretaker(
        self, owner_client, caretaker, caretaker_client, request_row
    ):
        move(caretaker_client, request_row, status="in_progress")

        response = owner_client.get(
            f"/api/caretakers/team-activity/?caretaker={caretaker.id}"
        )
        assert response.status_code == 200
        assert response.data["data"]["count"] == 2

    def test_the_caretaker_of_another_owner_cannot_be_read(
        self, owner_client, other_owner
    ):
        foreign = CareTaker.objects.create(
            owner=other_owner,
            name="Foreign Caretaker",
            phone="+977777777777",
            joining_date=date.today(),
        )
        response = owner_client.get(
            f"/api/caretakers/team-activity/?caretaker={foreign.id}"
        )
        assert response.status_code == 400

    def test_a_caretaker_without_a_trail_shows_nothing(self, owner_client, caretaker):
        response = owner_client.get("/api/caretakers/team-activity/")
        assert response.status_code == 200
        assert response.data["data"]["count"] == 0
        assert response.data["data"]["results"] == []

    def test_the_limit_is_honoured(
        self, owner_client, caretaker, caretaker_client, request_row
    ):
        move(caretaker_client, request_row, status="in_progress")
        move(caretaker_client, request_row, status="resolved")

        response = owner_client.get("/api/caretakers/team-activity/?limit=1")
        assert response.status_code == 200
        assert len(response.data["data"]["results"]) == 1
        assert response.data["data"]["count"] == 3

    def test_an_anonymous_visitor_is_refused(self, db):
        client = APIClient()
        response = client.get("/api/caretakers/team-activity/")
        assert response.status_code in (401, 403)


def other_owner_client(other_owner):
    client = APIClient()
    client.force_authenticate(user=other_owner)
    return client
