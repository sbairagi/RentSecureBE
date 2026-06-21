import hashlib
import hmac
import json
import logging
import secrets
import uuid
from datetime import timedelta
from typing import Any, cast

import razorpay
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Group
from django.db.models import Sum
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from twilio.rest import Client

from core.utils.export_utils import generate_owner_rent_report
from notification.services.rent_notify_service import send_payout_notification
from properties.models import RentRecord
from referral_and_earn.models import Referral
from rentsecure_be.services.cashfree_service import (
    delete_beneficiary,
    process_rent_payout,
)
from rentsecure_be.type_compat import override
from rentsecure_be.utils.cashfree_payout import add_beneficiary

from .models import (
    OTP,
    AddOnPurchase,
    OwnerBankDetails,
    PlanFeatureLimit,
    SubscriptionPlan,
    UsageLimit,
    User,
    UserSubscription,
)
from .serializers import (
    AddOnPurchaseSerializer,
    PlanFeatureLimitSerializer,
    SubscriptionPlanSerializer,
    UsageLimitSerializer,
    UserSubscriptionSerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# OTP / Authentication
# ---------------------------------------------------------------------------


def send_otp(phone_number: str, code: str) -> None:
    """Send OTP via Twilio in production; log locally during development."""
    if not settings.DEBUG:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = f"Your verification code is {code}"
        client.messages.create(
            body=message, from_=settings.TWILIO_PHONE_NUMBER, to=phone_number
        )
    else:
        print(f"[MOCK OTP to {phone_number}] Your OTP is {code}")


class SendOTP(APIView):
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        phone = request.data.get("phone")
        referral_code = request.data.get("referral_code", "").strip()

        if not phone:
            return Response({"error": "Phone number required"}, status=400)

        # Prevent spamming (resend OTP limit: 60 seconds)
        recent_otp = (
            OTP.objects.filter(phone_number=phone).order_by("-created_at").first()
        )
        if recent_otp and (timezone.now() - recent_otp.created_at).seconds < 60:
            return Response({"error": "Wait before requesting another OTP"}, status=429)

        code = str(secrets.randbelow(900000) + 100000)

        OTP.objects.create(phone_number=phone, code=code, referral_code=referral_code)
        send_otp(phone, code)

        return Response({"message": "OTP sent"}, status=200)


def _process_referral(otp: OTP, user: User) -> Response | None:
    """Shared referral logic for owner/renter OTP verification."""
    if otp.referral_code:
        try:
            referrer_referral = Referral.objects.get(referral_code=otp.referral_code)
            referrer = referrer_referral.user

            referral, _ = Referral.objects.get_or_create(user=user)
            if not referral.referred_by:
                referral.referred_by = referrer
                referral.save()
                referrer_referral.bonus_earned += 500
                referrer_referral.save()
        except Referral.DoesNotExist:
            return Response({"error": "Invalid referral code"}, status=400)
    return None


def _verify_otp_and_login(
    phone: str | None, code: str | None, group_name: str
) -> tuple[dict[str, object], int]:
    """Shared OTP verification logic for owner/renter login.

    Returns (response_dict, status_code) tuple.
    """
    if not phone or not code:
        return {"error": "Phone and OTP required"}, 400

    otp = (
        OTP.objects.filter(phone_number=phone, code=code, is_verified=False)
        .order_by("-created_at")
        .first()
    )

    if not (otp and (timezone.now() - otp.created_at) < timedelta(minutes=5)):
        return {"error": "Invalid or expired OTP"}, 400

    otp.is_verified = True
    otp.save()

    user, _ = User.objects.get_or_create(phone=phone, defaults={"username": phone})
    user.is_phone_verified = True
    user.save()

    group, _ = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)

    # Referral logic
    error_response = _process_referral(otp, user)
    if error_response is not None:
        return {"error": "Invalid referral code"}, 400

    # Delete old OTPs
    OTP.objects.filter(phone_number=phone).exclude(pk=otp.pk).delete()

    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user": {"id": user.pk, "phone": user.phone},
    }, 200


