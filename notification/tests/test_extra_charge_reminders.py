from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import UserProfile
from notification.services.extra_charge_reminders import send_due_extra_charge_reminders
from properties.models import ExtraCharge, Renter, Unit

User = get_user_model()


# ---------------------------------------------------------------------------
# Helper: build a minimal renter chain (owner → unit → renter → user + profile)
# ---------------------------------------------------------------------------


def _build_renter_chain(
    username,
    phone="+910000000000",
    whatsapp_number=None,
    language_preference="en",
    user=None,
):
    owner = User.objects.create_user(
        username=f"{username}_owner",
        password="p",
        full_name=f"{username} Owner",
        whatsapp_number="+919999999999",
    )
    unit = Unit.objects.create(
        owner=owner,
        unit=username[:10],
        unit_type=Unit.UnitType.FLAT,
        address_line=f"{username} Street",
        city="Mumbai",
        state="Maharashtra",
        country="India",
        postal_code="400001",
    )
    if user is None:
        user = User.objects.create_user(
            username=username,
            password="p",
            full_name=username,
            whatsapp_number=phone,
        )
        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                "whatsapp_number": whatsapp_number or phone,
                "language_preference": language_preference,
            },
        )
    # Create renter directly (bypass factory which sets user=None)
    renter = Renter(
        unit=unit,
        user=user,
        name=username,
        phone=phone,
        whatsapp_number=whatsapp_number or phone,
        rent_amount=10000,
        start_date=date.today(),
    )
    renter.save()
    return owner, unit, renter, user


# ---------------------------------------------------------------------------
# Branch: no phone → continue (line 29-30)
# ---------------------------------------------------------------------------


class ExtraChargeReminderNoPhoneTest(TestCase):
    def test_skips_renter_without_phone(self):
        owner, unit, renter, _ = _build_renter_chain(
            "nophone",
            phone="",
            whatsapp_number="",
        )
        # Override: no phone at all
        renter.phone = ""
        renter.whatsapp_number = ""
        renter.save(update_fields=["phone", "whatsapp_number"])

        ExtraCharge.objects.create(
            renter=renter,
            unit=unit,
            name="Maintenance",
            amount=500,
            due_date=date.today(),
            status=ExtraCharge.Status.DUE,
        )

        with (
            patch(
                "notification.services.extra_charge_reminders.send_whatsapp_message"
            ) as mock_msg,
            patch(
                "notification.services.extra_charge_reminders.send_whatsapp_audio"
            ) as mock_audio,
            patch(
                "notification.services.extra_charge_reminders.generate_voice_note",
                return_value=None,
            ) as mock_voice,
        ):
            result = send_due_extra_charge_reminders()

        self.assertEqual(result, 1)  # charge_list has 1 item even though skipped
        mock_msg.assert_not_called()
        mock_voice.assert_not_called()
        mock_audio.assert_not_called()


# ---------------------------------------------------------------------------
# Branch: renter.user is None → lang = "en" (line 33 false branch)
# ---------------------------------------------------------------------------


class ExtraChargeReminderNoUserDefaultEnTest(TestCase):
    def test_defaults_to_en_when_renter_has_no_user(self):
        owner, unit, renter, _ = _build_renter_chain(
            "nouser",
            phone="+910000000001",
        )
        renter.user = None
        renter.save(update_fields=["user"])

        ExtraCharge.objects.create(
            renter=renter,
            unit=unit,
            name="Maintenance",
            amount=500,
            due_date=date.today(),
            status=ExtraCharge.Status.DUE,
        )

        with (
            patch(
                "notification.services.extra_charge_reminders.send_whatsapp_message"
            ) as mock_msg,
            patch(
                "notification.services.extra_charge_reminders.send_whatsapp_audio"
            ) as mock_audio,
            patch(
                "notification.services.extra_charge_reminders.generate_voice_note",
                return_value=None,
            ) as mock_voice,
        ):
            result = send_due_extra_charge_reminders()

        self.assertEqual(result, 1)
        mock_msg.assert_called_once()
        mock_voice.assert_called_once()
        # lang should be "en"
        mock_voice.assert_called_once_with(mock_msg.call_args[0][1], "en")
        mock_audio.assert_not_called()  # voice_note returns None from mock


# ---------------------------------------------------------------------------
# Branch: hasattr(user, "userprofile") is False → lang = "en"
# ---------------------------------------------------------------------------


class ExtraChargeReminderNoProfileDefaultEnTest(TestCase):
    def test_defaults_to_en_when_user_has_no_profile(self):
        user = User.objects.create_user(
            username="noprofile",
            password="p",
            full_name="NoProfile",
            whatsapp_number="+910000000002",
        )
        # No UserProfile created
        owner, unit, renter, _ = _build_renter_chain(
            "noprofile_unit",
            phone="+910000000003",
            user=user,
        )

        ExtraCharge.objects.create(
            renter=renter,
            unit=unit,
            name="Maintenance",
            amount=500,
            due_date=date.today(),
            status=ExtraCharge.Status.DUE,
        )

        with (
            patch(
                "notification.services.extra_charge_reminders.send_whatsapp_message"
            ) as mock_msg,
            patch(
                "notification.services.extra_charge_reminders.send_whatsapp_audio"
            ) as mock_audio,
            patch(
                "notification.services.extra_charge_reminders.generate_voice_note",
                return_value=None,
            ) as mock_voice,
        ):
            result = send_due_extra_charge_reminders()

        self.assertEqual(result, 1)
        mock_msg.assert_called_once()
        mock_voice.assert_called_once_with(mock_msg.call_args[0][1], "en")
        mock_audio.assert_not_called()


