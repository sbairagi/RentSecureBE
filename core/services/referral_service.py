from __future__ import annotations

from typing import Any

from core.services.base import BaseService, ServiceResult
from shared.exceptions import ValidationError


class ReferralService(BaseService):
    """Service for referral workflows.

    Expected responsibilities:
    - Referral code validation
    - Referral link creation
    - Bonus awarding
    """

    @staticmethod
    def process_referral(otp: Any, user: Any) -> None:
        if not otp.referral_code:
            return

        from referral_and_earn.models import Referral

        try:
            referrer_referral = Referral.objects.get(referral_code=otp.referral_code)
        except Referral.DoesNotExist:
            raise ValidationError("Invalid referral code") from None

        referrer = referrer_referral.user
        referral, _ = Referral.objects.get_or_create(user=user)
        if not referral.referred_by:
            referral.referred_by = referrer
            referral.save()
            referrer_referral.bonus_earned += 500
            referrer_referral.save()

    def execute(self, *args: Any, **kwargs: Any) -> ServiceResult[Any]:
        raise NotImplementedError
