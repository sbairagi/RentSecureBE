from __future__ import annotations

import secrets
from datetime import timedelta

from twilio.rest import Client

from django.conf import settings
from django.utils import timezone

from core.services.base import BaseService
from shared.exceptions import ValidationError

from ..models import OTP


class OTPService(BaseService):
    """Service for OTP workflows.

    Expected responsibilities:
    - OTP generation and storage
    - OTP delivery via chosen channel
    - OTP verification and rate limiting
    - OTP expiration handling
    """

    @staticmethod
    def send_otp(phone_number: str, referral_code: str = "") -> None:
        # Prevent spamming (resend OTP limit: 60 seconds)
        recent_otp = (
            OTP.objects.filter(phone_number=phone_number)
            .order_by("-created_at")
            .first()
        )
        if recent_otp and (timezone.now() - recent_otp.created_at).seconds < 60:
            raise ValidationError("Wait before requesting another OTP")

        code = str(secrets.randbelow(900000) + 100000)
        OTP.objects.create(
            phone_number=phone_number, code=code, referral_code=referral_code
        )
        _deliver_otp(phone_number, code)

    @staticmethod
    def verify(phone: str, code: str) -> OTP:
        otp = (
            OTP.objects.filter(phone_number=phone, code=code, is_verified=False)
            .order_by("-created_at")
            .first()
        )

        if not otp or (timezone.now() - otp.created_at) >= timedelta(minutes=5):
            raise ValidationError("Invalid or expired OTP")

        otp.is_verified = True
        otp.save()

        OTP.objects.filter(phone_number=phone).exclude(pk=otp.pk).delete()

        return otp


def _deliver_otp(phone_number: str, code: str) -> None:
    if not settings.DEBUG:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = f"Your verification code is {code}"
        client.messages.create(
            body=message, from_=settings.TWILIO_PHONE_NUMBER, to=phone_number
        )
    else:
        print(f"[MOCK OTP to {phone_number}] Your OTP is {code}")
