from typing import TYPE_CHECKING, Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from notification.services.voice_service import generate_voice_note
from notification.services.whatsapp_service import (
    send_whatsapp_audio,
    send_whatsapp_message,
)
from properties.models import Caretaker, PropertyTaxRecord, RentRecord
from rentsecure_be.services.i18n_service import translate_msg
from rentsecure_be.type_compat import override

if TYPE_CHECKING:
    from core.models import User
else:
    User = get_user_model()


class Command(BaseCommand):
    help = "Send daily property summary to caretakers via WhatsApp."

    @override
    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--user-id",
            type=int,
            help="Send summary for a specific caretaker user ID only",
        )
        parser.add_argument(
            "--no-whatsapp",
            action="store_true",
            help="Skip WhatsApp notifications",
        )

    @override
    def handle(self, *args: Any, **options: Any) -> None:
        user_id = options.get("user_id")
        send_whatsapp = not options.get("no_whatsapp")

        if user_id:
            self._send_to_single_caretaker(user_id, send_whatsapp)
        else:
            self._send_to_all_caretakers(send_whatsapp)

    def _send_to_single_caretaker(self, user_id: int, send_whatsapp: bool) -> None:
        try:
            caretaker = Caretaker.objects.select_related("user", "unit").get(
                user_id=user_id
            )
        except Caretaker.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Caretaker with user ID {user_id} not found.")
            )
            return

        self._send_caretaker_summary(caretaker, send_whatsapp)

    def _send_to_all_caretakers(self, send_whatsapp: bool) -> None:
        caretakers = Caretaker.objects.select_related("user", "unit").filter(
            is_active=True
        )

        if not caretakers.exists():
            self.stdout.write(self.style.WARNING("No active caretakers found."))
            return

        self.stdout.write(
            f"Sending daily summaries to {caretakers.count()} caretaker(s)..."
        )

        for caretaker in caretakers:
            self._send_caretaker_summary(caretaker, send_whatsapp)

        self.stdout.write(
            self.style.SUCCESS("\n✅ Daily caretaker summary job completed.")
        )

    def _send_caretaker_summary(
        self, caretaker: Caretaker, send_whatsapp: bool
    ) -> None:
        user = caretaker.user
        if not user or not getattr(user, "whatsapp_number", None):
            self.stdout.write(
                self.style.WARNING(
                    f"  ⚠️ {caretaker.name}: no WhatsApp number configured"
                )
            )
            return

        today = timezone.now().date()
        unit = caretaker.unit

        rent_due = RentRecord.objects.filter(
            unit=unit,
            due_date=today,
            status=RentRecord.Status.PENDING,
        ).select_related("renter")

        tax_due = PropertyTaxRecord.objects.filter(
            property=unit.building,
            due_date=today,
            paid=False,
        )

        building_name = (
            unit.building_name or unit.building.name if unit.building else "Standalone"
        )
        lines = [
            f"📋 Daily Summary ({today.strftime('%d %b')}):",
            f"🏠 Unit: {unit.unit} | {building_name}",
            f"🔔 Rent Due Today: {rent_due.count()}",
        ]
        for rent in rent_due:
            renter_name = rent.renter.name if rent.renter else "Unknown"
            lines.append(f"  - {renter_name}: ₹{rent.amount}")

        lines.append(f"🧾 Tax Due Today: {tax_due.count()}")
        for tax in tax_due:
            lines.append(f"  - {tax.property.name}: ₹{tax.amount}")

        if unit.maintenance_notes:
            lines.append(f"🧹 Maintenance: {unit.maintenance_notes[:200]}")

        message = "\n".join(lines)

        if send_whatsapp:
            try:
                lang = (
                    getattr(getattr(user, "profile", None), "language_preference", None)
                    or "en"
                )
                translated = translate_msg(message, lang)

                send_whatsapp_message(
                    user.whatsapp_number,
                    translated,
                    user=user,
                    rent_record=None,
                )

                try:
                    audio_path = generate_voice_note(translated, lang)
                    if audio_path:
                        send_whatsapp_audio(
                            user.whatsapp_number,
                            audio_path,
                            user=user,
                            rent_record=None,
                        )
                except Exception as exc:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠️ {caretaker.name}: voice note failed: {exc}"
                        )
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✅ {caretaker.name} ({user.whatsapp_number})"
                    )
                )
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"  ❌ {caretaker.name}: {exc}"))
        else:
            self.stdout.write(f"  ℹ️ {caretaker.name}: WhatsApp skipped")
