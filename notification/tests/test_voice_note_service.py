"""Tests for notification/services/voice_note_service.py."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

from django.test import TestCase, override_settings

import notification.services.voice_note_service as _vns
from properties.models import Building, Renter, RentRecord, Unit

_ORIGINAL_SEND_THANK_YOU = _vns.send_thank_you_voice_note
_ORIGINAL_SEND_LATE = _vns.send_late_rent_reminder
_ORIGINAL_ALERT_OWNER = _vns.alert_owner_about_delay


@override_settings(ENABLE_WHATSAPP=True, ENABLE_VOICE=True)
class SendThankYouVoiceNoteTests(TestCase):
    def setUp(self):
        owner_cls = (
            RentRecord._meta.get_field("renter")
            .remote_field.model._meta.get_field("unit")
            .remote_field.model._meta.get_field("owner")
            .remote_field.model
        )
        self.owner = owner_cls.objects.create_user(
            username="voice_owner", password="p", full_name="VoiceOwner", phone="+91"
        )
        self.building = Building.objects.create(
            name="VoiceB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
            owner=self.owner,
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="V1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Voice Renter",
            phone="+911234567890",
            email="vr@test.com",
            rent_amount=10000,
            start_date=date(2024, 1, 1),
        )
        self.renter.whatsapp_number = "+919876543210"
        self.renter.save()
        self.rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=10000,
            payment_method="upi",
            status="PAID",
            paid_on=date(2024, 1, 5),
            due_date=date(2024, 1, 5),
        )

    def test_send_voice_note_to_renter(self):
        _vns.send_thank_you_voice_note = _ORIGINAL_SEND_THANK_YOU
        with patch(
            "notification.services.notification_service.NotificationService.send_whatsapp_audio"
        ) as mock_send:
            with patch(
                "notification.services.notification_service.NotificationService.generate_voice_note"
            ) as mock_generate:
                mock_generate.return_value = "/tmp/test_audio.mp3"
                mock_send.return_value = None
                from notification.services.voice_note_service import (
                    send_thank_you_voice_note,
                )

                send_thank_you_voice_note(self.rent)
                mock_generate.assert_called_once()
                mock_send.assert_called_once()

    @patch(
        "notification.services.notification_service.NotificationService.send_whatsapp_audio"
    )
    @patch(
        "notification.services.notification_service.NotificationService.generate_voice_note"
    )
    def test_send_voice_note_skipped_when_no_audio(self, mock_generate, mock_send):
        _vns.send_thank_you_voice_note = _ORIGINAL_SEND_THANK_YOU
        mock_generate.return_value = None
        from notification.services.voice_note_service import send_thank_you_voice_note

        send_thank_you_voice_note(self.rent)
        mock_send.assert_not_called()

    def test_send_voice_note_skipped_when_no_renter(self):
        _vns.send_thank_you_voice_note = _ORIGINAL_SEND_THANK_YOU
        from notification.services.voice_note_service import send_thank_you_voice_note

        self.rent.renter = None
        send_thank_you_voice_note(self.rent)


@override_settings(ENABLE_WHATSAPP=True, ENABLE_VOICE=True)
class SendLateRentReminderTests(TestCase):
    def setUp(self):
        owner_cls = (
            RentRecord._meta.get_field("renter")
            .remote_field.model._meta.get_field("unit")
            .remote_field.model._meta.get_field("owner")
            .remote_field.model
        )
        self.owner = owner_cls.objects.create_user(
            username="late_owner", password="p", full_name="LateOwner", phone="+91"
        )
        self.building = Building.objects.create(
            name="LateB2",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
            owner=self.owner,
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="L1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Late Renter",
            phone="+911234567891",
            email="lr@test.com",
            rent_amount=10000,
            start_date=date(2024, 1, 1),
        )
        self.renter.whatsapp_number = "+919876543211"
        self.renter.save()
        self.rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=10000,
            payment_method="upi",
            status="PENDING",
            due_date=date(2024, 1, 5),
        )

    def test_send_late_reminder(self):
        _vns.send_late_rent_reminder = _ORIGINAL_SEND_LATE
        with patch(
            "notification.adapters.whatsapp.WhatsAppAdapter.send_whatsapp_audio"
        ) as mock_send:
            with patch(
                "notification.adapters.voice.VoiceAdapter.generate_voice_note"
            ) as mock_generate:
                mock_generate.return_value = "/tmp/test_audio.mp3"
                mock_send.return_value = None
                from notification.services.voice_note_service import (
                    send_late_rent_reminder,
                )

                send_late_rent_reminder(self.rent)
                mock_generate.assert_called_once()
                mock_send.assert_called_once()

    def test_send_late_reminder_skipped_when_no_renter(self):
        _vns.send_late_rent_reminder = _ORIGINAL_SEND_LATE
        from notification.services.voice_note_service import send_late_rent_reminder

        self.rent.renter = None
        send_late_rent_reminder(self.rent)
        from properties.models.renter_models import RentReminderLog

        self.assertEqual(RentReminderLog.objects.count(), 0)

    def test_send_late_reminder_creates_log(self):
        _vns.send_late_rent_reminder = _ORIGINAL_SEND_LATE
        with patch(
            "notification.adapters.whatsapp.WhatsAppAdapter.send_whatsapp_audio"
        ):
            with patch("notification.adapters.voice.VoiceAdapter.generate_voice_note"):
                from notification.services.voice_note_service import (
                    send_late_rent_reminder,
                )

                send_late_rent_reminder(self.rent)
                from properties.models.renter_models import RentReminderLog

                self.assertEqual(RentReminderLog.objects.count(), 1)
                log = RentReminderLog.objects.first()
                self.assertEqual(log.renter, self.renter)
                self.assertEqual(log.message_type, "LATE")


@override_settings(ENABLE_WHATSAPP=True, ENABLE_VOICE=True)
class AlertOwnerAboutDelayTests(TestCase):
    def setUp(self):
        owner_cls = (
            RentRecord._meta.get_field("renter")
            .remote_field.model._meta.get_field("unit")
            .remote_field.model._meta.get_field("owner")
            .remote_field.model
        )
        self.owner = owner_cls.objects.create_user(
            username="alert_owner", password="p", full_name="AlertOwner", phone="+91"
        )
        self.building = Building.objects.create(
            name="AlertB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
            owner=self.owner,
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="A1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Alert Renter",
            phone="+911234567892",
            email="ar@test.com",
            rent_amount=10000,
            start_date=date(2024, 1, 1),
        )
        self.rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=10000,
            payment_method="upi",
            status="PENDING",
            due_date=date(2024, 1, 5),
        )

    def test_alert_owner_sends_message(self):
        _vns.alert_owner_about_delay = _ORIGINAL_ALERT_OWNER
        with patch(
            "notification.adapters.whatsapp.WhatsAppAdapter.send_whatsapp_message"
        ) as mock_send:
            self.owner.whatsapp_number = "+919876543210"
            self.owner.save()
            from notification.services.voice_note_service import alert_owner_about_delay

            alert_owner_about_delay(self.rent)
            mock_send.assert_called_once()

    def test_alert_owner_skipped_when_no_renter(self):
        _vns.alert_owner_about_delay = _ORIGINAL_ALERT_OWNER
        from notification.services.voice_note_service import alert_owner_about_delay

        self.rent.renter = None
        alert_owner_about_delay(self.rent)

    def test_alert_owner_skipped_when_no_number(self):
        _vns.alert_owner_about_delay = _ORIGINAL_ALERT_OWNER
        with patch(
            "notification.adapters.whatsapp.WhatsAppAdapter.send_whatsapp_message"
        ) as mock_send:
            self.owner.whatsapp_number = ""
            self.owner.save()
            from notification.services.voice_note_service import alert_owner_about_delay

            alert_owner_about_delay(self.rent)
            mock_send.assert_not_called()
