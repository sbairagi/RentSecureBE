# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import User, UserProfile
from .models import SubscriptionPlan, UserSubscription

@receiver(post_save, sender=User)
def assign_default_plan(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'usersubscription'):
        UserProfile.objects.create(user=instance)
        try:
            default_plan = SubscriptionPlan.objects.get(name='Free')
            UserSubscription.objects.create(user=instance, plan=default_plan)
        except SubscriptionPlan.DoesNotExist:
            pass
