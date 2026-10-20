"""Tests for the Rent collection tab workflows.

Covers the rules from the approved concept:

* rent records are never deleted;
* a record is cancelled with a mandatory reason and stays visible;
* a part payment is only possible while the month is pending or overdue,
  the unit allows parts, the amount is positive, the amount does not
  exceed the balance and the paid-on date is not before the due date;
* the last part settles the month;
* settled and cancelled records are locked against edits.
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from rest_framework.test import APIClient

from django.test import TestCase

from core.models import User
from properties.models import Building, Renter, RentRecord, RentRecordPart, Unit


class RentCollectionTestBase(TestCase):
    """Shared fixtures: one owner with a unit, a renter and a rent record."""

    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username="rent_collection_owner",
            password="testpass123",
            full_name="Rent Collection Owner",
            phone="+911000000001",
        )
        self.other_owner = User.objects.create_user(
            username="rent_collection_other",
            password="testpass123",
            full_name="Other Owner",
            phone="+911000000002",
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="RCB",
            address_line="1 Street",
            city="Pune",
            state="MH",
            country="IN",
            postal_code="411001",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="RC-101",
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

    def payload(self, **overrides):
        body = {
            "amount": "10000",
            "paid_on": (self.due_date + timedelta(days=1)).isoformat(),
            "payment_method": "upi",
            "transaction_id": "UPI-1",
            "note": "First instalment",
        }
        body.update(overrides)
        return body

    @staticmethod
    def rows(response):
        """Return the ledger rows of a listing response."""
        body = response.json()
        if isinstance(body, dict):
            return body["results"]
        return body


class RentRecordDeletionTests(RentCollectionTestBase):
    def test_delete_is_blocked(self):
        response = self.client.delete(f"/api/rent-records/{self.rent.id}/")
        self.assertEqual(response.status_code, 405)
        self.assertTrue(RentRecord.objects.filter(pk=self.rent.pk).exists())

    def test_unit_with_rent_history_cannot_be_deleted(self):
        response = self.client.delete(f"/api/units/{self.unit.id}/")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Unit.objects.filter(pk=self.unit.pk).exists())


class RentRecordCreationTests(RentCollectionTestBase):
    """The clients send the unit and the renter as ids.

    Both are rendered as nested objects, so the ids have to be resolved on the
    way in — otherwise every create is rejected because the ownership guard
    never sees a unit.
    """

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
    def test_a_record_is_created_from_the_unit_and_renter_ids(self, _link, _whatsapp):
        response = self.client.post(
            "/api/rent-records/", self.create_body(), format="json"
        )
        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        self.assertEqual(body["unit"]["id"], self.unit.id)
        self.assertEqual(body["renter"]["id"], self.renter.id)
        self.assertEqual(body["status"], RentRecord.Status.PENDING)
        self.assertEqual(body["balance"], "25000.00")

    @patch("notification.utils.send_whatsapp_message")
    @patch("rentsecure_be.services.razorpay_service.create_payment_link")
    def test_a_unit_of_another_owner_is_refused(self, _link, _whatsapp):
        other_unit = Unit.objects.create(
            owner=self.other_owner,
            unit="OTHER-1",
            unit_type="flat",
            address_line="2 Street",
            city="Pune",
            state="MH",
            country="IN",
            postal_code="411001",
        )
        response = self.client.post(
            "/api/rent-records/",
            self.create_body(unit=other_unit.id),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(RentRecord.objects.filter(unit=other_unit).count(), 0)

    @patch("notification.utils.send_whatsapp_message")
    @patch("rentsecure_be.services.razorpay_service.create_payment_link")
    def test_a_renter_of_another_unit_is_refused(self, _link, _whatsapp):
        other_unit = Unit.objects.create(
            owner=self.owner,
            unit="RC-102",
            unit_type="flat",
            address_line="1 Street",
            city="Pune",
            state="MH",
            country="IN",
            postal_code="411001",
        )
        other_renter = Renter.objects.create(
            unit=other_unit,
            name="Someone Else",
            phone="+912345678999",
            email="someone@example.com",
            rent_amount=20000,
            start_date=date(2025, 1, 1),
        )
        response = self.client.post(
            "/api/rent-records/",
            self.create_body(renter=other_renter.id),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(RentRecord.objects.filter(renter=other_renter).count(), 0)

    @patch("notification.utils.send_whatsapp_message")
    @patch("rentsecure_be.services.razorpay_service.create_payment_link")
    def test_the_same_period_cannot_be_recorded_twice(self, _link, _whatsapp):
        response = self.client.post(
            "/api/rent-records/", self.create_body(), format="json"
        )
        self.assertEqual(response.status_code, 201, response.content)
        again = self.client.post(
            "/api/rent-records/", self.create_body(), format="json"
        )
        self.assertEqual(again.status_code, 400)


class CancelRentRecordTests(RentCollectionTestBase):
    def test_reason_is_mandatory(self):
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/cancel/",
            {"reason": "   "},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.rent.refresh_from_db()
        self.assertEqual(self.rent.status, RentRecord.Status.PENDING)

    def test_cancel_keeps_the_record_visible(self):
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/cancel/",
            {"reason": "Renter vacated before the due date"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.rent.refresh_from_db()
        self.assertEqual(self.rent.status, RentRecord.Status.CANCELLED)
        self.assertEqual(self.rent.cancel_reason, "Renter vacated before the due date")
        self.assertIsNotNone(self.rent.cancelled_at)
        self.assertEqual(self.rent.cancelled_by, self.owner)

        listing = self.client.get("/api/rent-records/")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(self.rows(listing)), 1)

    def test_cannot_cancel_after_money_was_received(self):
        self.rent.amount_paid = Decimal("5000")
        self.rent.save(update_fields=["amount_paid"])
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/cancel/",
            {"reason": "Trying to cancel"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.rent.refresh_from_db()
        self.assertEqual(self.rent.status, RentRecord.Status.PENDING)

    def test_cannot_cancel_a_settled_record(self):
        self.rent.status = RentRecord.Status.PAID
        self.rent.amount_paid = Decimal("30000")
        self.rent.save(update_fields=["status", "amount_paid"])
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/cancel/",
            {"reason": "Trying to cancel"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_cannot_cancel_twice(self):
        self.client.post(
            f"/api/rent-records/{self.rent.id}/cancel/",
            {"reason": "First cancellation"},
            format="json",
        )
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/cancel/",
            {"reason": "Second cancellation"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class PartPaymentTests(RentCollectionTestBase):
    def test_part_payment_is_recorded(self):
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/payments/",
            self.payload(),
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.rent.refresh_from_db()
        self.assertEqual(self.rent.amount_paid, Decimal("10000"))
        self.assertEqual(self.rent.balance, Decimal("20000"))
        self.assertEqual(self.rent.status, RentRecord.Status.PENDING)
        part = RentRecordPart.objects.get(rent_record=self.rent)
        self.assertEqual(part.amount, Decimal("10000"))
        self.assertEqual(
            part.receipt_no, f"rent_receipt_{self.rent.id}_202610_part1.pdf"
        )
        self.assertEqual(part.created_by, self.owner)

    def test_amount_must_be_positive(self):
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/payments/",
            self.payload(amount="0"),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(RentRecordPart.objects.count(), 0)

    def test_amount_cannot_exceed_the_balance(self):
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/payments/",
            self.payload(amount="40000"),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(RentRecordPart.objects.count(), 0)

    def test_paid_on_cannot_be_before_the_due_date(self):
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/payments/",
            self.payload(paid_on=(self.due_date - timedelta(days=1)).isoformat()),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(RentRecordPart.objects.count(), 0)

    def test_part_payment_needs_the_unit_flag(self):
        self.unit.allow_partial_payments = False
        self.unit.save(update_fields=["allow_partial_payments"])
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/payments/",
            self.payload(),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(RentRecordPart.objects.count(), 0)

    def test_last_part_settles_the_month(self):
        self.client.post(
            f"/api/rent-records/{self.rent.id}/payments/",
            self.payload(amount="20000"),
            format="json",
        )
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/payments/",
            self.payload(
                amount="10000", paid_on=(self.due_date + timedelta(days=2)).isoformat()
            ),
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.rent.refresh_from_db()
        self.assertEqual(self.rent.status, RentRecord.Status.PAID)
        self.assertEqual(self.rent.amount_paid, Decimal("30000"))
        self.assertEqual(self.rent.balance, Decimal("0"))
        self.assertEqual(self.rent.paid_on, self.due_date + timedelta(days=2))

    def test_overdue_record_accepts_a_part(self):
        self.rent.status = RentRecord.Status.OVERDUE
        self.rent.late_fee = Decimal("1500")
        self.rent.save(update_fields=["status", "late_fee"])
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/payments/",
            self.payload(amount="5000"),
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.rent.refresh_from_db()
        self.assertEqual(self.rent.status, RentRecord.Status.OVERDUE)
        self.assertEqual(self.rent.balance, Decimal("26500"))

    def test_settled_record_rejects_a_part(self):
        self.rent.status = RentRecord.Status.PAID
        self.rent.amount_paid = Decimal("30000")
        self.rent.save(update_fields=["status", "amount_paid"])
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/payments/",
            self.payload(),
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_cancelled_record_rejects_a_part(self):
        self.rent.status = RentRecord.Status.CANCELLED
        self.rent.save(update_fields=["status"])
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/payments/",
            self.payload(),
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_other_owner_cannot_record_a_part(self):
        self.client.force_authenticate(self.other_owner)
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/payments/",
            self.payload(),
            format="json",
        )
        self.assertIn(response.status_code, (403, 404))
        self.assertEqual(RentRecordPart.objects.count(), 0)


class RentRecordUpdateProtectionTests(RentCollectionTestBase):
    def test_settled_record_cannot_be_edited(self):
        self.rent.status = RentRecord.Status.PAID
        self.rent.amount_paid = Decimal("30000")
        self.rent.save(update_fields=["status", "amount_paid"])
        response = self.client.patch(
            f"/api/rent-records/{self.rent.id}/",
            {"notes": "Trying to edit"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.rent.refresh_from_db()
        self.assertNotEqual(self.rent.notes, "Trying to edit")

    def test_cancelled_record_cannot_be_edited(self):
        self.rent.status = RentRecord.Status.CANCELLED
        self.rent.save(update_fields=["status"])
        response = self.client.patch(
            f"/api/rent-records/{self.rent.id}/",
            {"notes": "Trying to edit"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_late_fee_and_discount_freeze_after_a_part(self):
        RentRecordPart.objects.create(
            rent_record=self.rent,
            amount=Decimal("10000"),
            paid_on=self.due_date,
            payment_method="cash",
        )
        self.rent.amount_paid = Decimal("10000")
        self.rent.save(update_fields=["amount_paid"])

        blocked = self.client.patch(
            f"/api/rent-records/{self.rent.id}/",
            {"late_fee": "500"},
            format="json",
        )
        self.assertEqual(blocked.status_code, 400)

        allowed = self.client.patch(
            f"/api/rent-records/{self.rent.id}/",
            {"notes": "Followed up", "adjustment_reason": "Waived the rest"},
            format="json",
        )
        self.assertEqual(allowed.status_code, 200)
        self.rent.refresh_from_db()
        self.assertEqual(self.rent.notes, "Followed up")
        self.assertEqual(self.rent.adjustment_reason, "Waived the rest")

    def test_unpaid_record_allows_the_four_fields(self):
        response = self.client.patch(
            f"/api/rent-records/{self.rent.id}/",
            {
                "late_fee": "500",
                "discount": "200",
                "notes": "Called the renter",
                "adjustment_reason": "Late fee added",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.rent.refresh_from_db()
        self.assertEqual(self.rent.total_due, Decimal("30300"))


class ReminderAndReceiptTests(RentCollectionTestBase):
    @patch("properties.services.rent_collection_service.send_whatsapp_message")
    def test_reminder_asks_for_the_balance(self, whatsapp):
        whatsapp.return_value = True
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/send-reminder/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["sent"])
        self.assertEqual(response.json()["balance"], "30000.00")
        whatsapp.assert_called_once()
        self.assertIn("30,000", whatsapp.call_args[0][1])
        self.rent.refresh_from_db()
        self.assertIsNotNone(self.rent.last_reminded_at)

    @patch("properties.services.rent_collection_service.send_whatsapp_message")
    def test_reminder_for_a_partially_paid_record_asks_for_the_rest(self, whatsapp):
        whatsapp.return_value = True
        self.rent.amount_paid = Decimal("12000")
        self.rent.save(update_fields=["amount_paid"])
        self.client.post(
            f"/api/rent-records/{self.rent.id}/send-reminder/",
            {},
            format="json",
        )
        self.assertIn("18,000", whatsapp.call_args[0][1])

    def test_receipt_needs_a_payment_first(self):
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/send-receipt/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_receipt_is_refused_while_the_month_is_open(self):
        """A partially paid month cannot be receipted manually.

        Every part payment carries its own receipt, and the settlement
        receipt only exists once the balance reaches zero.
        """
        self.rent.amount_paid = Decimal("12000")
        self.rent.save(update_fields=["amount_paid"])
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/send-receipt/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("not settled", response.json()["error"])

    @patch("properties.services.receipt_service.generate_rent_receipt_pdf")
    @patch("properties.services.receipt_service.EmailMessage.send")
    def test_a_part_payment_sends_its_own_receipt(self, send, pdf):
        pdf.return_value = b"%PDF-1.4 test"
        send.return_value = 1
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/payments/",
            self.payload(),
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        send.assert_called_once()
        part = RentRecordPart.objects.get(rent_record=self.rent)
        self.assertEqual(
            part.receipt_no, f"rent_receipt_{self.rent.id}_202610_part1.pdf"
        )
        self.rent.refresh_from_db()
        self.assertEqual(self.rent.amount_paid, Decimal("10000"))
        self.assertEqual(self.rent.status, RentRecord.Status.PENDING)

    @patch("properties.services.receipt_service.generate_rent_receipt_pdf")
    @patch("properties.services.receipt_service.EmailMessage.send")
    def test_a_failed_receipt_does_not_undo_the_part(self, send, pdf):
        pdf.return_value = b"%PDF-1.4 test"
        send.side_effect = RuntimeError("smtp is down")
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/payments/",
            self.payload(),
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.rent.refresh_from_db()
        self.assertEqual(self.rent.amount_paid, Decimal("10000"))

    @patch("properties.services.rent_collection_service.generate_rent_receipt_pdf")
    @patch("properties.services.rent_collection_service.send_whatsapp_message")
    def test_receipt_stamps_the_sent_time(self, whatsapp, pdf):
        whatsapp.return_value = True
        pdf.return_value = b"%PDF-1.4 test"
        self.rent.amount_paid = Decimal("30000")
        self.rent.status = RentRecord.Status.PAID
        self.rent.save(update_fields=["amount_paid", "status"])
        response = self.client.post(
            f"/api/rent-records/{self.rent.id}/send-receipt/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.rent.refresh_from_db()
        self.assertIsNotNone(self.rent.receipt_sent_at)


class RentRecordListingTests(RentCollectionTestBase):
    def test_listing_exposes_the_ledger_fields(self):
        response = self.client.get("/api/rent-records/")
        self.assertEqual(response.status_code, 200)
        row = self.rows(response)[0]
        for key in (
            "amount",
            "amount_paid",
            "total_due",
            "balance",
            "parts",
            "status",
            "allow_partial_payments",
            "is_partially_paid",
        ):
            self.assertIn(key, row)
        self.assertEqual(str(row["total_due"]), "30000.00")
        self.assertEqual(str(row["balance"]), "30000.00")
        self.assertTrue(row["allow_partial_payments"])

    def test_listing_includes_the_parts(self):
        RentRecordPart.objects.create(
            rent_record=self.rent,
            amount=Decimal("8000"),
            paid_on=self.due_date,
            payment_method="upi",
        )
        self.rent.amount_paid = Decimal("8000")
        self.rent.save(update_fields=["amount_paid"])
        response = self.client.get("/api/rent-records/")
        row = self.rows(response)[0]
        self.assertEqual(len(row["parts"]), 1)
        self.assertEqual(str(row["parts"][0]["amount"]), "8000.00")
        self.assertEqual(row["parts"][0]["payment_method_label"], "UPI")
        self.assertTrue(row["is_partially_paid"])
