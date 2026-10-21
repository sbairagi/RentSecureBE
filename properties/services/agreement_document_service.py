"""Generation of the rent agreement document by the backend.

The owner never uploads an agreement PDF. The backend owns the document: it
reads the details captured on the agreement and renders them into a signed
looking PDF that is stored on the agreement record.

The service has two renderers:

* WeasyPrint renders the HTML template when the native libraries are
  available (the production servers and the Linux CI).
* :mod:`properties.services.simple_pdf` renders the same content as a plain
  text PDF everywhere else, so the workflow never dead-ends on a machine
  without the native libraries.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any

from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import timezone

from properties.models import RentAgreementDraft

from .simple_pdf import TextStyle, build_text_pdf

logger = logging.getLogger(__name__)

PAYMENT_MODE_LABELS: dict[str, str] = {
    "bank_transfer": "Bank transfer",
    "upi": "UPI",
    "cash": "Cash",
    "cheque": "Cheque",
    "card": "Card",
    "online": "Online payment",
    "other": "Other",
}

STATUS_LABELS: dict[str, str] = {
    "in_progress": "In progress",
    "draft": "Draft",
    "pending_signature": "Pending signature",
    "partially_signed": "Partially signed",
    "fully_signed": "Fully signed",
    "active": "Active",
    "expired": "Expired",
    "terminated": "Terminated",
}


def agreement_number(draft: RentAgreementDraft) -> str:
    """Return the stable, human readable number of an agreement."""
    if draft.agreement_number:
        return draft.agreement_number
    return f"RSA-{timezone.localdate().year}-{draft.pk or 0:05d}"


def _money(value: Decimal | int | float | None) -> str:
    """Format an amount the way the agreement reads it."""
    amount = Decimal(str(value or 0)).quantize(Decimal("0.01"))
    return f"INR {amount:,.2f}"


def _date_text(value: date | None) -> str:
    """Format a date for the document, or a dash when it is not set."""
    return value.strftime("%d %B %Y") if value else "-"


def build_agreement_context(draft: RentAgreementDraft) -> dict[str, Any]:
    """Collect everything the document needs from the agreement record."""
    owner = draft.user
    renter = draft.renter
    unit = draft.unit
    building = getattr(unit, "building", None)

    return {
        "agreement_number": agreement_number(draft),
        "generated_on": timezone.localdate(),
        "status_label": STATUS_LABELS.get(draft.status, draft.status),
        "owner": {
            "name": getattr(owner, "full_name", "") or owner.username,
            "email": owner.email,
            "phone": owner.phone,
        },
        "renter": {
            "name": renter.name,
            "email": renter.email,
            "phone": renter.phone,
        },
        "premises": {
            "building": getattr(building, "name", "") or "-",
            "unit": unit.unit,
            "type": unit.unit_type,
            "address": " ".join(
                part
                for part in (
                    unit.address_line,
                    getattr(building, "city", ""),
                    getattr(building, "state", ""),
                    unit.postal_code,
                )
                if part
            ),
        },
        "rent": {
            "monthly": _money(draft.monthly_rent or renter.rent_amount),
            "deposit": _money(draft.security_deposit),
            "due_day": draft.rent_due_day,
            "payment_mode": PAYMENT_MODE_LABELS.get(
                draft.payment_mode, draft.payment_mode.replace("_", " ").title()
            ),
            "notice_period_months": draft.notice_period_months,
        },
        "term": {
            "start_date": _date_text(draft.start_date or renter.start_date),
            "end_date": _date_text(draft.end_date or renter.end_date),
        },
        "jurisdiction": draft.jurisdiction
        or getattr(building, "city", "")
        or getattr(building, "state", "")
        or "Bengaluru, Karnataka",
        "witness_name": draft.witness_name,
        "special_clauses": draft.special_clauses,
        "signatures": {
            "owner": owner.get_full_name() if hasattr(owner, "get_full_name") else "",
            "renter": renter.name,
            "owner_signed_at": draft.owner_signed_at,
            "renter_signed_at": draft.renter_signed_at,
        },
    }


def _fallback_lines(context: dict[str, Any]) -> list[tuple[str, TextStyle]]:
    """Return the agreement as plain text lines for the simple renderer."""
    lines: list[tuple[str, TextStyle]] = [
        ("Rent Agreement", "title"),
        (f"Agreement number {context['agreement_number']}", "muted"),
        (f"Generated on {_date_text(context['generated_on'])}", "muted"),
        ("", "gap"),
        ("1. Parties", "heading"),
        (
            f"This agreement is made on {_date_text(context['generated_on'])} "
            f"between {context['owner']['name']} (the Owner) and "
            f"{context['renter']['name']} (the Renter).",
            "body",
        ),
        ("", "gap"),
        ("2. Premises", "heading"),
        (
            f"Flat {context['premises']['unit']}, {context['premises']['building']}, "
            f"{context['premises']['address']}.",
            "body",
        ),
        ("", "gap"),
        ("3. Term and rent", "heading"),
        (
            f"The lease runs from {context['term']['start_date']} to "
            f"{context['term']['end_date']}.",
            "body",
        ),
        (
            f"Monthly rent {context['rent']['monthly']}, security deposit "
            f"{context['rent']['deposit']}, payable on day "
            f"{context['rent']['due_day']} of every month by "
            f"{context['rent']['payment_mode']}.",
            "body",
        ),
        (
            f"Either party may end the lease with "
            f"{context['rent']['notice_period_months']} month(s) notice.",
            "body",
        ),
        ("", "gap"),
        ("4. Jurisdiction", "heading"),
        (
            f"This agreement is governed by the laws of {context['jurisdiction']}.",
            "body",
        ),
    ]
    if context.get("special_clauses"):
        lines += [
            ("", "gap"),
            ("5. Special clauses", "heading"),
            (context["special_clauses"], "body"),
        ]
    lines += [
        ("", "gap"),
        ("Signatures", "heading"),
        (
            f"Owner: {context['signatures']['owner'] or '-'} "
            f"({context['signatures']['owner_signed_at'] or 'pending'})",
            "body",
        ),
        (
            f"Renter: {context['signatures']['renter'] or '-'} "
            f"({context['signatures']['renter_signed_at'] or 'pending'})",
            "body",
        ),
    ]
    if context.get("witness_name"):
        lines.append(f"Witness: {context['witness_name']}", "body")
    return lines


def render_agreement_pdf(context: dict[str, Any]) -> bytes:
    """Render the agreement and return the PDF bytes."""
    try:
        from weasyprint import HTML  # noqa: PLC0415

        html = render_to_string("agreement_document.html", context)
        return bytes(HTML(string=html).write_pdf())
    except Exception as exc:  # pragma: no cover - depends on the host
        logger.info("WeasyPrint is unavailable, using the plain PDF renderer: %s", exc)
    return build_text_pdf(_fallback_lines(context))


def generate_agreement_document(
    draft: RentAgreementDraft, save: bool = True
) -> RentAgreementDraft:
    """Render the agreement document and store it on the agreement.

    The agreement moves to ``draft`` when the document is ready. A failure
    is recorded in ``generation_error`` and the agreement stays
    ``in_progress`` so the owner can try again.
    """
    context = build_agreement_context(draft)
    number = agreement_number(draft)
    try:
        pdf = render_agreement_pdf(context)
    except Exception as exc:
        logger.exception("Could not render the agreement document")
        draft.generation_error = str(exc)[:255]
        if save:
            draft.status = RentAgreementDraft.AgreementStatus.IN_PROGRESS
            draft.save(update_fields=["generation_error", "status"])
        return draft

    if not pdf:
        draft.generation_error = "The document renderer returned an empty file."
        if save:
            draft.status = RentAgreementDraft.AgreementStatus.IN_PROGRESS
            draft.save(update_fields=["generation_error", "status"])
        return draft

    draft.file.save(f"agreement-{number}.pdf", ContentFile(pdf), save=False)
    draft.agreement_number = number
    draft.document_generated_at = timezone.now()
    draft.generation_error = ""
    draft.status = RentAgreementDraft.AgreementStatus.DRAFT
    if save:
        draft.save(
            update_fields=[
                "file",
                "agreement_number",
                "document_generated_at",
                "generation_error",
                "status",
            ]
        )
    return draft
