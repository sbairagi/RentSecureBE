"""Tests for the ledger query — the filters, the facets and the pagination.

The ledger is queried on the server: the client sends the filters it applied
and the page it wants, and the server answers with the rows of that page, the
grouped filter options and the state of the pagination.  These tests lock
that contract.
"""

from datetime import date
from decimal import Decimal

from rest_framework.test import APIClient

from django.core.cache import cache
from django.test import TestCase

from core.models import User
from properties.models import Building, Renter, RentRecord, Unit
from properties.services.rent_ledger_query import (
    DEFAULT_PAGE_SIZE,
    PAGE_SIZES,
    build_ledger_page,
    parse_page_size,
    parse_values,
)


def make_owner(username: str) -> User:
    return User.objects.create_user(
        username=username,
        password="testpass123",
        full_name=username.replace("_", " ").title(),
        phone=f"+9110000{abs(hash(username)) % 10000:04d}",
    )


def make_building(owner: User, name: str) -> Building:
    return Building.objects.create(
        owner=owner,
        name=name,
        address_line="1 Street",
        city="Pune",
        state="MH",
        country="IN",
        postal_code="411001",
    )


def make_unit(owner: User, building: Building, code: str) -> Unit:
    return Unit.objects.create(
        owner=owner,
        building=building,
        unit=code,
        unit_type="flat",
        address_line="1 Street",
        city="Pune",
        state="MH",
        country="IN",
        postal_code="411001",
    )


def make_record(
    unit: Unit, code: str, due: date, status: str, amount: str = "30000"
) -> RentRecord:
    renter = Renter.objects.create(
        unit=unit,
        name=code,
        phone=f"+9123456{abs(hash(code)) % 10000:04d}",
        email=f"{code.lower().replace(' ', '.')}@example.com",
        rent_amount=Decimal(amount),
        start_date=date(2025, 1, 1),
    )
    return RentRecord.objects.create(
        renter=renter,
        unit=unit,
        due_date=due,
        amount=Decimal(amount),
        payment_method="upi",
        status=status,
        amount_paid=(
            Decimal(amount) if status == RentRecord.Status.PAID else Decimal("0")
        ),
    )


class LedgerQueryTestBase(TestCase):
    """One owner with two buildings, four units and a handful of records."""

    def setUp(self):
        # The API throttles per user and the tests share the user ids of
        # the rolled back rows — a fresh cache keeps every test its own quota.
        cache.clear()
        self.client = APIClient()
        self.owner = make_owner("ledger_owner")
        self.other = make_owner("ledger_other")

        self.maple = make_building(self.owner, "Maple Heights")
        self.lakeview = make_building(self.owner, "Lakeview Residency")
        self.foreign_building = make_building(self.other, "Foreign House")

        self.b101 = make_unit(self.owner, self.maple, "B-101")
        self.b102 = make_unit(self.owner, self.maple, "B-102")
        self.a102 = make_unit(self.owner, self.lakeview, "A-102")
        self.foreign_unit = make_unit(self.other, self.foreign_building, "F-101")

        self.paid = make_record(
            self.b101, "Jesse Thomas", date(2026, 10, 5), RentRecord.Status.PAID
        )
        self.pending = make_record(
            self.b101, "Meera Iyer", date(2026, 9, 5), RentRecord.Status.PENDING
        )
        self.overdue = make_record(
            self.b102, "Rohan Gupta", date(2026, 8, 5), RentRecord.Status.OVERDUE
        )
        self.cancelled = make_record(
            self.b102, "Riya Kapoor", date(2026, 7, 5), RentRecord.Status.CANCELLED
        )
        self.settled_elsewhere = make_record(
            self.a102, "Priya Shah", date(2026, 6, 5), RentRecord.Status.PAID
        )
        self.foreign = make_record(
            self.foreign_unit,
            "Foreign Renter",
            date(2026, 10, 1),
            RentRecord.Status.PAID,
        )

        self.client.force_authenticate(self.owner)

    def ledger(self, query: str = "") -> dict:
        response = self.client.get(f"/api/rent-records/ledger/{query}")
        self.assertEqual(response.status_code, 200)
        return response.json()

    @staticmethod
    def units_of(page: dict) -> list[str]:
        return [row["unit"]["unit"] for row in page["results"]]


