import logging
from typing import Any

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from visitors.models import Visitor, VisitorHistory

logger = logging.getLogger(__name__)


def _log_history(
    visitor: Visitor,
    action: str,
    description: str = "",
    performed_by: Any = None,
    metadata: dict | None = None,
) -> None:
    try:
        VisitorHistory.objects.create(
            visitor=visitor,
            action=action,
            description=description,
            performed_by=performed_by,
            metadata=metadata or {},
        )
    except Exception:
        logger.exception(
            "Failed to create visitor history entry for visitor %s", visitor.id
        )


@receiver(pre_save, sender=Visitor)
def track_visitor_status_change(sender, instance: Visitor, **kwargs: Any) -> None:
    if instance.pk:
        try:
            old_instance = Visitor.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                _log_history(
                    visitor=instance,
                    action=instance.status,
                    description=(
                        f"Status changed from {old_instance.status}"
                        f" to {instance.status}"
                    ),
                    performed_by=getattr(instance, "_current_user", None),
                )
        except Visitor.DoesNotExist:
            pass


@receiver(post_save, sender=Visitor)
def handle_visitor_post_save(
    sender, instance: Visitor, created: bool, **kwargs: Any
) -> None:
    if created:
        _log_history(
            visitor=instance,
            action=VisitorHistory.Action.CREATED,
            description=f"Visitor request created by {instance.created_by}",
            performed_by=instance.created_by,
            metadata={
                "visitor_name": instance.visitor_name,
                "renter_id": instance.renter_id,
                "unit_id": instance.unit_id,
                "building_id": instance.building_id,
            },
        )
        logger.info(
            "Visitor request created: ID=%s, name=%s",
            instance.id,
            instance.visitor_name,
        )

    if instance.status == Visitor.Status.APPROVED and instance.approved_by:
        logger.info(
            "Visitor %s approved by %s — notification can be triggered here",
            instance.id,
            instance.approved_by.id,
        )

    if instance.status == Visitor.Status.CHECKED_IN:
        logger.info(
            "Visitor %s checked in by %s",
            instance.id,
            instance.verified_by_id,
        )

    if instance.status == Visitor.Status.CHECKED_OUT:
        logger.info("Visitor %s checked out", instance.id)
