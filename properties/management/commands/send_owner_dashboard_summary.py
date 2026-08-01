from typing import TYPE_CHECKING, Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from properties.services.owner_dashboard_summary_service import (
    run_daily_owner_summaries,
    run_weekly_owner_summaries,
    send_summary_to_owner,
)
from rentsecure_be.type_compat import override

if TYPE_CHECKING:
    from core.models import User
else:
    User = get_user_model()


class Command(BaseCommand):
    help = (
        "Send WhatsApp dashboard summary to property owners "
        "covering vacant units, pending rents, overdue taxes, and flagged renters."
    )

    @override
    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--user-id",
            type=int,
            help="Send summary for a specific user ID only",
        )
        parser.add_argument(
            "--frequency",
            type=str,
            choices=["daily", "weekly"],
            default="daily",
            help="Summary frequency (default: daily)",
        )

    @override
    def handle(self, *args: Any, **options: Any) -> None:
        user_id = options.get("user_id")
        frequency = options.get("frequency", "daily")

        if user_id:
            self._send_to_single_user(user_id)
        else:
            self._send_to_all_owners(frequency)

    def _send_to_single_user(self, user_id: int) -> None:
        try:
            owner = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with ID {user_id} not found."))
            return

        success = send_summary_to_owner(owner)
        if success:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Dashboard summary sent to {owner.username}")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed to send summary to {owner.username}")
            )

    def _send_to_all_owners(self, frequency: str) -> None:
        owners = User.objects.filter(units__isnull=False).distinct()

        if not owners.exists():
            self.stdout.write(self.style.WARNING("No property owners found."))
            return

        self.stdout.write(
            f"Sending {frequency} dashboard summaries to {owners.count()} owner(s)..."
        )

        if frequency == "weekly":
            sent_count = run_weekly_owner_summaries()
        else:
            sent_count = run_daily_owner_summaries()

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ {frequency.capitalize()} dashboard summary job completed. "
                f"Sent {sent_count} notification(s)."
            )
        )
