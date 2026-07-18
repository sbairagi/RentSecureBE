from typing import TYPE_CHECKING, Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from properties.services.summary_service import send_monthly_rent_summary_email
from shared.type_compat import override

if TYPE_CHECKING:
    from core.models import User
else:
    User = get_user_model()


class Command(BaseCommand):
    help = (
        "Send monthly rent collection summary to all property owners via "
        "email and WhatsApp."
    )

    @override
    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--user-id",
            type=int,
            help="Send summary for a specific user ID only",
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
            self._send_to_single_user(user_id, send_whatsapp)
        else:
            self._send_to_all_owners(send_whatsapp)

    def _send_to_single_user(self, user_id: int, send_whatsapp: bool) -> None:
        try:
            owner = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with ID {user_id} not found."))
            return

        success = send_monthly_rent_summary_email(owner, send_whatsapp=send_whatsapp)
        if success:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Summary sent to {owner.username} ({owner.email})"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed to send summary to {owner.username}")
            )

    def _send_to_all_owners(self, send_whatsapp: bool) -> None:
        owners = User.objects.filter(units__isnull=False).distinct()

        if not owners.exists():
            self.stdout.write(self.style.WARNING("No property owners found."))
            return

        self.stdout.write(f"Sending monthly summaries to {owners.count()} owner(s)...")

        for owner in owners:
            self._send_summary_to_owner(owner, send_whatsapp)

        self.stdout.write(self.style.SUCCESS("\n✅ Monthly summary job completed."))

    def _send_summary_to_owner(self, owner: User, send_whatsapp: bool) -> None:
        try:
            success = send_monthly_rent_summary_email(
                owner, send_whatsapp=send_whatsapp
            )
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"  ❌ {owner.username}: {exc}"))
            return

        if success:
            self.stdout.write(
                self.style.SUCCESS(f"  ✅ {owner.username} ({owner.email})")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"  ⚠️ {owner.username} - partial failure")
            )