class LedgerPageTests(LedgerQueryTestBase):
    def test_the_ledger_answers_with_the_page_and_its_state(self):
        page = self.ledger()
        self.assertEqual(page["count"], 5)
        self.assertEqual(page["page"], 1)
        self.assertEqual(page["page_size"], DEFAULT_PAGE_SIZE)
        self.assertEqual(page["total_pages"], 1)
        self.assertEqual(page["page_sizes"], list(PAGE_SIZES))
        self.assertIsNone(page["previous_page"])
        self.assertIsNone(page["next_page"])
        self.assertEqual(page["first_row"], 1)
        self.assertEqual(page["last_row"], 5)
        self.assertEqual(len(page["results"]), 5)

    def test_the_page_holds_the_rows_the_client_asked_for(self):
        page = self.ledger("?page_size=10")
        self.assertEqual(page["page_size"], 10)
        self.assertEqual(page["total_pages"], 1)
        self.assertIsNone(page["previous_page"])
        self.assertIsNone(page["next_page"])
        self.assertEqual(len(page["results"]), 5)

    def test_a_page_beyond_the_last_one_lands_on_the_last_one(self):
        page = self.ledger("?page=99")
        self.assertEqual(page["page"], 1)
        self.assertEqual(page["total_pages"], 1)

    def test_a_page_size_that_is_not_offered_falls_back_to_the_default(self):
        page = self.ledger("?page_size=37")
        self.assertEqual(page["page_size"], DEFAULT_PAGE_SIZE)

    def test_every_offered_page_size_is_accepted(self):
        for size in PAGE_SIZES:
            self.assertEqual(parse_page_size(size), size)
            self.assertEqual(self.ledger(f"?page_size={size}")["page_size"], size)

    def test_the_rows_are_ordered_by_the_month(self):
        page = self.ledger()
        due_dates = [row["due_date"] for row in page["results"]]
        self.assertEqual(due_dates, sorted(due_dates, reverse=True))

    def test_the_records_of_another_owner_never_show_up(self):
        page = self.ledger()
        ids = {row["id"] for row in page["results"]}
        self.assertNotIn(self.foreign.id, ids)
        self.assertEqual(page["count"], 5)


class LedgerFilterTests(LedgerQueryTestBase):
    def test_the_status_filter_narrows_the_ledger_down(self):
        page = self.ledger("?status=paid")
        self.assertEqual(page["count"], 2)
        self.assertEqual(page["selected_filters"]["status"], ["paid"])
        self.assertTrue(all(row["status"] == "paid" for row in page["results"]))

    def test_the_status_filter_takes_more_than_one_value(self):
        page = self.ledger("?status=paid,overdue")
        self.assertEqual(page["count"], 3)
        self.assertEqual(
            sorted(row["status"] for row in page["results"]),
            ["overdue", "paid", "paid"],
        )

    def test_the_status_filter_accepts_repeated_parameters(self):
        page = self.ledger("?status=paid&status=cancelled")
        self.assertEqual(page["count"], 3)

    def test_the_building_filter_narrows_the_ledger_down(self):
        page = self.ledger(f"?building={self.maple.id}")
        self.assertEqual(page["count"], 4)
        self.assertEqual(
            sorted(self.units_of(page)), ["B-101", "B-101", "B-102", "B-102"]
        )

    def test_the_unit_filter_narrows_the_ledger_down(self):
        page = self.ledger(f"?unit={self.b101.id}")
        self.assertEqual(page["count"], 2)
        self.assertEqual(self.units_of(page), ["B-101", "B-101"])

    def test_the_filters_combine(self):
        page = self.ledger(f"?building={self.maple.id}&unit={self.b101.id}&status=paid")
        self.assertEqual(page["count"], 1)
        self.assertEqual(page["results"][0]["id"], self.paid.id)

    def test_a_filter_of_another_owner_matches_nothing(self):
        page = self.ledger(f"?unit={self.foreign_unit.id}")
        self.assertEqual(page["count"], 0)
        self.assertEqual(page["results"], [])

    def test_an_unknown_status_is_ignored(self):
        page = self.ledger("?status=not-a-status")
        self.assertEqual(page["count"], 5)
        self.assertEqual(page["selected_filters"]["status"], [])

    def test_the_search_narrows_the_ledger_down(self):
        page = self.ledger("?search=Meera")
        self.assertEqual(page["count"], 1)
        self.assertEqual(page["results"][0]["id"], self.pending.id)

    def test_the_search_covers_the_building(self):
        page = self.ledger("?search=Lakeview")
        self.assertEqual(page["count"], 1)
        self.assertEqual(page["results"][0]["id"], self.settled_elsewhere.id)

    def test_the_page_of_a_filtered_ledger_still_carries_the_totals(self):
        page = self.ledger("?status=paid&page_size=10")
        self.assertEqual(page["count"], 2)
        self.assertEqual(page["total_pages"], 1)
        self.assertEqual(len(page["results"]), 2)
        self.assertEqual(page["summary"]["paid"], 2)


