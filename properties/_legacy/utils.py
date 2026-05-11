from notification.services.late_fees_notify_service import notify_owner_about_late_fee, notify_renter_about_late_fee
from core.models import UsageLimit, UserSubscription, PlanFeatureLimit, AddOnPurchase
from properties.models import RentRecord, Unit
from rest_framework.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Sum
from datetime import date
from dateutil.relativedelta import relativedelta
import hashlib

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
    

def generate_file_hash(file):
    """Generate SHA256 hash for uploaded file content"""
    hash_sha256 = hashlib.sha256()
    for chunk in file.chunks():
        hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def get_feature_limit(user, feature_key):
    # Check Add-on Usage Limit first
    from .models import PlanFeatureLimit
    addon = UsageLimit.objects.filter(user=user, feature_key=feature_key).first()
    if addon:
        return int(addon.usage_count)

    # Fallback to plan limits
    plan = user.usersubscription.plan
    plan_limit = PlanFeatureLimit.objects.filter(plan=plan, feature_key=feature_key).first()
    if not plan_limit:
        return 0
    return float('inf') if plan_limit.value == 'unlimited' else int(plan_limit.value)


def get_limit_for_source(source, feature_key):
    if isinstance(source, UserSubscription):
        return PlanFeatureLimit.objects.get(plan=source.plan, feature_key=feature_key).value
    elif isinstance(source, AddOnPurchase):
        return source.features.get(feature_key, 0)  # assume dict field
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
    """
    Deducts feature usage by scanning active subscriptions and addons
    in priority order. Raises error if usage can't be fulfilled.
    """

    now = timezone.now()

    # 1. Get active user subscriptions ordered by expiry date
    active_subs = UserSubscription.objects.filter(
        user=user,
        is_active=True,
        end_date__gt=now
    ).order_by('end_date')

    # 2. Get active addon purchases ordered by creation
    active_addons = AddOnPurchase.objects.filter(
        user=user,
        is_active=True,
        expires_at__gt=now
    ).order_by('created_at')

    # 3. Merge both into a single priority queue
    usage_sources = list(active_subs) + list(active_addons)

    units_remaining = units_to_deduct

    with transaction.atomic():
        for source in usage_sources:
            limit = get_limit_for_source(source, feature_key)
            used = get_used_units(user, feature_key, source)

            available = limit - used
            if available <= 0:
                continue  # skip this source

            deduct = min(available, units_remaining)

            # Record usage
            UsageLimit.objects.create(
                user=user,
                feature_key=feature_key,
                used_units=deduct,
                user_subscription=source if isinstance(source, UserSubscription) else None,
                addon_purchase=source if isinstance(source, AddOnPurchase) else None,
            )

            units_remaining -= deduct

            if units_remaining <= 0:
                break  # all done

    if units_remaining > 0:
        raise ValidationError(f"Not enough available units for feature: {feature_key}")



# utils/pdf_utils.py
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile

def generate_rent_invoice_pdf(rent):
    html_string = render_to_string("invoices/rent_invoice.html", {"rent": rent})
    html = HTML(string=html_string)
    result = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    html.write_pdf(target=result.name)
    return result.name


# utils/pdf_utils.py
# from django.template.loader import render_to_string
# from weasyprint import HTML
# import os

# def generate_rent_invoice_pdf(rent, output_path):
#     html_content = render_to_string("invoice/rent_invoice.html", {"rent": rent})
#     HTML(string=html_content).write_pdf(output_path)



from datetime import date
from dateutil.relativedelta import relativedelta

def apply_late_fee_if_needed(rent: RentRecord):
    """
    Apply late fee if rent is paid after rent_due_date.
    Adds late fee to next month's rent record.
    """
    if rent.payment_status != "PAID":
        return

    if rent.date_paid and rent.date_paid > rent.rent_due_date:
        days_late = (rent.date_paid - rent.rent_due_date).days
        late_fee = days_late * 100  # ₹100/day
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
