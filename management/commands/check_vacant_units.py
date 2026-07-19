import logging
from datetime import date
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from notification.services.notification_service import NotificationService
from properties.models import Unit
from shared.type_compat import override

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Notify property owners when units remain vacant for 30 or more days."

    @override
    def handle(self, *args: Any, **options: Any) -> None:
        today = timezone.now().date()
        units = Unit.objects.filter(is_vacant=True, last_vacated_at__isnull=False)

        if not units.exists():
            self.stdout.write(
                self.style.NOTICE("No vacant units found with a vacancy date.")
            )
            return

        for unit in units:
            self._process_vacant_unit(unit, today)

    def _process_vacant_unit(self, unit: Unit, today: date) -> None:
        last_vacated: date | None = unit.last_vacated_at
        if last_vacated is None:
            return
        days_vacant = (today - last_vacated).days
        if days_vacant < 30:
            return

        owner = unit.owner
        building_name = (
            unit.building.name
            if unit.building
            else unit.building_name or "your property"
        )
        unit_label = unit.unit
        message = f"📭 Your unit {unit_label} in {building_name} has been vacant for {days_vacant} days."

        whatsapp_sent = self._send_whatsapp_alert(owner, message)
        email_sent = self._send_email_alert(owner, unit_label, message)

        self.stdout.write(
            self.style.SUCCESS(
                f"Vacancy alert sent for unit {unit_label} ({days_vacant} days): whatsapp={whatsapp_sent}, email={email_sent}"
            )
        )

    def _send_whatsapp_alert(self, owner: Any, message: str) -> bool:
        if not owner.whatsapp_number:
            return False
        return NotificationService().send_whatsapp_message(
            owner.whatsapp_number, message
        )

    def _send_email_alert(self, owner: Any, unit_label: str, message: str) -> bool:
        if not owner.email:
            return False
        try:
            from notification.services.notification_service import NotificationService

            return NotificationService().send_email(
                subject="Vacant Unit Alert",
                message=message,
                recipient_list=[owner.email],
                from_email="no-reply@rentsecure.in",
            )
        except Exception as exc:
            logger.warning(
                f"Failed to send vacancy email to {owner.email} "
                f"for unit {unit_label}: {exc}"
            )
            self.stderr.write(
                f"Failed to send vacancy email to {owner.email} "
                f"for unit {unit_label}: {exc}"
            )
            return False
