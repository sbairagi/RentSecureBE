from django.core.management.base import BaseCommand

from properties.services.extra_charge_service import generate_monthly_extra_charges


class Command(BaseCommand):
    help = (
        "Generate recurring monthly extra charges such as electricity and "
        "maintenance for active renters."
    )

    def handle(self, *args, **options):
        created = generate_monthly_extra_charges()
        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Created {len(created)} extra charge(s).")
            )
        else:
            self.stdout.write(
                self.style.WARNING("No new extra charges generated for this month.")
            )
