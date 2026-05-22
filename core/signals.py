# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import NotificationPreference, User, UserProfile

from .models import SubscriptionPlan, UserSubscription


@receiver(post_save, sender=User)
def assign_default_plan(sender, instance, created, **kwargs):
    if created:
        if not hasattr(instance, 'userprofile'):
            UserProfile.objects.create(user=instance)
        if not hasattr(instance, 'notification_preference'):
            NotificationPreference.objects.create(owner=instance)
        default_plan, _ = SubscriptionPlan.objects.get_or_create(
            name='free',
            defaults={
                'monthly_price': 0,
                'yearly_price': 0,
                'is_active': True,
            }
        )
        UserSubscription.objects.create(user=instance, plan=default_plan)
