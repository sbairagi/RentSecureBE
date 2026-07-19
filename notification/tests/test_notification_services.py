"""Tests for notification services."""

from unittest.mock import MagicMock, patch

from twilio.base.exceptions import TwilioRestException

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from notification.services.rent_notify_service import (
    _renter_lang,
    _renter_phone,
    notify_owner,
    notify_owner_post_payout,
    notify_renter,
    send_payout_notification,
)

User = get_user_model()


def _fake_twilio_msg(sid: str = "SM_TEST") -> MagicMock:
    msg = MagicMock()
    msg.sid = sid
    return msg


class RentNotifyServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="notify_user",
            email="notify@test.com",
            password="p",
            full_name="Notify",
            phone="+1",
        )
        self.renter = MagicMock()
        self.renter.id = 1
        self.renter.profile.whatsapp_number = "+911234567890"
        self.renter.profile.language_preference = "en"
        self.owner = MagicMock()
        self.owner.id = 1
        self.owner.profile.whatsapp_number = "+919876543210"
        self.owner.profile.language_preference = "hi"

    @override_settings(ENABLE_WHATSAPP=True)
    @patch("notification.services.i18n_service.translate_msg")
    @patch("notification.adapters.voice.VoiceAdapter.generate_voice_note")
    @patch("notification.adapters.whatsapp.Client")
    def test_notify_renter(self, mock_client, mock_voice, mock_translate):
        mock_translate.return_value = "Translated message"
        mock_voice.return_value = "/tmp/audio.mp3"
        mock_client.return_value.messages.create.return_value = _fake_twilio_msg()
        notify_renter(self.renter, "Test message")
        mock_client.return_value.messages.create.assert_called()
        mock_translate.assert_called_once()

    @override_settings(ENABLE_WHATSAPP=True)
    @patch("notification.services.i18n_service.translate_msg")
    @patch("notification.adapters.voice.VoiceAdapter.generate_voice_note")
    @patch("notification.adapters.whatsapp.Client")
    def test_notify_owner(self, mock_client, mock_voice, mock_translate):
        mock_translate.return_value = "Translated message"
        mock_voice.return_value = "/tmp/audio.mp3"
        mock_client.return_value.messages.create.return_value = _fake_twilio_msg()
        notify_owner(self.owner, "Test message")
        mock_client.return_value.messages.create.assert_called()

    @patch("notification.services.rent_notify_service.notify_renter")
    def test_send_payout_notification_success(self, mock_notify):
        rent = MagicMock()
        rent.payout_status = "SUCCESS"
        rent.amount = 15000
        rent.renter = self.renter
        send_payout_notification(rent)
        mock_notify.assert_called_once()

    @patch("notification.services.rent_notify_service.notify_renter")
    def test_send_payout_notification_failed(self, mock_notify):
        rent = MagicMock()
        rent.payout_status = "FAILED"
        rent.amount = 15000
        rent.renter = self.renter
        send_payout_notification(rent)
        mock_notify.assert_called_once()

    @patch("notification.services.rent_notify_service.notify_renter")
    def test_send_payout_notification_other_status(self, mock_notify):
        rent = MagicMock()
        rent.payout_status = "PENDING"
        rent.id = 1
        rent.renter = self.renter
        send_payout_notification(rent)
        mock_notify.assert_not_called()

    @override_settings(ENABLE_WHATSAPP=True)
    @patch("notification.adapters.whatsapp.Client")
    @patch("notification.adapters.voice.VoiceAdapter.generate_voice_note")
    @patch("notification.services.i18n_service.translate_msg")
    def test_notify_owner_post_payout(self, mock_translate, mock_voice, mock_client):
        mock_translate.return_value = "Translated message"
        mock_voice.return_value = "/tmp/audio.mp3"
        mock_client.return_value.messages.create.return_value = _fake_twilio_msg()
        rent = MagicMock()
        rent.payout_status = "SUCCESS"
        rent.amount = 15000
        rent.renter.property.owner = self.owner
        notify_owner_post_payout(rent)
        mock_client.return_value.messages.create.assert_called()


