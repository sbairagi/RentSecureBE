from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from properties.services.ca_summary_service import (
    generate_ca_summary_csv,
    generate_ca_summary_json,
)
from rentsecure_be.type_compat import override

User = get_user_model()


class Command(BaseCommand):
    help = "Export CA summary sheet as CSV and JSON for owners."

    @override
    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--start", type=str, required=True, help="Start date yyyy-mm-dd"
        )
        parser.add_argument(
            "--end", type=str, required=True, help="End date yyyy-mm-dd"
        )
        parser.add_argument(
            "--owner-id", type=int, help="Limit export to a specific owner"
        )

    @override
    def handle(self, *args: Any, **options: Any) -> None:
        start_date = options["start"]
        end_date = options["end"]

        owners = User.objects.filter(units__isnull=False).distinct()
        if options.get("owner-id"):
            owners = owners.filter(id=options["owner-id"])

        if not owners.exists():
            self.stdout.write(self.style.WARNING("No property owners found."))
            return

        for owner in owners:
            base_name = f"ca_summary_{start_date}_to_{end_date}_{owner.username}"
            csv_bytes = generate_ca_summary_csv(owner, start_date, end_date)
            json_bytes = generate_ca_summary_json(owner, start_date, end_date)

            csv_path = f"{base_name}.csv"
            json_path = f"{base_name}.json"

            with open(csv_path, "wb") as csv_file:
                csv_file.write(csv_bytes)
            with open(json_path, "wb") as json_file:
                json_file.write(json_bytes)

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ {owner.username}: CSV={csv_path}, JSON={json_path}"
                )
            )
