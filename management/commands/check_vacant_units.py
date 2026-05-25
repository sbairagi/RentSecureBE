import logging

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)

from notification.services.whatsapp_service import send_whatsapp_message
from properties.models import Unit


class Command(BaseCommand):
    help = "Notify property owners when units remain vacant for 30 or more days."

    def handle(self, *args, **options):
        today = timezone.now().date()
        units = Unit.objects.filter(current_renter__isnull=True, last_vacated_at__isnull=False)

        if not units.exists():
            self.stdout.write(self.style.NOTICE("No vacant units found with a vacancy date."))
            return

        for unit in units:
            days_vacant = (today - unit.last_vacated_at).days
            if days_vacant < 30:
                continue

            owner = unit.owner
            building_name = unit.building.name if unit.building else unit.building_name or "your property"
            unit_label = unit.unit
            message = (
                f"📭 Your unit {unit_label} in {building_name} has been vacant for {days_vacant} days."
            )

            whatsapp_sent = False
            email_sent = False

            if hasattr(owner, 'profile') and getattr(owner.profile, 'whatsapp_number', None):
                whatsapp_sent = send_whatsapp_message(owner.profile.whatsapp_number, message)

            if owner.email:
                try:
                    send_mail(
                        subject="Vacant Unit Alert",
                        message=message,
                        from_email="no-reply@rentsecure.in",
                        recipient_list=[owner.email],
                        fail_silently=False,
                    )
                    email_sent = True
                except Exception as exc:
                    logger.warning(
                        f"Failed to send vacancy email to {owner.email} "
                        f"for unit {unit_label}: {exc}"
                    )
                    self.stderr.write(
                        f"Failed to send vacancy email to {owner.email} "
                        f"for unit {unit_label}: {exc}"
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Vacancy alert sent for unit {unit_label} ({days_vacant} days): whatsapp={whatsapp_sent}, email={email_sent}"
                )
            )
