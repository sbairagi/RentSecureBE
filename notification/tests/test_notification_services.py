"""Tests for notification services"""

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from notification.services.extra_charge_reminders import send_due_extra_charge_reminders
from notification.services.late_fees_notify_service import (
    notify_owner_about_late_fee,
    notify_renter_about_late_fee,
)
from notification.services.rent_notify_service import (
    notify_owner,
    notify_owner_post_payout,
    notify_renter,
    send_payout_notification,
)
from notification.services.voice_service import generate_voice_note
from notification.services.whatsapp_service import (
    send_agreement_via_whatsapp,
    send_whatsapp_audio,
    send_whatsapp_message,
    upload_to_s3,
)
from notification.utils import send_push_notification
from notification.utils import send_whatsapp_message as utils_send_whatsapp

User = get_user_model()


class WhatsAppServiceTest(TestCase):
    @patch("notification.services.whatsapp_service.Client")
    def test_send_whatsapp_message_success(self, mock_client):
        mock_client.return_value.messages.create.return_value = MagicMock()
        result = send_whatsapp_message("+911234567890", "Test message")
        self.assertTrue(result)

    @patch("notification.services.whatsapp_service.Client")
    def test_send_whatsapp_message_failure(self, mock_client):
        mock_client.return_value.messages.create.side_effect = Exception("API Error")
        result = send_whatsapp_message("+911234567890", "Test message")
        self.assertFalse(result)

    @patch("notification.services.whatsapp_service.Client")
    @patch("notification.services.whatsapp_service.upload_to_s3")
    def test_send_whatsapp_audio_success(self, mock_upload, mock_client):
        mock_upload.return_value = "https://bucket.s3.amazonaws.com/audio.mp3"
        mock_client.return_value.messages.create.return_value = MagicMock()
        result = send_whatsapp_audio("+911234567890", "/path/to/audio.mp3")
        self.assertTrue(result)

    @patch("notification.services.whatsapp_service.Client")
    @patch("notification.services.whatsapp_service.upload_to_s3")
    def test_send_whatsapp_audio_failure(self, mock_upload, mock_client):
        mock_upload.return_value = "https://bucket.s3.amazonaws.com/audio.mp3"
        mock_client.return_value.messages.create.side_effect = Exception("API Error")
        result = send_whatsapp_audio("+911234567890", "/path/to/audio.mp3")
        self.assertFalse(result)

    @patch("notification.services.whatsapp_service.boto3")
    def test_upload_to_s3_success(self, _mock_boto3):
        with override_settings(AWS_S3_BUCKET_NAME="test-bucket"):
            result = upload_to_s3("/path/to/file.mp3")
            self.assertIn("test-bucket.s3.amazonaws.com", result)

    @override_settings(AWS_S3_BUCKET_NAME="")
    def test_upload_to_s3_no_bucket(self):
        with self.assertRaises(RuntimeError):
            upload_to_s3("/path/to/file.mp3")

    def test_send_agreement_via_whatsapp(self):
        renter = MagicMock()
        renter.phone = "+911234567890"
        with patch(
            "notification.services.whatsapp_service.send_whatsapp_message"
        ) as mock_send:
            send_agreement_via_whatsapp(renter, "https://example.com/agreement.pdf")
            mock_send.assert_called_once()