class LedgerFacetTests(LedgerQueryTestBase):
    def test_the_building_facet_is_grouped_by_the_server(self):
        page = self.ledger()
        options = {
            option["value"]: option for option in page["filters"]["building"]["options"]
        }
        self.assertEqual(options[str(self.maple.id)]["label"], "Maple Heights")
        self.assertEqual(options[str(self.maple.id)]["count"], 4)
        self.assertEqual(options[str(self.lakeview.id)]["count"], 1)

    def test_the_unit_facet_carries_the_building_of_the_unit(self):
        page = self.ledger()
        options = {
            option["value"]: option for option in page["filters"]["unit"]["options"]
        }
        self.assertEqual(options[str(self.b101.id)]["label"], "B-101")
        self.assertEqual(options[str(self.b101.id)]["meta"], "Maple Heights")
        self.assertEqual(options[str(self.b101.id)]["count"], 2)

    def test_the_status_facet_carries_the_badge_label(self):
        page = self.ledger()
        options = {
            option["value"]: option for option in page["filters"]["status"]["options"]
        }
        self.assertEqual(options["paid"]["label"], "Paid")
        self.assertEqual(options["paid"]["count"], 2)
        self.assertEqual(options["cancelled"]["count"], 1)

    def test_the_picked_values_are_marked(self):
        page = self.ledger(f"?status=paid&building={self.maple.id}")
        statuses = page["filters"]["status"]["options"]
        picked = [option for option in statuses if option["selected"]]
        self.assertEqual([option["value"] for option in picked], ["paid"])
        buildings = page["filters"]["building"]["options"]
        self.assertTrue(
            all(
                option["selected"] == (option["value"] == str(self.maple.id))
                for option in buildings
            )
        )

    def test_a_facet_counts_with_the_other_filters_applied(self):
        page = self.ledger(f"?building={self.maple.id}")
        units = {
            option["value"]: option for option in page["filters"]["unit"]["options"]
        }
        # The unit of the other building cannot match any more.
        self.assertNotIn(str(self.a102.id), units)
        self.assertEqual(units[str(self.b101.id)]["count"], 2)

    def test_the_facets_of_a_searched_ledger_follow_the_search(self):
        page = self.ledger("?search=Meera")
        units = {
            option["value"]: option for option in page["filters"]["unit"]["options"]
        }
        self.assertNotIn(str(self.b102.id), units)


