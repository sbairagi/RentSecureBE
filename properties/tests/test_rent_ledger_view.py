"""Tests for the authoritative rent-collection read model.

The server decides what a ledger row shows — its badge set, the actions it
still allows, the charge breakdown, the payment progress, the bounds of the
next part payment and the receipt.  The web client only renders it.

These tests lock that contract, so a change in the ledger rules has to be a
deliberate change in the code **and** in this file.

The rules behind them are documented in
``properties/RENT_COLLECTION_BUSINESS_RULES.md``.
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from rest_framework.test import APIClient

from django.core.cache import cache
from django.test import TestCase

from core.models import User
from properties.models import Building, Renter, RentRecord, RentRecordPart, Unit


class RentLedgerViewTestBase(TestCase):
    """Shared fixtures: one owner with a unit, a renter and a rent record."""

    def setUp(self):
        # The API throttles per user and the tests share the user ids of
        # the rolled back rows — a fresh cache keeps every test its own quota.
        cache.clear()
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username="ledger_owner",
            password="testpass123",
            full_name="Ledger Owner",
            phone="+911000000011",
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="LGB",
            address_line="1 Street",
            city="Pune",
            state="MH",
            country="IN",
            postal_code="411001",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="LG-101",
            unit_type="flat",
            address_line="1 Street",
            city="Pune",
            state="MH",
            country="IN",
            postal_code="411001",
            allow_partial_payments=True,
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Meera Iyer",
            phone="+912345678901",
            email="meera@example.com",
            rent_amount=30000,
            start_date=date(2025, 1, 1),
        )
        self.due_date = date(2026, 10, 5)
        self.rent = RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            due_date=self.due_date,
            amount=Decimal("30000"),
            payment_method="upi",
            status=RentRecord.Status.PENDING,
        )
        self.client.force_authenticate(self.owner)

    def ledger(self, rent=None, **kwargs):
        """The ledger view of a record, straight from the service."""
        from properties.services.rent_ledger_view import build_ledger_view

        return build_ledger_view(rent or self.rent, **kwargs)

    @staticmethod
    def rows(response):
        body = response.json()
        if isinstance(body, dict):
            return body["results"]
        return body


class LedgerRowStateTests(RentLedgerViewTestBase):
    """Which actions a row still allows."""

    def test_an_open_row_can_be_edited_cancelled_and_reminded(self):
        state = self.ledger()["row_state"]
        self.assertTrue(state["can_edit"])
        self.assertTrue(state["can_cancel"])
        self.assertTrue(state["can_remind"])
        self.assertTrue(state["can_record_part"])
        self.assertFalse(state["can_send_receipt"])
        self.assertFalse(state["is_locked"])
        self.assertFalse(state["has_receipt"])

    def test_a_settled_row_is_locked(self):
        self.rent.status = RentRecord.Status.PAID
        self.rent.amount_paid = Decimal("30000")
        self.rent.save(update_fields=["status", "amount_paid"])
        state = self.ledger()["row_state"]
        self.assertTrue(state["is_settled"])
        self.assertTrue(state["is_locked"])
        self.assertFalse(state["can_edit"])
        self.assertFalse(state["can_cancel"])
        self.assertFalse(state["can_remind"])
        self.assertFalse(state["can_record_part"])
        self.assertTrue(state["can_send_receipt"])

    def test_a_cancelled_row_is_locked(self):
        self.rent.status = RentRecord.Status.CANCELLED
        self.rent.save(update_fields=["status"])
        state = self.ledger()["row_state"]
        self.assertTrue(state["is_cancelled"])
        self.assertTrue(state["is_locked"])
        self.assertFalse(state["can_edit"])
        self.assertFalse(state["can_cancel"])
        self.assertFalse(state["can_record_part"])

    def test_a_partially_paid_row_cannot_be_cancelled_anymore(self):
        self.rent.amount_paid = Decimal("5000")
        self.rent.save(update_fields=["amount_paid"])
        state = self.ledger()["row_state"]
        self.assertTrue(state["is_partially_paid"])
        self.assertTrue(state["has_receipt"])
        self.assertFalse(state["can_cancel"])
        self.assertTrue(state["can_edit"])
        self.assertTrue(state["can_record_part"])

    def test_a_settled_row_is_never_partially_paid(self):
        self.rent.status = RentRecord.Status.PAID
        self.rent.amount_paid = Decimal("30000")
        self.rent.save(update_fields=["status", "amount_paid"])
        self.assertFalse(self.ledger()["row_state"]["is_partially_paid"])

    def test_a_part_needs_the_unit_flag_and_a_balance(self):
        self.unit.allow_partial_payments = False
        self.unit.save(update_fields=["allow_partial_payments"])
        self.assertFalse(self.ledger()["row_state"]["can_record_part"])

        self.unit.allow_partial_payments = True
        self.unit.save(update_fields=["allow_partial_payments"])
        self.rent.amount_paid = Decimal("30000")
        self.rent.save(update_fields=["amount_paid"])
        self.assertFalse(self.ledger()["row_state"]["can_record_part"])


class LedgerBadgeTests(RentLedgerViewTestBase):
    """The badge set of a row."""

    def badges(self, rent=None):
        return self.ledger(rent)["status_badges"]

    def test_a_settled_row_shows_only_paid(self):
        self.rent.status = RentRecord.Status.PAID
        self.rent.amount_paid = Decimal("30000")
        self.rent.save(update_fields=["status", "amount_paid"])
        self.assertEqual(self.badges(), [{"tone": "paid", "label": "Paid"}])

    def test_a_cancelled_row_shows_only_cancelled(self):
        self.rent.status = RentRecord.Status.CANCELLED
        self.rent.save(update_fields=["status"])
        self.assertEqual(self.badges(), [{"tone": "cancelled", "label": "Cancelled"}])

    def test_an_open_row_shows_pending(self):
        self.assertEqual(self.badges(), [{"tone": "pending", "label": "Pending"}])

    def test_a_partially_paid_row_shows_partial_and_pending(self):
        self.rent.amount_paid = Decimal("5000")
        self.rent.save(update_fields=["amount_paid"])
        self.assertEqual(
            self.badges(),
            [
                {"tone": "partial", "label": "Partially paid"},
                {"tone": "pending", "label": "Pending"},
            ],
        )

    def test_an_overdue_partially_paid_row_shows_overdue_first(self):
        self.rent.status = RentRecord.Status.OVERDUE
        self.rent.amount_paid = Decimal("5000")
        self.rent.save(update_fields=["status", "amount_paid"])
        self.assertEqual(
            self.badges(),
            [
                {"tone": "overdue", "label": "Overdue"},
                {"tone": "partial", "label": "Partially paid"},
                {"tone": "pending", "label": "Pending"},
            ],
        )


class LedgerAmountTests(RentLedgerViewTestBase):
    """The money of a row."""

    def test_the_billed_amount_adds_the_late_fee_and_takes_the_discount(self):
        self.rent.late_fee = Decimal("1500")
        self.rent.discount = Decimal("500")
        self.rent.save(update_fields=["late_fee", "discount"])
        amounts = self.ledger()["amounts"]
        self.assertEqual(amounts["total_due"], "31000.00")
        self.assertEqual(amounts["balance"], "31000.00")
        self.assertTrue(amounts["has_charges"])
        self.assertEqual(amounts["total_due_display"], "₹31,000")

    def test_the_balance_falls_with_every_part(self):
        self.rent.amount_paid = Decimal("8000")
        self.rent.save(update_fields=["amount_paid"])
        amounts = self.ledger()["amounts"]
        self.assertEqual(amounts["amount_paid"], "8000.00")
        self.assertEqual(amounts["balance"], "22000.00")
        self.assertEqual(amounts["balance_display"], "₹22,000")
        self.assertTrue(amounts["has_balance"])
        self.assertTrue(amounts["collected"])

    def test_the_charge_breakdown_names_every_extra_charge(self):
        self.rent.late_fee = Decimal("1500")
        self.rent.discount = Decimal("500")
        self.rent.save(update_fields=["late_fee", "discount"])
        self.assertEqual(
            self.ledger()["charge_breakdown"],
            [
                {"tone": "due", "label": "+ ₹1,500 late fee"},
                {"tone": "settled", "label": "− ₹500 discount"},
            ],
        )

    def test_the_charge_breakdown_is_empty_without_extra_charges(self):
        self.assertEqual(self.ledger()["charge_breakdown"], [])

    def test_the_progress_is_the_share_of_the_bill_that_was_received(self):
        self.rent.amount_paid = Decimal("8000")
        self.rent.save(update_fields=["amount_paid"])
        progress = self.ledger()["progress"]
        self.assertEqual(progress["paid_percent"], 27)
        self.assertFalse(progress["settled"])
        self.assertFalse(progress["has_parts"])

    def test_a_settled_row_is_settled(self):
        self.rent.amount_paid = Decimal("30000")
        self.rent.save(update_fields=["amount_paid"])
        progress = self.ledger()["progress"]
        self.assertEqual(progress["paid_percent"], 100)
        self.assertTrue(progress["settled"])


class LedgerPartRuleTests(RentLedgerViewTestBase):
    """The bounds of the next part payment."""

    def test_the_part_cannot_be_larger_than_the_balance(self):
        rules = self.ledger()["part_rules"]
        self.assertEqual(rules["max_amount"], "30000.00")
        self.assertEqual(rules["max_amount_display"], "₹30,000")
        self.assertTrue(rules["can_record_part"])

    def test_a_part_cannot_be_dated_before_the_due_date(self):
        rules = self.ledger()["part_rules"]
        self.assertEqual(rules["min_paid_on"], "2026-10-05")
        self.assertEqual(rules["default_paid_on"], "2026-10-05")

    def test_an_overdue_month_starts_from_today(self):
        self.rent.status = RentRecord.Status.OVERDUE
        self.rent.save(update_fields=["status"])
        rules = self.ledger(today=date(2026, 10, 20))["part_rules"]
        self.assertEqual(rules["default_paid_on"], "2026-10-20")
        self.assertEqual(rules["min_paid_on"], "2026-10-05")

    def test_the_messages_carry_the_balance(self):
        rules = self.ledger()["part_rules"]
        self.assertEqual(
            rules["messages"]["amount_too_large"],
            "This part is larger than the remaining balance of ₹30,000.",
        )
        self.assertEqual(
            rules["messages"]["amount_required"],
            "Enter the amount received in this part.",
        )
        self.assertEqual(
            rules["messages"]["date_before_due"],
            "The part date cannot be earlier than the rent due date.",
        )

    def test_the_ledger_renders_the_indian_dates(self):
        rules = self.ledger()["part_rules"]
        self.assertEqual(rules["due_date_display"], "05-Oct-2026")
        self.assertEqual(rules["min_paid_on_display"], "05-Oct-2026")

    def test_the_ledger_renders_september_as_sept(self):
        self.rent.due_date = date(2026, 9, 5)
        self.rent.save(update_fields=["due_date"])
        rules = self.ledger()["part_rules"]
        self.assertEqual(rules["due_date_display"], "05-Sept-2026")

    def test_the_overdue_hint_names_the_late_fee(self):
        self.rent.status = RentRecord.Status.OVERDUE
        self.rent.late_fee = Decimal("1500")
        self.rent.save(update_fields=["status", "late_fee"])
        rules = self.ledger()["part_rules"]
        self.assertTrue(rules["late_fee_included"])
        self.assertEqual(rules["late_fee_display"], "₹1,500")


class LedgerReceiptTests(RentLedgerViewTestBase):
    """The receipt the ledger hands to the client."""

    def test_the_month_receipt_carries_the_file_name_and_the_amounts(self):
        ledger = self.ledger()
        self.assertEqual(
            ledger["receipt_filename"],
            f"rent_receipt_{self.rent.id}_202610.pdf",
        )
        receipt = ledger["receipt"]
        self.assertEqual(receipt["receipt_no"], ledger["receipt_filename"])
        self.assertEqual(receipt["dues_amount"], "₹30,000")
        self.assertEqual(receipt["payee"], "Meera Iyer")
        self.assertEqual(receipt["period"], "October 2026")
        self.assertEqual(receipt["due_date"], "05 Oct 2026")

    def test_every_part_carries_its_own_receipt(self):
        part = RentRecordPart.objects.create(
            rent_record=self.rent,
            amount=Decimal("8000"),
            paid_on=self.due_date,
            payment_method="upi",
        )
        self.rent.amount_paid = Decimal("8000")
        self.rent.save(update_fields=["amount_paid"])

        from properties.services.rent_ledger_view import build_part_view

        view = build_part_view(self.rent, part)
        self.assertEqual(view["sequence"], 1)
        self.assertEqual(view["cumulative_amount"], "8000.00")
        self.assertEqual(
            view["receipt_filename"],
            f"rent_receipt_{self.rent.id}_202610_part1.pdf",
        )
        self.assertEqual(view["receipt"]["part_label"], "Part 1 of 1")
        self.assertEqual(view["receipt"]["total_paid"], "₹8,000")

    def test_the_parts_are_numbered_in_ledger_order(self):
        first = RentRecordPart.objects.create(
            rent_record=self.rent,
            amount=Decimal("8000"),
            paid_on=self.due_date,
            payment_method="upi",
        )
        second = RentRecordPart.objects.create(
            rent_record=self.rent,
            amount=Decimal("7000"),
            paid_on=self.due_date + timedelta(days=1),
            payment_method="cash",
        )

        from properties.services.rent_ledger_view import build_part_view

        self.assertEqual(build_part_view(self.rent, first)["sequence"], 1)
        self.assertEqual(build_part_view(self.rent, second)["sequence"], 2)
        self.assertEqual(
            build_part_view(self.rent, second)["cumulative_amount"], "15000.00"
        )


class LedgerApiTests(RentLedgerViewTestBase):
    """The API ships the ledger view to the client."""

    def test_the_listing_carries_the_ledger_view(self):
        response = self.client.get("/api/rent-records/")
        self.assertEqual(response.status_code, 200)
        row = self.rows(response)[0]
        self.assertIn("ledger", row)
        ledger = row["ledger"]
        self.assertIn("row_state", ledger)
        self.assertIn("status_badges", ledger)
        self.assertIn("charge_breakdown", ledger)
        self.assertIn("progress", ledger)
        self.assertIn("part_rules", ledger)
        self.assertIn("receipt", ledger)
        self.assertEqual(ledger["amounts"]["total_due"], "30000.00")
        self.assertEqual(ledger["status_badges"][0]["label"], "Pending")

    def test_the_parts_carry_their_position_and_receipt(self):
        RentRecordPart.objects.create(
            rent_record=self.rent,
            amount=Decimal("8000"),
            paid_on=self.due_date,
            payment_method="upi",
        )
        response = self.client.get("/api/rent-records/")
        part = self.rows(response)[0]["parts"][0]
        self.assertEqual(part["sequence"], 1)
        self.assertEqual(part["cumulative_amount"], "8000.00")
        self.assertEqual(
            part["receipt_filename"],
            f"rent_receipt_{self.rent.id}_202610_part1.pdf",
        )
        self.assertEqual(part["receipt"]["part_label"], "Part 1 of 1")

    def test_the_rules_endpoint_ships_the_limits_and_the_wording(self):
        response = self.client.get("/api/rent-records/rules/")
        self.assertEqual(response.status_code, 200)
        rules = response.json()
        self.assertEqual(rules["amount"]["max"], "1000000.00")
        self.assertEqual(
            rules["amount"]["required_message"],
            "Enter a rent amount greater than zero.",
        )
        self.assertEqual(
            rules["charges"]["non_negative_message"],
            "Late fee and discount cannot be negative.",
        )
        self.assertTrue(rules["cancel"]["requires_reason"])
        self.assertFalse(rules["duplicate"]["allowed"])


class RentRecordAmountValidationTests(RentLedgerViewTestBase):
    """A new record is billed for a positive amount."""

    def create_body(self, **overrides):
        body = {
            "unit": self.unit.id,
            "renter": self.renter.id,
            "amount": "25000",
            "payment_method": "cash",
            "due_date": "2026-11-05",
        }
        body.update(overrides)
        return body

    @patch("notification.utils.send_whatsapp_message")
    @patch("rentsecure_be.services.razorpay_service.create_payment_link")
    def test_a_zero_amount_is_refused(self, _link, _whatsapp):
        response = self.client.post(
            "/api/rent-records/", self.create_body(amount="0"), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["amount"][0], "Enter a rent amount greater than zero."
        )

    @patch("notification.utils.send_whatsapp_message")
    @patch("rentsecure_be.services.razorpay_service.create_payment_link")
    def test_a_negative_amount_is_refused(self, _link, _whatsapp):
        response = self.client.post(
            "/api/rent-records/", self.create_body(amount="-500"), format="json"
        )
        self.assertEqual(response.status_code, 400)

    @patch("notification.utils.send_whatsapp_message")
    @patch("rentsecure_be.services.razorpay_service.create_payment_link")
    def test_a_negative_late_fee_is_refused(self, _link, _whatsapp):
        response = self.client.post(
            "/api/rent-records/",
            self.create_body(late_fee="-100"),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["late_fee"][0],
            "Late fee and discount cannot be negative.",
        )

    @patch("notification.utils.send_whatsapp_message")
    @patch("rentsecure_be.services.razorpay_service.create_payment_link")
    def test_a_negative_discount_is_refused(self, _link, _whatsapp):
        response = self.client.post(
            "/api/rent-records/",
            self.create_body(discount="-100"),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
