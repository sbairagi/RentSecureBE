"""Tests for rent record and extra charge viewsets"""

from datetime import date
from decimal import Decimal

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import PlanFeatureLimit, SubscriptionPlan, UserSubscription
from properties.models import Building, Renter, RentRecord, Unit

User = get_user_model()


class RentRecordViewSetTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.o = User.objects.create_user(
            username="rro@t.com",
            email="rro@t.com",
            password="p",
            full_name="RRO",
            phone="+1",
        )
        cls.pp, _ = SubscriptionPlan.objects.get_or_create(
            name="rr_pro",
            defaults={
                "monthly_price": Decimal("29.99"),
                "yearly_price": Decimal("299.99"),
                "features": "Pro",
            },
        )

    def setUp(self):
        UserSubscription.objects.update_or_create(
            user=self.o, defaults={"plan": self.pp, "is_active": True}
        )
        b, _ = Building.objects.get_or_create(
            owner=self.o,
            name="RRB",
            defaults={
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )
        self.u, _ = Unit.objects.get_or_create(
            owner=self.o,
            building=b,
            unit="RR101",
            defaults={
                "unit_type": "flat",
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )

    def _auth(self):
        c = APIClient()
        c.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.o).access_token}"
        )
        return c

    def test_unauth_list(self):
        self.assertEqual(self.client.get("/properties/rent-records/").status_code, 401)

    def test_list(self):
        self.assertEqual(self._auth().get("/properties/rent-records/").status_code, 200)