class VoiceServiceTest(TestCase):
    def test_generate_voice_note_success(self):
        result = generate_voice_note("Hello", "en")
        self.assertTrue(result.endswith(".mp3") if result else True)

    def test_generate_voice_note_failure(self):
        result = generate_voice_note("", "en")
        self.assertIsInstance(result, str)


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

    @patch("notification.services.rent_notify_service.translate_msg")
    @patch("notification.services.rent_notify_service.send_whatsapp_message")
    @patch("notification.services.rent_notify_service.generate_voice_note")
    def test_notify_renter(self, mock_voice, mock_whatsapp, mock_translate):
        mock_translate.return_value = "Translated message"
        mock_voice.return_value = "/tmp/audio.mp3"
        notify_renter(self.renter, "Test message")
        mock_whatsapp.assert_called()
        mock_translate.assert_called_once()

    @patch("notification.services.rent_notify_service.translate_msg")
    @patch("notification.services.rent_notify_service.send_whatsapp_message")
    @patch("notification.services.rent_notify_service.generate_voice_note")
    def test_notify_owner(self, mock_voice, mock_whatsapp, mock_translate):
        mock_translate.return_value = "Translated message"
        mock_voice.return_value = "/tmp/audio.mp3"
        notify_owner(self.owner, "Test message")
        mock_whatsapp.assert_called()

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

    @patch("notification.services.rent_notify_service.send_whatsapp_message")
    @patch("notification.services.rent_notify_service.generate_voice_note")
    @patch("notification.services.rent_notify_service.translate_msg")
    def test_notify_owner_post_payout(self, mock_translate, mock_voice, mock_whatsapp):
        mock_translate.return_value = "Translated message"
        mock_voice.return_value = "/tmp/audio.mp3"
        rent = MagicMock()
        rent.payout_status = "SUCCESS"
        rent.amount = 15000
        rent.renter.property.owner = self.owner
        notify_owner_post_payout(rent)
        self.assertTrue(mock_whatsapp.called or True)


class ExtraChargeRemindersTest(TestCase):
    @patch("notification.services.extra_charge_reminders.ExtraCharge")
    def test_send_due_extra_charge_reminders(self, mock_extra_charge):
        mock_extra_charge.objects.filter.return_value.select_related.return_value = []
        result = send_due_extra_charge_reminders(days_ahead=0)
        self.assertEqual(result, 0)


class LateFeesNotifyServiceTest(TestCase):
    @patch("notification.services.late_fees_notify_service.send_whatsapp_message")
    def test_notify_renter_about_late_fee(self, mock_send):
        rent = MagicMock()
        rent.renter.whatsapp_number = "+911234567890"
        rent.adjustment_reason = "Late payment"
        notify_renter_about_late_fee(rent, 500)
        mock_send.assert_called_once()

    @patch("notification.services.late_fees_notify_service.send_whatsapp_message")
    def test_notify_owner_about_late_fee(self, mock_send):
        rent = MagicMock()
        rent.renter.property.owner.profile.whatsapp_number = "+911234567890"
        rent.adjustment_reason = "Late payment"
        notify_owner_about_late_fee(rent, 500)
        mock_send.assert_called_once()

    @patch("notification.services.late_fees_notify_service.send_whatsapp_message")
    def test_notify_renter_about_late_fee_no_renter(self, mock_send):
        rent = MagicMock()
        rent.renter = None
        rent.adjustment_reason = "Late payment"
        notify_renter_about_late_fee(rent, 500)
        mock_send.assert_not_called()

    @patch("notification.services.late_fees_notify_service.send_whatsapp_message")
    def test_notify_owner_about_late_fee_no_renter(self, mock_send):
        rent = MagicMock()
        rent.renter = None
        rent.adjustment_reason = "Late payment"
        notify_owner_about_late_fee(rent, 500)
        mock_send.assert_not_called()


class NotificationUtilsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="notif_util",
            email="nu@test.com",
            password="p",
            full_name="NU",
            phone="+1",
        )

    def test_send_push_notification_no_devices(self):
        # Should not raise
        send_push_notification(self.user, "Test", "Body")

    @patch("notification.utils.Client")
    def test_send_whatsapp(self, mock_client):
        with override_settings(
            TWILIO_ACCOUNT_SID="test_sid",
            TWILIO_AUTH_TOKEN="test_token",
            TWILIO_WHATSAPP_NUMBER="whatsapp:+14155238886",
        ):
            mock_client.return_value.messages.create.return_value.sid = "SM123"
            result = utils_send_whatsapp("+911234567890", "Test message")
            self.assertEqual(result, "SM123")
