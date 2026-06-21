# core/signals.py
from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import NotificationPreference, User, UserProfile

from .models import PlanFeatureLimit, SubscriptionPlan, UserSubscription


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
        default_limits = {
            "max_buildings": "2",
            "max_units": "3",
            "max_renters": "3",
            "max_caretakers": "1",
            "max_unit_images": "3",
            "max_document_uploads": "2",
            "unit_images": "3",
            "unit_documents": "2",
            "rent_records": "12",
            "rent_agreement_drafts": "1",
        }
        for feature_key, value in default_limits.items():
            PlanFeatureLimit.objects.get_or_create(
                plan=default_plan,
                feature_key=feature_key,
                defaults={"value": value},
            )
        UserSubscription.objects.create(user=instance, plan=default_plan)
