from django.utils import timezone
from core.models import UsageLimit, PlanFeatureLimit, AddOnPurchase, UserSubscription
from django.db.models import Sum

class FeatureEnforcer:
    def __init__(self, user):
        self.user = user

    def get_plan_name(self):
        try:
            return self.user.usersubscription.plan.name.lower()
        except UserSubscription.DoesNotExist:
            return 'free'

    def is_expired(self):
        try:
            sub = self.user.usersubscription
            return sub.end_date and sub.end_date < timezone.now()
        except UserSubscription.DoesNotExist:
            return False  # free user, not expired

    def is_past_grace_period(self, grace_days=7):
        try:
            sub = self.user.usersubscription
            if not sub.end_date:
                return False
            expired_since = timezone.now() - sub.end_date
            return expired_since.days > grace_days
        except UserSubscription.DoesNotExist:
            return False

    def _get_plan_limit(self, key):
        try:
            sub = self.user.usersubscription
            limit_value = PlanFeatureLimit.objects.get(plan=sub.plan, feature_key=key).value
            if limit_value == 'unlimited':
                return 'unlimited'
            return int(limit_value)
        except (UserSubscription.DoesNotExist, PlanFeatureLimit.DoesNotExist, ValueError):
            return 0

    def _get_addon_limit(self, key):
        # Sum all add-ons of this feature_key for the user
        addon_sum = AddOnPurchase.objects.filter(user=self.user, name=key).aggregate(
            total=Sum('amount')
        )['total']
        return int(addon_sum) if addon_sum else 0

    def _get_free_plan_limit(self, key):
        from core.models import SubscriptionPlan
        try:
            free_plan = SubscriptionPlan.objects.get(name__iexact='free')
            limit = PlanFeatureLimit.objects.get(plan=free_plan, feature_key=key).value
            if limit == 'unlimited':
                return 'unlimited'
            return int(limit)
        except (SubscriptionPlan.DoesNotExist, PlanFeatureLimit.DoesNotExist, ValueError):
            return 0

    def get_active_limit(self, key):
        # If subscription expired and past grace period, fallback to free plan limits
        if self.is_expired() and self.is_past_grace_period():
            return self._get_free_plan_limit(key)

        plan_limit = self._get_plan_limit(key)
        if plan_limit == 'unlimited':
            return 'unlimited'

        addon_limit = self._get_addon_limit(key)
        return plan_limit + addon_limit

    def can_create(self, key):
        limit = self.get_active_limit(key)
        if limit == 'unlimited':
            return True

        current_usage = UsageLimit.objects.filter(user=self.user, feature_key=key).first()
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

