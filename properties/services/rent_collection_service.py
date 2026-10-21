"""Rent collection workflows.

The rules implemented here mirror the approved "Rent collection" concept:

* a rent record is **never deleted** — it is cancelled with a mandatory
  reason and stays visible for the audit trail;
* a settled (``paid``) or cancelled record is fully locked;
* a part payment is allowed while the month is **pending or overdue** and
  the unit allows part payments; the amount must be positive, must not
  exceed the remaining balance, and the paid-on date cannot be earlier
  than the rent due date;
* the last part settles the month and issues the settlement receipt.

The rules are binding and documented in
``properties/RENT_COLLECTION_BUSINESS_RULES.md``.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from rest_framework.exceptions import ValidationError

from django.core.mail import EmailMessage
from django.db import transaction
from django.utils import timezone

from documents.receipt import build_receipt, format_period, receipt_filename
from notification.services.whatsapp_service import send_whatsapp_message
from properties.models import RentRecord, RentRecordAction, RentRecordPart
from properties.services.receipt_service import (
    generate_rent_receipt_pdf,
    send_rent_part_receipt_email,
)
from properties.services.rent_actions import latest_history_id, log_rent_action
from properties.services.rent_ledger_view import (
    PART_PAYMENT_MESSAGES,
    format_money,
    format_money_exact,
)

logger = logging.getLogger(__name__)

ZERO = Decimal("0")


def _format_money(value: Any) -> str:
    """Render a money amount the way the ledger renders it (₹30,000)."""
    return format_money(value)


def _renter_phone(rent_record: RentRecord) -> str:
    renter = rent_record.renter
    if renter is None:
        return ""
    return getattr(renter, "whatsapp_number", "") or getattr(renter, "phone", "") or ""


def cancel_rent_record(rent_record: RentRecord, reason: str, user: Any) -> RentRecord:
    """Cancel a rent record with a mandatory reason.

    Args:
        rent_record: The record to cancel.
        reason: Why the record is being voided — required.
        user: The owner cancelling the record.

    Returns:
        The cancelled :class:`RentRecord`.

    Raises:
        ValidationError: When the record cannot be cancelled.
    """
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(
            {
                "error": (
                    "A reason is required so the ledger history explains the "
                    "cancellation."
                )
            }
        )

    status = str(rent_record.status or "").lower()
    if status == RentRecord.Status.CANCELLED:
        raise ValidationError({"error": "This rent record is already cancelled."})
    if status == RentRecord.Status.PAID:
        raise ValidationError(
            {
                "error": (
                    "This rent record is settled — money was received, so it cannot be "
                    "cancelled. Raise an adjustment instead."
                )
            }
        )
    if (rent_record.amount_paid or ZERO) > 0:
        raise ValidationError(
            {
                "error": (
                    f"Part payments of {_format_money(rent_record.amount_paid)} were "
                    "received against this record, so it can no longer be cancelled."
                )
            }
        )

    rent_record.status = RentRecord.Status.CANCELLED
    rent_record.cancel_reason = reason
    rent_record.cancelled_at = timezone.now()
    rent_record.cancelled_by = user
    rent_record.save(
        update_fields=[
            "status",
            "cancel_reason",
            "cancelled_at",
            "cancelled_by",
            "updated_at",
        ]
    )
    # The cancellation is an action of the owner — it belongs in the trail
    # of the record next to the reason that explains it.
    log_rent_action(
        rent_record,
        RentRecordAction.Kind.CANCELLED,
        summary="Month cancelled",
        detail=reason,
        actor=user,
        history_id=latest_history_id(rent_record),
    )
    return rent_record


def record_part_payment(
    rent_record: RentRecord,
    *,
    amount: Decimal,
    paid_on: Any,
    payment_method: str,
    transaction_id: str = "",
    note: str = "",
    user: Any = None,
    split_allowed: bool = True,
) -> RentRecordPart:
    """Record one instalment against a monthly rent record.

    The part and the new total of the record are written in **one**
    transaction, with the record locked for the write: two parts of the same
    month can never be counted twice, and a month can never be settled by a
    part that was measured against a stale balance.

    Args:
        rent_record: The monthly record the part belongs to.
        amount: How much was received — positive, at most the balance.
        paid_on: When it was received — never before the due date.
        payment_method: Mode of payment for this part.
        transaction_id: Optional gateway / bank reference.
        note: Optional note for this part.
        user: The owner recording the part.
        split_allowed: Whether the month may be split at all. The renter pays
            the balance of their own month: when the unit does not allow part
            payments, only a payment that settles the whole month is accepted.

    Returns:
        The created :class:`RentRecordPart`.

    Raises:
        ValidationError: When the part cannot be recorded.
    """
    with transaction.atomic():
        # The record is locked for the write and re-read, so the balance this
        # part is measured against is the balance of this very moment.
        locked = (
            RentRecord.objects.select_for_update().filter(pk=rent_record.pk).first()
        )
        if locked is None:
            raise ValidationError({"error": "This rent record no longer exists."})

        _guard_part_payment(
            locked, amount=amount, paid_on=paid_on, split_allowed=split_allowed
        )

        part = RentRecordPart.objects.create(
            rent_record=locked,
            amount=amount,
            paid_on=paid_on,
            payment_method=payment_method,
            transaction_id=transaction_id or "",
            note=note or "",
            created_by=user,
        )

        locked.amount_paid = (locked.amount_paid or ZERO) + amount
        locked.transaction_id = transaction_id or locked.transaction_id
        if locked.amount_paid >= locked.total_due:
            locked.status = RentRecord.Status.PAID
            locked.paid_on = paid_on
            locked.payment_method = payment_method
        locked.save(
            update_fields=[
                "amount_paid",
                "status",
                "paid_on",
                "payment_method",
                "transaction_id",
                "updated_at",
            ]
        )

    # The caller keeps working with the record it was given — the copy it
    # holds has to carry the new total as well.
    rent_record.amount_paid = locked.amount_paid
    rent_record.status = locked.status
    rent_record.transaction_id = locked.transaction_id
    if locked.status == RentRecord.Status.PAID:
        rent_record.paid_on = locked.paid_on
        rent_record.payment_method = locked.payment_method

    # Every part carries its own receipt — the renter is never left without
    # proof of what was paid.  A failed delivery must not undo the payment,
    # so the receipt is sent once the transaction has been committed.
    _send_part_receipt(rent_record, part)
    return part


def _guard_part_payment(
    rent_record: RentRecord,
    *,
    amount: Decimal,
    paid_on: Any,
    split_allowed: bool = True,
) -> None:
    """Every rule that decides whether a part payment may be recorded.

    Args:
        rent_record: The monthly record the part belongs to.
        amount: How much the part claims to be.
        paid_on: When the money was received.
        split_allowed: Whether the month may be split at all. When the month
            may not be split, only a payment that settles the whole balance is
            accepted — that is what the renter pays when the owner keeps the
            month in one piece.

    Raises:
        ValidationError: When the part may not be recorded.
    """
    status = str(rent_record.status or "").lower()
    if status == RentRecord.Status.CANCELLED:
        raise ValidationError(
            {
                "error": (
                    "This rent record was cancelled, so no part payment can be "
                    "recorded."
                )
            }
        )
    if status == RentRecord.Status.PAID:
        raise ValidationError(
            {
                "error": (
                    "This rent record is already settled — there is no balance left to "
                    "split."
                )
            }
        )
    if not getattr(rent_record.unit, "allow_partial_payments", False):
        if not split_allowed:
            # The month is kept in one piece: the only payment that is allowed
            # is the one that settles the whole balance.
            balance = rent_record.balance
            if amount is None or amount <= ZERO:
                raise ValidationError(
                    {"error": PART_PAYMENT_MESSAGES["amount_required"]}
                )
            if amount != balance:
                raise ValidationError(
                    {
                        "error": (
                            "This month is paid in one go. Pay the whole balance of "
                            f"{format_money_exact(balance)}."
                        )
                    }
                )
        else:
            raise ValidationError(
                {
                    "error": (
                        "Part payments are off for this unit. Turn them on in "
                        "Unit details to split the rent."
                    )
                }
            )
    if amount is None or amount <= ZERO:
        raise ValidationError({"error": PART_PAYMENT_MESSAGES["amount_required"]})

    balance = rent_record.balance
    if amount > balance:
        raise ValidationError(
            {
                "error": PART_PAYMENT_MESSAGES["amount_too_large"].format(
                    balance=format_money_exact(balance)
                )
            }
        )
    if paid_on is not None and rent_record.due_date and paid_on < rent_record.due_date:
        raise ValidationError(
            {
                "error": (
                    f"{PART_PAYMENT_MESSAGES['date_before_due']} "
                    f"({rent_record.due_date.strftime('%d %b %Y')})."
                )
            }
        )


def _send_part_receipt(rent_record: RentRecord, part: RentRecordPart) -> bool:
    """Email the receipt of a part payment, swallowing delivery failures."""
    try:
        delivered = send_rent_part_receipt_email(rent_record, part)
    except Exception:  # pragma: no cover - defensive, the service catches
        logger.exception(
            "Failed to send the part receipt for rent %s part %s",
            rent_record.id,
            part.id,
        )
        return False
    if delivered:
        part.receipt_no = receipt_filename(rent_record, part)
        part.save(update_fields=["receipt_no", "updated_at"])
    return bool(delivered)


def send_rent_reminder(rent_record: RentRecord, user: Any = None) -> bool:
    """Nudge the renter for whatever balance is still left.

    Args:
        rent_record: The record to follow up on.
        user: The owner sending the reminder.

    Returns:
        ``True`` when the message was handed to WhatsApp.
    """
    balance = rent_record.balance
    status = str(rent_record.status or "").lower()
    if status == RentRecord.Status.CANCELLED:
        raise ValidationError(
            {
                "error": (
                    "This rent record was cancelled — there is nothing to follow up "
                    "on."
                )
            }
        )
    if balance <= ZERO:
        raise ValidationError(
            {"error": "This rent record is settled — there is nothing to follow up on."}
        )

    phone = _renter_phone(rent_record)
    if not phone:
        raise ValidationError(
            {"error": "This renter has no phone number on file to remind."}
        )

    period = format_period(rent_record.due_date) if rent_record.due_date else ""
    message = (
        f"Hello {getattr(rent_record.renter, 'name', 'there')}, a gentle reminder that "
        f"{_format_money(balance)} of rent for {period} is still due"
        f" (due {rent_record.due_date.strftime('%d %b %Y')})."
    )
    sent = send_whatsapp_message(
        phone,
        message,
        user=user,
        rent_record=rent_record,
    )

    # The stamp of the reminder is bookkeeping, not a change of the month —
    # the action log is what tells the owner that a reminder went out.
    rent_record.skip_history_when_saving = True
    try:
        rent_record.last_reminded_at = timezone.now()
        rent_record.save(update_fields=["last_reminded_at", "updated_at"])
    finally:
        del rent_record.skip_history_when_saving
    # The reminder is an action of the owner — it is in the trail even when
    # the message could not leave the building.
    log_rent_action(
        rent_record,
        RentRecordAction.Kind.REMINDER_SENT,
        summary=(
            f"Reminder sent for the balance of {_format_money(balance)}"
            if sent
            else "Reminder not delivered"
        ),
        detail=(
            f"{_format_money(balance)} of rent for {period} is still due"
            " · sent on WhatsApp"
            if sent
            else (
                f"The reminder for {_format_money(balance)} could not be "
                f"delivered to the renter."
            )
        ),
        outcome=(
            RentRecordAction.Outcome.SENT if sent else RentRecordAction.Outcome.FAILED
        ),
        actor=user,
    )
    return bool(sent)


def send_rent_receipt(rent_record: RentRecord, user: Any = None) -> bool:
    """Send the receipt the renter is owed to the renter.

    A settled month gets the settlement receipt; a month that is still
    open gets the receipt of the latest part.

    Args:
        rent_record: The record to send the receipt for.
        user: The owner sending the receipt.

    Returns:
        ``True`` when the receipt was sent.
    """
    renter = rent_record.renter
    if renter is None:
        raise ValidationError({"error": "This rent record has no renter to send to."})

    parts = list(rent_record.parts.all())
    part = None
    if parts and str(rent_record.status or "").lower() != RentRecord.Status.PAID:
        part = parts[-1]

    receipt = build_receipt(rent_record, part)
    pdf_bytes = generate_rent_receipt_pdf(rent_record, part)

    delivered = False
    email = getattr(renter, "email", "") or ""
    if email:
        period = format_period(rent_record.due_date) if rent_record.due_date else ""
        subject = f"Rent Receipt - {period} | {receipt.total_amount}"
        body = (
            f"Dear {getattr(renter, 'name', 'there')},\n\n"
            f"Please find attached your rent receipt for {period}.\n\n"
            f"Property: {rent_record.unit.unit}\n"
            f"Amount: {receipt.total_amount}\n"
            f"Date Paid: {receipt.paid_on}\n"
            f"Payment Status: {rent_record.get_status_display()}\n\n"
            f"Thank you for your timely payment!\n\n"
            f"Best regards,\n"
            f"RentSecure Team"
        )
        message = EmailMessage(
            subject=subject,
            body=body,
            from_email="no-reply@rentsecure.in",
            to=[email],
        )
        message.attach(
            receipt_filename(rent_record, part), pdf_bytes, "application/pdf"
        )
        # ``fail_silently`` keeps a mail-server outage from breaking the
        # request, but it also hides the failure — the return value is the
        # only way to know whether the receipt really left the building.
        try:
            sent = int(message.send(fail_silently=True) or 0)
        except Exception:  # pragma: no cover - defensive, fail_silently covers
            sent = 0
        if sent:
            delivered = True
        else:
            logger.warning(
                "The rent receipt email for rent %s could not be delivered",
                rent_record.id,
            )

    phone = _renter_phone(rent_record)
    if phone:
        share_message = (
            f"Hello {getattr(renter, 'name', 'there')}, your rent receipt for "
            f"{rent_record.due_date.strftime('%B %Y')} "
            f"({receipt.total_amount}) is ready."
        )
        try:
            shared = bool(
                send_whatsapp_message(
                    phone,
                    share_message,
                    user=user,
                    rent_record=rent_record,
                )
            )
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning("Failed to share receipt on WhatsApp: %s", exc)
            shared = False
        if shared:
            delivered = True

    # The timestamp follows the delivery: a receipt that never left the
    # building was never sent.
    if delivered:
        # The stamp is bookkeeping, not a change of the month — the action
        # log is what tells the owner that the receipt went out.
        rent_record.skip_history_when_saving = True
        try:
            rent_record.receipt_sent_at = timezone.now()
            rent_record.save(update_fields=["receipt_sent_at", "updated_at"])
        finally:
            del rent_record.skip_history_when_saving
    # The receipt is an action of the owner — it is in the trail whether it
    # was delivered or not.
    log_rent_action(
        rent_record,
        RentRecordAction.Kind.RECEIPT_SENT,
        summary=("Settlement receipt sent" if delivered else "Receipt not delivered"),
        detail=(
            f"{receipt_filename(rent_record, part)} · {receipt.total_amount}"
            if delivered
            else "The receipt could not be delivered to the renter."
        ),
        outcome=(
            RentRecordAction.Outcome.SENT
            if delivered
            else RentRecordAction.Outcome.FAILED
        ),
        actor=user,
    )
    return delivered
