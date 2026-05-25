import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

from properties.services.summary_service import send_monthly_rent_summary_email

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Send monthly rent collection summary to all property owners "
        "via email and WhatsApp."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Send summary for a specific user ID only',
        )
        parser.add_argument(
            '--no-whatsapp',
            action='store_true',
            help='Skip WhatsApp notifications',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        send_whatsapp = not options.get('no_whatsapp')

        if user_id:
            try:
                owner = User.objects.get(id=user_id)
                success = send_monthly_rent_summary_email(
                    owner, send_whatsapp=send_whatsapp
                )
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Summary sent to {owner.username} "
                            f"({owner.email})"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ Failed to send summary to {owner.username}"
                        )
                    )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User with ID {user_id} not found.")
                )
        else:
            # Send to all users who have at least one unit (property owners)
            owners = User.objects.filter(units__isnull=False).distinct()

            if not owners.exists():
                self.stdout.write(self.style.WARNING("No property owners found."))
                return

            self.stdout.write(
                f"Sending monthly summaries to {owners.count()} owner(s)..."
            )

            for owner in owners:
                try:
                    success = send_monthly_rent_summary_email(
                        owner, send_whatsapp=send_whatsapp
                    )
                    if success:
                        self.stdout.write(
                            self.style.SUCCESS(f"  ✅ {owner.username} ({owner.email})")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  ⚠️ {owner.username} - partial failure"
                            )
                        )
                except Exception as exc:
                    self.stdout.write(
                        self.style.ERROR(f"  ❌ {owner.username}: {exc}")
                    )

            self.stdout.write(self.style.SUCCESS("\n✅ Monthly summary job completed."))
