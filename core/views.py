from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
import uuid
from datetime import timedelta
from typing import TYPE_CHECKING, Any, cast, override

import razorpay  # type: ignore[import-untyped]
import requests
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken
from twilio.rest import Client

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Group
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.db.models import Sum
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_time
from django.views.decorators.csrf import csrf_exempt

from notification.services.rent_notify_service import send_payout_notification
from rentsecure_be.services.cashfree_service import (
    delete_beneficiary,
    process_rent_payout,
)
from rentsecure_be.utils.cashfree_payout import add_beneficiary
from rentsecure_be.utils.export_utils import generate_owner_rent_report
from rentsecure_be.utils.tax_advice_utils import suggest_tax_savings
from rentsecure_be.utils.tax_report_pdf_utils import generate_tax_report_pdf

from .models import (
    OTP,
    AddOnPurchase,
    AppVersion,
    MaintenanceMode,
    OwnerBankDetails,
    PlanFeatureLimit,
    SubscriptionPlan,
    UsageLimit,
    User,
    UserProfile,
    UserSubscription,
)
from .serializers import (
    AddOnPurchaseSerializer,
    LoginSerializer,
    PlanFeatureLimitSerializer,
    ProfileSerializer,
    RegisterSerializer,
    SocialAuthSerializer,
    SubscriptionPlanSerializer,
    UsageLimitSerializer,
    UserSubscriptionSerializer,
)

if TYPE_CHECKING:
    from properties.models.rent_record_models import RentRecord  # nosonar

logger = logging.getLogger(__name__)

_ERROR_INVALID_METHOD = "Invalid method"


# ---------------------------------------------------------------------------
# Social Auth Token Verification
# ---------------------------------------------------------------------------


def _verify_google_token(id_token: str) -> tuple[str, str]:
    tokeninfo_url = "https://oauth2.googleapis.com/tokeninfo?id_token=" + id_token
    try:
        response = requests.get(tokeninfo_url, timeout=10)
    except requests.RequestException as exc:
        logger.warning("Failed to contact Google token verification endpoint: %s", exc)
        return "", ""

    if response.status_code != 200:
        logger.warning("Invalid Google ID token: status %s", response.status_code)
        return "", ""

    data = response.json()
    email = data.get("email", "")
    name = data.get("name", "")

    if not email:
        logger.warning("Email missing from Google token")
        return "", ""

    return email, name


def _verify_apple_token(identity_token: str) -> tuple[str, str]:
    raise ImproperlyConfigured(
        "Apple social auth requires Apple identity token verification. "
        "Configure APPLE_TEAM_ID, APPLE_KEY_ID, APPLE_CLIENT_ID, and APPLE_PRIVATE_KEY "
        "in settings to enable Apple sign-in."
    )


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

        client_ip = request.META.get("REMOTE_ADDR") or ""
        otp_cache_key = f"otp_send_limit:{phone}:{client_ip}"
        request_count = cache.get(otp_cache_key, 0)
        if request_count >= 5:
            return Response(
                {"error": "Too many OTP requests. Try again later."}, status=429
            )

        # Prevent spamming (resend OTP limit: 60 seconds)
        recent_otp = (
            OTP.objects.filter(phone_number=phone).order_by("-created_at").first()
        )
        if recent_otp and (timezone.now() - recent_otp.created_at).seconds < 60:
            return Response({"error": "Wait before requesting another OTP"}, status=429)

        code = str(secrets.randbelow(900000) + 100000)

        OTP.objects.create(phone_number=phone, code=code, referral_code=referral_code)
        send_otp(phone, code)

        cache.set(otp_cache_key, request_count + 1, timeout=3600)
        return Response({"message": "OTP sent"}, status=200)