# ---------------------------------------------------------------------------
# Branch: hasattr(user, "userprofile") is True → lang from profile
# ---------------------------------------------------------------------------


class ExtraChargeReminderWithProfileLangTest(TestCase):
    def test_uses_profile_language_preference(self):
        user = User.objects.create_user(
            username="withprofile",
            password="p",
            full_name="WithProfile",
            whatsapp_number="+910000000004",
        )
        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={"whatsapp_number": "+910000000004", "language_preference": "hi"},
        )
        profile.language_preference = "hi"
        profile.save()

        owner, unit, renter, _ = _build_renter_chain(
            "withprofile_unit",
            phone="+910000000005",
            user=user,
        )

        ExtraCharge.objects.create(
            renter=renter,
            unit=unit,
            name="Maintenance",
            amount=500,
            due_date=date.today(),
            status=ExtraCharge.Status.DUE,
        )

        with (
            patch(
                "notification.services.extra_charge_reminders.send_whatsapp_message"
            ) as mock_msg,
            patch(
                "notification.services.extra_charge_reminders.send_whatsapp_audio"
            ) as mock_audio,
            patch(
                "notification.services.extra_charge_reminders.generate_voice_note",
                return_value=None,
            ) as mock_voice,
        ):
            result = send_due_extra_charge_reminders()

        self.assertEqual(result, 1)
        mock_msg.assert_called_once()
        mock_voice.assert_called_once_with(mock_msg.call_args[0][1], "hi")
        mock_audio.assert_not_called()


# ---------------------------------------------------------------------------
# Branch: send_whatsapp_message raises → continue (line 45-47)
# ---------------------------------------------------------------------------


class ExtraChargeReminderWhatsappMessageExceptionTest(TestCase):
    def test_continues_on_whatsapp_message_exception(self):
        owner, unit, renter, _ = _build_renter_chain(
            "msgexc",
            phone="+910000000010",
        )

        ExtraCharge.objects.create(
            renter=renter,
            unit=unit,
            name="Maintenance",
            amount=500,
            due_date=date.today(),
            status=ExtraCharge.Status.DUE,
        )

        with (
            patch(
                "notification.services.extra_charge_reminders.send_whatsapp_message",
                side_effect=Exception("Twilio error"),
            ) as mock_msg,
            patch(
                "notification.services.extra_charge_reminders.send_whatsapp_audio"
            ) as mock_audio,
            patch(
                "notification.services.extra_charge_reminders.generate_voice_note"
            ) as mock_voice,
        ):
            result = send_due_extra_charge_reminders()

        # charge_list still has 1 item; text send failed but charge is counted
        self.assertEqual(result, 1)
        mock_msg.assert_called_once()
        mock_voice.assert_not_called()
        mock_audio.assert_not_called()


# ---------------------------------------------------------------------------
# Branch: audio_path is falsy (None) → skip audio block (line 50 false)
# ---------------------------------------------------------------------------


class ExtraChargeReminderNoAudioPathTest(TestCase):
    def test_skips_audio_when_voice_note_returns_none(self):
        owner, unit, renter, _ = _build_renter_chain(
            "noneaudio",
            phone="+910000000020",
        )

        ExtraCharge.objects.create(
            renter=renter,
            unit=unit,
            name="Maintenance",
            amount=500,
            due_date=date.today(),
            status=ExtraCharge.Status.DUE,
        )

        with (
            patch(
                "notification.services.extra_charge_reminders.send_whatsapp_message"
            ) as mock_msg,
            patch(
                "notification.services.extra_charge_reminders.send_whatsapp_audio"
            ) as mock_audio,
            patch(
                "notification.services.extra_charge_reminders.generate_voice_note",
                return_value=None,
            ) as mock_voice,
        ):
            result = send_due_extra_charge_reminders()

        self.assertEqual(result, 1)
        mock_msg.assert_called_once()
        mock_voice.assert_called_once()
        mock_audio.assert_not_called()

    def test_sends_audio_when_voice_note_returns_path(self):
        owner, unit, renter, _ = _build_renter_chain(
            "withaudio",
            phone="+910000000021",
        )

        ExtraCharge.objects.create(
            renter=renter,
            unit=unit,
            name="Maintenance",
            amount=500,
            due_date=date.today(),
            status=ExtraCharge.Status.DUE,
        )

        with (
            patch(
                "notification.services.extra_charge_reminders.send_whatsapp_message"
            ) as mock_msg,
            patch(
                "notification.services.extra_charge_reminders.send_whatsapp_audio"
            ) as mock_audio,
            patch(
                "notification.services.extra_charge_reminders.generate_voice_note",
                return_value="/tmp/test_audio.mp3",
            ) as mock_voice,
        ):
            result = send_due_extra_charge_reminders()

        self.assertEqual(result, 1)
        mock_msg.assert_called_once()
        mock_voice.assert_called_once()
        mock_audio.assert_called_once_with(
            renter.whatsapp_number, "/tmp/test_audio.mp3"
        )


