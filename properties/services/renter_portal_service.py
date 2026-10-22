"""The numbers of the renter portal.

The renter screens are built on three questions:

* how much rent is open, how much was paid and what is the next due date,
* what is the state of the requests of the flat,
* where does the police verification stand.

The answers are computed here, on the server, so every screen of the renter
app shows the same numbers and the business rules live in one place.
"""

from __future__ import annotations

from typing import Any

from django.db.models import Q
from django.utils import timezone

from properties.models import (
    MaintenanceRequest,
    PoliceVerification,
    RentAgreementDraft,
    Renter,
    RentRecord,
)

# The support of SecureNest — the last contact of the renter.
SUPPORT_PHONE = "+91 80000 00000"
SUPPORT_EMAIL = "support@securenest.in"


def effective_status(record: RentRecord, today: Any | None = None) -> str:
    """Return the status of the record as the renter should read it.

    A month that is still open after its due date reads as overdue, even when
    the stored status has not been moved yet — the renter should not have to
    wait for a scheduled job to learn that the rent is late.
    """
    today = today or timezone.localdate()
    if record.status == RentRecord.Status.PENDING and record.due_date < today:
        return RentRecord.Status.OVERDUE
    return record.status


def rent_summary(renter: Renter, today: Any | None = None) -> dict[str, Any]:
    """Return the rent picture of the renter."""
    today = today or timezone.localdate()
    records = RentRecord.objects.filter(renter=renter).order_by("-due_date")

    open_records = records.filter(
        status__in=[RentRecord.Status.PENDING, RentRecord.Status.OVERDUE]
    )
    outstanding = sum(
        (record.balance for record in open_records),
        start=0,
    )
    current = open_records.first()

    year = today.year
    year_records = [record for record in records if record.due_date.year == year]
    paid_this_year = sum(
        (record.amount_paid or 0 for record in year_records),
        start=0,
    )
    paid_records = [
        record for record in year_records if record.status == RentRecord.Status.PAID
    ]

    next_due = None
    if current is not None:
        next_due = current.due_date
    else:
        future = [
            record
            for record in records
            if record.status == RentRecord.Status.PENDING and record.due_date >= today
        ]
        if future:
            next_due = future[-1].due_date

    late = [
        record
        for record in open_records
        if effective_status(record, today) == RentRecord.Status.OVERDUE
    ]
    oldest_late = min((record.due_date for record in late), default=None)

    return {
        "rent_amount": str(renter.rent_amount or 0),
        "due_this_month": str(current.total_due) if current is not None else "0",
        "outstanding": str(outstanding),
        "outstanding_months": open_records.count(),
        "paid_this_year": str(paid_this_year),
        "months_paid": len(paid_records),
        "months_total": len(year_records),
        "next_due_date": next_due.isoformat() if next_due else None,
        "next_due_in_days": (next_due - today).days if next_due else None,
        "overdue": bool(late),
        "overdue_days": (today - oldest_late).days if oldest_late else 0,
        "current_record_id": current.id if current is not None else None,
    }


def maintenance_summary(renter: Renter) -> dict[str, Any]:
    """Return the state of the requests of the flat of the renter."""
    requests_qs = MaintenanceRequest.objects.filter(
        Q(renter=renter) | Q(unit=renter.unit)
    )
    open_count = requests_qs.filter(
        status__in=[
            MaintenanceRequest.Status.OPEN,
            MaintenanceRequest.Status.IN_PROGRESS,
            MaintenanceRequest.Status.WAITING,
        ]
    ).count()
    latest = requests_qs.order_by("-reported_at").first()
    return {
        "total": requests_qs.count(),
        "open": open_count,
        "in_progress": requests_qs.filter(
            status=MaintenanceRequest.Status.IN_PROGRESS
        ).count(),
        "resolved": requests_qs.filter(
            status=MaintenanceRequest.Status.RESOLVED
        ).count(),
        "latest": (
            {
                "id": latest.id,
                "title": latest.title,
                "status": latest.status,
                "status_label": latest.get_status_display(),
                "reported_at": latest.reported_at.isoformat(),
            }
            if latest is not None
            else None
        ),
    }


def verification_summary(renter: Renter) -> dict[str, Any]:
    """Return the state of the police verification of the renter."""
    verification = PoliceVerification.objects.filter(renter=renter).first()
    if verification is None:
        return {
            "id": None,
            "status": PoliceVerification.PoliceVerificationStatus.NOT_STARTED,
            "status_label": "Not started",
            "submitted_at": None,
            "verified_at": None,
            "reviewed_at": None,
            "reviewed_by_name": "",
            "file_name": "",
            "file_size": "",
            "rejection_reason": "",
        }
    return {
        "id": verification.id,
        "status": verification.status,
        "status_label": verification.get_status_display(),
        "submitted_at": (
            verification.submitted_at.isoformat() if verification.submitted_at else None
        ),
        "verified_at": (
            verification.verified_at.isoformat() if verification.verified_at else None
        ),
        "reviewed_at": (
            verification.reviewed_at.isoformat() if verification.reviewed_at else None
        ),
        "reviewed_by_name": (
            getattr(verification.reviewed_by, "full_name", "")
            or getattr(verification.reviewed_by, "username", "")
            if verification.reviewed_by
            else ""
        ),
        "file_name": (
            verification.file.name.rsplit("/", 1)[-1] if verification.file else ""
        ),
        "file_size": file_size_label(verification.file),
        "rejection_reason": verification.rejection_reason or "",
    }