def _process_referral(otp: OTP, user: User) -> Response | None:
    """Shared referral logic for owner/renter OTP verification."""
    from referral_and_earn.models import Referral

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

    with transaction.atomic():
        otp = (
            OTP.objects.filter(phone_number=phone, code=code, is_verified=False)
            .select_for_update()
            .order_by("-created_at")
            .first()
        )

        if not (otp and (timezone.now() - otp.created_at) < timedelta(minutes=5)):
            return {"error": "Invalid or expired OTP"}, 400

        if otp.attempts >= OTP.MAX_OTP_ATTEMPTS:
            return {"error": "Too many attempts. Request a new OTP."}, 429

        otp.attempts += 1
        otp.is_verified = True
        otp.save(update_fields=["attempts", "is_verified"])

        user, _ = User.objects.get_or_create(phone=phone, defaults={"username": phone})
        user.is_phone_verified = True
        user.save(update_fields=["is_phone_verified"])

        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)

        otp_pk = otp.pk

    error_response = _process_referral(otp, user)
    if error_response is not None:
        return {"error": "Invalid referral code"}, 400

    OTP.objects.filter(phone_number=phone).exclude(pk=otp_pk).delete()

    refresh = RefreshToken.for_user(user)
    role = (
        "owner"
        if user.groups.filter(name="owner").exists()
        else "renter" if user.groups.filter(name="renter").exists() else "user"
    )
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user": {
            "id": user.pk,
            "phone": user.phone,
            "email": user.email,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "fullName": user.full_name,
            "username": user.username,
            "role": role,
        },
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
    """Authenticated password reset.

    Users can reset their own password while logged in without providing
    the old password.
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


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def forgot_password(request: Request, /, *args: Any, **kwargs: Any) -> Response:
    from core.models import PasswordResetToken

    email = request.data.get("email")
    if not email:
        return Response({"error": "Email is required."}, status=400)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {"message": "If an account exists, a reset link has been sent."},
            status=200,
        )

    token = PasswordResetToken.objects.create(user=user)
    reset_url = f"{settings.FRONTEND_URL}/reset-password/{token.token}"

    if settings.DEBUG:
        print(f"[PASSWORD RESET] {email} -> {reset_url}")
    else:
        from django.core.mail import send_mail

        send_mail(
            subject="Password Reset",
            message=f"Reset your password: {reset_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )

    return Response(
        {"message": "If an account exists, a reset link has been sent."},
        status=200,
    )


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def reset_password_confirm(
    request: Request, token: str, /, *args: Any, **kwargs: Any
) -> Response:
    from core.models import PasswordResetToken

    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirmPassword")

    if not new_password or not confirm_password:
        return Response(
            {"error": "new_password and confirmPassword are required."}, status=400
        )

    if new_password != confirm_password:
        return Response({"error": "Passwords do not match."}, status=400)

    try:
        reset_token = PasswordResetToken.objects.get(token=token)
    except PasswordResetToken.DoesNotExist:
        return Response({"error": "Invalid reset token."}, status=400)

    if not reset_token.is_valid():
        return Response({"error": "Reset token has expired."}, status=400)

    user = reset_token.user
    user.set_password(new_password)
    user.save()
    reset_token.used_at = timezone.now()
    reset_token.save(update_fields=["used_at"])

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


# Webhook endpoint: CSRF is exempted. This endpoint receives inbound callbacks
# from external payment/webhook providers. Those callers do not have browser
# sessions and therefore cannot supply a CSRF token.
# Security: Cashfree webhook signature is verified inline below (hmac + sha256)
# before any business logic executes. The CASHFREE_WEBHOOK_SECRET setting must
# be configured in production; the endpoint refuses all requests if it is absent.
@csrf_exempt
def cashfree_payout_webhook(request: HttpRequest) -> JsonResponse:
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
        return JsonResponse({"error": "Invalid signature!"}, status=400)

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

    try:
        send_payout_notification(rent)
    except Exception as e:
        logger.exception(f"Failed to send payout notification for rent {rent.id}: {e}")

    return JsonResponse({"message": "Webhook received"}, status=200)


def create_rent_payment(request: HttpRequest) -> JsonResponse:  # nosonar
    """Create a Razorpay order for rent payment."""
    from properties.models.rent_record_models import RentRecord  # nosonar

    if request.method != "POST":
        return JsonResponse({"error": _ERROR_INVALID_METHOD}, status=405)

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


# Webhook endpoint: CSRF is exempted. This endpoint receives inbound callbacks
# from external payment/webhook providers. Those callers do not have browser
# sessions and therefore cannot supply a CSRF token.
# Security: Razorpay webhook signature is verified inline below (hmac + sha256)
# before any business logic executes. The RAZORPAY_WEBHOOK_SECRET setting must
# be configured in production; the endpoint refuses all requests if it is absent.
@csrf_exempt
def razorpay_webhook(request: HttpRequest) -> JsonResponse:
    """Single Razorpay webhook handler with HMAC signature verification.

    Handles both payment.captured (order-based) and payment_link.paid events.
    Consolidated from three duplicate definitions into one secure handler.
    """
    from properties.models.rent_record_models import RentRecord  # nosonar

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
        return JsonResponse({"error": "Invalid signature!"}, status=400)

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    event = data.get("event")
    rent = _get_rent_from_event(data, event)

    if rent is not None:
        if rent.payment_status == RentRecord.Status.PAID:
            return JsonResponse({"status": "ok", "message": "Already processed"})
        _process_rent_payment(rent)

    return JsonResponse({"status": "ok"})


def _get_rent_from_event(data: dict, event: str) -> RentRecord | None:
    from properties.models.rent_record_models import RentRecord  # nosonar

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
    from properties.models.rent_record_models import RentRecord  # nosonar

    rent.payment_status = RentRecord.Status.PAID
    rent.date_paid = timezone.now().date()
    rent.save(update_fields=["status", "paid_on", "updated_at"])
    try:
        process_rent_payout(rent)
    except Exception as e:
        logger.exception(f"Failed to process payout for rent {rent.id}: {e}")


# ---------------------------------------------------------------------------
# Alert Preferences
# ---------------------------------------------------------------------------


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_owner_alert_preferences(
    request: Request, /, *args: Any, **kwargs: Any
) -> Response:
    owner: User = cast(User, request.user)
    try:
        profile = owner.userprofile
    except UserProfile.DoesNotExist:
        return Response(
            {"error": "UserProfile not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    data = request.data
    profile.language_preference = data.get(
        "language_preference", profile.language_preference
    )
    profile.alert_frequency = data.get("alert_frequency", profile.alert_frequency)
    profile.receive_rent_alerts = data.get(
        "receive_rent_alerts", profile.receive_rent_alerts
    )
    profile.receive_tax_alerts = data.get(
        "receive_tax_alerts", profile.receive_tax_alerts
    )
    profile.receive_vacancy_alerts = data.get(
        "receive_vacancy_alerts", profile.receive_vacancy_alerts
    )
    profile.receive_flagged_alerts = data.get(
        "receive_flagged_alerts", profile.receive_flagged_alerts
    )
    profile.receive_voice_alerts = data.get(
        "receive_voice_alerts", profile.receive_voice_alerts
    )
    profile.greeting_prefix = data.get("greeting_prefix", profile.greeting_prefix)
    profile.reminder_time = data.get("reminder_time", profile.reminder_time)
    profile.rent_reminders_enabled = data.get(
        "rent_reminders_enabled", profile.rent_reminders_enabled
    )
    profile.save(
        update_fields=[
            "language_preference",
            "alert_frequency",
            "receive_rent_alerts",
            "receive_tax_alerts",
            "receive_vacancy_alerts",
            "receive_flagged_alerts",
            "receive_voice_alerts",
            "greeting_prefix",
            "reminder_time",
            "rent_reminders_enabled",
        ]
    )
    return Response({"success": True, "message": "Alert preferences updated."})


class ReminderTimeUpdateView(APIView):
    """Update the authenticated owner's reminder time."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, /, *args: Any, **kwargs: Any) -> Response:
        reminder_time_str = request.data.get("reminder_time")
        if not reminder_time_str:
            return Response(
                {"error": "reminder_time is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reminder_time = parse_time(reminder_time_str)
        if reminder_time is None:
            return Response(
                {"error": "Invalid time format. Use HH:MM or HH:MM:SS."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        owner: User = cast(User, request.user)
        try:
            profile = owner.userprofile
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "UserProfile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        profile.reminder_time = reminder_time
        profile.save(update_fields=["reminder_time"])
        return Response(
            {"success": True, "message": "Reminder time updated."},
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Bank Details
# ---------------------------------------------------------------------------


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_owner_bank_details(
    request: Request, /, *args: Any, **kwargs: Any
) -> Response:
    """Update owner bank details and register beneficiary with Cashfree.

    Fixed: Added missing uuid import.
    Fixed: Uses register_beneficiary from cashfree_service.
    Fixed: Uses correct RentRecord field (owner) instead of renter__property__owner.
    """
    from properties.models.rent_record_models import RentRecord  # nosonar

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
    RentRecord.objects.filter(unit__owner=owner, payout_status="FAILED").update(
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
def rent_inflow_summary(request: Request, /, *args: Any, **kwargs: Any) -> Response:
    """Owner rent inflow summary.

    Fixed: Uses correct RentRecord field (owner) and (amount) and (PENDING).
    """
    from properties.models.rent_record_models import RentRecord  # nosonar

    owner: User = cast(User, request.user)
    total_received = (
        RentRecord.objects.filter(unit__owner=owner, status="PAID").aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    pending_count = RentRecord.objects.filter(
        unit__owner=owner, status="PENDING"
    ).count()

    failed_payouts = RentRecord.objects.filter(
        unit__owner=owner, payout_status="FAILED"
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
def owner_rent_records(request: Request, /, *args: Any, **kwargs: Any) -> Response:
    """Owner rent records list.

    Fixed: Uses correct FK path (unit.owner, renter.name, unit.unit).
    """
    from properties.models.rent_record_models import RentRecord  # nosonar

    owner: User = cast(User, request.user)
    rents = (
        RentRecord.objects.filter(unit__owner=owner)
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
def download_rent_excel(request: Request, /, *args: Any, **kwargs: Any) -> HttpResponse:
    """Download owner rent report as Excel."""
    file = generate_owner_rent_report(request.user)
    response = HttpResponse(file, content_type="application/vnd.ms-excel")
    response["Content-Disposition"] = 'attachment; filename="rent_report.xlsx"'
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_ca_summary(request: Request, /, *args: Any, **kwargs: Any) -> HttpResponse:
    """Download owner CA summary as CSV or JSON."""
    from properties.services.ca_summary_service import (
        generate_ca_summary_csv,
        generate_ca_summary_json,
    )

    start_date = request.query_params.get("start")
    end_date = request.query_params.get("end")
    fmt = request.query_params.get("format", "csv").lower()

    if not start_date or not end_date:
        return Response(
            {"error": "start and end query parameters are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if fmt == "json":
        data = generate_ca_summary_json(request.user, start_date, end_date)
        content_type = "application/json"
        filename = f"ca_summary_{start_date}_to_{end_date}.json"
    else:
        data = generate_ca_summary_csv(request.user, start_date, end_date)
        content_type = "text/csv"
        filename = f"ca_summary_{start_date}_to_{end_date}.csv"

    response = HttpResponse(data, content_type=content_type)
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tax_saving_tips(request: Request, /, *args: Any, **kwargs: Any) -> Response:
    """Return personalized tax saving suggestions for the authenticated user."""
    tips = suggest_tax_savings(request.user)
    return Response({"tax_saving_tips": tips})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_tax_report(request: Request, /, *args: Any, **kwargs: Any) -> HttpResponse:
    """Generate and return a downloadable income tax report PDF."""
    pdf_path = generate_tax_report_pdf(request.user)
    try:
        with open(pdf_path, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="tax_report.pdf"'
            return response
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


# ---------------------------------------------------------------------------
# Authentication Endpoints
# ---------------------------------------------------------------------------


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {"error": "User is inactive"}, status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)
        group = user.groups.first()
        role = group.name if group else "user"
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.pk,
                    "phone": user.phone,
                    "email": user.email,
                    "firstName": user.first_name,
                    "lastName": user.last_name,
                    "fullName": user.full_name,
                    "username": user.username,
                    "role": role,
                },
            },
            status=status.HTTP_200_OK,
        )


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if data["password"] != data["confirmPassword"]:
            return Response(
                {"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=data["email"]).exists():
            return Response(
                {"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST
            )

        base_username = data["phone"]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        user = User.objects.create(
            username=username,
            email=data["email"],
            first_name=data["firstName"],
            last_name=data["lastName"],
            full_name=f"{data['firstName']} {data['lastName']}",
            phone=data["phone"],
        )
        user.set_password(data["password"])
        user.save()

        group, _ = Group.objects.get_or_create(name=data["role"])
        user.groups.add(group)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.pk,
                    "phone": user.phone,
                    "email": user.email,
                    "firstName": user.first_name,
                    "lastName": user.last_name,
                    "fullName": user.full_name,
                    "username": user.username,
                    "role": data["role"],
                },
            },
            status=status.HTTP_201_CREATED,
        )


class SocialAuthView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = SocialAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        provider = serializer.validated_data["provider"]
        token = serializer.validated_data["token"]

        if provider not in ("google", "apple"):
            return Response(
                {"error": "Invalid provider"}, status=status.HTTP_400_BAD_REQUEST
            )

        verified_email = ""
        verified_name = ""

        try:
            if provider == "google":
                verified_email, verified_name = _verify_google_token(token)
            elif provider == "apple":
                verified_email, verified_name = _verify_apple_token(token)
        except ImproperlyConfigured as exc:
            logger.warning("Social auth provider not configured: %s", exc)
            return Response(
                {"error": str(exc)},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )
        except Exception:
            logger.exception("Social auth token verification failed")
            return Response(
                {"error": "Failed to verify social token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = verified_email or request.data.get("email", "")
        full_name = verified_name or request.data.get("name", "")

        if not email:
            return Response(
                {"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": email,
                    "full_name": full_name,
                    "phone": "",
                },
            )

            if created:
                user.set_unusable_password()
                user.save()
                group, _ = Group.objects.get_or_create(name="user")
                user.groups.add(group)

            refresh = RefreshToken.for_user(user)
            group = user.groups.first()
            role = group.name if group else "user"
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": {
                        "id": user.pk,
                        "phone": user.phone,
                        "email": user.email,
                        "firstName": user.first_name,
                        "lastName": user.last_name,
                        "fullName": user.full_name,
                        "username": user.username,
                        "role": role,
                    },
                    "isNewUser": created,
                },
                status=status.HTTP_200_OK,
            )
        except Exception:
            logger.exception("Social auth user creation failed")
            return Response(
                {"error": "Failed to create or retrieve user account"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        serializer = ProfileSerializer(user)
        return Response({"user": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        serializer = ProfileSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"user": serializer.data}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            logger.exception("Logout failed")
        return Response(
            {"message": "Logged out successfully"}, status=status.HTTP_200_OK
        )


class LogoutAllDevicesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = cast(User, request.user)
        try:
            outstanding_tokens = OutstandingToken.objects.filter(user=user)
            for token in outstanding_tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception:
            logger.exception("Logout from all devices failed")
            return Response(
                {"error": "Failed to logout from all devices"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            {"message": "Logged out from all devices"}, status=status.HTTP_200_OK
        )


class BiometricSetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        user.userprofile.biometric_enabled = True
        user.userprofile.save(update_fields=["biometric_enabled"])
        return Response(
            {"message": "Biometric enabled", "isBiometricEnabled": True},
            status=status.HTTP_200_OK,
        )


class BiometricDisableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        user.userprofile.biometric_enabled = False
        user.userprofile.save(update_fields=["biometric_enabled"])
        return Response(
            {"message": "Biometric disabled", "isBiometricEnabled": False},
            status=status.HTTP_200_OK,
        )


class DeviceRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response({"message": "Device registered"}, status=status.HTTP_200_OK)


class AppVersionView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        version = AppVersion.get_active()
        return Response(
            {
                "isUpdateRequired": version.is_force_update,
                "isOptional": False,
                "latestVersion": version.latest_version,
                "minSupportedVersion": version.min_supported_version,
                "storeUrl": version.store_url,
            },
            status=status.HTTP_200_OK,
        )


class MaintenanceView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        mode = MaintenanceMode.get_active()
        return Response(
            {
                "isMaintenance": mode.is_active,
                "message": mode.message,
                "scheduledAt": mode.scheduled_at,
            },
            status=status.HTTP_200_OK,
        )


class BootstrapView(APIView):
    """Single-call bootstrap endpoint that returns all data needed at app startup.

    Response is the same for authenticated and unauthenticated callers:
    - Maintenance status is always returned.
    - App version info is always returned.
    - If the caller is authenticated, user profile, subscription, feature limits,
      add-ons, and dashboard summary are also returned.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        mode = MaintenanceMode.get_active()
        version = AppVersion.get_active()

        data: dict[str, Any] = {
            "maintenance": {
                "isMaintenance": mode.is_active,
                "message": mode.message,
                "scheduledAt": mode.scheduled_at,
            },
            "appVersion": {
                "isUpdateRequired": version.is_force_update,
                "isOptional": False,
                "latestVersion": version.latest_version,
                "minSupportedVersion": version.min_supported_version,
                "storeUrl": version.store_url,
            },
        }

        if request.user.is_authenticated:
            user = request.user
            role = (
                "owner"
                if user.groups.filter(name="owner").exists()
                else "renter" if user.groups.filter(name="renter").exists() else "user"
            )
            perms: set[str] = set()
            for group in user.groups.all():
                perms.update(group.permissions.values_list("codename", flat=True))

            data["user"] = {
                "id": user.pk,
                "phone": user.phone,
                "email": user.email,
                "firstName": user.first_name,
                "lastName": user.last_name,
                "fullName": user.full_name,
                "username": user.username,
                "role": role,
                "permissions": sorted(perms),
            }

            try:
                subscription = user.usersubscription
                data["subscription"] = {
                    "id": subscription.id,
                    "user": subscription.user_id,
                    "plan": {
                        "id": subscription.plan_id,
                        "name": subscription.plan.name if subscription.plan else "free",
                        "monthly_price": (
                            str(subscription.plan.monthly_price)
                            if subscription.plan
                            else "0"
                        ),
                        "yearly_price": (
                            str(subscription.plan.yearly_price)
                            if subscription.plan
                            else "0"
                        ),
                        "features": (
                            subscription.plan.features if subscription.plan else ""
                        ),
                        "is_active": (
                            subscription.plan.is_active if subscription.plan else False
                        ),
                    },
                    "start_date": str(subscription.start_date),
                    "end_date": str(subscription.end_date),
                    "is_active": subscription.is_active,
                    "is_yearly": subscription.is_yearly,
                    "tax_reminder_days_before": subscription.tax_reminder_days_before,
                    "rent_reminder_days_before": subscription.rent_reminder_days_before,
                    "created_at": subscription.created_at,
                    "updated_at": subscription.updated_at,
                }
            except UserSubscription.DoesNotExist:
                data["subscription"] = None

            addons = AddOnPurchase.objects.filter(user=user)
            data["addOns"] = AddOnPurchaseSerializer(addons, many=True).data

            limits = UsageLimit.objects.filter(user=user)
            data["featureLimits"] = UsageLimitSerializer(limits, many=True).data

            from properties.views.owner_dashboard import owner_dashboard_summary

            if role == "owner":
                try:
                    dashboard_response = owner_dashboard_summary(
                        type("FakeRequest", (), {"user": user, "GET": {}})(),
                    )
                    data["dashboardSummary"] = dashboard_response.data
                except Exception:  # noqa: BLE001
                    data["dashboardSummary"] = None
            else:
                data["dashboardSummary"] = None

        return Response(data, status=status.HTTP_200_OK)