class OwnerVerifyOTP(APIView):
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        phone = request.data.get("phone")
        code = request.data.get("otp")
        data, status = _verify_otp_and_login(phone, code, "owner")
        return Response(data, status=status)


class RenterVerifyOTP(APIView):
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        phone = request.data.get("phone")
        code = request.data.get("otp")
        data, status = _verify_otp_and_login(phone, code, "renter")
        return Response(data, status=status)


# ---------------------------------------------------------------------------
# Password Management
# ---------------------------------------------------------------------------


class ChangePasswordView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return self.update(request, *args, **kwargs)

    @override
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response(
                {"error": "Both old and new passwords are required."}, status=400
            )

        if not user.check_password(old_password):
            return Response({"error": "Old password is incorrect."}, status=400)

        if old_password == new_password:
            return Response({"error": "New password must be different."}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({"message": "Password changed successfully."}, status=200)


class ResetPasswordView(APIView):
    """Password reset — requires authentication to prevent account takeover.

    Users can only reset their own password.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        new_password = request.data.get("new_password")

        if not new_password:
            return Response({"error": "New password is required."}, status=400)

        user = request.user
        user.set_password(new_password)
        user.save()
        return Response({"message": "Password reset successful."}, status=200)


# ---------------------------------------------------------------------------
# Subscription ViewSets
# ---------------------------------------------------------------------------


class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]


class PlanFeatureLimitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PlanFeatureLimit.objects.all()
    serializer_class = PlanFeatureLimitSerializer
    permission_classes = [permissions.AllowAny]


class UserSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    @override
    def get_queryset(self) -> Any:
        if isinstance(self.request.user, AnonymousUser):
            return self.queryset.none()
        return UserSubscription.objects.filter(user=self.request.user)

    @override
    def perform_create(self, serializer: Any) -> None:
        serializer.save(user=self.request.user)

    @override
    def perform_update(self, serializer: Any) -> None:
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You can't edit another user's subscription.")
        serializer.save()

    @override
    def perform_destroy(self, instance: UserSubscription) -> None:
        if instance.user != self.request.user:
            raise PermissionDenied("You can't delete another user's subscription.")
        instance.delete()


class AddOnPurchaseViewSet(viewsets.ModelViewSet):
    queryset = AddOnPurchase.objects.all()
    serializer_class = AddOnPurchaseSerializer
    permission_classes = [IsAuthenticated]

    @override
    def get_queryset(self) -> Any:
        if isinstance(self.request.user, AnonymousUser):
            return self.queryset.none()
        return AddOnPurchase.objects.filter(user=self.request.user)

    @override
    def perform_create(self, serializer: Any) -> None:
        serializer.save(user=self.request.user)

    @override
    def perform_update(self, serializer: Any) -> None:
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You can't modify another user's purchase.")
        serializer.save()

    @override
    def perform_destroy(self, instance: AddOnPurchase) -> None:
        if instance.user != self.request.user:
            raise PermissionDenied("You can't delete another user's purchase.")
        instance.delete()


class UsageLimitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UsageLimit.objects.all()
    serializer_class = UsageLimitSerializer
    permission_classes = [IsAuthenticated]

    @override
    def get_queryset(self) -> Any:
        if isinstance(self.request.user, AnonymousUser):
            return self.queryset.none()
        return UsageLimit.objects.filter(user=self.request.user)


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------


@csrf_exempt
def cashfree_payout_webhook(request: HttpRequest) -> JsonResponse:
    """Handle Cashfree payout status webhook.

    Fixed: rent.save() no longer overwrites `rent` with None.
    Fixed: Removed invalid rent.renter.property.owner chain.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    payload = json.loads(request.body)
    transfer_id = payload.get("transferId")
    event_status = payload.get("event")

    try:
        rent = RentRecord.objects.get(payout_reference=transfer_id)
    except RentRecord.DoesNotExist:
        return JsonResponse({"error": "Invalid transfer ID"}, status=404)

    if event_status == "TRANSFER_SUCCESS":
        rent.payout_status = "SUCCESS"
    elif event_status == "TRANSFER_FAILED":
        rent.payout_status = "FAILED"
    rent.save()

    # Send payout notification
    try:
        send_payout_notification(rent)
    except Exception as e:
        logger.warning(f"Failed to send payout notification for rent {rent.id}: {e}")

    return JsonResponse({"message": "Webhook received"}, status=200)


@csrf_exempt
def create_rent_payment(request: HttpRequest) -> JsonResponse:
    """Create a Razorpay order for rent payment."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    data = json.loads(request.body)
    rent_id = data.get("rent_id")

    try:
        rent = RentRecord.objects.get(id=rent_id)
    except RentRecord.DoesNotExist:
        return JsonResponse({"error": "Rent record not found"}, status=404)

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )
    razorpay_order = client.order.create(
        {
            "amount": int(rent.amount * 100),  # In paise
            "currency": "INR",
            "receipt": f"rent_{rent.id}",
            "payment_capture": 1,
        }
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


def check_signature_or_return_http_response(
    webhook_secret: str | None,
    signature: str | None,
    body: bytes,
) -> JsonResponse | None:
    """Verify HMAC signature and return error response if invalid."""
    if webhook_secret and signature:
        if not hmac.compare_digest(
            hmac.new(webhook_secret.encode("utf-8"), body, hashlib.sha256).hexdigest(),
            signature,
        ):
            logger.warning("Razorpay webhook: invalid signature")
            return JsonResponse({"error": "Invalid signature!"}, status=400)
    elif webhook_secret and not signature:
        logger.warning("Razorpay webhook: missing signature header")
        return JsonResponse({"error": "Missing signature!"}, status=400)
    return None


@csrf_exempt
def razorpay_webhook(request: HttpRequest) -> JsonResponse:  # noqa: C901
    """Single Razorpay webhook handler with HMAC signature verification.

    Handles both payment.captured (order-based) and payment_link.paid events.
    Consolidated from three duplicate definitions into one secure handler.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    body = request.body
    signature = request.headers.get("X-Razorpay-Signature")

    webhook_secret = getattr(settings, "RAZORPAY_WEBHOOK_SECRET", None)
    error_response = check_signature_or_return_http_response(
        webhook_secret, signature, body
    )
    if error_response is not None:
        return error_response

    try:
        data = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    event = data.get("event")

    # Handle payment_link.paid event (primary flow)
    if event == "payment_link.paid":
        try:
            ref_id = data["payload"]["payment_link"]["entity"]["reference_id"]
        except (KeyError, TypeError):
            logger.warning("Razorpay webhook: missing reference_id in payload")
            return JsonResponse({"error": "Invalid payload"}, status=400)

        try:
            rent = RentRecord.objects.get(id=ref_id)
        except RentRecord.DoesNotExist:
            logger.warning(f"Razorpay webhook: RentRecord {ref_id} not found")
            return JsonResponse({"error": "RentRecord not found"}, status=404)

        # Idempotent: only process if not already PAID
        if rent.payment_status == RentRecord.Status.PAID:
            return JsonResponse({"status": "ok", "message": "Already processed"})

        rent.payment_status = RentRecord.Status.PAID
        rent.date_paid = timezone.now().date()
        rent.save(update_fields=["payment_status", "date_paid", "updated_at"])

        try:
            process_rent_payout(rent)
        except Exception as e:
            logger.error(f"Failed to process payout for rent {rent.id}: {e}")

        return JsonResponse({"status": "ok"})

    # Handle payment.captured event (order-based flow)
    elif event == "payment.captured":
        try:
            razorpay_order_id = data["payload"]["payment"]["entity"]["order_id"]
        except (KeyError, TypeError):
            logger.warning("Razorpay webhook: missing order_id in payload")
            return JsonResponse({"error": "Invalid payload"}, status=400)

        try:
            rent = RentRecord.objects.get(razorpay_order_id=razorpay_order_id)
        except RentRecord.DoesNotExist:
            logger.warning(
                f"Razorpay webhook: RentRecord for order {razorpay_order_id} not found"
            )
            return JsonResponse({"error": "RentRecord not found"}, status=404)

        # Idempotent: only process if not already PAID
        if rent.payment_status == RentRecord.Status.PAID:
            return JsonResponse({"status": "ok", "message": "Already processed"})

        rent.payment_status = RentRecord.Status.PAID
        rent.date_paid = timezone.now().date()
        rent.save(update_fields=["payment_status", "date_paid", "updated_at"])

        try:
            process_rent_payout(rent)
        except Exception as e:
            logger.error(f"Failed to process payout for rent {rent.id}: {e}")

    return JsonResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# Bank Details
# ---------------------------------------------------------------------------


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_owner_bank_details(request: Request, *args: Any, **kwargs: Any) -> Response:
    """Update owner bank details and register beneficiary with Cashfree.

    Fixed: Added missing uuid import.
    Fixed: Uses register_beneficiary from cashfree_service.
    Fixed: Uses correct RentRecord field (owner) instead of renter__property__owner.
    """
    data = request.data
    owner: User = cast(User, request.user)

    required_fields = ["account_number", "ifsc_code", "account_holder_name"]
    if not all(data.get(field) for field in required_fields):
        return Response({"error": "Missing fields"}, status=400)

    # Delete old beneficiary on Cashfree
    try:
        bank = OwnerBankDetails.objects.get(owner=owner)
        if bank.beneficiary_id:
            delete_beneficiary(bank.beneficiary_id)
    except OwnerBankDetails.DoesNotExist:
        bank = OwnerBankDetails(owner=owner)

    # Register new beneficiary
    bene_id = f"owner_{owner.pk}_{uuid.uuid4().hex[:8]}"
    response = add_beneficiary(
        {
            "beneId": bene_id,
            "name": data["account_holder_name"],
            "phone": owner.phone or "",
            "email": owner.email or "",
            "bankAccount": data["account_number"],
            "ifsc": data["ifsc_code"],
            "address1": "India",
        }
    )

    if response.get("subCode") != "200":
        return Response(
            {"error": "Bank registration failed", "response": response}, status=400
        )

    # Save bank details
    bank.bank_account_number = data["account_number"]
    bank.ifsc_code = data["ifsc_code"]
    bank.beneficiary_id = bene_id
    bank.save()

    # Retry all failed payouts for this owner (using correct field: owner)
    RentRecord.objects.filter(owner=owner, payout_status="FAILED").update(
        payout_status="PENDING"
    )

    return Response(
        {"message": "Bank details updated & pending payouts marked for retry ✅"}
    )


# ---------------------------------------------------------------------------
# Owner Reporting Endpoints
# ---------------------------------------------------------------------------


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def rent_inflow_summary(request: Request, *args: Any, **kwargs: Any) -> Response:
    """Owner rent inflow summary.

    Fixed: Uses correct RentRecord field (owner) and (amount) and (PENDING).
    """
    owner: User = cast(User, request.user)
    total_received = (
        RentRecord.objects.filter(owner=owner, status="PAID").aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    pending_count = RentRecord.objects.filter(owner=owner, status="PENDING").count()

    failed_payouts = RentRecord.objects.filter(
        owner=owner, payout_status="FAILED"
    ).count()

    return Response(
        {
            "total_received": total_received,
            "pending_payments": pending_count,
            "failed_payouts": failed_payouts,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def owner_rent_records(request: Request, *args: Any, **kwargs: Any) -> Response:
    """Owner rent records list.

    Fixed: Uses correct FK path (unit.owner, renter.name, unit.unit).
    """
    owner: User = cast(User, request.user)
    rents = (
        RentRecord.objects.filter(owner=owner)
        .select_related("renter", "unit")
        .order_by("-due_date")
    )

    return Response(
        [
            {
                "property": r.unit.unit,
                "renter": r.renter.name if r.renter else "",
                "month": r.due_date.strftime("%B %Y"),
                "rent": float(r.amount),
                "status": r.status,
                "payout_status": r.payout_status,
            }
            for r in rents
        ]
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_rent_excel(request: Request, *args: Any, **kwargs: Any) -> HttpResponse:
    """Download owner rent report as Excel."""
    file = generate_owner_rent_report(request.user)
    response = HttpResponse(file, content_type="application/vnd.ms-excel")
    response["Content-Disposition"] = 'attachment; filename="rent_report.xlsx"'
    return response
