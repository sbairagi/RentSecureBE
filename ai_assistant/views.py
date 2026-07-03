# ruff: noqa: I001
# mypy: ignore-errors

from __future__ import annotations

import json
from datetime import date, timedelta

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response

from django.contrib.auth.models import AnonymousUser
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from ai_assistant.services.finance_ai import analyze_financial_health
from core.models import UserProfile
from notification.services.whatsapp_service import send_whatsapp_message
from properties.models import PropertyTaxRecord, Renter, RentRecord
from smartbot.services.chatbot_service import handle_chat_message


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ai_assistant_insights(request: DRFRequest) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=401)
    owner = request.user
    today = date.today()

    paid_rents = RentRecord.objects.filter(
        renter__unit__owner=owner,
        status=RentRecord.Status.PAID,
        due_date__month=today.month,
        due_date__year=today.year,
    )

    late_rents = RentRecord.objects.filter(
        renter__unit__owner=owner,
        due_date__lt=today,
        payout_status="PENDING",
    )

    payouts = RentRecord.objects.filter(renter__unit__owner=owner)
    success = payouts.filter(payout_status="SUCCESS").count()
    failed = payouts.filter(payout_status="FAILED").count()

    no_agreement = Renter.objects.filter(
        unit__owner=owner,
        rent_agreement="",
        status__in=["active", "notice_period"],
    )

    no_police = Renter.objects.filter(
        unit__owner=owner,
        policeverification__isnull=True,
        status__in=["active", "notice_period"],
    )

    upcoming_tax = PropertyTaxRecord.objects.filter(
        property__owner=owner,
        paid_date__isnull=True,
    ).order_by("due_date")[:5]

    return Response(
        {
            "total_rent_this_month": sum(r.amount for r in paid_rents),
            "late_rent_count": late_rents.count(),
            "payout_success_rate": f"{success} success / {failed} failed",
            "missing_agreements": no_agreement.count(),
            "missing_police_verifications": no_police.count(),
            "upcoming_tax_dues": [
                {
                    "property": tax.unit.name if hasattr(tax, "unit") else "",
                    "due": getattr(tax, "rent_due_date", None)
                    or getattr(tax, "due_date", None),
                    "amount": tax.amount,
                }
                for tax in upcoming_tax
            ],
        }
    )


# <Card title="📊 Smart Insights">
#   <Text>Total Rent This Month: ₹{data.total_rent_this_month}</Text>
#   <Text>Late Payments: {data.late_rent_count}</Text>
#   <Text>Payouts: {data.payout_success_rate}</Text>
#   <Text>Missing Agreements: {data.missing_agreements}</Text>
#   <Text>Police Verification Pending: {data.missing_police_verifications}</Text>
# </Card>


# dashboard/api.py


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def rent_analytics_data(request: DRFRequest) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=401)
    owner = request.user

    # Last 6 months
    today = date.today()
    start_date = today.replace(day=1) - timedelta(days=180)

    monthly_rent = (
        RentRecord.objects.filter(renter__unit__owner=owner, created_at__gte=start_date)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    this_month = today.month
    this_year = today.year

    paid = (
        RentRecord.objects.filter(
            renter__unit__owner=owner,
            due_date__month=this_month,
            due_date__year=this_year,
            status=RentRecord.Status.PAID,
        ).aggregate(total=Sum("amount"))["total"]
        or 0
    )

    unpaid = (
        RentRecord.objects.filter(
            renter__unit__owner=owner,
            due_date__month=this_month,
            due_date__year=this_year,
            status=RentRecord.Status.PENDING,
        ).aggregate(total=Sum("amount"))["total"]
        or 0
    )

    return Response(
        {"monthly_rent": list(monthly_rent), "paid": paid, "unpaid": unpaid}
    )


# npx expo install react-native-svg
# npm install victory-native

# import { VictoryBar, VictoryPie, VictoryLine } from 'victory-native';

# // Monthly Bar Chart
# <VictoryBar
#   data={monthlyRent.map(item => ({
#     x: item.month.slice(0, 7),
#     y: item.total
#   }))}
#   style={{ data: { fill: "#4CAF50" } }}
# />

# // Paid vs Unpaid Pie Chart
# <VictoryPie
#   data={[
#     { x: "Paid", y: paid },
#     { x: "Unpaid", y: unpaid }
#   ]}
#   colorScale={["#4CAF50", "#FF5722"]}
# />


# views.py


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def financial_health_report(request: DRFRequest) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=401)
    user = request.user

    rent_records = RentRecord.objects.filter(renter__user=user)
    tax_records = PropertyTaxRecord.objects.filter(property__owner=user)

    analysis = analyze_financial_health(list(rent_records), list(tax_records))
    return Response(analysis)


# views.py


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat_with_assistant(request: DRFRequest) -> Response:
    query = request.data.get("message", "")
    response = handle_chat_message(user=request.user, message=query)
    return Response({"reply": response})


# // Simple chat interface
# <FlatList
#   data={messages}
#   renderItem={({ item }) => (
#     <Text style={{ alignSelf: item.sender === 'user' ? 'flex-end' : 'flex-start' }}>
#       {item.text}
# //     </Text>
# //   )}
# />
# <TextInput
#   value={input}
# //   onChangeText={setInput}
# //   onSubmitEditing={sendMessage}
# // />


@csrf_exempt
@require_POST
def whatsapp_webhook(request: HttpRequest) -> JsonResponse:
    payload = json.loads(request.body)
    phone = payload.get("from")
    message = payload.get("text")

    try:
        user = UserProfile.objects.get(whatsapp_number=phone)
    except UserProfile.DoesNotExist:
        return JsonResponse({"message": "User not found"}, status=404)

    reply = handle_chat_message(user, message)
    send_whatsapp_message(phone, reply)
    return JsonResponse({"message": "OK"})
