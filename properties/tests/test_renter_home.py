"""The renter home: the tenancy, the terms, the documents and the requests.

The screens of the renter app are built on the answers of the backend. These
tests hold the contract of the endpoints the app reads: the home of the
renter, the numbers of the dashboard, the ledger of a month and the state of
the police verification.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from properties.models import (
    CareTaker,
    CareTakerAssignment,
    MaintenanceRequest,
    PoliceVerification,
    RentAgreementDraft,
    Renter,
    RentRecord,
    RentRecordPart,
)

from .test_renter_portal import RenterPortalTestBase


class RenterHomeTests(RenterPortalTestBase):
    def setUp(self):
        super().setUp()
        cache.clear()
        self.agreement = RentAgreementDraft.objects.create(
            user=self.owner,
            renter=self.renter,
            unit=self.unit,
            agreement_number="RSA-2026-00042",
            monthly_rent=Decimal("28000"),
            security_deposit=Decimal("56000"),
            start_date=date(2026, 10, 1),
            end_date=date(2027, 9, 30),
            rent_due_day=5,
            payment_mode="bank_transfer",
            notice_period_months=2,
            jurisdiction="Bengaluru, Karnataka",
            special_clauses="No pets inside the flat.",
            owner_signed=True,
            owner_signed_at=timezone.now(),
            document_generated_at=timezone.now(),
        )
        self.agreement.status = self.agreement.refresh_status()
        self.agreement.save(update_fields=["status"])

    def test_the_home_carries_the_tenancy(self):
        response = self.renter_client.get("/properties/renter/home/")
        self.assertEqual(response.status_code, 200)
        profile = response.data["profile"]
        self.assertEqual(profile["unit_label"], "A-101")
        self.assertEqual(profile["owner_name"], "Arjun Mehta")
        self.assertEqual(profile["owner_phone"], "+911234567890")
        self.assertEqual(profile["rent_amount"], "28000.00")

    def test_the_home_carries_the_terms_of_the_agreement(self):
        response = self.renter_client.get("/properties/renter/home/")
        terms = response.data["terms"]
        self.assertEqual(terms["agreement_number"], "RSA-2026-00042")
        self.assertEqual(terms["monthly_rent"], "28000.00")
        self.assertEqual(terms["rent_due_day"], 5)
        self.assertTrue(terms["owner_signed"])
        self.assertFalse(terms["renter_signed"])

    def test_the_home_carries_the_requests_of_the_flat(self):
        MaintenanceRequest.objects.create(
            owner=self.owner,
            unit=self.unit,
            renter=self.renter,
            title="Bedroom fan stopped working",
            status=MaintenanceRequest.Status.IN_PROGRESS,
        )
        response = self.renter_client.get("/properties/renter/home/")
        self.assertEqual(len(response.data["requests"]), 1)
        self.assertEqual(response.data["maintenance"]["open"], 1)

    def test_the_home_carries_the_documents(self):
        response = self.renter_client.get("/properties/renter/home/")
        self.assertIn("id_proof_url", response.data["documents"])
        self.assertIn("rent_agreement_url", response.data["documents"])

    def test_the_caretaker_of_the_home_is_named(self):
        caretaker = CareTaker.objects.create(
            owner=self.owner,
            name="Kavita Rao",
            phone="+919876543210",
            joining_date=date.today(),
        )
        CareTakerAssignment.objects.create(caretaker=caretaker, unit=self.unit)
        response = self.renter_client.get("/properties/renter/home/")
        self.assertEqual(len(response.data["profile"]["caretakers"]), 1)
        self.assertEqual(
            response.data["profile"]["caretakers"][0]["name"], "Kavita Rao"
        )

    def test_a_user_without_a_tenancy_gets_nothing(self):
        response = self.prospective_client.get("/properties/renter/home/")
        self.assertEqual(response.status_code, 404)

    def test_the_home_carries_the_months_of_the_renter(self):
        RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("28000"),
            amount_paid=Decimal("0"),
            payment_method=RentRecord.PaymentMethod.UPI,
            status=RentRecord.Status.PENDING,
            due_date=date(2026, 10, 5),
        )
        response = self.renter_client.get("/properties/renter/home/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["records"]), 1)
        self.assertEqual(response.data["records"][0]["balance"], "28000.00")
        self.assertEqual(response.data["rent_summary"]["outstanding"], "28000.00")

    def test_a_late_month_reads_as_overdue(self):
        # The month of the test is written in the past, so the renter must
        # read it as overdue even when the stored status still says pending.
        RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("28000"),
            amount_paid=Decimal("0"),
            payment_method=RentRecord.PaymentMethod.UPI,
            status=RentRecord.Status.PENDING,
            due_date=date.today() - timedelta(days=5),
        )
        response = self.renter_client.get("/properties/renter/home/")
        self.assertEqual(response.status_code, 200)
        record = response.data["records"][0]
        self.assertEqual(record["payment_status"], "overdue")
        self.assertTrue(response.data["rent_summary"]["overdue"])
        self.assertEqual(response.data["rent_summary"]["overdue_days"], 5)

    def test_the_receipt_of_a_month_is_downloadable(self):
        rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("28000"),
            amount_paid=Decimal("28000"),
            payment_method=RentRecord.PaymentMethod.UPI,
            status=RentRecord.Status.PAID,
            due_date=date(2026, 10, 5),
            paid_on=date(2026, 10, 4),
        )
        response = self.renter_client.get(
            f"/properties/renter/rent-records/{rent.id}/receipt/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_the_receipt_of_another_renter_is_not_reachable(self):
        from django.contrib.auth import get_user_model

        other_user = get_user_model().objects.create_user(
            username="other_renter",
            password="p",
            full_name="Sameer Kapoor",
            phone="+911234567899",
            email="other@test.com",
        )
        other_renter = Renter.objects.create(
            user=other_user,
            unit=self.vacant_unit,
            name="Sameer Kapoor",
            phone="+911234567899",
            email="other@test.com",
            rent_amount=Decimal("18000"),
            start_date=date(2026, 10, 1),
            status="active",
        )
        other = RentRecord.objects.create(
            unit=self.vacant_unit,
            renter=other_renter,
            amount=Decimal("18000"),
            amount_paid=Decimal("0"),
            payment_method=RentRecord.PaymentMethod.UPI,
            status=RentRecord.Status.PENDING,
            due_date=date(2026, 10, 5),
        )
        response = self.renter_client.get(
            f"/properties/renter/rent-records/{other.id}/receipt/"
        )
        self.assertEqual(response.status_code, 404)


class RenterDashboardTests(RenterPortalTestBase):
    def setUp(self):
        super().setUp()
        cache.clear()
        self.rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("28000"),
            amount_paid=Decimal("0"),
            payment_method=RentRecord.PaymentMethod.UPI,
            status=RentRecord.Status.PENDING,
            due_date=date(2026, 10, 5),
        )

    def test_the_dashboard_carries_the_rent_summary(self):
        response = self.renter_client.get("/properties/renter/dashboard/")
        self.assertEqual(response.status_code, 200)
        summary = response.data["rent_summary"]
        self.assertEqual(summary["outstanding"], "28000.00")
        self.assertEqual(summary["outstanding_months"], 1)
        self.assertEqual(summary["current_record_id"], self.rent.id)
        self.assertEqual(summary["next_due_date"], "2026-10-05")

    def test_the_dashboard_carries_the_verification_and_the_maintenance(self):
        MaintenanceRequest.objects.create(
            owner=self.owner,
            unit=self.unit,
            renter=self.renter,
            title="Kitchen tap dripping",
        )
        response = self.renter_client.get("/properties/renter/dashboard/")
        self.assertEqual(response.data["verification"]["status"], "not_started")
        self.assertEqual(response.data["maintenance"]["open"], 1)

    def test_the_dashboard_suggests_the_vacant_homes(self):
        response = self.renter_client.get("/properties/renter/dashboard/")
        ids = [home["id"] for home in response.data["suggested_homes"]]
        self.assertIn(self.vacant_unit.id, ids)
        self.assertNotIn(self.unit.id, ids)

    def test_the_dashboard_of_a_prospective_renter(self):
        # the renter sign in puts the account in the renter group, even when
        # there is no tenancy yet
        from django.contrib.auth.models import Group

        group, _ = Group.objects.get_or_create(name="renter")
        self.prospective.groups.add(group)
        response = self.prospective_client.get("/properties/renter/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["profile"])
        self.assertTrue(response.data["suggested_homes"])


class RenterLedgerTests(RenterPortalTestBase):
    def setUp(self):
        super().setUp()
        cache.clear()
        self.rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("28000"),
            amount_paid=Decimal("20000"),
            payment_method=RentRecord.PaymentMethod.UPI,
            status=RentRecord.Status.PENDING,
            due_date=date(2026, 10, 5),
        )
        RentRecordPart.objects.create(
            rent_record=self.rent,
            amount=Decimal("20000"),
            paid_on=date(2026, 10, 4),
            payment_method=RentRecord.PaymentMethod.UPI,
            transaction_id="UPI-8821",
            receipt_no="RC-2026-10-00087",
        )

    def test_the_ledger_carries_the_amounts(self):
        response = self.renter_client.get("/properties/renter/rent-records/")
        self.assertEqual(response.status_code, 200)
        row = response.data["data"][0]
        self.assertEqual(row["rent_amount"], "28000.00")
        self.assertEqual(row["amount_paid"], "20000.00")
        self.assertEqual(row["balance"], "8000.00")
        self.assertTrue(row["is_partially_paid"])

    def test_the_ledger_carries_the_parts(self):
        response = self.renter_client.get(
            f"/properties/renter/rent-records/{self.rent.id}/"
        )
        self.assertEqual(response.status_code, 200)
        parts = response.data["parts"]
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0]["receipt_no"], "RC-2026-10-00087")
        self.assertEqual(parts[0]["transaction_id"], "UPI-8821")


class RenterVerificationPayloadTests(RenterPortalTestBase):
    def setUp(self):
        super().setUp()
        cache.clear()
        self.verification = PoliceVerification.objects.create(
            user=self.owner,
            renter=self.renter,
            unit=self.unit,
            status=PoliceVerification.PoliceVerificationStatus.VERIFIED,
            file=SimpleUploadedFile(
                "police-verification-riya.pdf",
                b"%PDF-1.4",
                content_type="application/pdf",
            ),
            submitted_at=timezone.now(),
            verified_at=timezone.now(),
            reviewed_at=timezone.now(),
            reviewed_by=self.owner,
        )

    def test_the_verification_carries_the_reviewer_and_the_file(self):
        response = self.renter_client.get("/properties/renter/verification/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["reviewed_by_name"], "Arjun Mehta")
        self.assertIn("police-verification-riya", response.data["file_name"])
        self.assertEqual(response.data["status_label"], "Verified")
