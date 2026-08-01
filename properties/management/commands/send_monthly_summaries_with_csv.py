import calendar
from typing import TYPE_CHECKING, Any

from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.utils import timezone

from properties.services.ca_summary_service import generate_ca_summary_csv
from rentsecure_be.type_compat import override

if TYPE_CHECKING:
    from core.models import User
else:
    User = get_user_model()


class Command(BaseCommand):
    help = "Send monthly rent + tax summary to each owner as a CSV email attachment."

    @override
    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--owner-id",
            type=int,
            help="Send summary for a specific owner ID only",
        )
        parser.add_argument(
            "--month",
            type=str,
            help="Target month in YYYY-MM format. Defaults to previous month.",
        )

    @override
    def handle(self, *args: Any, **options: Any) -> None:
        target_month = options.get("month")
        if target_month:
            try:
                year, month = [int(part) for part in target_month.split("-")]
                start_date = timezone.datetime(year, month, 1).date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR("--month must be in YYYY-MM format.")
                )
                return
        else:
            today = timezone.now().date()
            previous_month = today.month - 1 or 12
            previous_year = today.year if today.month > 1 else today.year - 1
            start_date = today.replace(year=previous_year, month=previous_month, day=1)

        end_date = self._last_day_of_month(start_date)

        owners = User.objects.filter(units__isnull=False).distinct()
        if options.get("owner-id"):
            owners = owners.filter(id=options["owner-id"])

        if not owners.exists():
            self.stdout.write(self.style.WARNING("No property owners found."))
            return

        sent = 0
        skipped = 0
        for owner in owners:
            if not getattr(owner, "email", None):
                skipped += 1
                continue

            prefs = getattr(owner, "notification_preference", None)
            if prefs is not None and not getattr(prefs, "monthly_summary_email", True):
                skipped += 1
                continue

            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            from properties.models import RentRecord  # nosonar

            has_rents = RentRecord.objects.filter(
                unit__owner=owner, paid_on__range=[start_str, end_str]
            ).exists()

            if not has_rents:
                skipped += 1
                continue

            try:
                csv_bytes = generate_ca_summary_csv(owner, start_str, end_str)
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"  ❌ {owner.username}: failed to generate CSV: {exc}"
                    )
                )
                continue

            subject = f"📊 Monthly Property Summary - {start_date.strftime('%B %Y')}"
            body = (
                f"Hi {owner.get_full_name() or owner.email},\n\n"
                f"Please find attached your monthly rent and tax summary "
                f"for {start_date.strftime('%B %Y')}.\n\n"
                f"Regards,\nRentSecure Team"
            )
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email="no-reply@rentsecure.in",
                to=[owner.email],
            )
            filename = (
                f"{owner.username}_summary_" f"{start_date.strftime('%Y_%m')}.csv"
            )
            email.attach(filename, csv_bytes, "text/csv")
            email.send(fail_silently=False)
            sent += 1
            self.stdout.write(
                self.style.SUCCESS(f"  ✅ {owner.username} ({owner.email})")
            )

        self.stdout.write(
            self.style.SUCCESS(
                "\n✅ Monthly summary email job completed. "
                f"Sent={sent}, Skipped={skipped}"
            )
        )

    @staticmethod
    def _last_day_of_month(start_date) -> "timezone.datetime":
        last_day = calendar.monthrange(start_date.year, start_date.month)[1]
        return start_date.replace(day=last_day)