def file_size_label(field: Any) -> str:
    """Return the size of an uploaded file in a readable way."""
    if field is None:
        return ""
    try:
        size = field.size
    except (OSError, ValueError):
        return ""
    if not size:
        return ""
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{round(size / 1024)} KB"
    return f"{round(size / (1024 * 1024), 1)} MB"


def shared_documents(renter: Renter) -> list[dict[str, Any]]:
    """Return the documents that were shared with the renter.

    Every row carries the title the renter reads, when the document was
    shared, how big the file is and the link that opens it.
    """
    documents: list[dict[str, Any]] = []

    verification = PoliceVerification.objects.filter(renter=renter).first()
    if verification is not None:
        documents.append(
            {
                "id": f"verification-{verification.id}",
                "title": (
                    "Police verification — "
                    f"{verification.get_status_display().lower()}"
                ),
                "shared_on": (
                    (
                        verification.verified_at
                        or verification.submitted_at
                        or verification.generated_at
                    ).isoformat()
                    if (verification.verified_at or verification.submitted_at)
                    else None
                ),
                "size": file_size_label(verification.file),
                "url": verification.file.url if verification.file else None,
                "action": "View",
            }
        )

    agreement = RentAgreementDraft.objects.filter(renter=renter).first()
    documents.append(
        {
            "id": f"lease-{agreement.id}" if agreement is not None else "lease",
            "title": "Lease agreement",
            "shared_on": (
                agreement.start_date.isoformat()
                if agreement is not None and agreement.start_date
                else renter.created_at.isoformat() if renter.created_at else None
            ),
            "size": file_size_label(renter.rent_agreement),
            "url": renter.rent_agreement.url if renter.rent_agreement else None,
            "action": "Open",
        }
    )
    documents.append(
        {
            "id": "identity-proof",
            "title": "Identity proof",
            "shared_on": renter.created_at.isoformat() if renter.created_at else None,
            "size": file_size_label(renter.id_proof),
            "url": renter.id_proof.url if renter.id_proof else None,
            "action": "View",
        }
    )
    return documents


def profile_completion(renter: Renter) -> int:
    """Return how much of the profile of the renter is filled, in percent.

    The number is the one the sidebar shows, so the renter sees what is still
    missing from their own file.
    """
    checks = [
        bool(renter.name),
        bool(renter.phone),
        bool(renter.email),
        bool(renter.alternate_phone),
        bool(renter.emergency_contact_name),
        bool(renter.emergency_contact_number),
        bool(renter.id_proof),
        bool(renter.rent_agreement),
        bool(renter.kyc_status and renter.kyc_status != "not_started"),
    ]
    done = sum(1 for check in checks if check)
    return round(done * 100 / len(checks))


def renter_contacts(renter: Renter) -> list[dict[str, Any]]:
    """Return the people the renter can call about the flat.

    The owner, the caretakers of the flat and the support of SecureNest.
    """
    unit = renter.unit
    owner = getattr(unit, "owner", None)
    contacts: list[dict[str, Any]] = []
    if owner is not None:
        contacts.append(
            {
                "role": "Owner",
                "name": getattr(owner, "full_name", "") or owner.username,
                "phone": getattr(owner, "phone", "") or "",
                "email": getattr(owner, "email", "") or "",
            }
        )
    for caretaker in _caretakers_of_unit(unit):
        contacts.append(
            {
                "role": "Caretaker",
                "name": caretaker.name,
                "phone": caretaker.phone or "",
                "email": caretaker.email or "",
            }
        )
    contacts.append(
        {
            "role": "SecureNest support",
            "name": "SecureNest support",
            "phone": SUPPORT_PHONE,
            "email": SUPPORT_EMAIL,
        }
    )
    return contacts


def _caretakers_of_unit(unit: Any) -> list[Any]:
    """Return the caretakers that look after the given home."""
    from properties.services.caretaker_scope import caretakers_for_unit

    if unit is None:
        return []
    return list(caretakers_for_unit(unit))


def agreement_terms(renter: Renter) -> dict[str, Any] | None:
    """Return the terms of the agreement of the renter, when there is one."""
    agreement = RentAgreementDraft.objects.filter(renter=renter).first()
    if agreement is None:
        return None
    return {
        "id": agreement.id,
        "agreement_number": agreement.agreement_number,
        "status": agreement.status,
        "status_label": agreement.get_status_display(),
        "owner_signed": agreement.owner_signed,
        "renter_signed": agreement.renter_signed,
        "owner_signed_at": (
            agreement.owner_signed_at.isoformat() if agreement.owner_signed_at else None
        ),
        "renter_signed_at": (
            agreement.renter_signed_at.isoformat()
            if agreement.renter_signed_at
            else None
        ),
        "monthly_rent": str(agreement.monthly_rent or 0),
        "security_deposit": str(agreement.security_deposit or 0),
        "start_date": (
            agreement.start_date.isoformat() if agreement.start_date else None
        ),
        "end_date": agreement.end_date.isoformat() if agreement.end_date else None,
        "rent_due_day": agreement.rent_due_day,
        "payment_mode": agreement.payment_mode,
        "notice_period_months": agreement.notice_period_months,
        "jurisdiction": agreement.jurisdiction,
        "special_clauses": agreement.special_clauses,
        "document_generated_at": (
            agreement.document_generated_at.isoformat()
            if agreement.document_generated_at
            else None
        ),
    }
