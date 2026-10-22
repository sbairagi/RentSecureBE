"""Rent receipt presentation model.

The receipt card is rendered in three places:

* ``documents.views.GenerateRentReceiptPdfViewSet.pdf_receipt`` — the PDF
  the owner downloads from the web client.
* ``properties.services.receipt_service.generate_rent_receipt_pdf`` — the
  PDF attached to the receipt email sent to the renter.
* ``properties.services.rent_collection_service`` — the PDF attached to a
  part-payment receipt.

All of them render ``documents/templates/receipt_card.html`` so the
downloaded receipt, the emailed receipt and the part receipt are
identical.  The web client (``rentsecure-web``) mirrors the same card,
which is why every derived value (labels, amounts, dates, file name) is
computed here once instead of being repeated inside the template.
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
    "partial": "partial",
}

DASH = "—"

# The month names are fixed on purpose: ``strftime("%B")`` follows the locale
# of the machine the server runs on, so the very same month could be written
# "October" in one deployment and "Oktober" in another.  The ledger, the
# receipt and the reminder all speak the same names because they share this
# list.
MONTH_NAMES: tuple[str, ...] = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


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
    total_paid: str
    net_balance: str
    total_amount: str
    total_label: str
    subtitle: str
    part_label: str
    is_part: bool
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


def month_name(month: int) -> str:
    """The name of a month (1-12), independent of the locale of the server.

    Args:
        month: The number of the month.

    Returns:
        The name of the month.
    """
    return MONTH_NAMES[month - 1]


def format_period(value: Any) -> str:
    """Format the rent period the way the web client renders it."""
    if not value:
        return DASH
    return f"{month_name(value.month)} {value.year}"


def _period_slug(rent_record: Any) -> str:
    due_date = rent_record.due_date
    return due_date.strftime("%Y%m") if due_date else "000000"


def receipt_filename(rent_record: Any, part: Any = None) -> str:
    """File name used for the downloaded and the emailed receipt.

    ``rent_receipt_<id>_<YYYYMM>.pdf`` for the month, and
    ``rent_receipt_<id>_<YYYYMM>_part<N>.pdf`` for a single part.
    """
    period = _period_slug(rent_record)
    if part is None:
        return f"rent_receipt_{rent_record.id}_{period}.pdf"
    number = _part_number(rent_record, part)
    return f"rent_receipt_{rent_record.id}_{period}_part{number}.pdf"


def _part_number(rent_record: Any, part: Any) -> int:
    """1-based position of a part inside its rent record."""
    parts = list(rent_record.parts.all())
    for index, entry in enumerate(parts):
        if entry.id == part.id:
            return index + 1
    return len(parts)


def _cumulative_paid(rent_record: Any, part: Any) -> Decimal:
    """Total received up to and including ``part``."""
    total = Decimal("0")
    for entry in rent_record.parts.all():
        total += entry.amount or Decimal("0")
        if entry.id == part.id:
            break
    return total


def receipt_lines(rent_record: Any, part: Any = None) -> list[tuple[str, str]]:
    """Return the receipt as plain text lines for the simple PDF renderer.

    The renderer is the fallback for the hosts where WeasyPrint cannot run
    because its native libraries are missing.

    Args:
        rent_record: The :class:`properties.models.RentRecord` to describe.
        part: Optional :class:`properties.models.RentRecordPart` — when
            given the lines describe that instalment instead of the month.

    Returns:
        The lines of the receipt as ``(text, style)`` pairs.
    """
    receipt = build_receipt(rent_record, part)
    lines: list[tuple[str, str]] = [
        ("SecureNest - Rent receipt", "title"),
        (receipt.subtitle, "muted"),
        ("", "gap"),
        (f"Receipt no.: {receipt.receipt_no}", "body"),
        (f"Payee: {receipt.payee}", "body"),
        (f"Property: {receipt.property}", "body"),
        (f"Rent period: {receipt.period}", "body"),
    ]
    if receipt.part_label:
        lines.append((f"Part payment: {receipt.part_label}", "body"))
    lines.extend(
        [
            (f"Due date: {receipt.due_date}", "body"),
            (f"Paid on: {receipt.paid_on}", "body"),
            (f"Payment mode: {receipt.payment_method}", "body"),
            ("", "gap"),
            ("Amounts", "heading"),
            (f"Dues amount: {receipt.dues_amount}", "body"),
            (f"Paid amount: {receipt.paid_amount}", "body"),
            (f"Total paid: {receipt.total_paid}", "body"),
            (f"Net balance: {receipt.net_balance}", "body"),
            ("", "gap"),
            (f"{receipt.total_label}: {receipt.total_amount}", "heading"),
            (f"Status: {receipt.status_label}", "body"),
        ]
    )
    if receipt.transaction_id:
        lines.append((f"Transaction: {receipt.transaction_id}", "body"))
    lines.append(("", "gap"))
    lines.append(("Generated by SecureNest.", "muted"))
    return lines


def build_receipt(rent_record: Any, part: Any = None) -> Receipt:
    """Build the receipt card model for a rent record (or one of its parts).

    Args:
        rent_record: The :class:`properties.models.RentRecord` to describe.
        part: Optional :class:`properties.models.RentRecordPart` — when
            given the card describes that instalment instead of the whole
            month.

    Returns:
        A :class:`Receipt` holding every label and amount the card shows.
    """
    unit = rent_record.unit
    building_name = getattr(unit, "building_name", "") or ""
    unit_label = getattr(unit, "unit", "") or ""
    property_label = " · ".join(piece for piece in (building_name, unit_label) if piece)

    renter = rent_record.renter
    payee = getattr(renter, "name", "") or DASH

    dues = rent_record.total_due
    received = rent_record.amount_paid or Decimal("0")
    status = str(rent_record.status or "pending").lower()
    payment_method = str(rent_record.payment_method or "").lower()
    parts = list(rent_record.parts.all())

    filename = receipt_filename(rent_record, part)
    subtitle = "Rent receipt"
    part_label = ""
    total_label = "Amount paid by tenant"
    paid_on = format_date(rent_record.paid_on)
    method = PAYMENT_METHOD_LABELS.get(payment_method, DASH)
    paid_amount = received
    total_paid = received
    outstanding = dues - received
    total_amount = received
    status_label = STATUS_LABELS.get(status, (status[:1].upper() + status[1:]) or DASH)
    status_tone = STATUS_TONES.get(status, "pending")
    transaction_id = getattr(rent_record, "transaction_id", "") or ""

    if part is not None:
        number = _part_number(rent_record, part)
        count = len(parts)
        cumulative = _cumulative_paid(rent_record, part)
        part_label = f"Part {number} of {count}"
        subtitle = f"Rent receipt · Part {number} of {count}"
        total_label = "Amount received (this part)"
        paid_on = format_date(part.paid_on)
        method = PAYMENT_METHOD_LABELS.get(str(part.payment_method or "").lower(), DASH)
        paid_amount = part.amount or Decimal("0")
        total_paid = cumulative
        outstanding = dues - cumulative
        total_amount = paid_amount
        status_label = "Part paid"
        status_tone = "partial"
        transaction_id = part.transaction_id or ""
    elif parts:
        last = parts[-1]
        part_label = f"{len(parts)} parts"
        paid_on = format_date(last.paid_on)
        method = PAYMENT_METHOD_LABELS.get(
            str(last.payment_method or "").lower(), method
        )

    net_balance = DASH if outstanding <= 0 else format_inr(outstanding)

    return Receipt(
        receipt_no=filename,
        filename=filename,
        payee=payee,
        property=property_label or DASH,
        period=format_period(rent_record.due_date),
        due_date=format_date(rent_record.due_date),
        paid_on=paid_on,
        payment_method=method,
        dues_amount=format_inr(dues),
        paid_amount=format_inr(paid_amount),
        total_paid=format_inr(total_paid),
        net_balance=net_balance,
        total_amount=format_inr(total_amount),
        total_label=total_label,
        subtitle=subtitle,
        part_label=part_label,
        is_part=part is not None,
        status=status,
        status_label=status_label,
        status_tone=status_tone,
        transaction_id=transaction_id,
        notes=getattr(rent_record, "notes", "") or "",
    )
