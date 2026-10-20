"""Edge cases of the rent collection tab.

The tests in this module encode the rules of
``properties/RENT_COLLECTION_BUSINESS_RULES.md`` at their edges — the cases
that rarely happen and therefore rot first:

* a cancelled month must stay silent (no reminder, no receipt);
* an open month must still be editable in the fields the rules allow;
* a discount may never make the bill negative;
* a part payment must never push the record over the bill;
* the ledger query must never leak a record of another owner.
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from rest_framework.test import APIClient

from django.core.cache import cache
from django.test import TestCase

from core.models import User
from properties.models import Building, Renter, RentRecord, Unit
from properties.services.rent_ledger_view import build_ledger_view


class EdgeCaseTestBase(TestCase):
    """One owner with two units, one renter each and one open month."""

    def setUp(self):
        # The API throttles per user and the tests share the user ids of
        # the rolled back rows — a fresh cache keeps every test its own quota.
        cache.clear()
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username="edge_owner",
            password="testpass123",
            full_name="Edge Owner",
            phone="+911000000011",
        )
        self.other_owner = User.objects.create_user(
            username="edge_other",
            password="testpass123",
            full_name="Edge Other",
            phone="+911000000012",
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="Edge House",
            address_line="1 Street",
            city="Pune",
            state="MH",
            country="IN",
            postal_code="411001",
        )
        self.other_building = Building.objects.create(
            owner=self.other_owner,
            name="Foreign House",
            address_line="2 Street",
            city="Pune",
            state="MH",
            country="IN",
            postal_code="411002",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="E-101",
            unit_type="flat",
            address_line="1 Street",
            city="Pune",
            state="MH",
            country="IN",
            postal_code="411001",
            allow_partial_payments=True,
        )
        self.other_unit = Unit.objects.create(
            owner=self.other_owner,
            building=self.other_building,
            unit="F-101",
            unit_type="flat",
            address_line="2 Street",
            city="Pune",
            state="MH",
            country="IN",
            postal_code="411002",
            allow_partial_payments=True,
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Edge Renter",
            phone="+912345678900",
            email="edge.renter@example.com",
            rent_amount=Decimal("30000"),
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

    def cancel(self, rent=None, reason="Vacated"):
        response = self.client.post(
            f"/api/rent-records/{(rent or self.rent).id}/cancel/",
            {"reason": reason},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def settle(self, rent=None, amount="30000"):
        rent = rent or self.rent
        response = self.client.post(
            f"/api/rent-records/{rent.id}/payments/",
            {
                "amount": amount,
                "paid_on": (rent.due_date + timedelta(days=1)).isoformat(),
                "payment_method": "upi",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        return response.json()


class CancelledMonthSilenceTests(EdgeCaseTestBase):
    """A cancelled month is voided — it must not talk to the renter anymore."""

    def test_a_cancelled_row_cannot_be_reminded(self):
        self.cancel()
        rent = RentRecord.objects.get(pk=self.rent.pk)
        state = build_ledger_view(rent)["row_state"]
        self.assertFalse(state["can_remind"])
        self.assertFalse(state["can_send_receipt"])
        self.assertFalse(state["can_record_part"])
        self.assertFalse(state["can_cancel"])
        self.assertFalse(state["can_edit"])

    def test_a_cancelled_record_is_never_reminded(self):
        self.cancel()
        with patch(
            "properties.services.rent_collection_service.send_whatsapp_message"
        ) as whatsapp:
            response = self.client.post(
                f"/api/rent-records/{self.rent.id}/send-reminder/"
            )
            self.assertEqual(response.status_code, 400)
            whatsapp.assert_not_called()

    def test_a_cancelled_record_never_gets_a_receipt(self):
        self.cancel()
        response = self.client.post(f"/api/rent-records/{self.rent.id}/send-receipt/")
        self.assertEqual(response.status_code, 400)

    def test_a_cancelled_record_keeps_its_reason_and_its_place(self):
        self.cancel(reason="Tenant left in October")
        rent = RentRecord.objects.get(pk=self.rent.pk)
        self.assertEqual(rent.status, RentRecord.Status.CANCELLED)
        self.assertEqual(rent.cancel_reason, "Tenant left in October")
        self.assertIsNotNone(rent.cancelled_at)
        self.assertEqual(rent.cancelled_by, self.owner)
        # It stays in the ledger — it is voided, not deleted.
        listing = self.client.get("/api/rent-records/").json()
        rows = listing["results"] if isinstance(listing, dict) else listing
        self.assertIn(self.rent.id, [row["id"] for row in rows])


class OpenMonthEditTests(EdgeCaseTestBase):
    """The fields the rules allow may still be edited while the month is open."""

    def test_the_paid_on_date_of_an_open_record_can_be_edited(self):
        response = self.client.patch(
            f"/api/rent-records/{self.rent.id}/",
            {"paid_on": "2026-10-08"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            str(RentRecord.objects.get(pk=self.rent.pk).paid_on), "2026-10-08"
        )

    def test_the_notes_of_an_open_record_can_be_edited(self):
        response = self.client.patch(
            f"/api/rent-records/{self.rent.id}/",
            {"notes": "Owner called on Monday"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            RentRecord.objects.get(pk=self.rent.pk).notes, "Owner called on Monday"
        )

    def test_the_paid_on_date_cannot_be_moved_before_the_due_date(self):
        response = self.client.patch(
            f"/api/rent-records/{self.rent.id}/",
            {"paid_on": "2026-10-01"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_the_discount_cannot_be_larger_than_the_bill(self):
        response = self.client.patch(
            f"/api/rent-records/{self.rent.id}/",
            {"discount": "40000"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(RentRecord.objects.get(pk=self.rent.pk).discount, Decimal("0"))

    def test_the_bill_never_shows_negative_money(self):
        """Even a record that was written with a wild discount never shows a negative total."""
        self.rent.discount = Decimal("45000")
        self.rent.save(update_fields=["discount"])
        amounts = build_ledger_view(self.rent)["amounts"]
        self.assertFalse(amounts["total_due"].startswith("-"))
        self.assertGreaterEqual(Decimal(amounts["balance"]), Decimal("0"))


class PartPaymentEdgeTests(EdgeCaseTestBase):
    """The parts of a month."""

    def test_the_parts_add_up_to_the_amount_that_was_received(self):
        self.client.post(
            f"/api/rent-records/{self.rent.id}/payments/",
            {
                "amount": "10000",
                "paid_on": "2026-10-06",
                "payment_method": "upi",
            },
            format="json",
        )
        self.settle(amount="20000")
        rent = RentRecord.objects.get(pk=self.rent.pk)
        self.assertEqual(rent.amount_paid, Decimal("30000"))
        self.assertEqual(rent.status, RentRecord.Status.PAID)
        self.assertEqual(rent.parts.count(), 2)
        parts = list(rent.parts.order_by("paid_on", "id"))
        self.assertEqual(
            [part.amount for part in parts], [Decimal("10000"), Decimal("20000")]
        )

    def test_a_part_of_exactly_the_balance_settles_the_month(self):
        self.settle(amount="30000")
        rent = RentRecord.objects.get(pk=self.rent.pk)
        self.assertEqual(rent.status, RentRecord.Status.PAID)
        self.assertEqual(rent.balance, Decimal("0"))

    def test_a_part_cannot_be_recorded_without_a_date(self):
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/payments/",
            {"amount": "1000", "payment_method": "upi"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.rent.parts.count(), 0)

    def test_a_part_cannot_exceed_the_bill_in_the_second_step(self):
        self.client.post(
            f"/api/rent-records/{self.rent.id}/payments/",
            {
                "amount": "20000",
                "paid_on": "2026-10-06",
                "payment_method": "upi",
            },
            format="json",
        )
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/payments/",
            {
                "amount": "15000",
                "paid_on": "2026-10-07",
                "payment_method": "upi",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            RentRecord.objects.get(pk=self.rent.pk).amount_paid, Decimal("20000")
        )

    def test_the_balance_of_the_record_follows_the_parts(self):
        self.client.post(
            f"/api/rent-records/{self.rent.id}/payments/",
            {
                "amount": "12000",
                "paid_on": "2026-10-06",
                "payment_method": "upi",
            },
            format="json",
        )
        rent = RentRecord.objects.get(pk=self.rent.pk)
        self.assertEqual(rent.balance, Decimal("18000"))
        amounts = build_ledger_view(rent)["amounts"]
        self.assertEqual(amounts["balance"], "18000.00")
        self.assertEqual(amounts["amount_paid"], "12000.00")

    def test_a_part_of_a_record_of_another_owner_is_refused(self):
        self.client.force_authenticate(self.other_owner)
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/payments/",
            {
                "amount": "1000",
                "paid_on": "2026-10-06",
                "payment_method": "upi",
            },
            format="json",
        )
        self.assertIn(response.status_code, (403, 404))
        self.assertEqual(self.rent.parts.count(), 0)


class OwnershipEdgeTests(EdgeCaseTestBase):
    """Nothing of another owner may be read or written."""

    def test_another_owner_cannot_read_the_record(self):
        self.client.force_authenticate(self.other_owner)
        self.assertEqual(
            self.client.get(f"/api/rent-records/{self.rent.id}/").status_code, 404
        )

    def test_another_owner_cannot_cancel_the_record(self):
        self.client.force_authenticate(self.other_owner)
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/cancel/",
            {"reason": "Not mine"},
            format="json",
        )
        self.assertIn(response.status_code, (403, 404))
        self.assertEqual(
            RentRecord.objects.get(pk=self.rent.pk).status, RentRecord.Status.PENDING
        )

    def test_another_owner_cannot_edit_the_record(self):
        self.client.force_authenticate(self.other_owner)
        response = self.client.patch(
            f"/api/rent-records/{self.rent.id}/",
            {"notes": "Not mine"},
            format="json",
        )
        self.assertIn(response.status_code, (403, 404))
        self.assertEqual(RentRecord.objects.get(pk=self.rent.pk).notes, "")

    def test_the_ledger_of_another_owner_is_empty(self):
        self.client.force_authenticate(self.other_owner)
        page = self.client.get("/api/rent-records/ledger/").json()
        self.assertEqual(page["count"], 0)
        self.assertEqual(page["results"], [])
        self.assertEqual(page["filters"]["building"]["options"], [])


class LedgerQueryEdgeTests(EdgeCaseTestBase):
    """The ledger query at its edges."""

    def test_an_empty_ledger_answers_with_an_empty_page(self):
        self.client.force_authenticate(self.other_owner)
        page = self.client.get("/api/rent-records/ledger/?page=3&page_size=10").json()
        self.assertEqual(page["count"], 0)
        self.assertEqual(page["total_pages"], 1)
        self.assertEqual(page["page"], 1)
        self.assertEqual(page["first_row"], 0)
        self.assertEqual(page["last_row"], 0)
        self.assertIsNone(page["next_page"])

    def test_a_filter_that_matches_nothing_answers_with_an_empty_page(self):
        page = self.client.get(
            f"/api/rent-records/ledger/?building={self.other_building.id}"
        ).json()
        self.assertEqual(page["count"], 0)
        self.assertEqual(page["results"], [])
        self.assertEqual(page["summary"]["paid"], 0)

    def test_the_page_size_is_refused_when_it_is_not_offered(self):
        page = self.client.get("/api/rent-records/ledger/?page_size=13").json()
        self.assertEqual(page["page_size"], 25)

    def test_a_negative_page_lands_on_the_first_one(self):
        page = self.client.get("/api/rent-records/ledger/?page=-4").json()
        self.assertEqual(page["page"], 1)

    def test_the_search_matches_the_renter(self):
        page = self.client.get("/api/rent-records/ledger/?search=Edge Renter").json()
        self.assertEqual(page["count"], 1)

    def test_the_search_matches_the_building(self):
        page = self.client.get("/api/rent-records/ledger/?search=Edge House").json()
        self.assertEqual(page["count"], 1)

    def test_the_search_matches_the_unit(self):
        page = self.client.get("/api/rent-records/ledger/?search=E-101").json()
        self.assertEqual(page["count"], 1)

    def test_a_search_that_matches_nothing_answers_with_an_empty_page(self):
        page = self.client.get("/api/rent-records/ledger/?search=nothing-here").json()
        self.assertEqual(page["count"], 0)
        self.assertEqual(page["results"], [])

    def test_the_facets_survive_a_filter_that_matches_nothing(self):
        page = self.client.get("/api/rent-records/ledger/?status=cancelled").json()
        self.assertEqual(page["count"], 0)
        # The options of the status filter are counted with the other filters
        # applied — a cancelled filter offers the other statuses only.
        offered = [option["value"] for option in page["filters"]["status"]["options"]]
        self.assertNotIn("cancelled", offered)
        self.assertIn("pending", offered)


class DuplicateMonthTests(EdgeCaseTestBase):
    """A unit is billed once for a month — whoever the renter is."""

    def setUp(self):
        super().setUp()
        self.second_renter = Renter.objects.create(
            unit=self.unit,
            name="Edge Second Renter",
            phone="+912345678922",
            email="edge.second@example.com",
            rent_amount=Decimal("30000"),
            start_date=date(2026, 1, 1),
        )

    def test_the_same_month_cannot_be_billed_twice_for_a_unit(self):
        self.settle()
        first = self.client.post(
            "/api/rent-records/",
            {
                "unit": self.unit.id,
                "renter": self.renter.id,
                "amount": "30000",
                "due_date": "2026-11-05",
                "payment_method": "cash",
            },
            format="json",
        )
        self.assertEqual(first.status_code, 201)
        # A different renter for the very same unit and month — the database
        # guards the pair, so the second record has to be refused.
        second = self.client.post(
            "/api/rent-records/",
            {
                "unit": self.unit.id,
                "renter": self.second_renter.id,
                "amount": "30000",
                "due_date": "2026-11-05",
                "payment_method": "cash",
            },
            format="json",
        )
        self.assertEqual(second.status_code, 400)
        self.assertEqual(
            RentRecord.objects.filter(
                unit=self.unit, due_date=date(2026, 11, 5)
            ).count(),
            1,
        )

    def test_the_duplicate_is_refused_and_not_crashed(self):
        """The database guards ``(unit, due_date)`` — the API has to agree with it."""
        self.settle()
        self.client.post(
            "/api/rent-records/",
            {
                "unit": self.unit.id,
                "renter": self.renter.id,
                "amount": "30000",
                "due_date": "2026-11-05",
                "payment_method": "cash",
            },
            format="json",
        )
        with patch(
            "properties.views.rent_record_views.create_payment_link",
            side_effect=AssertionError("the record must not be created"),
        ):
            response = self.client.post(
                "/api/rent-records/",
                {
                    "unit": self.unit.id,
                    "renter": self.second_renter.id,
                    "amount": "30000",
                    "due_date": "2026-11-05",
                    "payment_method": "cash",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 400)


class ReceiptDeliveryTests(EdgeCaseTestBase):
    """A receipt that could not be delivered was never sent."""

    def test_a_failed_delivery_is_reported_as_a_failure(self):
        self.settle()
        with (
            patch("django.core.mail.EmailMessage.send", return_value=0),
            patch(
                "properties.services.rent_collection_service.send_whatsapp_message",
                return_value=False,
            ),
            patch(
                "properties.services.rent_collection_service.generate_rent_receipt_pdf",
                return_value=b"%PDF-1.4 test",
            ),
        ):
            response = self.client.post(
                f"/api/rent-records/{self.rent.id}/send-receipt/"
            )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["sent"])
        self.assertIsNone(response.json()["receipt_sent_at"])
        self.assertIsNone(RentRecord.objects.get(pk=self.rent.pk).receipt_sent_at)

    def test_a_delivered_receipt_is_reported_as_a_success(self):
        self.settle()
        with (
            patch("django.core.mail.EmailMessage.send", return_value=1),
            patch(
                "properties.services.rent_collection_service.send_whatsapp_message",
                return_value=False,
            ),
            patch(
                "properties.services.rent_collection_service.generate_rent_receipt_pdf",
                return_value=b"%PDF-1.4 test",
            ),
        ):
            response = self.client.post(
                f"/api/rent-records/{self.rent.id}/send-receipt/"
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["sent"])
        self.assertIsNotNone(RentRecord.objects.get(pk=self.rent.pk).receipt_sent_at)


class MonthNameTests(EdgeCaseTestBase):
    """The month names never depend on the locale of the server."""

    def test_the_cycle_names_the_month_in_english(self):
        state = self.client.get(f"/api/rent-records/cycle/?unit={self.unit.id}").json()
        self.assertEqual(state["previous_month"], "October 2026")
        self.assertEqual(state["next_month"], "November 2026")

    def test_the_receipt_period_is_written_in_english(self):
        self.settle()
        with (
            patch("django.core.mail.EmailMessage.send", return_value=1),
            patch(
                "properties.services.rent_collection_service.send_whatsapp_message",
                return_value=False,
            ),
            patch(
                "properties.services.rent_collection_service.generate_rent_receipt_pdf",
                return_value=b"%PDF-1.4 test",
            ),
        ):
            self.client.post(f"/api/rent-records/{self.rent.id}/send-receipt/")
        receipt = build_ledger_view(RentRecord.objects.get(pk=self.rent.pk))["receipt"]
        self.assertEqual(receipt["period"], "October 2026")


class BrokenChainTests(EdgeCaseTestBase):
    """An imported history may leave a hole in the chain — it must not stay open."""

    def setUp(self):
        super().setUp()
        self.chain_unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="E-202",
            unit_type="flat",
            address_line="1 Street",
            city="Pune",
            state="MH",
            country="IN",
            postal_code="411001",
            allow_partial_payments=True,
        )
        self.chain_renter = Renter.objects.create(
            unit=self.chain_unit,
            name="Chain Renter",
            phone="+912345678933",
            email="chain@example.com",
            rent_amount=Decimal("30000"),
            start_date=date(2026, 1, 1),
        )
        # A history that was imported around the rules: August is settled,
        # September was never settled and October was billed anyway.
        for month, status in ((8, "paid"), (9, "pending"), (10, "paid")):
            RentRecord.objects.create(
                renter=self.chain_renter,
                unit=self.chain_unit,
                due_date=date(2026, month, 5),
                amount=Decimal("30000"),
                amount_paid=Decimal("30000") if status == "paid" else Decimal("0"),
                payment_method="upi",
                status=status,
            )

    def test_an_open_month_holds_the_chain_even_when_a_later_month_is_settled(self):
        response = self.client.post(
            "/api/rent-records/",
            {
                "unit": self.chain_unit.id,
                "renter": self.chain_renter.id,
                "amount": "30000",
                "due_date": "2026-11-05",
                "payment_method": "cash",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("September 2026", str(response.json()))

    def test_the_cycle_names_the_month_that_holds_the_chain(self):
        state = self.client.get(
            f"/api/rent-records/cycle/?unit={self.chain_unit.id}"
        ).json()
        self.assertFalse(state["allowed"])
        self.assertEqual(state["blocking_month"], "September 2026")
        self.assertIn("September 2026", state["blocked_message"])

    def test_the_chain_opens_again_once_the_open_month_is_settled(self):
        open_month = RentRecord.objects.get(
            unit=self.chain_unit, due_date=date(2026, 9, 5)
        )
        response = self.client.post(
            f"/api/rent-records/{open_month.id}/payments/",
            {
                "amount": "30000",
                "paid_on": "2026-09-06",
                "payment_method": "upi",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        state = self.client.get(
            f"/api/rent-records/cycle/?unit={self.chain_unit.id}"
        ).json()
        self.assertTrue(state["allowed"])
        self.assertEqual(state["next_due_date"], "2026-11-05")


class CreatePayloadTests(EdgeCaseTestBase):
    """A new record starts unpaid — whatever the payload carries."""

    def setUp(self):
        super().setUp()
        self.fresh_unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="E-303",
            unit_type="flat",
            address_line="1 Street",
            city="Pune",
            state="MH",
            country="IN",
            postal_code="411001",
        )
        self.fresh_renter = Renter.objects.create(
            unit=self.fresh_unit,
            name="Fresh Renter",
            phone="+912345678944",
            email="fresh@example.com",
            rent_amount=Decimal("30000"),
            start_date=date(2026, 1, 1),
        )

    def test_a_paid_on_date_is_ignored_on_create(self):
        response = self.client.post(
            "/api/rent-records/",
            {
                "unit": self.fresh_unit.id,
                "renter": self.fresh_renter.id,
                "amount": "30000",
                "due_date": "2026-10-05",
                "payment_method": "cash",
                "paid_on": "2026-10-01",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        rent = RentRecord.objects.get(pk=response.json()["id"])
        self.assertIsNone(rent.paid_on)
        self.assertEqual(rent.amount_paid, Decimal("0"))
        self.assertEqual(rent.status, RentRecord.Status.PENDING)


class CycleEdgeTests(EdgeCaseTestBase):
    """The billing cycle at its edges."""

    def test_the_chain_continues_over_a_cancelled_month(self):
        self.cancel()
        response = self.client.post(
            "/api/rent-records/",
            {
                "unit": self.unit.id,
                "renter": self.renter.id,
                "amount": "30000",
                "due_date": "2026-11-05",
                "payment_method": "cash",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_a_month_cannot_be_billed_twice(self):
        self.settle()
        response = self.client.post(
            "/api/rent-records/",
            {
                "unit": self.unit.id,
                "renter": self.renter.id,
                "amount": "30000",
                "due_date": "2026-11-05",
                "payment_method": "cash",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        second = self.client.post(
            "/api/rent-records/",
            {
                "unit": self.unit.id,
                "renter": self.renter.id,
                "amount": "30000",
                "due_date": "2026-11-05",
                "payment_method": "cash",
            },
            format="json",
        )
        self.assertEqual(second.status_code, 400)

    def test_the_cycle_belongs_to_the_unit_and_not_to_the_renter(self):
        """A new renter in the same unit does not start a second chain."""
        self.settle()
        new_renter = Renter.objects.create(
            unit=self.unit,
            name="Second Renter",
            phone="+912345678911",
            email="second@example.com",
            rent_amount=Decimal("30000"),
            start_date=date(2026, 11, 1),
        )
        response = self.client.post(
            "/api/rent-records/",
            {
                "unit": self.unit.id,
                "renter": new_renter.id,
                "amount": "30000",
                "due_date": "2026-12-05",
                "payment_method": "cash",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
