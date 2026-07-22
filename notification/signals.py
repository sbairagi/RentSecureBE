from django.db.models.signals import post_save
from django.dispatch import receiver

from core.events.domain.publisher import DomainEventPublisher
from core.models import User
from core.signals import otp_created
from notification.models import NotificationPreference
from notification.services.notification_service import NotificationService


@receiver(post_save, sender=User)
def create_notification_preference(
    sender: type[object],
    instance: User,
    created: bool,
    **kwargs: object,
) -> None:
    if created:
        if not hasattr(instance, "notification_preferences"):
            NotificationPreference.objects.create(owner=instance)

            from uuid import UUID

            from django.db import transaction

            from core.events.domain.user_events import UserPreferencesCreated

            event = UserPreferencesCreated(aggregate_id=UUID(int=instance.pk))

            transaction.on_commit(
                lambda: DomainEventPublisher.get_instance().publish(event)
            )


@receiver(otp_created)
def send_otp_notification(
    sender: type[object],
    phone_number: str,
    code: str,
    **kwargs: object,
) -> None:
    NotificationService().send_otp(phone_number, code)
