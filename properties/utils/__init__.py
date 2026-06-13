"""Property utility functions.

All helpers here are pure, type-safe, and safe to call from views, services
or management commands. Anything that touches external systems (PDF,
email, notifications) lives in dedicated service modules.
"""

from __future__ import annotations

import hashlib
import tempfile
from typing import TYPE_CHECKING, Literal

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Model, Sum
from django.template.loader import render_to_string
from rest_framework.exceptions import PermissionDenied
from weasyprint import HTML

from core.models import AddOnPurchase, PlanFeatureLimit, UsageLimit, UserSubscription
from notification.services.late_fees_notify_service import (
    notify_owner_about_late_fee,
    notify_renter_about_late_fee,
)
from properties.feature_enforcer import FeatureEnforcer
from properties.models import RentRecord, Unit

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

#: A normalized feature limit is either an integer count or the literal
#: ``"unlimited"``.
FeatureLimit = int | Literal["unlimited"]

#: Result of :func:`check_feature_limit`.
FeatureCheckResult = tuple[bool, int, FeatureLimit, int]


# ---------------------------------------------------------------------------
# Plan / feature helpers
# ---------------------------------------------------------------------------


def get_plan_limit(user: AbstractUser, feature_key: str) -> str | None:
    """Return the raw ``value`` for the user's plan/feature, or ``None``."""
    try:
        plan = user.usersubscription.plan
        limit: PlanFeatureLimit = PlanFeatureLimit.objects.get(
            plan=plan, feature_key=feature_key
        )
    except (
        AttributeError,
        PlanFeatureLimit.DoesNotExist,
        UserSubscription.DoesNotExist,
    ):
        return None
    return limit.value


def has_remaining_usage(user: AbstractUser, feature_key: str) -> bool:
    """Return ``True`` if the user can perform one more action of ``feature_key``."""
    plan_limit: str | None = get_plan_limit(user, feature_key)
    if plan_limit in ("unlimited", "yes"):
        return True
    try:
        allowed: int = int(plan_limit)  # type: ignore[arg-type]
        used: int = UsageLimit.objects.get(
            user=user, feature_key=feature_key
        ).usage_count
    except (TypeError, ValueError, UsageLimit.DoesNotExist):
        return False
    return used < allowed


def update_usage_count(
    user: AbstractUser, feature_key: str, model_class: type[Model]
) -> None:
    """Recompute and persist the user's usage count for ``feature_key``."""
    if not user.is_authenticated:
        return

    if model_class is Unit:
        count: int = model_class.objects.filter(owner=user).count()
    elif model_class.__name__ == "Building":
        count = model_class.objects.filter(owner=user).count()
    else:
        count = model_class.objects.filter(unit__owner=user).count()

    usage_limit: UsageLimit
    usage_limit, _ = UsageLimit.objects.get_or_create(
        user=user, feature_key=feature_key
    )
    usage_limit.usage_count = count
    usage_limit.save()


def enforce_limit(user: AbstractUser, feature_key: str) -> None:
    """Raise :class:`PermissionDenied` if the user cannot use ``feature_key``."""
    if not user.is_authenticated:
        return

    subscription: UserSubscription | None = UserSubscription.objects.filter(
        user=user, is_active=True
    ).first()
    if not subscription:
        raise PermissionDenied("No active subscription found.")

    try:
        feature_limit: PlanFeatureLimit = PlanFeatureLimit.objects.get(
            plan=subscription.plan, feature_key=feature_key
        )
    except PlanFeatureLimit.DoesNotExist as exc:
        raise PermissionDenied(
            f"Feature limit for {feature_key} not found in plan."
        ) from exc

    allowed_value: str = feature_limit.value
    usage: UsageLimit | None = UsageLimit.objects.filter(
        user=user, feature_key=feature_key
    ).first()
    current_usage: int = usage.usage_count if usage else 0

    if allowed_value.lower() in ("unlimited", "yes"):
        return

    if allowed_value.lower() == "no":
        raise PermissionDenied(
            f"This feature ({feature_key}) is not available in your plan."
        )

    if current_usage >= int(allowed_value):
        raise PermissionDenied(
            f"Feature limit exceeded for {feature_key}: "
            f"allowed {allowed_value}, used {current_usage}."
        )


# ---------------------------------------------------------------------------
# File utilities
# ---------------------------------------------------------------------------


def generate_file_hash(file: UploadedFile) -> str:
    """Compute the SHA-256 hex digest of an uploaded file's content."""
    hash_sha256 = hashlib.sha256()
    for chunk in file.chunks():
        hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def _normalize_feature_limit_value(value: object) -> FeatureLimit:
    """Normalize a raw plan-limit string to :data:`FeatureLimit`."""
    if value is None:
        return 0
    if isinstance(value, str):
        lower: str = value.strip().lower()
        if lower in ("unlimited", "yes"):
            return "unlimited"
        if lower == "no":
            return 0
        try:
            return int(lower)
        except ValueError:
            return 0
    if isinstance(value, int):
        return value
    return 0