# ---------------------------------------------------------------------------
# Branch: send_whatsapp_audio raises → continue (line 53-55)
# ---------------------------------------------------------------------------


class ExtraChargeReminderWhatsappAudioExceptionTest(TestCase):
    def test_continues_on_whatsapp_audio_exception(self):
        owner, unit, renter, _ = _build_renter_chain(
            "audioexc",
            phone="+910000000030",
        )

        ExtraCharge.objects.create(
            renter=renter,
            unit=unit,
            name="Maintenance",
            amount=500,
            due_date=date.today(),
            status=ExtraCharge.Status.DUE,
        )

        with (
            patch(
                "notification.services.extra_charge_reminders.send_whatsapp_message"
            ) as mock_msg,
            patch(
                "notification.services.extra_charge_reminders.send_whatsapp_audio",
                side_effect=Exception("Audio send error"),
            ) as mock_audio,
            patch(
                "notification.services.extra_charge_reminders.generate_voice_note",
                return_value="/tmp/test.mp3",
            ) as mock_voice,
        ):
            result = send_due_extra_charge_reminders()

        self.assertEqual(result, 1)
        mock_msg.assert_called_once()
        mock_voice.assert_called_once()
        mock_audio.assert_called_once()

    def test_processes_multiple_charges_when_one_audio_fails(self):
        owner, unit, renter1, _ = _build_renter_chain(
            "multi1",
            phone="+910000000031",
        )
        renter2 = Renter.objects.create(
            unit=unit,
            name="Multi2",
            phone="+910000000032",
            whatsapp_number="+910000000032",
            rent_amount=10000,
            start_date=date.today(),
        )

        ExtraCharge.objects.create(
            renter=renter1,
            unit=unit,
            name="Charge1",
            amount=500,
            due_date=date.today(),
            status=ExtraCharge.Status.DUE,
        )
        ExtraCharge.objects.create(
            renter=renter2,
            unit=unit,
            name="Charge2",
            amount=300,
            due_date=date.today(),
            status=ExtraCharge.Status.DUE,
        )

        call_count = [0]

        def audio_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Audio error")
            return True

        with (
            patch(
                "notification.services.extra_charge_reminders.send_whatsapp_message"
            ) as mock_msg,
            patch(
                "notification.services.extra_charge_reminders.send_whatsapp_audio",
                side_effect=audio_side_effect,
            ) as mock_audio,
            patch(
                "notification.services.extra_charge_reminders.generate_voice_note",
                return_value="/tmp/test.mp3",
            ),
        ):
            result = send_due_extra_charge_reminders()

        self.assertEqual(result, 2)
        self.assertEqual(mock_msg.call_count, 2)
        self.assertEqual(mock_audio.call_count, 2)


# ---------------------------------------------------------------------------
# days_ahead parameter: target_date calculation
# ---------------------------------------------------------------------------


class ExtraChargeReminderDaysAheadTest(TestCase):
    def test_days_ahead_filters_charges_correctly(self):
        owner, unit, renter, _ = _build_renter_chain(
            "daysahead",
            phone="+910000000040",
        )

        today = date.today()
        tomorrow = today + timedelta(days=1)
        day_after = today + timedelta(days=2)

        ExtraCharge.objects.create(
            renter=renter,
            unit=unit,
            name="Today Charge",
            amount=100,
            due_date=today,
            status=ExtraCharge.Status.DUE,
        )
        ExtraCharge.objects.create(
            renter=renter,
            unit=unit,
            name="Tomorrow Charge",
            amount=200,
            due_date=tomorrow,
            status=ExtraCharge.Status.DUE,
        )
        ExtraCharge.objects.create(
            renter=renter,
            unit=unit,
            name="DayAfter Charge",
            amount=300,
            due_date=day_after,
            status=ExtraCharge.Status.DUE,
        )

        with (
            patch(
                "notification.services.extra_charge_reminders.send_whatsapp_message"
            ) as mock_msg,
            patch("notification.services.extra_charge_reminders.send_whatsapp_audio"),
            patch(
                "notification.services.extra_charge_reminders.generate_voice_note",
                return_value=None,
            ),
        ):
            result = send_due_extra_charge_reminders(days_ahead=1)

        # days_ahead=1 → target_date = today+1 = tomorrow → only 1 charge matches
        self.assertEqual(result, 1)
        mock_msg.assert_called_once()
        called_messages = {call.args[1] for call in mock_msg.call_args_list}
        self.assertTrue(
            any("Tomorrow Charge" in msg for msg in called_messages),
            f"Expected 'Tomorrow Charge' in messages: {called_messages}",
        )
