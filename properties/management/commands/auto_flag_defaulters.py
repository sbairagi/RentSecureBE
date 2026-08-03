from typing import TYPE_CHECKING, Any

from django.core.management.base import BaseCommand

from properties.services.rent_monitor_service import check_renter_defaulter_status
from rentsecure_be.type_compat import override

if TYPE_CHECKING:
    from core.models import User
else:
    from django.contrib.auth import get_user_model

    User = get_user_model()


class Command(BaseCommand):
    help = "Auto-flag and auto-revoke renters based on missed rents."

    @override
    def handle(self, *args: Any, **options: Any) -> None:
        updated = check_renter_defaulter_status()
        self.stdout.write(
            self.style.SUCCESS(
                f"Checked renter default status. Updated {updated} renter(s)."
            )
        )
