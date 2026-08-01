import logging
from datetime import date, timedelta
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from notification.services.voice_service import generate_voice_note
from notification.services.whatsapp_service import send_whatsapp_message
from properties.models import Unit
from properties.services.vacancy_service import VacancyReport, build_vacancy_report
from rentsecure_be.services.i18n_service import translate_msg
from rentsecure_be.type_compat import override

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Notify property owners about vacant units: "
        "7-day alerts with suggestions and 30+ day reminders."
    )

    @override
    def handle(self, *args: Any, **options: Any) -> None:
        today = timezone.now().date()
        report: VacancyReport = build_vacancy_report()

        self.stdout.write(f"Found {report['total_vacant_units']} vacant unit(s).")

        self._process_recent_vacancies(today)
        self._process_long_term_vacancies(today)

    def _process_recent_vacancies(self, today: date) -> None:
        cutoff = today - timedelta(days=30)
        units = Unit.objects.filter(
            is_vacant=True,
            last_vacated_at__gte=cutoff,
            last_vacated_at__isnull=False,
        ).select_related("owner", "building")

        if not units.exists():
            self.stdout.write(self.style.NOTICE("No recent vacant units found."))
            return

        for unit in units:
            self._send_suggested_vacancy_alert(unit, today)

    def _process_long_term_vacancies(self, today: date) -> None:
        units = Unit.objects.filter(
            is_vacant=True,
            last_vacated_at__isnull=False,
        ).select_related("owner", "building")

        for unit in units:
            last_vacated: date | None = unit.last_vacated_at
            if last_vacated is None:
                continue
            days_vacant = (today - last_vacated).days
            if days_vacant < 30:
                continue

            self._send_long_term_vacancy_alert(unit, today, days_vacant)

    def _send_suggested_vacancy_alert(self, unit: Unit, today: date) -> None:
        last_vacated: date | None = unit.last_vacated_at
        if last_vacated is None:
            return
        days_vacant = (today - last_vacated).days
        if days_vacant < 7:
            return

        owner = unit.owner
        building_name = (
            unit.building.name
            if unit.building
            else getattr(unit, "building_name", None) or "your property"
        )
        unit_label = unit.unit

        suggestions = [
            "📋 Add a new renter from your dashboard",
            "📢 Consider posting this unit on rental marketplaces",
        ]

        message = (
            f"🏠 Vacancy Alert: Unit {unit_label} in {building_name} "
            f"has been vacant for {days_vacant} days.\n\n"
            f"Suggestions:\n" + "\n".join(suggestions)
        )

        whatsapp_sent = self._send_whatsapp_alert(owner, message)
        email_sent = self._send_email_alert(
            owner, unit_label, f"Vacancy Alert: {days_vacant} days"
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Vacancy alert sent for unit {unit_label} "
                f"({days_vacant} days): whatsapp={whatsapp_sent}, email={email_sent}"
            )
        )

    def _send_long_term_vacancy_alert(
        self, unit: Unit, today: date, days_vacant: int
    ) -> None:
        owner = unit.owner
        building_name = (
            unit.building.name
            if unit.building
            else getattr(unit, "building_name", None) or "your property"
        )
        unit_label = unit.unit
        message = (
            f"📭 Long-term vacancy: Unit {unit_label} in {building_name} "
            f"has been vacant for {days_vacant} days. "
            f"Please review pricing or contact support for listing options."
        )

        whatsapp_sent = self._send_whatsapp_alert(owner, message)
        email_sent = self._send_email_alert(
            owner, unit_label, f"Long-term Vacancy Alert: {days_vacant} days"
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Long-term vacancy alert sent for unit {unit_label} "
                f"({days_vacant} days): whatsapp={whatsapp_sent}, email={email_sent}"
            )
        )

    def _send_whatsapp_alert(self, owner: Any, message: str) -> bool:
        if not owner.whatsapp_number:
            return False
        try:
            lang = (
                getattr(getattr(owner, "profile", None), "language_preference", None)
                or "en"
            )
            translated = translate_msg(message, lang)
            audio_path = generate_voice_note(translated, lang)
            send_whatsapp_message(owner.whatsapp_number, translated)
            if audio_path:
                send_whatsapp_message(
                    owner.whatsapp_number, "🎧 Voice Note:", media_path=audio_path
                )
            return True
        except Exception as exc:
            logger.warning(
                f"Failed to send vacancy WhatsApp to {owner.whatsapp_number}: {exc}"
            )
            return False

    def _send_email_alert(
        self, owner: Any, unit_label: str, subject_suffix: str
    ) -> bool:
        if not owner.email:
            return False
        try:
            from django.core.mail import send_mail

            send_mail(
                subject=f"Vacant Unit Alert - {subject_suffix}",
                message=(
                    f"Dear {owner.get_full_name() or 'Owner'},\n\n"
                    f"This is an alert regarding your unit {unit_label}."
                ),
                from_email="no-reply@rentsecure.in",
                recipient_list=[owner.email],
                fail_silently=False,
            )
            return True
        except Exception as exc:
            logger.warning(
                f"Failed to send vacancy email to {owner.email} "
                f"for unit {unit_label}: {exc}"
            )
            return False
