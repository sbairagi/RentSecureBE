"""The agreement workflow: the backend generates the document.

The owner never uploads an agreement PDF. The backend generates it from the
details captured on the form, moves the agreement through the workflow and
records the signature of both parties.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from core.models import PlanFeatureLimit, SubscriptionPlan, UserSubscription
from core.plan_limits import FREE_PLAN_LIMITS
from properties.models import Building, RentAgreementDraft, Renter, Unit

User = get_user_model()

DRAFTS_URL = "/properties/rent-agreement-drafts/"


def _auth(user):
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}"
    )
    return client


class AgreementWorkflowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(
            username="agreement_owner",
            password="p",
            full_name="Arjun Mehta",
            phone="+911234567890",
            email="owner@test.com",
        )
        self.renter_user = User.objects.create_user(
            username="agreement_renter",
            password="p",
            full_name="Riya Kapoor",
            phone="+911234567891",
            email="renter@test.com",
        )
        plan = SubscriptionPlan.objects.get(name="free")
        UserSubscription.objects.create(user=self.owner, plan=plan, is_active=True)
        for feature_key, value in FREE_PLAN_LIMITS.items():
            PlanFeatureLimit.objects.update_or_create(
                plan=plan, feature_key=feature_key, defaults={"value": value}
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
            phone="+911234567891",
            rent_amount=Decimal("28000"),
            start_date=date(2026, 10, 1),
            end_date=date(2027, 9, 30),
        )
        self.owner_client = _auth(self.owner)
        self.renter_client = _auth(self.renter_user)
        self.payload = {
            "renter": self.renter.id,
            "unit": self.unit.id,
            "start_date": "2026-10-01",
            "end_date": "2027-09-30",
            "monthly_rent": "28000.00",
            "security_deposit": "56000.00",
            "rent_due_day": 5,
            "payment_mode": "bank_transfer",
            "notice_period_months": 2,
            "jurisdiction": "Bengaluru, Karnataka",
            "special_clauses": "No pets inside the flat.",
        }

    def _create_agreement(self):
        with patch("properties.views.unit_views.send_agreement_for_signature"):
            return self.owner_client.post(DRAFTS_URL, self.payload, format="json")

    def test_backend_generates_the_document_without_an_upload(self):
        response = self._create_agreement()
        self.assertEqual(response.status_code, 201, response.data)
        agreement = RentAgreementDraft.objects.get()
        self.assertTrue(agreement.file)
        self.assertTrue(agreement.document_generated_at)
        self.assertEqual(
            agreement.status,
            RentAgreementDraft.AgreementStatus.PENDING_SIGNATURE,
        )
        self.assertTrue(agreement.agreement_number.startswith("RSA-"))
        self.assertEqual(agreement.generation_error, "")
        self.assertEqual(response.data["signature_progress"], 0)

    def test_the_document_stays_a_draft_without_a_signature_provider(self):
        """Without the e-sign provider the agreement waits as a draft."""
        with patch(
            "properties.views.unit_views.send_agreement_for_signature",
            side_effect=RuntimeError("no provider configured"),
        ):
            response = self.owner_client.post(DRAFTS_URL, self.payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        agreement = RentAgreementDraft.objects.get()
        self.assertEqual(agreement.status, RentAgreementDraft.AgreementStatus.DRAFT)
        self.assertTrue(agreement.file)

    def test_the_owner_signs_and_the_agreement_becomes_partially_signed(self):
        self._create_agreement()
        agreement = RentAgreementDraft.objects.get()
        response = self.owner_client.post(
            f"{DRAFTS_URL}{agreement.id}/sign/",
            {"role": "owner"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        agreement.refresh_from_db()
        self.assertTrue(agreement.owner_signed)
        self.assertIsNotNone(agreement.owner_signed_at)
        self.assertEqual(
            agreement.status, RentAgreementDraft.AgreementStatus.PARTIALLY_SIGNED
        )

    def test_the_renter_signs_and_the_agreement_becomes_fully_signed(self):
        self._create_agreement()
        agreement = RentAgreementDraft.objects.get()
        self.owner_client.post(
            f"{DRAFTS_URL}{agreement.id}/sign/", {"role": "owner"}, format="json"
        )
        response = self.renter_client.post(
            "/properties/renter/agreement/sign/",
            {"agreement": agreement.id},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        agreement.refresh_from_db()
        self.assertTrue(agreement.renter_signed)
        self.assertEqual(
            agreement.status, RentAgreementDraft.AgreementStatus.FULLY_SIGNED
        )
        self.assertEqual(agreement.signature_progress, 100)

    def test_the_renter_cannot_sign_the_agreement_of_somebody_else(self):
        self._create_agreement()
        agreement = RentAgreementDraft.objects.get()
        stranger = User.objects.create_user(
            username="stranger_two",
            password="p",
            full_name="Stranger",
            phone="+911234567898",
        )
        response = _auth(stranger).post(
            "/properties/renter/agreement/sign/",
            {"agreement": agreement.id},
            format="json",
        )
        self.assertIn(response.status_code, (403, 404))

    def test_a_stranger_cannot_sign_as_the_renter(self):
        self._create_agreement()
        agreement = RentAgreementDraft.objects.get()
        stranger = User.objects.create_user(
            username="stranger",
            password="p",
            full_name="Stranger",
            phone="+911234567899",
        )
        response = _auth(stranger).post(
            f"{DRAFTS_URL}{agreement.id}/sign/",
            {"role": "renter"},
            format="json",
        )
        # The agreement is not even visible to a stranger.
        self.assertIn(response.status_code, (403, 404))
        agreement.refresh_from_db()
        self.assertFalse(agreement.renter_signed)

    def test_signing_needs_a_generated_document(self):
        agreement = RentAgreementDraft.objects.create(
            user=self.owner,
            renter=self.renter,
            unit=self.unit,
            status=RentAgreementDraft.AgreementStatus.IN_PROGRESS,
        )
        response = self.owner_client.post(
            f"{DRAFTS_URL}{agreement.id}/sign/",
            {"role": "owner"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_the_sign_action_needs_a_known_role(self):
        self._create_agreement()
        agreement = RentAgreementDraft.objects.get()
        response = self.owner_client.post(
            f"{DRAFTS_URL}{agreement.id}/sign/", {"role": "stranger"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_the_document_action_returns_the_generated_file(self):
        self._create_agreement()
        agreement = RentAgreementDraft.objects.get()
        response = self.owner_client.get(f"{DRAFTS_URL}{agreement.id}/document/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["file"])
        self.assertEqual(response.data["agreement_number"], agreement.agreement_number)

    def test_regenerate_rebuilds_the_document(self):
        self._create_agreement()
        agreement = RentAgreementDraft.objects.get()
        response = self.owner_client.post(f"{DRAFTS_URL}{agreement.id}/generate/")
        self.assertEqual(response.status_code, 200, response.data)
        agreement.refresh_from_db()
        self.assertIsNotNone(agreement.document_generated_at)

    def test_the_status_filter_uses_the_workflow_state(self):
        self._create_agreement()
        response = self.owner_client.get(f"{DRAFTS_URL}?status=pending_signature")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        response = self.owner_client.get(f"{DRAFTS_URL}?status=fully_signed")
        self.assertEqual(len(response.data), 0)

    def test_the_upload_is_optional_but_not_writable(self):
        """The document belongs to the backend, the client cannot push one."""
        self._create_agreement()
        agreement = RentAgreementDraft.objects.get()
        response = self.owner_client.patch(
            f"{DRAFTS_URL}{agreement.id}/",
            {"file": SimpleUploadedFile("fake.pdf", b"pdf")},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200, response.data)
        agreement.refresh_from_db()
        self.assertNotEqual(agreement.file.name, "fake.pdf")
