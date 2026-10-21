"""The RentSecure Ops desk: the internal team that runs the trust side.

Ops reviews the police verifications, steps in when an agreement could not
be generated and watches the agreements that expired. Only the members of
the team can reach the desk.
"""

from datetime import date
from decimal import Decimal

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from properties.models import (
    Building,
    PoliceVerification,
    RentAgreementDraft,
    Renter,
    Unit,
)

User = get_user_model()


def _auth(user):
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}"
    )
    return client


class OpsDeskTests(TestCase):
    def setUp(self):
        cache.clear()
        self.ops = User.objects.create_user(
            username="ops_member",
            password="p",
            full_name="Ops Member",
            phone="+911234567880",
            is_ops=True,
        )
        self.owner = User.objects.create_user(
            username="ops_owner",
            password="p",
            full_name="Arjun Mehta",
            phone="+911234567881",
        )
        self.renter_user = User.objects.create_user(
            username="ops_renter",
            password="p",
            full_name="Riya Kapoor",
            phone="+911234567882",
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="Lakeview",
            address_line="24th Main Road",
            city="Bengaluru",
            state="Karnataka",
            country="India",
            postal_code="560102",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="A-101",
            unit_type="flat",
            address_line="24th Main Road",
            city="Bengaluru",
            state="Karnataka",
            country="India",
            postal_code="560102",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            user=self.renter_user,
            name="Riya Kapoor",
            email="renter@test.com",
            phone="+911234567882",
            rent_amount=Decimal("28000"),
            start_date=date(2026, 10, 1),
        )
        self.verification = PoliceVerification.objects.create(
            user=self.owner,
            renter=self.renter,
            unit=self.unit,
            file="police.pdf",
            status=PoliceVerification.PoliceVerificationStatus.SUBMITTED,
        )
        self.ops_client = _auth(self.ops)
        self.owner_client = _auth(self.owner)

    def test_a_stranger_cannot_reach_the_desk(self):
        response = self.owner_client.get("/properties/ops/police-verifications/")
        self.assertEqual(response.status_code, 403)

    def test_ops_sees_the_review_queue(self):
        response = self.ops_client.get("/properties/ops/police-verifications/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["renter_name"], "Riya Kapoor")

    def test_ops_approves_a_verification(self):
        response = self.ops_client.post(
            f"/properties/ops/police-verifications/{self.verification.id}/decision/",
            {"decision": "approve", "notes": "Checked against the register."},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.verification.refresh_from_db()
        self.assertEqual(
            self.verification.status,
            PoliceVerification.PoliceVerificationStatus.VERIFIED,
        )
        self.assertIsNotNone(self.verification.verified_at)
        self.assertEqual(self.verification.reviewed_by, self.ops)

    def test_a_rejection_needs_a_reason(self):
        response = self.ops_client.post(
            f"/properties/ops/police-verifications/{self.verification.id}/decision/",
            {"decision": "reject"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_ops_rejects_a_verification(self):
        response = self.ops_client.post(
            f"/properties/ops/police-verifications/{self.verification.id}/decision/",
            {"decision": "reject", "notes": "The document is not readable."},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.verification.refresh_from_db()
        self.assertEqual(
            self.verification.status,
            PoliceVerification.PoliceVerificationStatus.REJECTED,
        )
        self.assertEqual(
            self.verification.rejection_reason, "The document is not readable."
        )

    def test_the_decision_needs_a_known_decision(self):
        response = self.ops_client.post(
            f"/properties/ops/police-verifications/{self.verification.id}/decision/",
            {"decision": "maybe"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_ops_sees_the_agreement_queue_and_regenerates(self):
        agreement = RentAgreementDraft.objects.create(
            user=self.owner,
            renter=self.renter,
            unit=self.unit,
            status=RentAgreementDraft.AgreementStatus.IN_PROGRESS,
            generation_error="The document renderer returned an empty file.",
        )
        response = self.ops_client.get("/properties/ops/agreements/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)

        response = self.ops_client.post(
            f"/properties/ops/agreements/{agreement.id}/regenerate/"
        )
        self.assertEqual(response.status_code, 200, response.data)
        agreement.refresh_from_db()
        self.assertTrue(agreement.file)
        self.assertEqual(agreement.generation_error, "")
