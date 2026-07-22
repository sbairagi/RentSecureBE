from __future__ import annotations

import json
import logging
import uuid
from typing import Any, cast

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from django.conf import settings
from django.http import HttpRequest, JsonResponse

from core.models import OwnerBankDetails, User
from payments.adapters.cashfree import CashfreeAdapter
from payments.services.bank_details_service import BankDetailsService
from payments.services.payment_service import PaymentService

logger = logging.getLogger(__name__)


def create_rent_payment(request: HttpRequest) -> JsonResponse:  # nosonar
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    data = json.loads(request.body)
    rent_id = data.get("rent_id")

    try:
        from properties.models.rent_record_models import RentRecord

        rent = RentRecord.objects.get(id=rent_id)
    except RentRecord.DoesNotExist:  # type: ignore[possibly-undefined]
        return JsonResponse({"error": "Rent record not found"}, status=404)

    from payments.adapters.razorpay import RazorpayAdapter  # nosonar

    adapter = RazorpayAdapter()
    razorpay_order = adapter.create_order(
        amount=int(rent.amount * 100),
        currency="INR",
        receipt=f"rent_{rent.id}",
    )

    rent.razorpay_order_id = razorpay_order["id"]
    rent.save(update_fields=["razorpay_order_id"])

    return JsonResponse(
        {
            "order_id": razorpay_order["id"],
            "amount": rent.amount,
            "currency": "INR",
            "key_id": settings.RAZORPAY_KEY_ID,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_owner_bank_details(
    request: Request, /, *args: Any, **kwargs: Any
) -> Response:
    data = request.data
    owner: User = cast(User, request.user)

    try:
        BankDetailsService.validate_fields(data)
    except ValueError as e:
        return Response({"error": str(e)}, status=400)

    bank = BankDetailsService.get_existing_bank(owner)
    if bank is None:
        bank = OwnerBankDetails(owner=owner)

    if bank.beneficiary_id:
        payment_service = PaymentService(CashfreeAdapter())
        payment_service.delete_beneficiary(bank.beneficiary_id)

    response = BankDetailsService.register_beneficiary(
        owner, {**data, "bene_id_suffix": uuid.uuid4().hex[:8]}
    )

    if response.get("subCode") != "200":
        return Response(
            {"error": "Bank registration failed", "response": response}, status=400
        )

    beneficiary_id = response.get("beneId", "")
    BankDetailsService.save_bank_details(bank, data, beneficiary_id)
    BankDetailsService.retry_failed_payouts(owner)

    return Response(
        {"message": "Bank details updated & pending payouts marked for retry"}
    )
