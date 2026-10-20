"""Tests for the rent cycle of a unit.

A unit is billed once per month: the record that follows a settled month is
due on the same day of the next month — clamped to the length of that month
— and a month that is still open has to be settled before the next one may
be billed.

The rules behind these tests are documented in
``properties/RENT_COLLECTION_BUSINESS_RULES.md``.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from rest_framework.test import APIClient

from django.core.cache import cache
from django.test import TestCase

from core.models import User
from properties.models import Building, Renter, RentRecord, Unit
from properties.services.rent_cycle import (
    build_cycle_state,
    cycle_violation,
    days_in_month,
    next_cycle_due_date,
)


class RentCycleTestBase(TestCase):
    """One owner, one unit, one renter and one billed month."""

    def setUp(self):
        # The API throttles per user and the tests share the user ids of
        # the rolled back rows — a fresh cache keeps every test its own quota.
        cache.clear()
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username="cycle_owner",
            password="testpass123",
            full_name="Cycle Owner",
            phone="+911000000022",
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="CB",
            address_line="2 Street",
            city="Pune",
            state="MH",
            country="IN",
            postal_code="411002",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="C-101",
            unit_type="flat",
            address_line="2 Street",
            city="Pune",
            state="MH",
            country="IN",
            postal_code="411002",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Meera Iyer",
            phone="+912345678901",
            email="meera@example.com",
            rent_amount=30000,
            start_date=date(2025, 1, 1),
        )
        self.client.force_authenticate(self.owner)

    def bill(self, due_date, status=RentRecord.Status.PENDING, amount_paid="0"):
        """A rent record for a month, with the given state."""
        return RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            due_date=due_date,
            amount=Decimal("30000"),
            amount_paid=Decimal(amount_paid),
            payment_method="upi",
            status=status,
        )

    def create_body(self, due_date="2026-11-05", **overrides):
        body = {
            "unit": self.unit.id,
            "renter": self.renter.id,
            "amount": "25000",
            "payment_method": "cash",
            "due_date": due_date,
        }
        body.update(overrides)
        return body

    def create(self, due_date="2026-11-05", **overrides):
        with (
            patch("notification.utils.send_whatsapp_message"),
            patch("rentsecure_be.services.razorpay_service.create_payment_link"),
        ):
            return self.client.post(
                "/api/rent-records/",
                self.create_body(due_date, **overrides),
                format="json",
            )


class CycleDateTests(TestCase):
    """The date arithmetic of the cycle."""

    def test_a_month_keeps_its_day(self):
        self.assertEqual(next_cycle_due_date(date(2026, 10, 5)), date(2026, 11, 5))

    def test_december_rolls_over_to_january(self):
        self.assertEqual(next_cycle_due_date(date(2026, 12, 5)), date(2027, 1, 5))

    def test_the_31st_is_clamped_to_february(self):
        self.assertEqual(next_cycle_due_date(date(2026, 1, 31)), date(2026, 2, 28))

    def test_the_31st_is_clamped_to_the_29th_in_a_leap_year(self):
        self.assertEqual(next_cycle_due_date(date(2028, 1, 31)), date(2028, 2, 29))

    def test_the_30th_is_clamped_to_february(self):
        self.assertEqual(next_cycle_due_date(date(2026, 1, 30)), date(2026, 2, 28))

    def test_the_length_of_the_months(self):
        self.assertEqual(days_in_month(2026, 2), 28)
        self.assertEqual(days_in_month(2028, 2), 29)
        self.assertEqual(days_in_month(2026, 4), 30)
        self.assertEqual(days_in_month(2026, 12), 31)


class CycleStateTests(RentCycleTestBase):
    """Where the cycle of a unit stands."""

    def test_a_unit_without_history_may_start_its_cycle(self):
        state = build_cycle_state(self.unit)
        self.assertFalse(state["has_cycle"])
        self.assertTrue(state["allowed"])
        self.assertIsNone(state["next_due_date"])

    def test_a_settled_month_opens_the_next_one(self):
        self.bill(date(2026, 10, 5), RentRecord.Status.PAID, "30000")
        state = build_cycle_state(self.unit)
        self.assertTrue(state["has_cycle"])
        self.assertTrue(state["allowed"])
        self.assertTrue(state["previous_is_settled"])
        self.assertEqual(state["next_due_date"], "2026-11-05")
        self.assertEqual(state["next_due_date_display"], "05-Nov-2026")
        self.assertEqual(state["next_month"], "November 2026")
        self.assertEqual(state["next_month_days"], 30)
        self.assertFalse(state["clamped"])

    def test_an_open_month_blocks_the_next_one(self):
        self.bill(date(2026, 10, 5), RentRecord.Status.PENDING, "5000")
        state = build_cycle_state(self.unit)
        self.assertFalse(state["allowed"])
        self.assertTrue(state["previous_is_open"])
        self.assertIn("still open", state["blocked_message"])
        self.assertIn("₹25,000", state["blocked_message"])
        self.assertIn(
            "Settle it before you bill November 2026", state["blocked_message"]
        )

    def test_an_overdue_month_blocks_the_next_one(self):
        self.bill(date(2026, 10, 5), RentRecord.Status.OVERDUE)
        state = build_cycle_state(self.unit)
        self.assertFalse(state["allowed"])

    def test_a_cancelled_month_lets_the_chain_continue(self):
        self.bill(date(2026, 10, 5), RentRecord.Status.CANCELLED)
        state = build_cycle_state(self.unit)
        self.assertTrue(state["allowed"])
        self.assertEqual(state["next_due_date"], "2026-11-05")
        self.assertIn("was cancelled", state["message"])

    def test_the_cycle_names_the_length_of_the_next_month(self):
        self.bill(date(2026, 1, 31), RentRecord.Status.PAID, "30000")
        state = build_cycle_state(self.unit)
        self.assertEqual(state["next_due_date"], "2026-02-28")
        self.assertEqual(state["next_month_days"], 28)
        self.assertTrue(state["clamped"])
        self.assertIn("does not exist in February", state["clamp_note"])
        self.assertIn("28 days", state["message"])

    def test_the_violation_is_empty_for_the_next_month(self):
        self.bill(date(2026, 10, 5), RentRecord.Status.PAID, "30000")
        self.assertEqual(cycle_violation(self.unit, date(2026, 11, 5)), "")

    def test_the_violation_names_the_next_cycle(self):
        self.bill(date(2026, 10, 5), RentRecord.Status.PAID, "30000")
        violation = cycle_violation(self.unit, date(2026, 12, 5))
        self.assertIn("05-Nov-2026", violation)
        self.assertIn("November has 30 days", violation)


class CycleCreateTests(RentCycleTestBase):
    """The rule is enforced by the API."""

    def test_the_first_record_may_be_created(self):
        response = self.create("2026-10-05")
        self.assertEqual(response.status_code, 201)

    def test_the_month_after_a_settled_one_may_be_created(self):
        self.bill(date(2026, 10, 5), RentRecord.Status.PAID, "30000")
        response = self.create("2026-11-05")
        self.assertEqual(response.status_code, 201)

    def test_a_month_that_skips_one_is_refused(self):
        self.bill(date(2026, 10, 5), RentRecord.Status.PAID, "30000")
        response = self.create("2026-12-05")
        self.assertEqual(response.status_code, 400)
        self.assertIn("05-Nov-2026", str(response.json()))

    def test_the_same_month_is_refused(self):
        self.bill(date(2026, 10, 5), RentRecord.Status.PAID, "30000")
        response = self.create("2026-10-05")
        self.assertEqual(response.status_code, 400)

    def test_an_open_month_blocks_the_next_one(self):
        self.bill(date(2026, 10, 5), RentRecord.Status.PENDING, "5000")
        response = self.create("2026-11-05")
        self.assertEqual(response.status_code, 400)
        self.assertIn("still open", str(response.json()))

    def test_the_clamped_day_is_accepted(self):
        self.bill(date(2026, 1, 31), RentRecord.Status.PAID, "30000")
        response = self.create("2026-02-28")
        self.assertEqual(response.status_code, 201)

    def test_the_clamped_day_may_not_be_moved(self):
        self.bill(date(2026, 1, 31), RentRecord.Status.PAID, "30000")
        response = self.create("2026-02-15")
        self.assertEqual(response.status_code, 400)
        self.assertIn("28-Feb-2026", str(response.json()))


class CycleEndpointTests(RentCycleTestBase):
    """The client reads the cycle of a unit from the API."""

    def test_the_cycle_of_a_unit_is_shipped(self):
        self.bill(date(2026, 10, 5), RentRecord.Status.PAID, "30000")
        response = self.client.get(f"/api/rent-records/cycle/?unit={self.unit.id}")
        self.assertEqual(response.status_code, 200)
        cycle = response.json()
        self.assertTrue(cycle["has_cycle"])
        self.assertTrue(cycle["allowed"])
        self.assertEqual(cycle["next_due_date"], "2026-11-05")
        self.assertEqual(cycle["next_month_days"], 30)
        self.assertIn("The rent for October 2026 is settled", cycle["message"])
        self.assertIn("November has 30 days", cycle["message"])

    def test_a_unit_is_required(self):
        response = self.client.get("/api/rent-records/cycle/")
        self.assertEqual(response.status_code, 400)

    def test_a_foreign_unit_is_not_reachable(self):
        other = User.objects.create_user(
            username="cycle_other",
            password="testpass123",
            full_name="Other Owner",
            phone="+911000000033",
        )
        foreign_unit = Unit.objects.create(
            owner=other,
            building=self.building,
            unit="C-999",
            unit_type="flat",
            address_line="2 Street",
            city="Pune",
            state="MH",
            country="IN",
            postal_code="411002",
        )
        response = self.client.get(f"/api/rent-records/cycle/?unit={foreign_unit.id}")
        self.assertEqual(response.status_code, 404)

    def test_the_rules_catalogue_names_the_cycle(self):
        response = self.client.get("/api/rent-records/rules/")
        self.assertEqual(response.status_code, 200)
        rules = response.json()
        self.assertTrue(rules["cycle"]["one_month_at_a_time"])
        self.assertIn("one month at a time", rules["cycle"]["message"])
