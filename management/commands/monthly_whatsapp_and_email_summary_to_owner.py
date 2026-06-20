from typing import Any

from django.core.mail import EmailMessage
from django.utils.timezone import now

from core.models import User
from notification.services.whatsapp_service import send_whatsapp_message
from properties.models import RentRecord


def send_all_owners_monthly_summary() -> None:
    for owner in User.objects.filter(units__isnull=False).distinct():
        summary = generate_monthly_summary_for_owner(owner)
        msg = build_summary_message(summary)
        phone = owner.whatsapp_number or ""
        if phone:
            send_whatsapp_message(phone, msg)

        email = EmailMessage(
            subject="Your Monthly Rent Summary", body=msg, to=[owner.email]
        )
        email.send()


def generate_monthly_summary_for_owner(owner: User) -> dict[str, Any]:
    today = now().date()
    month = today.month - 1 or 12
    year = today.year if today.month > 1 else today.year - 1

    rents = RentRecord.objects.filter(
        unit__owner=owner, month=month, year=year
    ).select_related("renter", "unit")

    summary: dict[str, Any] = {
        "month": month,
        "year": year,
        "received": 0,
        "failed_payouts": [],
        "pending_rents": [],
    }

    for r in rents:
        if r.payment_status == "PAID":
            summary["received"] += r.amount_paid
            if r.payout_status != "SUCCESS":
                summary["failed_payouts"].append(
                    f"{r.renter.name} ({r.unit.unit}) - ₹{r.amount_paid}"
                )
        else:
            summary["pending_rents"].append(
                f"{r.renter.name} ({r.unit.unit}) - ₹{r.amount_paid}"
            )

    return summary


def build_summary_message(summary: dict[str, Any]) -> str:
    m = f"📊 *Monthly Rent Summary – {summary['month']:02}/{summary['year']}*\n\n"
    m += f"✅ Total Rent Received: ₹{summary['received']}\n"

    if summary["pending_rents"]:
        m += "\n❌ *Pending Payments:*\n" + "\n".join(summary["pending_rents"])

    if summary["failed_payouts"]:
        m += "\n⚠️ *Failed Payouts:*\n" + "\n".join(summary["failed_payouts"])

    return m
