# mypy: ignore-errors

"""Smartbot chatbot service.

Rule-based + OpenAI assistant for the RentSecure chatbot. Only uses
fields that actually exist on the canonical models.
"""

from typing import Any

import openai

from properties.models import RentAgreementDraft, RentRecord


def handle_chat_message(user: Any, message: str) -> str:
    """Route a chat message to the right handler and return the response.

    Args:
        user: The authenticated ``User`` instance.
        message: The raw text the user sent.
    """
    lowered = message.lower()

    if "rent due" in lowered:
        next_due = (
            RentRecord.objects.filter(renter__user=user, payout_status="PENDING")
            .order_by("due_date")
            .first()
        )
        if next_due is not None:
            return (
                f"🏠 Your next rent of ₹{next_due.amount_paid} "
                f"is due on {next_due.due_date}."
            )
        return "✅ No upcoming rent dues."

    if "agreement" in lowered:
        latest = (
            RentAgreementDraft.objects.filter(renter__user=user)
            .order_by("-generated_at")
            .first()
        )
        if latest is not None and latest.file:
            return f"📄 Here is your latest rent agreement: {latest.file.url}"
        return "No agreement found."

    response = openai.ChatCompletion.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant for RentSecure users.",
            },
            {"role": "user", "content": message},
        ],
    )
    return str(response.choices[0].message["content"])