class ExtraChargeRemindersTest(TestCase):
    @patch("properties.models.ExtraCharge")
    def test_send_due_extra_charge_reminders(self, mock_extra_charge):
        mock_extra_charge.objects.filter.return_value.select_related.return_value = []
        from notification.services.extra_charge_reminders import (
            send_due_extra_charge_reminders,
        )

        result = send_due_extra_charge_reminders(days_ahead=0)
        self.assertEqual(result, 0)


class LateFeesNotifyServiceTest(TestCase):
    @override_settings(ENABLE_WHATSAPP=True)
    @patch("notification.adapters.whatsapp.Client")
    def test_notify_renter_about_late_fee(self, mock_client):
        mock_client.return_value.messages.create.return_value = _fake_twilio_msg()
        rent = MagicMock()
        rent.renter.whatsapp_number = "+911234567890"
        rent.adjustment_reason = "Late payment"
        from notification.services.late_fees_notify_service import (
            notify_renter_about_late_fee,
        )

        notify_renter_about_late_fee(rent, 500)
        mock_client.return_value.messages.create.assert_called_once()

    @override_settings(ENABLE_WHATSAPP=True)
    @patch("notification.adapters.whatsapp.Client")
    def test_notify_owner_about_late_fee(self, mock_client):
        mock_client.return_value.messages.create.return_value = _fake_twilio_msg()
        rent = MagicMock()
        rent.renter.property.owner.profile.whatsapp_number = "+911234567890"
        rent.adjustment_reason = "Late payment"
        from notification.services.late_fees_notify_service import (
            notify_owner_about_late_fee,
        )

        notify_owner_about_late_fee(rent, 500)
        mock_client.return_value.messages.create.assert_called_once()

    @patch("notification.adapters.whatsapp.Client")
    def test_notify_renter_about_late_fee_no_renter(self, mock_client):
        rent = MagicMock()
        rent.renter = None
        rent.adjustment_reason = "Late payment"
        from notification.services.late_fees_notify_service import (
            notify_renter_about_late_fee,
        )

        notify_renter_about_late_fee(rent, 500)
        mock_client.return_value.messages.create.assert_not_called()

    @patch("notification.adapters.whatsapp.Client")
    def test_notify_owner_about_late_fee_no_renter(self, mock_client):
        rent = MagicMock()
        rent.renter = None
        rent.adjustment_reason = "Late payment"
        from notification.services.late_fees_notify_service import (
            notify_owner_about_late_fee,
        )

        notify_owner_about_late_fee(rent, 500)
        mock_client.return_value.messages.create.assert_not_called()


