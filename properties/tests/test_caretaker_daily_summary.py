"""Tests for send_caretaker_daily_summary management command."""

from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from properties.management.commands.send_caretaker_daily_summary import Command
from properties.models import (
    Building,
    Caretaker,
    PropertyTaxRecord,
    Renter,
    RentRecord,
    Unit,
)

User = get_user_model()


class SendCaretakerDailySummaryTests(TestCase):
    def setUp(self):
        self.command = Command()
        self.owner = User.objects.create_user(
            username="caretaker_owner",
            password="p",
            full_name="CaretakerOwner",
            phone="+1",
            email="caretaker_owner@test.com",
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="CaretakerB",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="C1",
            unit_type="flat",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        self.caretaker_user = User.objects.create_user(
            username="caretaker_user",
            password="p",
            full_name="CaretakerUser",
            phone="+1",
            email="caretaker@test.com",
            whatsapp_number="+919876543210",
        )
        self.caretaker = Caretaker.objects.create(
            unit=self.unit,
            user=self.caretaker_user,
            name="TestCaretaker",
            phone="+911234567890",
            joining_date=timezone.now().date(),
        )

    @patch(
        "properties.management.commands.send_caretaker_daily_summary.send_whatsapp_message"
    )
    @patch(
        "properties.management.commands.send_caretaker_daily_summary.send_whatsapp_audio"
    )
    @patch(
        "properties.management.commands.send_caretaker_daily_summary.generate_voice_note"
    )
    @patch(
        "properties.management.commands.send_caretaker_daily_summary.translate_msg",
        side_effect=lambda text, lang: text,
    )
    def test_sends_daily_summary_to_caretaker(
        self, mock_translate, mock_voice, mock_audio, mock_whatsapp
    ):
        today = timezone.now().date()
        renter = Renter.objects.create(
            unit=self.unit,
            name="TestRenter",
            phone="+911234567891",
            email="renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=today,
        )
        RentRecord.objects.create(
            unit=self.unit,
            renter=renter,
            amount=Decimal("10000"),
            due_date=today,
            status=RentRecord.Status.PENDING,
            payout_status="PENDING",
        )
        PropertyTaxRecord.objects.create(
            property=self.building,
            amount=Decimal("5000"),
            due_date=today,
            paid=False,
        )

        self.command.handle(user_id=self.caretaker_user.id)
        mock_whatsapp.assert_called_once()
        mock_voice.assert_called_once()
        mock_audio.assert_called_once()

    @patch(
        "properties.management.commands.send_caretaker_daily_summary.send_whatsapp_message"
    )
    def test_skips_caretaker_without_whatsapp(self, mock_whatsapp):
        self.caretaker_user.whatsapp_number = ""
        self.caretaker_user.save(update_fields=["whatsapp_number"])
        self.command.handle(user_id=self.caretaker_user.id)
        mock_whatsapp.assert_not_called()

    @patch(
        "properties.management.commands.send_caretaker_daily_summary.send_whatsapp_message"
    )
    @patch(
        "properties.management.commands.send_caretaker_daily_summary.send_whatsapp_audio"
    )
    @patch(
        "properties.management.commands.send_caretaker_daily_summary.generate_voice_note"
    )
    def test_sends_summary_without_records(self, mock_voice, mock_audio, mock_whatsapp):
        self.command.handle(user_id=self.caretaker_user.id)
        mock_whatsapp.assert_called_once()
        mock_voice.assert_called_once()
        mock_audio.assert_called_once()

    @patch(
        "properties.management.commands.send_caretaker_daily_summary.send_whatsapp_message"
    )
    def test_noop_when_no_caretakers(self, mock_whatsapp):
        Caretaker.objects.filter(user=self.caretaker_user).delete()
        self.command.handle()
        mock_whatsapp.assert_not_called()
