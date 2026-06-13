"""Feature enforcement for subscription plans and add-on quotas.

The :class:`FeatureEnforcer` is the single source of truth for plan-based
feature gating across the application. All methods are fully typed.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import TYPE_CHECKING, Literal, Union

from django.db.models import Sum
from django.utils import timezone

from core.models import (
    AddOnPurchase,
    PlanFeatureLimit,
    SubscriptionPlan,
    UsageLimit,
    UserSubscription,
)

from .constants import GRACE_PERIOD_DAYS

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

#: A limit value is either a concrete non-negative ``int`` or the literal
#: string ``"unlimited"`` (which is never consumed numerically).
FeatureLimit = Union[int, Literal["unlimited"]]


class FeatureEnforcer:
    """Enforce plan + add-on limits for a given user."""

    def __init__(self, user: AbstractUser) -> None:
        """Store the target user; no DB I/O happens here."""
        self.user: AbstractUser = user

    # ------------------------------------------------------------------
    # Subscription helpers
    # ------------------------------------------------------------------

    def get_plan_name(self) -> str:
        """Return the lower-cased plan name, or ``"free"`` if unsubscribed."""
        try:
            return self.user.usersubscription.plan.name.lower()
        except UserSubscription.DoesNotExist:
            return "free"

    def _coerce_date(self, value: date | datetime | None) -> date | None:
        """Coerce a ``datetime`` to ``date``; pass-through otherwise."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        return value

    def is_expired(self) -> bool:
        """Return ``True`` when the user's subscription end-date is in the past."""
        try:
            sub: UserSubscription = self.user.usersubscription
        except UserSubscription.DoesNotExist:
            return False
        end_date: date | None = self._coerce_date(sub.end_date)
        return bool(end_date and end_date < timezone.localdate())

    def is_past_grace_period(self, grace_days: int | None = None) -> bool:
        """Return ``True`` when the subscription has been expired for more
        than ``grace_days`` days.
        """
        if grace_days is None:
            grace_days = GRACE_PERIOD_DAYS
        try:
            sub: UserSubscription = self.user.usersubscription
        except UserSubscription.DoesNotExist:
            return False
        end_date: date | None = self._coerce_date(sub.end_date)
        if not end_date:
            return False
        expired_since: date = timezone.localdate() - end_date
        return expired_since.days > grace_days

    # ------------------------------------------------------------------
    # Limit lookups
    # ------------------------------------------------------------------

    def _get_plan_limit(self, key: str) -> FeatureLimit:
        """Return the plan's hard limit for ``key`` (or ``"unlimited"``)."""
        try:
            sub: UserSubscription = self.user.usersubscription
            limit_value: str = PlanFeatureLimit.objects.get(
                plan=sub.plan, feature_key=key
            ).value
        except UserSubscription.DoesNotExist:
            return 0
        except PlanFeatureLimit.DoesNotExist:
            return 0

        if limit_value == "unlimited":
            return "unlimited"
        try:
            return int(limit_value)
        except ValueError:
            logger.warning(
                "PlanFeatureLimit for key=%r is not numeric and not 'unlimited'",
                key,
            )
            return 0

    def _get_addon_limit(self, key: str) -> int:
        """Sum of all add-on purchases for the user/feature."""
        addon_sum = AddOnPurchase.objects.filter(user=self.user, name=key).aggregate(
            total=Sum("amount")
        )["total"]
        return int(addon_sum) if addon_sum else 0

    def _get_free_plan_limit(self, key: str) -> FeatureLimit:
        """Resolve the limit from the ``free`` plan as a safe fallback."""
        try:
            free_plan: SubscriptionPlan = SubscriptionPlan.objects.get(
                name__iexact="free"
            )
            limit: str = PlanFeatureLimit.objects.get(
                plan=free_plan, feature_key=key
            ).value
        except (SubscriptionPlan.DoesNotExist, PlanFeatureLimit.DoesNotExist):
            return 0
        if limit == "unlimited":
            return "unlimited"
        try:
            return int(limit)
        except ValueError:
            return 0

    def get_free_plan_limit(self, key: str) -> FeatureLimit:
        """Public alias for :meth:`_get_free_plan_limit`."""
        return self._get_free_plan_limit(key)

    def get_active_limit(self, key: str) -> FeatureLimit:
        """Return the effective limit (plan + add-ons) for the given feature.

        Falls back to the free plan if the user is unsubscribed or the
        subscription is past the grace period.
        """
        try:
            _subscription: UserSubscription = self.user.usersubscription
        except UserSubscription.DoesNotExist:
            return self._get_free_plan_limit(key)

        if self.is_expired() and self.is_past_grace_period():
            return self._get_free_plan_limit(key)

        plan_limit: FeatureLimit = self._get_plan_limit(key)
        if plan_limit == "unlimited":
            return "unlimited"

        addon_limit: int = self._get_addon_limit(key)
        return plan_limit + addon_limit

    # ------------------------------------------------------------------
    # Quota mutations
    # ------------------------------------------------------------------

    def can_create(self, key: str) -> bool:
        """Return ``True`` if the user can create one more of ``key``."""
        limit: FeatureLimit = self.get_active_limit(key)
        if limit == "unlimited":
            return True

        current_usage: UsageLimit | None = UsageLimit.objects.filter(
            user=self.user, feature_key=key
        ).first()
        current_count: int = current_usage.usage_count if current_usage else 0
        return current_count < limit

    def increment(self, key: str) -> None:
        """Increment the user's usage counter for ``key`` by 1."""
        obj: UsageLimit
        obj, _ = UsageLimit.objects.get_or_create(user=self.user, feature_key=key)
        obj.usage_count += 1
        obj.save()

    def decrement(self, key: str) -> None:
        """Decrement the user's usage counter for ``key`` by 1 (floor 0)."""
        obj: UsageLimit
        obj, _ = UsageLimit.objects.get_or_create(user=self.user, feature_key=key)
        if obj.usage_count > 0:
            obj.usage_count -= 1
            obj.save()
