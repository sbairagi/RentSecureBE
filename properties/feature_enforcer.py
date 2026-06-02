from datetime import datetime

from django.db.models import Sum
from django.utils import timezone

from core.models import AddOnPurchase, PlanFeatureLimit, UsageLimit, UserSubscription

from .constants import GRACE_PERIOD_DAYS


class FeatureEnforcer:
    def __init__(self, user):
        self.user = user

    def get_plan_name(self):
        try:
            return self.user.usersubscription.plan.name.lower()
        except UserSubscription.DoesNotExist:
            return "free"

    def _coerce_date(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        return value

    def is_expired(self):
        try:
            sub = self.user.usersubscription
            end_date = self._coerce_date(sub.end_date)
            return bool(end_date and end_date < timezone.localdate())
        except UserSubscription.DoesNotExist:
            return False  # free user, not expired

    def is_past_grace_period(self, grace_days=None):
        if grace_days is None:
            grace_days = GRACE_PERIOD_DAYS
        try:
            sub = self.user.usersubscription
            end_date = self._coerce_date(sub.end_date)
            if not end_date:
                return False
            expired_since = timezone.localdate() - end_date
            return expired_since.days > grace_days
        except UserSubscription.DoesNotExist:
            return False

    def _get_plan_limit(self, key):
        try:
            sub = self.user.usersubscription
            limit_value = PlanFeatureLimit.objects.get(
                plan=sub.plan, feature_key=key
            ).value
            if limit_value == "unlimited":
                return "unlimited"
            return int(limit_value)
        except UserSubscription.DoesNotExist:
            return 0
        except PlanFeatureLimit.DoesNotExist:
            return 0
        except ValueError:
            return 0

    def _get_addon_limit(self, key):
        # Sum all add-ons of this feature_key for the user
        addon_sum = AddOnPurchase.objects.filter(user=self.user, name=key).aggregate(
            total=Sum("amount")
        )["total"]
        return int(addon_sum) if addon_sum else 0

    def _get_free_plan_limit(self, key):
        from core.models import SubscriptionPlan

        try:
            free_plan = SubscriptionPlan.objects.get(name__iexact="free")
            limit = PlanFeatureLimit.objects.get(plan=free_plan, feature_key=key).value
            if limit == "unlimited":
                return "unlimited"
            return int(limit)
        except (
            SubscriptionPlan.DoesNotExist,
            PlanFeatureLimit.DoesNotExist,
            ValueError,
        ):
            return 0

    def get_free_plan_limit(self, key):
        return self._get_free_plan_limit(key)

    def get_active_limit(self, key):
        # If user has no subscription, use free plan limits.
        try:
            _subscription = self.user.usersubscription
        except UserSubscription.DoesNotExist:
            return self._get_free_plan_limit(key)

        # If subscription is expired and past grace period, fallback to free plan limits
        if self.is_expired() and self.is_past_grace_period():
            return self._get_free_plan_limit(key)

        plan_limit = self._get_plan_limit(key)
        if plan_limit == "unlimited":
            return "unlimited"

        addon_limit = self._get_addon_limit(key)
        return plan_limit + addon_limit

    def can_create(self, key):
        limit = self.get_active_limit(key)
        if limit == "unlimited":
            return True

        current_usage = UsageLimit.objects.filter(
            user=self.user, feature_key=key
        ).first()
        current_count = current_usage.usage_count if current_usage else 0
        return current_count < limit

    def increment(self, key):
        obj, _ = UsageLimit.objects.get_or_create(user=self.user, feature_key=key)
        obj.usage_count += 1
        obj.save()

    def decrement(self, key):
        obj, _ = UsageLimit.objects.get_or_create(user=self.user, feature_key=key)
        if obj.usage_count > 0:
            obj.usage_count -= 1
            obj.save()
