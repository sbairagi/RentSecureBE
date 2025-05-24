from wealth_concierge_platform.models import UsageLimit, UserSubscription, Property
from rest_framework.exceptions import PermissionDenied

def get_plan_limit(user, feature_key):
    try:
        from .models import PlanFeatureLimit
        plan = user.usersubscription.plan
        limit = PlanFeatureLimit.objects.get(plan=plan, feature_key=feature_key)
        return limit.value
    except:
        return None

def has_remaining_usage(user, feature_key):
    plan_limit = get_plan_limit(user, feature_key)
    if plan_limit in ['unlimited', 'yes']:
        return True
    try:
        from .models import UsageLimit
        allowed = int(plan_limit)
        used = UsageLimit.objects.get(user=user, feature_key=feature_key).usage_count
        return used < allowed
    except:
        return False

# Helper function to update feature usage counts
def update_usage_count(user, feature_key, model_class):
    if not user.is_authenticated:
        return

    if model_class == Property:
        count = model_class.objects.filter(owner=user).count()
    else:
        count = model_class.objects.filter(property__owner=user).count()

    usage_limit, _ = UsageLimit.objects.get_or_create(user=user, feature_key=feature_key)
    usage_limit.usage_count = count
    usage_limit.save()

def enforce_limit(user, feature_key):
    if not user.is_authenticated:
        return

    # 1. Get the active subscription
    subscription = UserSubscription.objects.filter(user=user, is_active=True).first()
    if not subscription:
        raise PermissionDenied("No active subscription found.")

    # 2. Get feature limit for the user’s plan
    try:
        from .models import PlanFeatureLimit
        feature_limit = PlanFeatureLimit.objects.get(plan=subscription.plan, feature_key=feature_key)
    except PlanFeatureLimit.DoesNotExist:
        raise PermissionDenied(f"Feature limit for {feature_key} not found in plan.")

    allowed_value = feature_limit.value

    # 3. Get current usage
    usage = UsageLimit.objects.filter(user=user, feature_key=feature_key).first()
    current_usage = usage.usage_count if usage else 0

    # 4. Enforce logic
    if allowed_value.lower() in ['unlimited', 'yes']:
        return  # No restriction

    if allowed_value.lower() == 'no':
        raise PermissionDenied(f"This feature ({feature_key}) is not available in your plan.")

    if current_usage >= int(allowed_value):
        raise PermissionDenied(f"Feature limit exceeded for {feature_key}: allowed {allowed_value}, used {current_usage}.")