def check_feature_limit(user: AbstractUser, feature_key: str) -> FeatureCheckResult:
    """Compute whether the user can perform one more action of ``feature_key``.

    Returns:
        A 4-tuple ``(allowed, current_usage, subscription_limit, add_on_limit)``.
    """
    subscription_limit: FeatureLimit = 0
    add_on_limit: int = 0
    current_usage: int = 0

    try:
        subscription: UserSubscription = user.usersubscription
        plan_limit: PlanFeatureLimit | None = PlanFeatureLimit.objects.filter(
            plan=subscription.plan, feature_key=feature_key
        ).first()
        if plan_limit is not None:
            subscription_limit = _normalize_feature_limit_value(plan_limit.value)
    except UserSubscription.DoesNotExist:
        subscription_limit = 0

    addon_sum = AddOnPurchase.objects.filter(user=user, name=feature_key).aggregate(
        total=Sum("amount")
    )["total"]
    add_on_limit = int(addon_sum) if addon_sum else 0

    usage: UsageLimit | None = UsageLimit.objects.filter(
        user=user, feature_key=feature_key
    ).first()
    current_usage = usage.usage_count if usage else 0

    if subscription_limit == "unlimited":
        return True, current_usage, subscription_limit, add_on_limit

    total_allowed: int = subscription_limit + add_on_limit
    allowed: bool = current_usage < total_allowed
    return allowed, current_usage, subscription_limit, add_on_limit


def get_feature_limit(user: AbstractUser, feature_key: str) -> int | float:
    """Return the effective plan limit for ``feature_key`` as a number.

    ``float('inf')`` is returned for unlimited plans so callers can compare
    without special-casing.
    """
    addon: UsageLimit | None = UsageLimit.objects.filter(
        user=user, feature_key=feature_key
    ).first()
    if addon:
        return int(addon.usage_count)

    plan = user.usersubscription.plan
    plan_limit: PlanFeatureLimit | None = PlanFeatureLimit.objects.filter(
        plan=plan, feature_key=feature_key
    ).first()
    if not plan_limit:
        return 0
    return float("inf") if plan_limit.value == "unlimited" else int(plan_limit.value)


def get_limit_for_source(
    source: UserSubscription | AddOnPurchase, feature_key: str
) -> int | str:
    """Return the limit value from a given subscription or add-on source."""
    if isinstance(source, UserSubscription):
        return PlanFeatureLimit.objects.get(
            plan=source.plan, feature_key=feature_key
        ).value
    if isinstance(source, AddOnPurchase):
        return source.features.get(feature_key, 0)
    return 0


def get_used_units(
    user: AbstractUser, feature_key: str, source: UserSubscription | AddOnPurchase
) -> int:
    """Return the units used for ``feature_key`` under the given ``source``."""
    filters: dict[str, object] = {"user": user, "feature_key": feature_key}
    if isinstance(source, UserSubscription):
        filters["user_subscription"] = source
    else:
        filters["addon_purchase"] = source
    used: int = (
        UsageLimit.objects.filter(**filters).aggregate(total=Sum("usage_count"))[
            "total"
        ]
        or 0
    )
    return int(used)


def deduct_feature_usage_with_priority(
    user: AbstractUser, feature_key: str, units_to_deduct: int = 1
) -> None:
    """Deduct ``units_to_deduct`` units from the user's quota."""
    enforcer = FeatureEnforcer(user)
    if not enforcer.can_create(feature_key):
        raise ValidationError(f"Not enough available units for feature: {feature_key}")

    for _ in range(units_to_deduct):
        if enforcer.can_create(feature_key):
            enforcer.increment(feature_key)
        else:
            raise ValidationError(
                f"Not enough available units for feature: {feature_key}"
            )


# ---------------------------------------------------------------------------
# PDF & late-fee helpers
# ---------------------------------------------------------------------------


def generate_rent_invoice_pdf(rent: RentRecord) -> str:
    """Render the rent invoice PDF to a temp file and return the path."""
    html_string: str = render_to_string("invoices/rent_invoice.html", {"rent": rent})
    html = HTML(string=html_string)
    result = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    html.write_pdf(target=result.name)
    return result.name


def apply_late_fee_if_needed(rent: RentRecord) -> None:
    """Apply a late fee and notify both renter and owner if the rent was paid late."""
    if rent.payment_status != "PAID":
        return
    if rent.date_paid is None or rent.date_paid <= rent.rent_due_date:
        return

    days_late: int = (rent.date_paid - rent.rent_due_date).days
    late_fee: int = days_late * 100
    rent.late_fee = late_fee
    rent.adjustment_reason = f"{days_late} days late x ₹100 = ₹{late_fee}"
    rent.save(update_fields=["late_fee", "adjustment_reason"])

    next_month = rent.rent_due_date.replace(day=1) + relativedelta(months=1)
    next_rent: RentRecord
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
        },
    )
    next_rent.adjustment_reason = f"Late fee from {rent.rent_due_date}"
    next_rent.save(update_fields=["adjustment_reason"])
    notify_renter_about_late_fee(rent, late_fee)
    notify_owner_about_late_fee(rent, late_fee)
