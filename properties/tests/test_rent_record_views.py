"""Tests for properties/views/rent_record_views.py — RentRecord CRUD and rent APIs."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from core.models import PlanFeatureLimit, SubscriptionPlan, UserSubscription
from properties.models import Building, Renter, RentRecord, Unit

User = get_user_model()


def _auth(u):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(u).access_token}")
    return c


class RentRecordViewSetTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="rr_owner", password="p", full_name="RROwner", phone="+1"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="rr_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="rent_records", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="RRB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="RR101",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def setUp(self):
        self._c = _auth(self.owner)
        cache.clear()

    def test_list_own_rent_records(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="RR Renter",
            phone="+911234567890",
            email="rr@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        RentRecord.objects.create(
            unit=self.unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PENDING",
            due_date=date.today() + timedelta(days=7),
        )
        response = self._c.get("/properties/rent-records/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_create_rent_record(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="RR Renter2",
            phone="+911234567891",
            email="rr2@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        with patch(
            "properties.views.rent_record_views.create_payment_link",
            return_value="https://pay.test/1",
        ):
            response = self._c.post(
                "/properties/rent-records/",
                {
                    "unit": self.unit.id,
                    "renter": renter.id,
                    "amount": "10000",
                    "payment_method": "upi",
                    "status": "PENDING",
                    "due_date": (date.today() + timedelta(days=7)).isoformat(),
                },
            )
        self.assertEqual(response.status_code, 201)

    def test_create_duplicate_rent_record_raises(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="RR Renter3",
            phone="+911234567892",
            email="rr3@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        RentRecord.objects.create(
            unit=self.unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PENDING",
            due_date=date.today() + timedelta(days=7),
        )
        response = self._c.post(
            "/properties/rent-records/",
            {
                "unit": self.unit.id,
                "renter": renter.id,
                "amount": "10000",
                "payment_method": "upi",
                "status": "PENDING",
                "due_date": (date.today() + timedelta(days=7)).isoformat(),
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_update_own_rent_record(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="RR Renter4",
            phone="+911234567893",
            email="rr4@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        rent = RentRecord.objects.create(
            unit=self.unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PENDING",
            due_date=date.today() + timedelta(days=7),
        )
        response = self._c.patch(
            f"/properties/rent-records/{rent.id}/", {"notes": "Updated notes"}
        )
        self.assertEqual(response.status_code, 200)
        rent.refresh_from_db()
        self.assertEqual(rent.notes, "Updated notes")

    def test_delete_own_rent_record(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="RR Renter5",
            phone="+911234567894",
            email="rr5@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        rent = RentRecord.objects.create(
            unit=self.unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PENDING",
            due_date=date.today() + timedelta(days=7),
        )
        response = self._c.delete(f"/properties/rent-records/{rent.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(RentRecord.objects.filter(id=rent.id).exists())


class RentRecordAPITests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="rr_api_owner", password="p", full_name="RROwner2", phone="+1"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="rr_api_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="rent_records", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="RRB2",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="RR102",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def setUp(self):
        self._c = _auth(self.owner)
        cache.clear()

    def test_owner_rent_records_lists_only_own(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="ORR Renter",
            phone="+911234567895",
            email="orr@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        RentRecord.objects.create(
            unit=self.unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PAID",
            due_date=date.today() - timedelta(days=7),
        )
        response = self._c.get("/properties/owner/rent-records/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_owner_rent_overview_returns_data(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="ORO Renter",
            phone="+911234567896",
            email="oro@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        RentRecord.objects.create(
            unit=self.unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PAID",
            due_date=date.today() - timedelta(days=7),
        )
        response = self._c.get("/properties/owner/rents/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertIn("tenant", response.data[0])
        self.assertIn("payout", response.data[0])

    def test_get_latest_due_rent_as_renter(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="GLD Renter",
            phone="+911234567897",
            email="gld@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
            user=self.owner,
        )
        RentRecord.objects.create(
            unit=self.unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PENDING",
            due_date=date.today() + timedelta(days=7),
        )
        response = self._c.get("/properties/renter/rent-due/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["amount"], Decimal("10000"))

    def test_get_latest_due_rent_no_pending_for_renter(self):
        Renter.objects.create(
            unit=self.unit,
            name="NoPending",
            phone="+911234567900",
            email="np@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
            user=self.owner,
        )
        response = self._c.get("/properties/renter/rent-due/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "No pending rent")

    def test_rent_history_as_renter(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="RH Renter",
            phone="+911234567898",
            email="rh@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
            user=self.owner,
        )
        RentRecord.objects.create(
            unit=self.unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PAID",
            due_date=date.today() - timedelta(days=14),
        )
        response = self._c.get("/properties/renter/rent-history/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertIn("status", response.data[0])

    def test_rent_history_no_renter(self):
        response = self._c.get("/properties/renter/rent-history/")
        self.assertEqual(response.status_code, 403)


class RetryPayoutApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="retry_owner", password="p", full_name="RetryOwner", phone="+1"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="retry_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="rent_records", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="RetryB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="R1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def setUp(self):
        self._c = _auth(self.owner)
        cache.clear()

    def test_retry_payout_not_retryable(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="Retry Renter",
            phone="+911234567899",
            email="retry@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        rent = RentRecord.objects.create(
            unit=self.unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PENDING",
            payout_status="PENDING",
            due_date=date.today() + timedelta(days=7),
        )
        response = self._c.post(f"/properties/owner/retry_payout_api/{rent.id}/")
        self.assertEqual(response.status_code, 400)

    def test_retry_payout_success(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="Retry Renter2",
            phone="+911234567900",
            email="retry2@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        rent = RentRecord.objects.create(
            unit=self.unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PAID",
            payout_status="FAILED",
            due_date=date.today() + timedelta(days=7),
        )
        with patch(
            "properties.views.rent_record_views.process_rent_payout",
            return_value={"status": "SUCCESS"},
        ):
            response = self._c.post(f"/properties/owner/retry_payout_api/{rent.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.data)
