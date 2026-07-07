from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import UserProfile
from notification.services.extra_charge_reminders import send_due_extra_charge_reminders
from properties.models import ExtraCharge, Renter, Unit


class ExtraChargeReminderTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass",
            full_name="Test User",
            whatsapp_number="+911234567890",
        )
        self.profile, _ = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={
                "whatsapp_number": "+911234567890",
                "language_preference": "hi",
            },
        )
        self.profile.whatsapp_number = "+911234567890"
        self.profile.language_preference = "hi"
        self.profile.save()

        self.owner = get_user_model().objects.create_user(
            username="owner",
            password="ownerpass",
            full_name="Owner User",
            whatsapp_number="+919876543210",
        )

        self.unit = Unit.objects.create(
            owner=self.owner,
            unit="101",
            unit_type=Unit.UnitType.FLAT,
            address_line="123 Test Street",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400001",
        )

        self.renter = Renter.objects.create(
            unit=self.unit,
            user=self.user,
            name="Renter Name",
            phone="+919999999999",
            whatsapp_number="+919999999999",
            rent_amount=10000,
            start_date=date.today(),
        )

    @patch("notification.services.whatsapp_service.send_whatsapp_audio")
    @patch("notification.services.whatsapp_service.send_whatsapp_message")
    @patch("notification.services.voice_service.generate_voice_note")
    @patch("ai_assistant.services.i18n_service.translate_msg")
    def test_send_due_extra_charge_reminders_sends_text_and_audio(
        self,
        mock_translate,
        mock_generate_voice_note,
        mock_send_whatsapp_message,
        mock_send_whatsapp_audio,
    ):
        mock_translate.return_value = "translated message"
        mock_generate_voice_note.return_value = "/tmp/fake.mp3"

        ExtraCharge.objects.create(
            renter=self.renter,
            unit=self.unit,
            name="Maintenance",
            amount=500,
            due_date=date.today(),
            status=ExtraCharge.Status.DUE,
        )

        result = send_due_extra_charge_reminders()

        self.assertEqual(result, 1)
        mock_translate.assert_called_once()
        mock_send_whatsapp_message.assert_called_once_with(
            self.renter.whatsapp_number,
            "translated message",
        )
        mock_generate_voice_note.assert_called_once_with("translated message", "hi")
        mock_send_whatsapp_audio.assert_called_once_with(
            self.renter.whatsapp_number,
            "/tmp/fake.mp3",
        )

    @patch("notification.services.whatsapp_service.send_whatsapp_message")
    def test_send_due_extra_charge_reminders_skips_paid_and_non_due_charges(
        self, mock_send_whatsapp_message
    ):
        ExtraCharge.objects.create(
            renter=self.renter,
            unit=self.unit,
            name="Electricity",
            amount=750,
            due_date=date.today(),
            status=ExtraCharge.Status.PAID,
        )
        ExtraCharge.objects.create(
            renter=self.renter,
            unit=self.unit,
            name="Late Fee",
            amount=250,
            due_date=date.today(),
            status=ExtraCharge.Status.MISSED,
        )

        result = send_due_extra_charge_reminders()

        self.assertEqual(result, 0)
        mock_send_whatsapp_message.assert_not_called()
