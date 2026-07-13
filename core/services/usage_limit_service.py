from __future__ import annotations

from typing import Any

from core.models import AddOnPurchase, UsageLimit
from core.services.base import BaseService, ServiceResult
from core.services.subscription_service import SubscriptionService


class UsageLimitService(BaseService):
    """Service for usage-limit enforcement.

    Expected responsibilities:
    - Current usage calculation
    - Limit comparison
    - Limit-exceeded handling
    - Reset scheduling
    """

    @staticmethod
    def get_user_usage_limits(user: Any) -> Any:
        return UsageLimit.objects.filter(user=user)

    @staticmethod
    def get_active_subscription(user: Any) -> Any | None:
        return SubscriptionService.get_active_subscription(user)

    @staticmethod
    def get_user_addon_purchases(user: Any) -> Any:
        return SubscriptionService.get_user_addon_purchases(user)

    @staticmethod
    def is_feature_available(user: Any, feature_key: str) -> bool:
        subscription = UsageLimitService.get_active_subscription(user)
        if not subscription:
            return False
        return subscription.plan.planfeaturelimit_set.filter(
            feature_key=feature_key, value__in=["yes", "unlimited"]
        ).exists()

    @staticmethod
    def get_effective_limit(user: Any, feature_key: str) -> int | float | None:
        subscription = UsageLimitService.get_active_subscription(user)
        if not subscription:
            addon = (
                AddOnPurchase.objects.filter(user=user, name=feature_key)
                .order_by("-purchase_date")
                .first()
            )
            if addon:
                return None
            return None

        plan_limit = subscription.plan.planfeaturelimit_set.filter(
            feature_key=feature_key
        ).first()
        if not plan_limit:
            return None

        if plan_limit.value == "unlimited":
            return float("inf")

        try:
            base = int(plan_limit.value)
        except (TypeError, ValueError):
            return None

        addon = (
            AddOnPurchase.objects.filter(user=user, name=feature_key)
            .order_by("-purchase_date")
            .first()
        )
        if addon:
            return base

        return base

    @staticmethod
    def get_used_units(user: Any, feature_key: str) -> int:
        limit = UsageLimit.objects.filter(user=user, feature_key=feature_key).first()
        return limit.usage_count if limit else 0

    @staticmethod
    def has_remaining_usage(user: Any, feature_key: str) -> bool:
        subscription = UsageLimitService.get_active_subscription(user)
        if not subscription:
            return False

        plan_limit = subscription.plan.planfeaturelimit_set.filter(
            feature_key=feature_key
        ).first()
        if not plan_limit:
            return False

        if plan_limit.value == "unlimited":
            return True

        try:
            limit = int(plan_limit.value)
        except (TypeError, ValueError):
            return False

        used = UsageLimitService.get_used_units(user, feature_key)
        return used < limit

    def execute(self, *args: Any, **kwargs: Any) -> ServiceResult[Any]:
        raise NotImplementedError
