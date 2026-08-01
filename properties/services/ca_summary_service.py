"""CA summary export service.

Generates accountant-friendly CSV and JSON summaries from rent and tax data.
"""

from __future__ import annotations

import csv
import io
import json
from typing import TYPE_CHECKING, Any

from django.db.models import QuerySet

if TYPE_CHECKING:
    from core.models import User
    from properties.models import PropertyTaxRecord, RentRecord


def _get_rents(owner: User, start_date: str, end_date: str) -> QuerySet[RentRecord]:
    from properties.models import RentRecord

    return RentRecord.objects.filter(
        unit__owner=owner,
        paid_on__range=[start_date, end_date],
    ).select_related("renter", "unit")


def _get_taxes(
    owner: User, start_date: str, end_date: str
) -> QuerySet[PropertyTaxRecord]:
    from properties.models import PropertyTaxRecord

    return PropertyTaxRecord.objects.filter(
        property__owner=owner,
        paid_date__range=[start_date, end_date],
    ).select_related("property")


def _property_label(rent: RentRecord) -> str:
    unit = rent.unit
    if unit is None:
        return ""
    building = getattr(unit, "building", None)
    parts = [
        getattr(building, "name", "") or "",
        getattr(unit, "unit", "") or "",
        getattr(unit, "address_line", "") or "",
        getattr(unit, "city", "") or "",
    ]
    return ", ".join(part for part in parts if part)


def _build_rows(owner: User, start_date: str, end_date: str) -> list[dict[str, Any]]:
    rents = _get_rents(owner, start_date, end_date)
    taxes = _get_taxes(owner, start_date, end_date)
    tax_map = {str(tax.property_id): tax for tax in taxes}

    rows: list[dict[str, Any]] = []
    for rent in rents:
        building = getattr(rent.unit, "building", None)
        property_id = str(building.pk) if building is not None else ""
        tax = tax_map.get(property_id)
        rows.append(
            {
                "property": _property_label(rent),
                "renter": rent.renter.name if rent.renter else "",
                "rent_amount": float(rent.amount or 0),
                "rent_payment_date": (
                    rent.paid_on.strftime("%Y-%m-%d") if rent.paid_on else ""
                ),
                "rent_status": rent.status or "",
                "payout_status": rent.payout_status or "",
                "tax_amount": float(tax.amount or 0) if tax else 0.0,
                "tax_payment_date": (
                    tax.paid_date.strftime("%Y-%m-%d") if tax and tax.paid_date else ""
                ),
                "tax_due_date": (
                    tax.due_date.strftime("%Y-%m-%d") if tax and tax.due_date else ""
                ),
            }
        )
    return rows


def generate_ca_summary_csv(owner: User, start_date: str, end_date: str) -> bytes:
    rows = _build_rows(owner, start_date, end_date)
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "property",
            "renter",
            "rent_amount",
            "rent_payment_date",
            "rent_status",
            "payout_status",
            "tax_amount",
            "tax_payment_date",
            "tax_due_date",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def generate_ca_summary_json(owner: User, start_date: str, end_date: str) -> bytes:
    rows = _build_rows(owner, start_date, end_date)
    payload = {
        "owner": owner.get_full_name() or owner.username,
        "start_date": start_date,
        "end_date": end_date,
        "records": rows,
    }
    return json.dumps(payload, indent=2).encode("utf-8")
