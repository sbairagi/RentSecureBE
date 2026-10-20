"""Tests for the history of one rent record.

The history is the server's story of a month: every change the record went
through, kept by ``django-simple-history``, and every part payment that was
received against it.  These tests lock that contract — what the client may
render and what it may not.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from rest_framework.test import APIClient

from django.core.cache import cache
from django.test import TestCase

from core.models import User
from properties.models import Building, Renter, RentRecord, RentRecordPart, Unit
from properties.services.rent_history import HISTORY_LIMIT


def make_owner(username: str) -> User:
    return User.objects.create_user(
        username=username,
        password="testpass123",
        full_name=username.replace("_", " ").title(),
        phone=f"+9110000{abs(hash(username)) % 10000:04d}",
    )


def make_unit(owner: User, name: str) -> Unit:
    building = Building.objects.create(
        owner=owner,
        name=name,
        address_line="1 Street",
        city="Pune",
        state="MH",
        country="IN",
        postal_code="411001",
    )
    return Unit.objects.create(
        owner=owner,
        building=building,
        unit="A-101",
        unit_type="flat",
        address_line="1 Street",
        city="Pune",
        state="MH",
        country="IN",
        postal_code="411001",
    )


def make_record(
    unit: Unit, name: str, status: str = RentRecord.Status.PENDING
) -> RentRecord:
    renter = Renter.objects.create(
        unit=unit,
        name=name,
        phone="+91234567890",
        email=f"{name.lower().replace(' ', '.')}@example.com",
        rent_amount=Decimal("30000"),
        start_date=date(2025, 1, 1),
    )
    return RentRecord.objects.create(
        renter=renter,
        unit=unit,
        due_date=date(2026, 10, 5),
        amount=Decimal("30000"),
        payment_method="upi",
        status=status,
        amount_paid=Decimal("0"),
    )


class RentHistoryTestBase(TestCase):
    def setUp(self):
        # The API throttles per user and the tests share the user ids of
        # the rolled back rows — a fresh cache keeps every test its own quota.
        cache.clear()
        self.client = APIClient()
        self.owner = make_owner("history_owner")
        self.other = make_owner("history_other")

        self.unit = make_unit(self.owner, "Maple Heights")
        self.foreign_unit = make_unit(self.other, "Foreign House")

        self.record = make_record(self.unit, "Meera Iyer")
        self.foreign = make_record(self.foreign_unit, "Foreign Renter")

        self.client.force_authenticate(self.owner)

    def history(self, record: RentRecord | None = None):
        record = record or self.record
        response = self.client.get(f"/api/rent-records/{record.id}/history/")
        return response


class RentHistoryEntryTests(RentHistoryTestBase):
    def test_the_history_of_a_fresh_record_is_its_creation(self):
        response = self.history()
        self.assertEqual(response.status_code, 200)
        entries = response.json()
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["action"], "+")
        self.assertEqual(entry["data"]["status"], RentRecord.Status.PENDING)
        self.assertEqual(entry["data"]["amount"], "30000.00")
        self.assertEqual(entry["data"]["balance"], "30000.00")
        self.assertEqual(entry["data"]["due_date"], "2026-10-05")

    def test_a_change_is_kept_with_the_snapshot_it_left_behind(self):
        self.record.amount = Decimal("31000")
        self.record.save()
        entries = self.history().json()
        self.assertEqual([entry["action"] for entry in entries], ["~", "+"])
        self.assertEqual(entries[0]["data"]["amount"], "31000.00")
        self.assertEqual(entries[1]["data"]["amount"], "30000.00")

    def test_the_entries_come_newest_first(self):
        self.record.amount = Decimal("31000")
        self.record.save()
        self.record.status = RentRecord.Status.PAID
        self.record.amount_paid = Decimal("31000")
        self.record.save()
        stamps = [entry["timestamp"] for entry in self.history().json()]
        self.assertEqual(stamps, sorted(stamps, reverse=True))

    def test_a_cancelled_record_keeps_the_reason_it_was_cancelled_for(self):
        self.record.status = RentRecord.Status.CANCELLED
        self.record.cancel_reason = "The tenant vacated the flat."
        self.record.save()
        latest = self.history().json()[0]
        self.assertEqual(
            latest["data"]["cancel_reason"], "The tenant vacated the flat."
        )

    def test_a_part_payment_is_part_of_the_trail(self):
        RentRecordPart.objects.create(
            rent_record=self.record,
            amount=Decimal("8000"),
            paid_on=date(2026, 10, 6),
            payment_method=RentRecord.PaymentMethod.UPI,
            transaction_id="TXN-1",
            note="First instalment",
            created_by=self.owner,
        )
        entries = self.history().json()
        part = entries[0]
        self.assertEqual(part["action"], "part")
        self.assertEqual(part["data"]["amount"], "8000.00")
        self.assertEqual(part["data"]["paid_on"], "2026-10-06")
        self.assertEqual(part["data"]["payment_method"], "upi")
        self.assertEqual(part["data"]["transaction_id"], "TXN-1")
        self.assertEqual(part["data"]["note"], "First instalment")
        self.assertEqual(part["changed_by"], self.owner.email or self.owner.username)

    def test_the_changes_and_the_parts_live_in_one_list(self):
        RentRecordPart.objects.create(
            rent_record=self.record,
            amount=Decimal("8000"),
            paid_on=date(2026, 10, 6),
            payment_method=RentRecord.PaymentMethod.CASH,
            created_by=self.owner,
        )
        self.record.amount_paid = Decimal("8000")
        self.record.save()
        actions = [entry["action"] for entry in self.history().json()]
        self.assertIn("part", actions)
        self.assertIn("~", actions)
        self.assertIn("+", actions)

    def test_the_trail_never_grows_past_the_cap(self):
        for index in range(HISTORY_LIMIT + 10):
            RentRecordPart.objects.create(
                rent_record=self.record,
                amount=Decimal("100"),
                paid_on=date(2026, 10, 6),
                payment_method=RentRecord.PaymentMethod.CASH,
                note=f"Part {index}",
                created_by=self.owner,
            )
        entries = self.history().json()
        self.assertEqual(len(entries), HISTORY_LIMIT)

    def test_every_entry_carries_the_who_and_the_when(self):
        entries = self.history().json()
        for entry in entries:
            self.assertIn("id", entry)
            self.assertIn("action", entry)
            self.assertIn("changed_by", entry)
            self.assertIn("timestamp", entry)
            self.assertIn("data", entry)


class RentHistoryAccessTests(RentHistoryTestBase):
    def test_the_record_of_another_owner_is_not_readable(self):
        response = self.history(self.foreign)
        self.assertIn(response.status_code, (403, 404))

    def test_an_anonymous_visitor_is_turned_away(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(f"/api/rent-records/{self.record.id}/history/")
        self.assertIn(response.status_code, (401, 403))

    def test_a_record_that_does_not_exist_is_not_invented(self):
        response = self.client.get("/api/rent-records/999999/history/")
        self.assertEqual(response.status_code, 404)


class RentHistoryActionTests(RentHistoryTestBase):
    """Every action a user takes has to leave a trace in the trail."""

    def actions(self) -> list[dict]:
        return self.history().json()

    def test_a_created_record_carries_the_creation_of_the_user(self):
        # A unit without a rent history may start at any date.
        unit = make_unit(self.owner, "Cedar Court")
        renter = Renter.objects.create(
            unit=unit,
            name="Aarav Sharma",
            phone="+91234567891",
            email="aarav@example.com",
            rent_amount=Decimal("25000"),
            start_date=date(2025, 1, 1),
        )
        response = self.client.post(
            "/api/rent-records/",
            {
                "unit": unit.id,
                "renter": renter.id,
                "due_date": "2026-11-05",
                "amount": "25000",
                "payment_method": "upi",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        record = RentRecord.objects.get(pk=response.json()["id"])
        entries = self.history(record).json()
        kinds = [entry["action"] for entry in entries]
        self.assertIn("created", kinds)
        created = [entry for entry in entries if entry["action"] == "created"][0]
        self.assertIn("25,000", created["data"]["detail"])
        self.assertIn("November 2026", created["data"]["detail"])
        self.assertEqual(created["changed_by"], self.owner.email or self.owner.username)

    def test_an_edit_leaves_an_action_of_the_user(self):
        response = self.client.patch(
            f"/api/rent-records/{self.record.id}/",
            {"late_fee": "1500"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        entries = self.history().json()
        edited = [entry for entry in entries if entry["action"] == "edited"]
        self.assertEqual(len(edited), 1)
        self.assertIn("late fee", edited[0]["data"]["detail"])
        self.assertEqual(
            edited[0]["changed_by"], self.owner.email or self.owner.username
        )

    def test_a_cancellation_leaves_an_action_with_the_reason(self):
        response = self.client.post(
            f"/api/rent-records/{self.record.id}/cancel/",
            {"reason": "The tenant vacated the flat."},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        entries = self.history().json()
        cancelled = [entry for entry in entries if entry["action"] == "cancelled"]
        self.assertEqual(len(cancelled), 1)
        self.assertEqual(cancelled[0]["data"]["detail"], "The tenant vacated the flat.")
        self.assertEqual(cancelled[0]["data"]["status"], RentRecord.Status.CANCELLED)

    def test_a_receipt_that_could_not_be_delivered_is_still_in_the_trail(self):
        with (
            patch(
                "properties.services.rent_collection_service.send_whatsapp_message",
                return_value=False,
            ),
            patch("django.core.mail.EmailMessage.send", return_value=0),
            patch(
                "properties.services.rent_collection_service.generate_rent_receipt_pdf",
                return_value=b"%PDF-1.4 test",
            ),
        ):
            self.record.status = RentRecord.Status.PAID
            self.record.amount_paid = Decimal("30000")
            self.record.save()
            response = self.client.post(
                f"/api/rent-records/{self.record.id}/send-receipt/", {}, format="json"
            )
        self.assertEqual(response.status_code, 200)
        entries = self.history().json()
        receipts = [entry for entry in entries if entry["action"] == "receipt_sent"]
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]["data"]["outcome"], "failed")
        self.assertIn("could not be delivered", receipts[0]["data"]["detail"])

    def test_a_reminder_leaves_an_action_of_the_user(self):
        with patch(
            "properties.services.rent_collection_service.send_whatsapp_message",
            return_value=True,
        ):
            response = self.client.post(
                f"/api/rent-records/{self.record.id}/send-reminder/", {}, format="json"
            )
        self.assertEqual(response.status_code, 200)
        entries = self.history().json()
        reminders = [entry for entry in entries if entry["action"] == "reminder_sent"]
        self.assertEqual(len(reminders), 1)
        self.assertEqual(reminders[0]["data"]["outcome"], "sent")
        self.assertIn("30,000", reminders[0]["data"]["summary"])

    def test_an_action_is_never_listed_twice(self):
        response = self.client.patch(
            f"/api/rent-records/{self.record.id}/",
            {"late_fee": "1500"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        entries = self.history().json()
        # The edit writes one action and one audit entry — the history shows
        # the action once, not the two of them side by side.  The creation of
        # the record (made outside the API in the test) stays a ``+``.
        self.assertEqual([entry["action"] for entry in entries], ["edited", "+"])
        self.assertEqual(entries[0]["data"]["late_fee"], "1500.00")

    def test_the_actions_of_a_record_stay_inside_its_own_trail(self):
        self.client.patch(
            f"/api/rent-records/{self.record.id}/",
            {"late_fee": "1500"},
            format="json",
        )
        self.assertEqual(self.record.actions.count(), 1)
        self.assertEqual(self.foreign.actions.count(), 0)
