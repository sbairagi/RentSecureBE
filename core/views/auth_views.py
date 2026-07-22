from __future__ import annotations

import logging
from typing import Any

from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import OTP, User
from core.services.auth_service import AuthService
from core.services.otp_service import OTPService
from core.services.password_service import PasswordService
from core.services.referral_service import ReferralService
from shared.exceptions import ValidationError
from shared.type_compat import override

logger = logging.getLogger(__name__)


class SendOTP(APIView):
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        phone = request.data.get("phone")
        referral_code = request.data.get("referral_code", "").strip()

        if not phone:
            return Response({"error": "Phone number required"}, status=400)

        try:
            OTPService.send_otp(phone, referral_code)
        except ValidationError as e:
            return Response({"error": str(e)}, status=429)

        return Response({"message": "OTP sent"}, status=200)


def _process_referral(otp: OTP, user: User) -> Response | None:
    """Shared referral logic for owner/renter OTP verification."""
    try:
        ReferralService.process_referral(otp, user)
    except ValidationError as e:
        return Response({"error": str(e)}, status=400)
    return None


def _verify_otp_and_login(
    phone: str | None, code: str | None, group_name: str
) -> tuple[dict[str, object], int]:
    """Shared OTP verification logic for owner/renter login.

    Returns (response_dict, status_code) tuple.
    """
    if not phone or not code:
        return {"error": "Phone and OTP required"}, 400

    try:
        otp = OTPService.verify(phone, code)
    except ValidationError as e:
        return {"error": str(e)}, 400

    user, tokens = AuthService.login_with_otp(phone, group_name)

    # Referral logic
    error_response = _process_referral(otp, user)
    if error_response is not None:
        return {"error": "Invalid referral code"}, 400

    # Delete old OTPs
    OTP.objects.filter(phone_number=phone).exclude(pk=otp.pk).delete()

    return tokens, 200


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


class ChangePasswordView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return self.update(request, *args, **kwargs)

    @override
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        old_password = request.data.get("old_password") or ""
        new_password = request.data.get("new_password") or ""

        try:
            PasswordService.change_password(user, old_password, new_password)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        return Response({"message": "Password changed successfully."}, status=200)


class ResetPasswordView(APIView):
    """Password reset — requires authentication to prevent account takeover.

    Users can only reset their own password.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        new_password = request.data.get("new_password") or ""

        try:
            PasswordService.reset_password(request.user, new_password)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        return Response({"message": "Password reset successful."}, status=200)