class LedgerPaginationTests(TestCase):
    """A ledger that is longer than one page."""

    def setUp(self):
        # The API throttles per user and the tests share the user ids of
        # the rolled back rows — a fresh cache keeps every test its own quota.
        cache.clear()
        self.client = APIClient()
        self.owner = make_owner("ledger_pagination_owner")
        building = make_building(self.owner, "Long House")
        self.unit = make_unit(self.owner, building, "L-101")
        for month in range(1, 13):
            make_record(
                self.unit,
                f"Long Renter {month}",
                date(2026, month, 5),
                RentRecord.Status.PAID,
            )
        self.client.force_authenticate(self.owner)

    def ledger(self, query: str = "") -> dict:
        response = self.client.get(f"/api/rent-records/ledger/{query}")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_the_ledger_is_walked_page_by_page(self):
        first = self.ledger("?page_size=10&page=1")
        second = self.ledger("?page_size=10&page=2")
        self.assertEqual(first["count"], 12)
        self.assertEqual(first["total_pages"], 2)
        self.assertEqual(first["next_page"], 2)
        self.assertIsNone(first["previous_page"])
        self.assertEqual(len(first["results"]), 10)
        self.assertEqual(second["previous_page"], 1)
        self.assertIsNone(second["next_page"])
        self.assertEqual(len(second["results"]), 2)
        ids = [row["id"] for row in first["results"] + second["results"]]
        self.assertEqual(len(set(ids)), 12)

    def test_the_rows_of_the_last_page_are_stated(self):
        page = self.ledger("?page_size=10&page=2")
        self.assertEqual(page["first_row"], 11)
        self.assertEqual(page["last_row"], 12)

    def test_a_page_beyond_the_last_one_lands_on_the_last_one(self):
        page = self.ledger("?page_size=10&page=9")
        self.assertEqual(page["page"], 2)
        self.assertEqual(page["total_pages"], 2)


class LedgerSummaryTests(LedgerQueryTestBase):
    def test_the_summary_counts_the_whole_ledger(self):
        page = self.ledger("?page_size=1")
        self.assertEqual(page["summary"]["paid"], 2)
        self.assertEqual(page["summary"]["pending"], 1)
        self.assertEqual(page["summary"]["overdue"], 1)
        self.assertEqual(page["summary"]["cancelled"], 1)

    def test_the_summary_follows_the_filters(self):
        page = self.ledger("?status=paid")
        self.assertEqual(page["summary"]["paid"], 2)
        self.assertEqual(page["summary"]["pending"], 0)
        self.assertEqual(page["summary"]["overdue"], 0)

    def test_a_partly_paid_month_is_counted(self):
        self.pending.amount_paid = Decimal("10000")
        self.pending.save(update_fields=["amount_paid"])
        page = self.ledger()
        self.assertEqual(page["summary"]["partially_paid"], 1)


class LedgerQueryHelperTests(TestCase):
    def test_a_multi_value_parameter_is_read_every_time(self):
        self.assertEqual(parse_values("1,2"), ["1", "2"])
        self.assertEqual(parse_values(["1", "2"]), ["1", "2"])
        self.assertEqual(parse_values("1, 2 ,1"), ["1", "2"])
        self.assertEqual(parse_values(None), [])
        self.assertEqual(parse_values(""), [])

    def test_the_page_size_falls_back_to_the_default(self):
        self.assertEqual(parse_page_size("25"), 25)
        self.assertEqual(parse_page_size("0"), DEFAULT_PAGE_SIZE)
        self.assertEqual(parse_page_size("abc"), DEFAULT_PAGE_SIZE)
        self.assertEqual(parse_page_size(None), DEFAULT_PAGE_SIZE)

    def test_the_ledger_page_can_be_built_without_a_request(self):
        owner = make_owner("ledger_helper_owner")
        building = make_building(owner, "Only House")
        unit = make_unit(owner, building, "O-101")
        make_record(unit, "Helper Renter", date(2026, 10, 5), RentRecord.Status.PAID)
        page = build_ledger_page(owner, {})
        self.assertEqual(page["count"], 1)
        self.assertEqual(len(page["results"]), 1)
        self.assertEqual(page["summary"]["paid"], 1)
