import hashlib
from datetime import date

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from core.models import AddOnPurchase, PlanFeatureLimit, UsageLimit, UserSubscription
from notification.services.late_fees_notify_service import (
    notify_owner_about_late_fee,
    notify_renter_about_late_fee,
)
from properties.feature_enforcer import FeatureEnforcer
from properties.models import RentRecord, Unit


def get_plan_limit(user, feature_key):
    try:
        from core.models import PlanFeatureLimit
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
        allowed = int(plan_limit)
        used = UsageLimit.objects.get(user=user, feature_key=feature_key).usage_count
        return used < allowed
    except:
        return False


def update_usage_count(user, feature_key, model_class):
    if not user.is_authenticated:
        return

    if model_class == Unit:
        count = model_class.objects.filter(owner=user).count()
    elif model_class.__name__ == 'Building':
        count = model_class.objects.filter(owner=user).count()
    else:
        count = model_class.objects.filter(unit__owner=user).count()

    usage_limit, _ = UsageLimit.objects.get_or_create(user=user, feature_key=feature_key)
    usage_limit.usage_count = count
    usage_limit.save()


def enforce_limit(user, feature_key):
    if not user.is_authenticated:
        return

    subscription = UserSubscription.objects.filter(user=user, is_active=True).first()
    if not subscription:
        raise PermissionDenied("No active subscription found.")

    try:
        from core.models import PlanFeatureLimit
        feature_limit = PlanFeatureLimit.objects.get(
            plan=subscription.plan, feature_key=feature_key
        )
    except PlanFeatureLimit.DoesNotExist as e:
        raise PermissionDenied(
            f"Feature limit for {feature_key} not found in plan."
        ) from e

    allowed_value = feature_limit.value
    usage = UsageLimit.objects.filter(user=user, feature_key=feature_key).first()
    current_usage = usage.usage_count if usage else 0

    if allowed_value.lower() in ['unlimited', 'yes']:
        return

    if allowed_value.lower() == 'no':
        raise PermissionDenied(
            f"This feature ({feature_key}) is not available in your plan."
        )

    if current_usage >= int(allowed_value):
        raise PermissionDenied(
            f"Feature limit exceeded for {feature_key}: "
            f"allowed {allowed_value}, used {current_usage}."
        )


def generate_file_hash(file):
    """Generate SHA256 hash for uploaded file content"""
    hash_sha256 = hashlib.sha256()
    for chunk in file.chunks():
        hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def _normalize_feature_limit_value(value):
    if value is None:
        return 0
    if isinstance(value, str):
        lower = value.strip().lower()
        if lower in ['unlimited', 'yes']:
            return 'unlimited'
        if lower in ['no']:
            return 0
        try:
            return int(lower)
        except ValueError:
            return 0
    return value


def check_feature_limit(user, feature_key):
    """
    Check whether the user can create a resource under a feature limit.

    Returns a tuple: (allowed, current_usage, subscription_limit, add_on_limit)
    """
    subscription_limit = 0
    add_on_limit = 0
    current_usage = 0

    try:
        subscription = user.usersubscription
        plan_limit = PlanFeatureLimit.objects.filter(
            plan=subscription.plan,
            feature_key=feature_key
        ).first()
        if plan_limit is not None:
            subscription_limit = _normalize_feature_limit_value(plan_limit.value)
    except UserSubscription.DoesNotExist:
        subscription_limit = 0

    addon_sum = AddOnPurchase.objects.filter(user=user, name=feature_key).aggregate(
        total=Sum('amount')
    )['total']
    add_on_limit = int(addon_sum) if addon_sum else 0

    usage = UsageLimit.objects.filter(user=user, feature_key=feature_key).first()
    current_usage = usage.usage_count if usage else 0

    if subscription_limit == 'unlimited':
        return True, current_usage, subscription_limit, add_on_limit

    total_allowed = subscription_limit + add_on_limit
    allowed = current_usage < total_allowed
    return allowed, current_usage, subscription_limit, add_on_limit


def get_feature_limit(user, feature_key):
    from core.models import PlanFeatureLimit
    addon = UsageLimit.objects.filter(user=user, feature_key=feature_key).first()
    if addon:
        return int(addon.usage_count)
    plan = user.usersubscription.plan
    plan_limit = PlanFeatureLimit.objects.filter(plan=plan, feature_key=feature_key).first()
    if not plan_limit:
        return 0
    return float('inf') if plan_limit.value == 'unlimited' else int(plan_limit.value)


def get_limit_for_source(source, feature_key):
    if isinstance(source, UserSubscription):
        return PlanFeatureLimit.objects.get(plan=source.plan, feature_key=feature_key).value
    elif isinstance(source, AddOnPurchase):
        return source.features.get(feature_key, 0)
    return 0


def get_used_units(user, feature_key, source):
    filters = {
        'user': user,
        'feature_key': feature_key,
    }
    if isinstance(source, UserSubscription):
        filters['user_subscription'] = source
    else:
        filters['addon_purchase'] = source
    return UsageLimit.objects.filter(**filters).aggregate(total=Sum('used_units'))['total'] or 0


def deduct_feature_usage_with_priority(user, feature_key, units_to_deduct=1):
    """Deduct feature usage from the user's subscription and add-ons.

    Fixed: Uses correct fields (usage_count instead of used_units,
    removed references to non-existent fields on AddOnPurchase and UsageLimit).
    """
    enforcer = FeatureEnforcer(user)

    # Check if there's enough capacity
    if not enforcer.can_create(feature_key):
        raise ValidationError(f"Not enough available units for feature: {feature_key}")

    # Simple approach: increment the usage counter
    for _ in range(units_to_deduct):
        if enforcer.can_create(feature_key):
            enforcer.increment(feature_key)
        else:
            raise ValidationError(f"Not enough available units for feature: {feature_key}")


import tempfile

from django.template.loader import render_to_string
from weasyprint import HTML


def generate_rent_invoice_pdf(rent):
    html_string = render_to_string("invoices/rent_invoice.html", {"rent": rent})
    html = HTML(string=html_string)
    result = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    html.write_pdf(target=result.name)
    return result.name



def apply_late_fee_if_needed(rent: RentRecord):
    if rent.payment_status != "PAID":
        return
    if rent.date_paid and rent.date_paid > rent.rent_due_date:
        days_late = (rent.date_paid - rent.rent_due_date).days
        late_fee = days_late * 100
        rent.late_fee = late_fee
        rent.adjustment_reason = f"{days_late} days late x ₹100 = ₹{late_fee}"
        rent.save(update_fields=['late_fee', 'adjustment_reason'])
        next_month = rent.rent_due_date.replace(day=1) + relativedelta(months=1)
        next_rent, _ = RentRecord.objects.get_or_create(
            renter=rent.renter,
            rent_month=next_month,
            defaults={
                "amount_paid": rent.renter.rent_amount,
                "rent_due_date": next_month,
                "payment_status": RentRecord.PaymentStatus.PENDING,
                "unit": rent.unit,
                "owner": rent.owner,
                "date_paid": next_month,
            }
        )
        next_rent.adjustment_reason = f"Late fee from {rent.rent_due_date}"
        next_rent.save(update_fields=['adjustment_reason'])
        notify_renter_about_late_fee(rent, late_fee)
        notify_owner_about_late_fee(rent, late_fee)
