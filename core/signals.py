# core/signals.py
from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import NotificationPreference, User, UserProfile

from .models import PlanFeatureLimit, SubscriptionPlan, UserSubscription
from .plan_limits import FREE_PLAN_LIMITS


@receiver(post_save, sender=User)
def assign_default_plan(
    sender: type[Any],
    instance: User,
    created: bool,
    **kwargs: Any,
) -> None:
    if created:
        if not hasattr(instance, "userprofile"):
            UserProfile.objects.create(user=instance)
        if not hasattr(instance, "notification_preference"):
            NotificationPreference.objects.create(owner=instance)
        default_plan, _ = SubscriptionPlan.objects.get_or_create(
            name="free",
            defaults={
                "monthly_price": 0,
                "yearly_price": 0,
                "features": "Free plan",
                "is_active": True,
            },
        )
        for feature_key, value in FREE_PLAN_LIMITS.items():
            PlanFeatureLimit.objects.get_or_create(
                plan=default_plan,
                feature_key=feature_key,
                defaults={"value": value},
            )
        UserSubscription.objects.create(user=instance, plan=default_plan)
