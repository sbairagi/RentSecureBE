"""Rent receipt presentation model.

The receipt card is rendered in two places:

* ``documents.views.GenerateRentReceiptPdfViewSet.pdf_receipt`` — the PDF
  the owner downloads from the web client.
* ``properties.services.receipt_service.generate_rent_receipt_pdf`` — the
  PDF attached to the receipt email sent to the renter.

Both render ``documents/templates/receipt_card.html`` so the downloaded
receipt and the emailed receipt are identical.  The web client
(``rentsecure-web``) mirrors the same card, which is why every derived
value (labels, amounts, dates, file name) is computed here once instead of
being repeated inside the template.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

PAYMENT_METHOD_LABELS: dict[str, str] = {
    "cash": "Cash",
    "bank_transfer": "Bank transfer",
    "upi": "UPI",
    "cheque": "Cheque",
    "card": "Card",
    "online": "Online payment",
    "other": "Other",
}

STATUS_LABELS: dict[str, str] = {
    "paid": "Paid",
    "pending": "Pending",
    "overdue": "Overdue",
    "cancelled": "Cancelled",
}

# Tones drive the status pill colours on the card.
STATUS_TONES: dict[str, str] = {
    "paid": "paid",
    "pending": "pending",
    "overdue": "overdue",
    "cancelled": "overdue",
}

DASH = "—"


@dataclass(frozen=True)
class Receipt:
    """Every value the receipt card needs to render."""

    receipt_no: str
    filename: str
    payee: str
    property: str
    period: str
    due_date: str
    paid_on: str
    payment_method: str
    dues_amount: str
    paid_amount: str
    net_balance: str
    total_amount: str
    status: str
    status_label: str
    status_tone: str
    transaction_id: str
    notes: str


def group_indian(amount: int) -> str:
    """Format an integer with Indian digit grouping (1,23,456)."""
    if amount >= 100_000:
        head, tail = str(amount)[:-3], str(amount)[-3:]
        parts: list[str] = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        return ",".join(parts) + "," + tail
    return f"{amount:,}"


def format_inr(value: Any) -> str:
    """Format a money value the way the web client renders it (₹28,000)."""
    amount = int(Decimal(value or 0).quantize(Decimal("1")))
    return f"₹{group_indian(amount)}"


def format_date(value: Any) -> str:
    """Format a date the way the web client renders it (05 Oct 2026)."""
    if not value:
        return DASH
    return value.strftime("%d %b %Y").replace(" 0", " ")


def format_period(value: Any) -> str:
    """Format the rent period the way the web client renders it."""
    if not value:
        return DASH
    return value.strftime("%B %Y")


def receipt_filename(rent_record: Any) -> str:
    """File name used for the downloaded and the emailed receipt."""
    due_date = rent_record.due_date
    period = due_date.strftime("%Y%m") if due_date else "000000"
    return f"rent_receipt_{rent_record.id}_{period}.pdf"


def build_receipt(rent_record: Any) -> Receipt:
    """Build the receipt card model for a rent record.

    Args:
        rent_record: The :class:`properties.models.RentRecord` to describe.

    Returns:
        A :class:`Receipt` holding every label and amount the card shows.
    """
    unit = rent_record.unit
    building_name = getattr(unit, "building_name", "") or ""
    unit_label = getattr(unit, "unit", "") or ""
    property_label = " · ".join(part for part in (building_name, unit_label) if part)

    renter = rent_record.renter
    payee = getattr(renter, "name", "") or DASH

    amount = Decimal(rent_record.amount or 0)
    late_fee = Decimal(rent_record.late_fee or 0)
    discount = Decimal(rent_record.discount or 0)

    dues = amount + late_fee - discount
    is_paid = str(rent_record.status or "").lower() == "paid"
    paid = amount if is_paid else Decimal("0")
    outstanding = dues - paid
    net_balance = DASH if outstanding <= 0 else format_inr(outstanding)

    status = str(rent_record.status or "pending").lower()
    payment_method = str(rent_record.payment_method or "").lower()

    return Receipt(
        receipt_no=receipt_filename(rent_record),
        filename=receipt_filename(rent_record),
        payee=payee,
        property=property_label or DASH,
        period=format_period(rent_record.due_date),
        due_date=format_date(rent_record.due_date),
        paid_on=format_date(rent_record.paid_on),
        payment_method=PAYMENT_METHOD_LABELS.get(payment_method, DASH),
        dues_amount=format_inr(dues),
        paid_amount=format_inr(paid),
        net_balance=net_balance,
        total_amount=format_inr(paid),
        status=status,
        status_label=STATUS_LABELS.get(
            status, (status[:1].upper() + status[1:]) or DASH
        ),
        status_tone=STATUS_TONES.get(status, "pending"),
        transaction_id=getattr(rent_record, "transaction_id", "") or "",
        notes=getattr(rent_record, "notes", "") or "",
    )
