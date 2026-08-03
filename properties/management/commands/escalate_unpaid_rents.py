from typing import TYPE_CHECKING, Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from properties.models import Caretaker, RentRecord
from rentsecure_be.type_compat import override

if TYPE_CHECKING:
    from core.models import User
else:
    User = get_user_model()

logger = __import__("logging").getLogger(__name__)


class Command(BaseCommand):
    help = "Escalate unpaid rents that are 3 days past due."

    @override
    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--user-id",
            type=int,
            help="Send escalation for a specific owner user ID only",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print escalation targets without sending messages",
        )

    @override
    def handle(self, *args: Any, **options: Any) -> None:
        user_id = options.get("user_id")
        dry_run = options.get("dry_run", False)

        if user_id:
            self._send_for_owner(user_id, dry_run)
        else:
            self._send_for_all_owners(dry_run)

    def _send_for_owner(self, user_id: int, dry_run: bool) -> None:
        try:
            owner = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Owner with user ID {user_id} not found.")
            )
            return

        rents = self._overdue_rents_qs().filter(unit__owner=owner)
        self._process_rents(rents, dry_run)

    def _send_for_all_owners(self, dry_run: bool) -> None:
        rents = self._overdue_rents_qs()
        self._process_rents(rents, dry_run)

    def _overdue_rents_qs(self):
        target_date = timezone.now().date() - timezone.timedelta(days=3)
        return RentRecord.objects.filter(
            due_date=target_date,
            status=RentRecord.Status.PENDING,
        ).select_related(
            "renter",
            "renter__user",
            "unit__owner",
        )

    def _process_rents(self, rents, dry_run: bool) -> None:
        if not rents.exists():
            self.stdout.write(self.style.WARNING("No overdue rents found."))
            return

        self.stdout.write(f"Found {rents.count()} overdue rent(s) to escalate...")

        processed = 0
        for rent in rents:
            if self._escalate_rent(rent, dry_run):
                processed += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Escalation job completed. Processed {processed} rent(s)."
            )
        )

    def _escalate_rent(self, rent: RentRecord, dry_run: bool) -> bool:
        renter = rent.renter
        if renter is None:
            return False

        from properties.models.renter_models import RentReminderLog

        if RentReminderLog.objects.filter(
            renter=renter,
            message_type="ESCALATION",
            sent_at__date=timezone.now().date(),
        ).exists():
            return False

        owner = rent.unit.owner
        caretakers = Caretaker.objects.filter(
            unit=rent.unit, is_active=True
        ).select_related("user")

        msg = (
            f"🚨 Reminder: ₹{rent.amount} rent for {rent.unit.unit} "
            f"was due on {rent.due_date.strftime('%d %B')} and is still unpaid."
        )

        if dry_run:
            self.stdout.write(f"[DRY RUN] Would escalate rent {rent.id}: {msg}")
            self._log_escalation(renter)
            return True

        try:
            self._notify_renter(renter, msg)
            self._notify_owner(owner, msg)
            for caretaker in caretakers:
                self._notify_caretaker(caretaker, msg)
            self._log_escalation(renter)
            self.stdout.write(
                self.style.SUCCESS(f"  ✅ Escalated rent {rent.id} for {renter.name}")
            )
            return True
        except Exception as exc:
            self.stdout.write(
                self.style.ERROR(f"  ❌ Failed to escalate rent {rent.id}: {exc}")
            )
            return False

    def _notify_renter(self, renter, msg: str) -> None:
        phone = renter.whatsapp_number or getattr(
            getattr(renter, "user", None), "whatsapp_number", None
        )
        if not phone:
            return

        renter_profile = getattr(getattr(renter, "user", None), "profile", None)
        lang = getattr(renter_profile, "language_preference", None) or "en"

        from rentsecure_be.services.i18n_service import translate_msg

        translated = translate_msg(msg, lang)

        from notification.services.whatsapp_service import send_whatsapp_message

        send_whatsapp_message(
            phone,
            translated,
            user=getattr(renter, "user", None),
            rent_record=None,
        )

        try:
            from notification.services.voice_service import generate_voice_note
            from notification.services.whatsapp_service import send_whatsapp_audio

            audio_path = generate_voice_note(translated, lang)
            if audio_path:
                send_whatsapp_audio(
                    phone,
                    audio_path,
                    user=getattr(renter, "user", None),
                    rent_record=None,
                )
        except Exception:
            logger.exception(
                "Failed to send escalation voice note to renter %s",
                getattr(renter, "name", renter.pk),
            )

    def _notify_owner(self, owner, msg: str) -> None:
        phone = getattr(owner, "whatsapp_number", None) or getattr(
            getattr(owner, "profile", None), "whatsapp_number", None
        )
        if not phone:
            return

        lang = (
            getattr(getattr(owner, "profile", None), "language_preference", None)
            or "en"
        )

        from rentsecure_be.services.i18n_service import translate_msg

        translated = translate_msg(msg, lang)

        from notification.services.whatsapp_service import send_whatsapp_message

        send_whatsapp_message(
            phone,
            translated,
            user=owner,
            rent_record=None,
        )

        try:
            from notification.services.voice_service import generate_voice_note
            from notification.services.whatsapp_service import send_whatsapp_audio

            audio_path = generate_voice_note(translated, lang)
            if audio_path:
                send_whatsapp_audio(
                    phone,
                    audio_path,
                    user=owner,
                    rent_record=None,
                )
        except Exception:
            logger.exception(
                "Failed to send escalation voice note to owner %s",
                getattr(owner, "username", getattr(owner, "pk", "unknown")),
            )

    def _notify_caretaker(self, caretaker, msg: str) -> None:
        user = caretaker.user
        if not user:
            return

        phone = getattr(user, "whatsapp_number", None) or getattr(
            getattr(user, "profile", None), "whatsapp_number", None
        )
        if not phone:
            return

        lang = (
            getattr(getattr(user, "profile", None), "language_preference", None) or "en"
        )

        from rentsecure_be.services.i18n_service import translate_msg

        translated = translate_msg(msg, lang)

        from notification.services.whatsapp_service import send_whatsapp_message

        send_whatsapp_message(
            phone,
            translated,
            user=user,
            rent_record=None,
        )

        try:
            from notification.services.voice_service import generate_voice_note
            from notification.services.whatsapp_service import send_whatsapp_audio

            audio_path = generate_voice_note(translated, lang)
            if audio_path:
                send_whatsapp_audio(
                    phone,
                    audio_path,
                    user=user,
                    rent_record=None,
                )
        except Exception:
            logger.exception(
                "Failed to send escalation voice note to caretaker %s",
                getattr(caretaker, "name", getattr(user, "username", "unknown")),
            )

    def _log_escalation(self, renter) -> None:
        from properties.models.renter_models import RentReminderLog

        RentReminderLog.objects.create(
            renter=renter,
            message_type="ESCALATION",
        )
