from datetime import date
from typing import Any

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response

from django.contrib.auth.models import AnonymousUser

from properties.models import RentRecord
from smartbot.services.gpt_services import gpt_smart_reply

from .actions import (
    retry_payout,
    send_agreement_for_signature,
    send_rent_agreement,
    send_rent_reminder,
)
from .intents import extract_intent
from .models import SmartBotChat


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def smart_bot_reply(request: DRFRequest) -> Any:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=401)
    user = request.user

    query_str: str = request.data.get("query", "")

    # Step 1: Get context
    today = date.today()
    current_month_rents = RentRecord.objects.filter(
        renter__unit__owner=user,
        due_date__month=today.month,
        due_date__year=today.year,
    )
    context = "\n".join(
        [
            f"{r.renter.name if r.renter else ''}: ₹{r.amount} - {r.payment_status}"
            for r in current_month_rents
        ]
    )

    last_5_chats = SmartBotChat.objects.filter(user=user).order_by("-timestamp")[:5]
    chat_context = "\n".join(
        [f"User: {c.message}\nBot: {c.reply}" for c in last_5_chats]
    )

    # Merge with rent data, etc.
    context_data = f"""
    Recent Chats:
    {chat_context}

    Current Month Rent:
    {context}

    Latest Agreements:
    None
    """

    # Step 2: Call GPT
    answer = gpt_smart_reply(user, query_str, context_data)

    # Detect and run action
    action = extract_intent(query_str)

    # In future, let GPT detect intent & extract name using:
    # name = extract_name_via_gpt(query)
    # intent = extract_intent_via_gpt(query)
    if action == "send_rent_reminder":
        # extract renter name with a simple rule (improve later with GPT parsing)
        name = query_str.split("to")[-1].strip()
        send_rent_reminder(name)
    elif action == "retry_payout":
        name = query_str.split("for")[-1].strip()
        retry_payout(name)
    elif action == "send_rent_agreement":
        name = query_str.split("to")[-1].strip()
        send_rent_agreement(name)
    elif action == "send_agreement_for_signature":
        name = query_str.split("to")[-1].strip()
        send_agreement_for_signature(name)

    # Save to DB
    SmartBotChat.objects.create(user=user, message=query_str, reply=context_data)
    return Response({"answer": answer})
