"""Smartbot chatbot service.

Rule-based + OpenAI assistant for the RentSecure chatbot. Only uses
fields that actually exist on the canonical models.
"""

import openai

from properties.models import RentAgreementDraft, RentRecord


def handle_chat_message(user, message: str) -> str:
    """Route a chat message to the right handler and return the response.

    Args:
        user: The authenticated ``User`` instance.
        message: The raw text the user sent.
    """
    lowered = message.lower()

    if "rent due" in lowered:
        next_due = (
            RentRecord.objects.filter(renter__user=user, payment_status="PENDING")
            .order_by("rent_due_date")
            .first()
        )
        if next_due is not None:
            return (
                f"🏠 Your next rent of ₹{next_due.amount_paid} "
                f"is due on {next_due.rent_due_date}."
            )
        return "✅ No upcoming rent dues."

    if "agreement" in lowered:
        # The signed/unsigned agreement lives on RentAgreementDraft
        # (which has a ``file`` FileField, not ``agreement_pdf``).
        latest = (
            RentAgreementDraft.objects.filter(renter__user=user)
            .order_by("-generated_at")
            .first()
        )
        if latest is not None and latest.file:
            return f"📄 Here is your latest rent agreement: {latest.file.url}"
        return "No agreement found."

    # Fallback to OpenAI assistant
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant for RentSecure users.",
            },
            {"role": "user", "content": message},
        ],
    )
    return response.choices[0].message["content"]
