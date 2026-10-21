"""The renter portal: browsing, viewing appointments, maintenance, signing.

A renter with a tenancy sees the flat they live in, raises the maintenance
of that flat, submits the police verification and signs the agreement. A
prospective renter has no tenancy yet: they browse the homes of every owner
and book a viewing.
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from core.models import PlanFeatureLimit, SubscriptionPlan, UserSubscription
from core.plan_limits import FREE_PLAN_LIMITS
from properties.models import (
    Building,
    MaintenanceRequest,
    PoliceVerification,
    RentAgreementDraft,
    Renter,
    RentRecord,
    Unit,
    ViewingAppointment,
)

User = get_user_model()


def _auth(user):
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}"
    )
    return client


class RenterPortalTestBase(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(
            username="portal_owner",
            password="p",
            full_name="Arjun Mehta",
            phone="+911234567890",
            email="owner@test.com",
        )
        self.renter_user = User.objects.create_user(
            username="portal_renter",
            password="p",
            full_name="Riya Kapoor",
            phone="+911234567891",
            email="renter@test.com",
        )
        self.prospective = User.objects.create_user(
            username="portal_prospective",
            password="p",
            full_name="Kavita Rao",
            phone="+911234567892",
            email="prospective@test.com",
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
        self.vacant_unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="A-102",
            unit_type="flat",
            address_line="24th Main Road",
            city="Bengaluru",
            state="Karnataka",
            country="India",
            postal_code="560102",
            status=Unit.VacancyStatus.VACANT,
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
        self.renter_client = _auth(self.renter_user)
        self.prospective_client = _auth(self.prospective)


class RenterListingTests(RenterPortalTestBase):
    def test_a_prospective_renter_browses_the_vacant_homes(self):
        response = self.prospective_client.get("/properties/renter/listings/")
        self.assertEqual(response.status_code, 200)
        ids = [row["id"] for row in response.data["data"]]
        self.assertIn(self.vacant_unit.id, ids)

    def test_the_search_narrows_the_listing(self):
        response = self.prospective_client.get(
            "/properties/renter/listings/?search=lakeview"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"])

    def test_the_listing_needs_an_account(self):
        response = APIClient().get("/properties/renter/listings/")
        self.assertEqual(response.status_code, 401)


class RenterAppointmentTests(RenterPortalTestBase):
    def test_a_prospective_renter_books_a_viewing(self):
        response = self.prospective_client.post(
            "/properties/renter/appointments/",
            {
                "unit": self.vacant_unit.id,
                "scheduled_for": (timezone.now() + timedelta(days=2)).isoformat(),
                "mode": "in_person",
                "notes": "I would like to see the flat in the evening.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        appointment = ViewingAppointment.objects.get()
        self.assertEqual(appointment.status, ViewingAppointment.Status.REQUESTED)
        self.assertEqual(appointment.unit, self.vacant_unit)
        self.assertEqual(appointment.renter_user, self.prospective)

    def test_a_viewing_in_the_past_is_refused(self):
        response = self.prospective_client.post(
            "/properties/renter/appointments/",
            {
                "unit": self.vacant_unit.id,
                "scheduled_for": (timezone.now() - timedelta(days=1)).isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_the_renter_lists_and_cancels_the_appointments(self):
        self.prospective_client.post(
            "/properties/renter/appointments/",
            {
                "unit": self.vacant_unit.id,
                "scheduled_for": (timezone.now() + timedelta(days=2)).isoformat(),
            },
            format="json",
        )
        response = self.prospective_client.get("/properties/renter/appointments/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)

        appointment = ViewingAppointment.objects.get()
        response = self.prospective_client.post(
            f"/properties/renter/appointments/{appointment.id}/cancel/"
        )
        self.assertEqual(response.status_code, 200, response.data)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, ViewingAppointment.Status.CANCELLED)

    def test_somebody_cannot_cancel_the_appointment_of_another_renter(self):
        self.prospective_client.post(
            "/properties/renter/appointments/",
            {
                "unit": self.vacant_unit.id,
                "scheduled_for": (timezone.now() + timedelta(days=2)).isoformat(),
            },
            format="json",
        )
        appointment = ViewingAppointment.objects.get()
        response = self.renter_client.post(
            f"/properties/renter/appointments/{appointment.id}/cancel/"
        )
        self.assertIn(response.status_code, (403, 404))


class RenterMaintenanceTests(RenterPortalTestBase):
    def test_the_renter_sees_the_maintenance_of_their_flat(self):
        MaintenanceRequest.objects.create(
            owner=self.owner,
            unit=self.unit,
            renter=self.renter,
            title="Tap leaking",
            description="The kitchen tap keeps dripping.",
        )
        response = self.renter_client.get("/properties/renter/maintenance/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["title"], "Tap leaking")

    def test_the_renter_raises_a_request_for_their_flat(self):
        response = self.renter_client.post(
            "/properties/renter/maintenance/",
            {
                "title": "Fan not working",
                "description": "The bedroom fan stopped working.",
                "category": "electrical",
                "priority": "high",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        request_obj = MaintenanceRequest.objects.get()
        self.assertEqual(request_obj.unit, self.unit)
        self.assertEqual(request_obj.renter, self.renter)
        self.assertEqual(request_obj.owner, self.owner)

    def test_a_request_needs_a_title(self):
        response = self.renter_client.post(
            "/properties/renter/maintenance/",
            {"description": "no title"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_a_prospective_renter_has_no_flat_to_maintain(self):
        response = self.prospective_client.get("/properties/renter/maintenance/")
        self.assertEqual(response.status_code, 404)


class RenterVerificationTests(RenterPortalTestBase):
    def test_the_renter_submits_the_police_verification(self):
        response = self.renter_client.post(
            "/properties/renter/verification/",
            {"file": SimpleUploadedFile("police.pdf", b"pdf content")},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.data)
        verification = PoliceVerification.objects.get()
        self.assertEqual(
            verification.status, PoliceVerification.PoliceVerificationStatus.SUBMITTED
        )
        self.assertIsNotNone(verification.submitted_at)
        self.assertEqual(verification.unit, self.unit)

    def test_the_status_is_readable_before_and_after_the_submission(self):
        response = self.renter_client.get("/properties/renter/verification/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["status"],
            PoliceVerification.PoliceVerificationStatus.NOT_STARTED,
        )

    def test_the_submission_needs_a_document(self):
        response = self.renter_client.post(
            "/properties/renter/verification/", {}, format="multipart"
        )
        self.assertEqual(response.status_code, 400)


class RenterPaymentTests(RenterPortalTestBase):
    def _rent_record(self) -> RentRecord:
        return RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("28000"),
            payment_method=RentRecord.PaymentMethod.BANK_TRANSFER,
            status=RentRecord.Status.PENDING,
            due_date=date(2026, 10, 5),
        )

    def test_the_renter_pays_the_balance_of_their_own_month(self):
        rent = self._rent_record()
        response = self.renter_client.post(
            f"/properties/renter/rent-records/{rent.id}/payments/",
            {
                "amount": "28000",
                "paid_on": "2026-10-06",
                "payment_method": "upi",
                "transaction_id": "UPI-4471",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        rent.refresh_from_db()
        self.assertEqual(rent.amount_paid, Decimal("28000"))
        self.assertEqual(rent.status, RentRecord.Status.PAID)
        self.assertEqual(response.data["balance"], "0")

    def test_a_month_paid_in_one_go_refuses_a_smaller_payment(self):
        rent = self._rent_record()
        response = self.renter_client.post(
            f"/properties/renter/rent-records/{rent.id}/payments/",
            {"amount": "10000", "paid_on": "2026-10-06"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("one go", str(response.data).lower())

    def test_the_renter_may_pay_in_parts_when_the_unit_allows_it(self):
        self.unit.allow_partial_payments = True
        self.unit.save(update_fields=["allow_partial_payments"])
        rent = self._rent_record()
        response = self.renter_client.post(
            f"/properties/renter/rent-records/{rent.id}/payments/",
            {"amount": "10000", "paid_on": "2026-10-06"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        rent.refresh_from_db()
        self.assertEqual(rent.amount_paid, Decimal("10000"))
        self.assertEqual(response.data["balance"], "18000.00")

    def test_the_renter_cannot_pay_the_month_of_somebody_else(self):
        other = User.objects.create_user(
            username="portal_other",
            password="p",
            full_name="Other Renter",
            phone="+911234567893",
        )
        other_renter = Renter.objects.create(
            unit=self.vacant_unit,
            user=other,
            name="Other Renter",
            email="other@test.com",
            phone="+911234567893",
            rent_amount=Decimal("20000"),
            start_date=date(2026, 10, 1),
        )
        rent = RentRecord.objects.create(
            unit=self.vacant_unit,
            renter=other_renter,
            amount=Decimal("20000"),
            payment_method=RentRecord.PaymentMethod.CASH,
            status=RentRecord.Status.PENDING,
            due_date=date(2026, 10, 5),
        )
        response = self.renter_client.post(
            f"/properties/renter/rent-records/{rent.id}/payments/",
            {"amount": "5000", "paid_on": "2026-10-06"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_a_payment_has_to_be_more_than_zero(self):
        rent = self._rent_record()
        response = self.renter_client.post(
            f"/properties/renter/rent-records/{rent.id}/payments/",
            {"amount": "0", "paid_on": "2026-10-06"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class RenterAgreementTests(RenterPortalTestBase):
    def _create_agreement(self):
        with patch("properties.views.unit_views.send_agreement_for_signature"):
            return _auth(self.owner).post(
                "/properties/rent-agreement-drafts/",
                {
                    "renter": self.renter.id,
                    "unit": self.unit.id,
                    "monthly_rent": "28000.00",
                    "start_date": "2026-10-01",
                    "end_date": "2027-09-30",
                },
                format="json",
            )

    def test_the_renter_reads_their_agreement(self):
        self._create_agreement()
        response = self.renter_client.get("/properties/renter/agreements/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["owner_name"], "Arjun Mehta")

    def test_the_renter_signs_the_agreement(self):
        self._create_agreement()
        agreement = RentAgreementDraft.objects.get()
        response = self.renter_client.post(
            "/properties/renter/agreement/sign/",
            {"agreement": agreement.id},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        agreement.refresh_from_db()
        self.assertTrue(agreement.renter_signed)
        self.assertIsNotNone(agreement.renter_signed_at)
