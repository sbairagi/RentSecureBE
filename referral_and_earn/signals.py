# signals.py

from typing import Any

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.events.domain.publisher import DomainEventPublisher

from .models import Referral


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_referral(sender: Any, instance: Any, created: bool, **kwargs: Any) -> None:
    if created:
        referral = Referral.objects.create(user=instance)

        from uuid import UUID

        from django.db import transaction

        from core.events.domain.user_events import ReferralCreated

        event = ReferralCreated(
            aggregate_id=UUID(int=referral.pk),
            user_id=UUID(int=instance.pk),
            referral_code=referral.referral_code,
        )

        transaction.on_commit(
            lambda: DomainEventPublisher.get_instance().publish(event)
        )
