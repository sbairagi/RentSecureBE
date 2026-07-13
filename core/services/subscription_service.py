from __future__ import annotations

from typing import Any

from core.models import AddOnPurchase, UserSubscription
from core.services.base import BaseService, ServiceResult


class SubscriptionService(BaseService):
    """Service for subscription and usage-limit workflows.

    Expected responsibilities:
    - Subscription plan resolution
    - Usage limit checks
    - Feature flag evaluation
    - Subscription expiry handling
    """

    @staticmethod
    def get_user_subscriptions(user: Any) -> Any:
        return UserSubscription.objects.filter(user=user)

    @staticmethod
    def get_active_subscription(user: Any) -> Any | None:
        return (
            UserSubscription.objects.filter(user=user, is_active=True)
            .select_related("plan")
            .first()
        )

    @staticmethod
    def get_user_addon_purchases(user: Any) -> Any:
        return AddOnPurchase.objects.filter(user=user)

    @staticmethod
    def can_user_modify(user: Any, subscription: Any) -> bool:
        return subscription.user == user

    @staticmethod
    def create_user_subscription(
        user: Any, validated_data: dict[str, Any]
    ) -> UserSubscription:
        validated_data["user"] = user
        user_data = validated_data.pop("user")
        subscription, _ = UserSubscription.objects.update_or_create(
            user=user_data,
            defaults=validated_data,
        )
        return subscription

    def execute(self, *args: Any, **kwargs: Any) -> ServiceResult[Any]:
        raise NotImplementedError
