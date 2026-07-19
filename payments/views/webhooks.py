from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from payments.adapters.cashfree import CashfreeAdapter
from payments.models import WebhookEvent
from payments.services.payment_service import PaymentService
from payments.signals import payout_processed

if TYPE_CHECKING:
    from properties.models.rent_record_models import RentRecord

logger = logging.getLogger(__name__)

_ERROR_INVALID_METHOD = "Invalid method"


@csrf_exempt
def cashfree_payout_webhook(request: HttpRequest) -> JsonResponse:  # noqa: C901
    """Handle Cashfree payout status webhook.

    Fixed: rent.save() no longer overwrites `rent` with None.
    Fixed: Removed invalid rent.renter.property.owner chain.
    """
    from properties.models.rent_record_models import RentRecord

    if request.method != "POST":
        return JsonResponse({"error": _ERROR_INVALID_METHOD}, status=405)

    webhook_secret = getattr(settings, "CASHFREE_WEBHOOK_SECRET", None)
    if not webhook_secret:
        raise ImproperlyConfigured("CASHFREE_WEBHOOK_SECRET is not set")
    signature = request.headers.get("X-Cashfree-Signature")
    if not signature:
        return JsonResponse({"error": "Missing signature!"}, status=400)
    if not hmac.compare_digest(
        hmac.new(
            webhook_secret.encode("utf-8"), request.body, hashlib.sha256
        ).hexdigest(),
        signature,
    ):
        logger.warning("Cashfree webhook: invalid signature")
        return JsonResponse({"error": "Invalid signature!"}, status=401)

    payload = json.loads(request.body)
    transfer_id = payload.get("transferId")
    event_status = payload.get("event")

    if not transfer_id:
        return JsonResponse({"error": "Missing transferId"}, status=400)

    if WebhookEvent.objects.filter(
        event_id=transfer_id,
        provider=WebhookEvent.Provider.CASHFREE,
    ).exists():
        return JsonResponse({"message": "Webhook already processed"}, status=200)

    try:
        rent = RentRecord.objects.get(payout_reference=transfer_id)
    except RentRecord.DoesNotExist:
        return JsonResponse({"error": "Invalid transfer ID"}, status=404)

    if event_status == "TRANSFER_SUCCESS":
        rent.payout_status = "SUCCESS"
    elif event_status == "TRANSFER_FAILED":
        rent.payout_status = "FAILED"
    rent.save()

    payout_processed.send(sender=None, rent=rent)

    WebhookEvent.objects.create(
        event_id=transfer_id,
        provider=WebhookEvent.Provider.CASHFREE,
        status=WebhookEvent.Status.PROCESSED,
        payload=payload,
    )

    return JsonResponse({"message": "Webhook received"}, status=200)


@csrf_exempt
def razorpay_webhook(request: HttpRequest) -> JsonResponse:
    """Single Razorpay webhook handler with HMAC signature verification.

    Handles both payment.captured (order-based) and payment_link.paid events.
    Consolidated from three duplicate definitions into one secure handler.
    """
    from properties.models.rent_record_models import RentRecord

    if request.method != "POST":
        return JsonResponse({"error": _ERROR_INVALID_METHOD}, status=405)

    body = request.body
    signature = request.headers.get("X-Razorpay-Signature")

    webhook_secret = getattr(settings, "RAZORPAY_WEBHOOK_SECRET", None)
    if not webhook_secret:
        raise ImproperlyConfigured("RAZORPAY_WEBHOOK_SECRET is not set")
    signature = request.headers.get("X-Razorpay-Signature")
    if not signature:
        return JsonResponse({"error": "Missing signature!"}, status=400)
    if not hmac.compare_digest(
        hmac.new(webhook_secret.encode("utf-8"), body, hashlib.sha256).hexdigest(),
        signature,
    ):
        logger.warning("Razorpay webhook: invalid signature")
        return JsonResponse({"error": "Invalid signature!"}, status=401)

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    event = data.get("event")
    rent = _get_rent_from_event(data, event)

    if rent is not None:
        if rent.payment_status == RentRecord.Status.PAID:
            return JsonResponse({"status": "ok", "message": "Already processed"})

        event_id = f"razorpay_{event}_{rent.id}"
        if WebhookEvent.objects.filter(
            event_id=event_id,
            provider=WebhookEvent.Provider.RAZORPAY,
        ).exists():
            return JsonResponse({"status": "ok", "message": "Already processed"})

        _process_rent_payment(rent)

        WebhookEvent.objects.create(
            event_id=event_id,
            provider=WebhookEvent.Provider.RAZORPAY,
            status=WebhookEvent.Status.PROCESSED,
            payload=data,
        )

    return JsonResponse({"status": "ok"})


def _get_rent_from_event(data: dict, event: str) -> RentRecord | None:
    from properties.models.rent_record_models import RentRecord

    if event == "payment_link.paid":
        try:
            ref_id = data["payload"]["payment_link"]["entity"]["reference_id"]
        except (KeyError, TypeError):
            logger.warning("Razorpay webhook: missing reference_id in payload")
            return None

        try:
            return RentRecord.objects.get(id=ref_id)
        except RentRecord.DoesNotExist:
            logger.warning(f"Razorpay webhook: RentRecord {ref_id} not found")
            return None

    if event == "payment.captured":
        try:
            razorpay_order_id = data["payload"]["payment"]["entity"]["order_id"]
        except (KeyError, TypeError):
            logger.warning("Razorpay webhook: missing order_id in payload")
            return None

        try:
            return RentRecord.objects.get(razorpay_order_id=razorpay_order_id)
        except RentRecord.DoesNotExist:
            logger.warning(
                f"Razorpay webhook: RentRecord for order {razorpay_order_id} not found"
            )
            return None

    return None


def _process_rent_payment(rent: RentRecord) -> None:
    from properties.models.rent_record_models import RentRecord

    rent.payment_status = RentRecord.Status.PAID
    rent.date_paid = timezone.now().date()
    rent.save(update_fields=["status", "paid_on", "updated_at"])
    try:
        payment_service = PaymentService(CashfreeAdapter())
        payment_service.process_payout(rent)
    except Exception as e:
        logger.exception(f"Failed to process payout for rent {rent.id}: {e}")