class RentNotifyServiceEdgeTests(TestCase):
    def test_renter_phone_with_profile(self):
        renter = MagicMock()
        profile = MagicMock()
        profile.whatsapp_number = "+919876543210"
        renter.user = MagicMock()
        renter.user.profile = profile
        self.assertEqual(_renter_phone(renter), "+919876543210")

    def test_renter_phone_without_profile(self):
        renter = MagicMock()
        renter.user = None
        renter.whatsapp_number = "+912222222222"
        self.assertEqual(_renter_phone(renter), "+912222222222")

    def test_renter_phone_returns_empty(self):
        renter = MagicMock()
        renter.user = None
        renter.whatsapp_number = ""
        renter.phone = ""
        self.assertEqual(_renter_phone(renter), "")

    def test_renter_lang_with_profile(self):
        renter = MagicMock()
        profile = MagicMock()
        profile.language_preference = "hi"
        renter.user = MagicMock()
        renter.user.profile = profile
        self.assertEqual(_renter_lang(renter, default="en"), "hi")

    def test_renter_lang_without_profile(self):
        renter = MagicMock()
        renter.user = None
        self.assertEqual(_renter_lang(renter, default="en"), "en")

    @override_settings(ENABLE_WHATSAPP=True, ENABLE_VOICE=True)
    @patch(
        "notification.services.i18n_service.translate_msg",
        side_effect=Exception("translation failed"),
    )
    @patch("notification.adapters.voice.VoiceAdapter.generate_voice_note")
    @patch("notification.adapters.whatsapp.Client")
    def test_notify_renter_translation_exception(
        self, mock_client, mock_voice, mock_translate
    ):
        mock_client.return_value.messages.create.return_value = _fake_twilio_msg()
        renter = MagicMock()
        renter.id = 1
        renter.user.profile.whatsapp_number = "+911234567890"
        renter.user.profile.language_preference = "en"
        renter.whatsapp_number = ""
        notify_renter(renter, "Test message")
        mock_translate.assert_called_once()

    @override_settings(ENABLE_WHATSAPP=True, ENABLE_VOICE=True)
    @patch("notification.services.i18n_service.translate_msg")
    @patch("notification.adapters.voice.VoiceAdapter.generate_voice_note")
    @patch(
        "notification.adapters.whatsapp.Client",
        side_effect=TwilioRestException(
            status=400, msg="API Error", uri="http://example.com"
        ),
    )
    def test_notify_renter_whatsapp_exception(
        self, mock_client, mock_voice, mock_translate
    ):
        renter = MagicMock()
        renter.id = 1
        renter.user.profile.whatsapp_number = "+911234567890"
        renter.user.profile.language_preference = "en"
        renter.whatsapp_number = ""
        mock_translate.return_value = "Test"
        notify_renter(renter, "Test message")
        mock_translate.assert_called_once()

    @override_settings(ENABLE_WHATSAPP=True, ENABLE_VOICE=True)
    @patch("notification.services.i18n_service.translate_msg")
    @patch(
        "notification.adapters.voice.VoiceAdapter.generate_voice_note",
        return_value=None,
    )
    @patch("notification.adapters.whatsapp.Client")
    def test_notify_renter_skips_audio_when_none(
        self, mock_client, mock_voice, mock_translate
    ):
        mock_client.return_value.messages.create.return_value = _fake_twilio_msg()
        renter = MagicMock()
        renter.id = 1
        renter.user.profile.whatsapp_number = "+911234567890"
        renter.user.profile.language_preference = "en"
        renter.whatsapp_number = ""
        mock_translate.return_value = "Test"
        notify_renter(renter, "Test message")
        mock_client.return_value.messages.create.assert_called_once()
        mock_voice.assert_called_once()

    @override_settings(ENABLE_WHATSAPP=True, ENABLE_VOICE=True)
    @patch("notification.services.i18n_service.translate_msg")
    @patch("notification.adapters.voice.VoiceAdapter.generate_voice_note")
    @patch("notification.adapters.whatsapp.Client")
    def test_notify_owner_translation_exception(
        self, mock_client, mock_voice, mock_translate
    ):
        mock_client.return_value.messages.create.return_value = _fake_twilio_msg()
        owner = MagicMock()
        owner.id = 1
        owner.profile = MagicMock()
        owner.profile.whatsapp_number = "+919876543210"
        owner.profile.language_preference = "hi"
        owner.phone = "+911111111111"
        notify_owner(owner, "Test message")
        mock_translate.assert_called_once()

    @override_settings(ENABLE_WHATSAPP=True, ENABLE_VOICE=True)
    @patch("notification.services.i18n_service.translate_msg")
    @patch("notification.adapters.voice.VoiceAdapter.generate_voice_note")
    @patch(
        "notification.adapters.whatsapp.Client",
        side_effect=TwilioRestException(
            status=400, msg="API Error", uri="http://example.com"
        ),
    )
    def test_notify_owner_whatsapp_exception(
        self, mock_client, mock_voice, mock_translate
    ):
        owner = MagicMock()
        owner.id = 1
        owner.profile = MagicMock()
        owner.profile.whatsapp_number = "+919876543210"
        owner.profile.language_preference = "hi"
        owner.phone = "+911111111111"
        mock_translate.return_value = "Test"
        notify_owner(owner, "Test message")
        mock_translate.assert_called_once()

    @override_settings(ENABLE_WHATSAPP=True, ENABLE_VOICE=True)
    @patch("notification.services.i18n_service.translate_msg")
    @patch(
        "notification.adapters.voice.VoiceAdapter.generate_voice_note",
        return_value=None,
    )
    @patch("notification.adapters.whatsapp.Client")
    def test_notify_owner_skips_audio_when_none(
        self, mock_client, mock_voice, mock_translate
    ):
        mock_client.return_value.messages.create.return_value = _fake_twilio_msg()
        owner = MagicMock()
        owner.id = 1
        owner.profile = MagicMock()
        owner.profile.whatsapp_number = "+919876543210"
        owner.profile.language_preference = "hi"
        owner.phone = "+911111111111"
        mock_translate.return_value = "Test"
        notify_owner(owner, "Test message")
        mock_client.return_value.messages.create.assert_called_once()
        mock_voice.assert_called_once()

    @patch("notification.services.rent_notify_service.notify_renter")
    def test_send_payout_notification_exception(self, mock_notify):
        mock_notify.side_effect = Exception("notify failed")
        rent = MagicMock()
        rent.payout_status = "SUCCESS"
        rent.amount = 15000
        rent.renter = MagicMock()
        rent.id = 1
        send_payout_notification(rent)
        mock_notify.assert_called_once()

    @override_settings(ENABLE_WHATSAPP=True)
    @patch("notification.adapters.whatsapp.Client")
    @patch("notification.services.i18n_service.translate_msg")
    @patch("notification.adapters.voice.VoiceAdapter.generate_voice_note")
    def test_notify_owner_post_payout_failed_status(
        self, mock_voice, mock_translate, mock_client
    ):
        mock_client.return_value.messages.create.return_value = _fake_twilio_msg()
        mock_translate.return_value = "Translated"
        owner = MagicMock()
        owner.id = 1
        owner.profile = MagicMock()
        owner.profile.whatsapp_number = "+919876543210"
        owner.profile.language_preference = "hi"
        owner.phone = "+911111111111"
        rent = MagicMock()
        rent.payout_status = "FAILED"
        rent.amount = 15000
        rent.renter.unit.owner = owner
        notify_owner_post_payout(rent)
        mock_translate.assert_called_once()

    @override_settings(ENABLE_WHATSAPP=True)
    @patch("notification.services.i18n_service.translate_msg")
    @patch("notification.adapters.whatsapp.Client")
    @patch("notification.adapters.voice.VoiceAdapter.generate_voice_note")
    def test_notify_owner_post_payout_no_phone(
        self, mock_voice, mock_client, mock_translate
    ):
        mock_translate.return_value = "Translated"
        owner = MagicMock()
        owner.id = 1
        owner.profile = MagicMock()
        owner.profile.whatsapp_number = ""
        owner.profile.language_preference = "hi"
        owner.phone = ""
        rent = MagicMock()
        rent.payout_status = "SUCCESS"
        rent.amount = 15000
        rent.renter.unit.owner = owner
        notify_owner_post_payout(rent)
        mock_translate.assert_called_once()
        mock_client.return_value.messages.create.assert_not_called()

    @override_settings(ENABLE_WHATSAPP=True, ENABLE_VOICE=True)
    @patch("notification.services.i18n_service.translate_msg")
    @patch(
        "notification.adapters.voice.VoiceAdapter.generate_voice_note",
        return_value=None,
    )
    @patch("notification.adapters.whatsapp.Client")
    def test_notify_owner_post_payout_skips_audio(
        self, mock_client, mock_voice, mock_translate
    ):
        mock_client.return_value.messages.create.return_value = _fake_twilio_msg()
        mock_translate.return_value = "Translated"
        owner = MagicMock()
        owner.id = 1
        owner.profile = MagicMock()
        owner.profile.whatsapp_number = "+919876543210"
        owner.profile.language_preference = "hi"
        owner.phone = "+911111111111"
        rent = MagicMock()
        rent.payout_status = "SUCCESS"
        rent.amount = 15000
        rent.renter.unit.owner = owner
        notify_owner_post_payout(rent)
        mock_client.return_value.messages.create.assert_called_once()
        mock_voice.assert_called_once()
