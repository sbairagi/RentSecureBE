from datetime import date
from wealth_concierge_platform.models import RentRecord
from core.models import Owner
from django.utils.timezone import now
from services.whatsapp_service import send_whatsapp_message
from django.core.mail import EmailMessage


def send_all_owners_monthly_summary():
    for owner in Owner.objects.all():
        summary = generate_monthly_summary_for_owner(owner)
        msg = build_summary_message(owner, summary)
        phone = owner.profile.whatsapp_number
        send_whatsapp_message(phone, msg)

        # Optional: Email with Invoices Attache
        email = EmailMessage(
            subject="Your Monthly Rent Summary",
            body=msg,
            to=[owner.email]
        )
        email.send()


def generate_monthly_summary_for_owner(owner: Owner):
    today = now().date()
    month, year = today.month - 1 or 12, today.year if today.month > 1 else today.year - 1

    rents = RentRecord.objects.filter(
        renter__property__owner=owner,
        month=month,
        year=year
    ).select_related("renter", "renter__property")

    summary = {
        "month": month,
        "year": year,
        "received": 0,
        "failed_payouts": [],
        "pending_rents": [],
    }

    for r in rents:
        if r.payment_status == "PAID":
            summary["received"] += r.amount
            if r.payout_status != "SUCCESS":
                summary["failed_payouts"].append(f"{r.renter.name} ({r.renter.property.name}) - ₹{r.amount}")
        else:
            summary["pending_rents"].append(f"{r.renter.name} ({r.renter.property.name}) - ₹{r.amount}")

    return summary



def build_summary_message(owner, summary):
    m = f"📊 *Monthly Rent Summary – {summary['month']:02}/{summary['year']}*\n\n"
    m += f"✅ Total Rent Received: ₹{summary['received']}\n"

    if summary["pending_rents"]:
        m += f"\n❌ *Pending Payments:*\n" + "\n".join(summary["pending_rents"])

    if summary["failed_payouts"]:
        m += f"\n⚠️ *Failed Payouts:*\n" + "\n".join(summary["failed_payouts"])

    return m