class RentRecordSerializerSecurityTests(TestCase):
    """Tests confirming RentRecordSerializer blocks sensitive field updates."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.o = User.objects.create_user(
            username="sec@t.com",
            email="sec@t.com",
            password="p",
            full_name="Sec",
            phone="+1",
        )
        cls.pp, _ = SubscriptionPlan.objects.get_or_create(
            name="sec_pro",
            defaults={
                "monthly_price": Decimal("29.99"),
                "yearly_price": Decimal("299.99"),
                "features": "Pro",
            },
        )

    def setUp(self):
        b, _ = Building.objects.get_or_create(
            owner=self.o,
            name="SECB",
            defaults={
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )
        self.u, _ = Unit.objects.get_or_create(
            owner=self.o,
            building=b,
            unit="SEC101",
            defaults={
                "unit_type": "flat",
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )
        self.renter = Renter.objects.create(
            unit=self.u,
            name="Sec Renter",
            phone="+919999999999",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
        )
        self.rent = RentRecord.objects.create(
            renter=self.renter,
            unit=self.u,
            due_date=date(2025, 1, 1),
            amount=10000,
            payment_method="upi",
            status=RentRecord.Status.PENDING,
            payout_status="PENDING",
        )

    def _auth(self):
        c = APIClient()
        c.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.o).access_token}"
        )
        return c

    def test_patch_rejects_payout_status(self):
        response = self._auth().patch(
            f"/properties/rent-records/{self.rent.id}/",
            {"payout_status": "SUCCESS"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.rent.refresh_from_db()
        self.assertEqual(self.rent.payout_status, "PENDING")

    def test_patch_rejects_status(self):
        response = self._auth().patch(
            f"/properties/rent-records/{self.rent.id}/",
            {"status": "paid"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.rent.refresh_from_db()
        self.assertEqual(self.rent.status, RentRecord.Status.PENDING)

    def test_patch_allows_safe_fields(self):
        response = self._auth().patch(
            f"/properties/rent-records/{self.rent.id}/",
            {"notes": "Late fee waived"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.rent.refresh_from_db()
        self.assertEqual(self.rent.notes, "Late fee waived")

    def test_post_sets_status_default_when_not_provided(self):
        response = self._auth().post(
            "/properties/rent-records/",
            {
                "renter": self.renter.id,
                "unit": self.u.id,
                "due_date": "2025-02-01",
                "amount": 12000,
                "payment_method": "upi",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        created_id = response.data["id"]
        created = RentRecord.objects.get(id=created_id)
        self.assertEqual(created.status, RentRecord.Status.PENDING)


class RentRecordCreationStatusValidationTests(TestCase):
    """Block rent record creation for revoked/deactivated renters."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.o = User.objects.create_user(
            username="stat@t.com",
            email="stat@t.com",
            password="p",
            full_name="Stat",
            phone="+1",
        )
        cls.pp, _ = SubscriptionPlan.objects.get_or_create(
            name="stat_pro",
            defaults={
                "monthly_price": Decimal("29.99"),
                "yearly_price": Decimal("299.99"),
                "features": "Pro",
            },
        )

    def setUp(self):
        UserSubscription.objects.update_or_create(
            user=self.o, defaults={"plan": self.pp, "is_active": True}
        )
        PlanFeatureLimit.objects.get_or_create(
            plan=self.pp, feature_key="rent_records", defaults={"value": "100"}
        )
        b, _ = Building.objects.get_or_create(
            owner=self.o,
            name="STATB",
            defaults={
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )
        self.u, _ = Unit.objects.get_or_create(
            owner=self.o,
            building=b,
            unit="STAT101",
            defaults={
                "unit_type": "flat",
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )

    def _auth(self):
        c = APIClient()
        c.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.o).access_token}"
        )
        return c

    def test_active_renter_can_create_rent_record(self):
        renter = Renter.objects.create(
            unit=self.u,
            name="Active Renter",
            phone="+911111111111",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            status=Renter.RenterStatus.ACTIVE,
        )
        response = self._auth().post(
            "/properties/rent-records/",
            {
                "renter": renter.id,
                "unit": self.u.id,
                "due_date": "2025-02-01",
                "amount": 12000,
                "payment_method": "upi",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_notice_period_renter_can_create_rent_record(self):
        renter = Renter.objects.create(
            unit=self.u,
            name="Notice Renter",
            phone="+911111111112",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            status=Renter.RenterStatus.NOTICE_PERIOD,
        )
        response = self._auth().post(
            "/properties/rent-records/",
            {
                "renter": renter.id,
                "unit": self.u.id,
                "due_date": "2025-02-01",
                "amount": 12000,
                "payment_method": "upi",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_revoked_renter_cannot_create_rent_record(self):
        renter = Renter.objects.create(
            unit=self.u,
            name="Revoked Renter",
            phone="+911111111113",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            status=Renter.RenterStatus.REVOKED,
        )
        response = self._auth().post(
            "/properties/rent-records/",
            {
                "renter": renter.id,
                "unit": self.u.id,
                "due_date": "2025-02-01",
                "amount": 12000,
                "payment_method": "upi",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_deactivated_renter_cannot_create_rent_record(self):
        renter = Renter.objects.create(
            unit=self.u,
            name="Deactivated Renter",
            phone="+911111111114",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            status=Renter.RenterStatus.DEACTIVATED,
        )
        response = self._auth().post(
            "/properties/rent-records/",
            {
                "renter": renter.id,
                "unit": self.u.id,
                "due_date": "2025-02-01",
                "amount": 12000,
                "payment_method": "upi",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class RentRecordHistoryTests(TestCase):
    """Tests confirming RentRecord history is created and tracked."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.o = User.objects.create_user(
            username="hist@t.com",
            email="hist@t.com",
            password="p",
            full_name="Hist",
            phone="+1",
        )
        cls.pp, _ = SubscriptionPlan.objects.get_or_create(
            name="hist_pro",
            defaults={
                "monthly_price": Decimal("29.99"),
                "yearly_price": Decimal("299.99"),
                "features": "Pro",
            },
        )

    def setUp(self):
        UserSubscription.objects.update_or_create(
            user=self.o, defaults={"plan": self.pp, "is_active": True}
        )
        b, _ = Building.objects.get_or_create(
            owner=self.o,
            name="HISTB",
            defaults={
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )
        self.u, _ = Unit.objects.get_or_create(
            owner=self.o,
            building=b,
            unit="HIST101",
            defaults={
                "unit_type": "flat",
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )
        self.renter = Renter.objects.create(
            unit=self.u,
            name="Hist Renter",
            phone="+919999999998",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
        )

    def test_create_rent_record_creates_history_entry(self):
        rent = RentRecord.objects.create(
            renter=self.renter,
            unit=self.u,
            due_date=date(2025, 1, 1),
            amount=10000,
            payment_method="upi",
            status=RentRecord.Status.PENDING,
            payout_status="PENDING",
        )
        self.assertEqual(RentRecord.history.filter(id=rent.id).count(), 1)
        entry = RentRecord.history.filter(id=rent.id).first()
        self.assertEqual(entry.history_type, "+")

    def test_update_rent_record_creates_history_entry(self):
        rent = RentRecord.objects.create(
            renter=self.renter,
            unit=self.u,
            due_date=date(2025, 1, 1),
            amount=10000,
            payment_method="upi",
            status=RentRecord.Status.PENDING,
            payout_status="PENDING",
        )
        rent.notes = "Updated via ORM"
        rent.save(update_fields=["notes"])

        entries = RentRecord.history.filter(id=rent.id)
        self.assertEqual(entries.count(), 2)
        latest = entries.first()
        self.assertEqual(latest.history_type, "~")
        self.assertEqual(latest.notes, "Updated via ORM")

    def test_delete_rent_record_creates_history_entry(self):
        rent = RentRecord.objects.create(
            renter=self.renter,
            unit=self.u,
            due_date=date(2025, 1, 1),
            amount=10000,
            payment_method="upi",
            status=RentRecord.Status.PENDING,
            payout_status="PENDING",
        )
        rent_id = rent.id
        rent.delete()
        entries = RentRecord.history.filter(id=rent_id)
        self.assertEqual(entries.count(), 2)
        latest = entries.first()
        self.assertEqual(latest.history_type, "-")

    def test_history_records_user_when_request_user_set(self):
        rent = RentRecord.objects.create(
            renter=self.renter,
            unit=self.u,
            due_date=date(2025, 1, 1),
            amount=10000,
            payment_method="upi",
            status=RentRecord.Status.PENDING,
            payout_status="PENDING",
        )
        rent.notes = "With user context"
        rent.save(update_fields=["notes"])

        latest = RentRecord.history.filter(id=rent.id).first()
        self.assertIsNotNone(latest)
        self.assertEqual(latest.notes, "With user context")


class ExtraChargeViewSetTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.o = User.objects.create_user(
            username="eco@t.com",
            email="eco@t.com",
            password="p",
            full_name="ECO",
            phone="+1",
        )
        cls.pp, _ = SubscriptionPlan.objects.get_or_create(
            name="ec_pro",
            defaults={
                "monthly_price": Decimal("29.99"),
                "yearly_price": Decimal("299.99"),
                "features": "Pro",
            },
        )

    def setUp(self):
        UserSubscription.objects.update_or_create(
            user=self.o, defaults={"plan": self.pp, "is_active": True}
        )
        b, _ = Building.objects.get_or_create(
            owner=self.o,
            name="ECB",
            defaults={
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )
        self.u, _ = Unit.objects.get_or_create(
            owner=self.o,
            building=b,
            unit="EC101",
            defaults={
                "unit_type": "flat",
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )

    def _auth(self):
        c = APIClient()
        c.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.o).access_token}"
        )
        return c

    def test_extra_charge_unauth(self):
        self.assertEqual(
            self.client.post("/properties/extra-charges/", {}).status_code, 401
        )
