# from rent.models import RentRecord
from datetime import date

# @api_view(["POST"])
# def smart_bot_reply(request):
#     query = request.data.get("query", "").lower()
#     user = request.user
#     today = date.today()
#     if "rent income" in query:
#         total = RentRecord.objects.filter(
#             renter__property__owner=user,
#             month=today.month,
#             year=today.year,
#             payment_status="PAID"
#         ).aggregate(total=models.Sum("amount"))["total"] or 0
#         return Response({"answer": f"Your rent income this month is ₹{total}."})
#     if "rent nahi diya" in query or "unpaid" in query:
#         unpaid = RentRecord.objects.filter(
#             renter__property__owner=user,
#             month=today.month,
#             year=today.year,
#             payment_status="UNPAID"
#         ).values("renter__name")
#         names = ", ".join([r["renter__name"] for r in unpaid]) or "None"
#         return Response({"answer": f"Unpaid tenants: {names}"})
#     return Response({"answer": "Sorry, I didn't understand that yet. Please rephrase."})
# npm install react-native-gifted-chat
# import { GiftedChat } from 'react-native-gifted-chat';
# import { useState } from 'react';
# import axios from 'axios';
# export default function SmartBotScreen() {
#   const [messages, setMessages] = useState([]);
#   const handleSend = async (newMessages = []) => {
#     setMessages(previous => GiftedChat.append(previous, newMessages));
#     const text = newMessages[0].text;
#     const res = await axios.post("/api/smartbot/", { query: text });
#     const botReply = {
#       _id: Math.random().toString(),
#       text: res.data.answer,
#       createdAt: new Date(),
#       user: { _id: 2, name: "SmartBot" }
#     };
#     setMessages(previous => GiftedChat.append(previous, [botReply]));
#   };
#   return (
#     <GiftedChat
#       messages={messages}
#       onSend={handleSend}
#       user={{ _id: 1 }}
#     />
#   );
# }
# smartbot/views.py
# from .gpt_service import gpt_smart_reply
# from rent.models import RentRecord
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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
def smart_bot_reply(request):
    query = request.data.get("query")
    user = request.user

    # Step 1: Get context
    today = date.today()
    current_month_rents = RentRecord.objects.filter(
        renter__property__owner=user,
        month=today.month,
        year=today.year
    )
    context = "\n".join([f"{r.renter.name}: ₹{r.amount} - {r.payment_status}" for r in current_month_rents])

    last_5_chats = SmartBotChat.objects.filter(user=user).order_by("-timestamp")[:5]
    chat_context = "\n".join([f"User: {c.message}\nBot: {c.reply}" for c in last_5_chats])

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
    answer = gpt_smart_reply(query, context_data)

    # Detect and run action
    action = extract_intent(query)

    # In future, let GPT detect intent & extract name using:
    # name = extract_name_via_gpt(query)
    # intent = extract_intent_via_gpt(query)
    if action == "send_rent_reminder":
        # extract renter name with a simple rule (improve later with GPT parsing)
        name = query.split("to")[-1].strip()
        send_rent_reminder(name)
    elif action == "retry_payout":
        name = query.split("for")[-1].strip()
        retry_payout(name)
    elif action == "send_rent_agreement":
        name = query.split("to")[-1].strip()
        send_rent_agreement(name)
    elif action == "send_agreement_for_signature":
        name = query.split("to")[-1].strip()
        send_agreement_for_signature(name)

    # Save to DB
    SmartBotChat.objects.create(user=user, message=query, reply=context_data)
    return Response({"answer": answer})

