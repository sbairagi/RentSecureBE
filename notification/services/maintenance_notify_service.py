import logging
from typing import Any

from notification.models import Notification
from notification.services.orchestrator import dispatch_notification
from notification.services.rent_notify_service import _owner_greeting_prefix

logger = logging.getLogger(__name__)


def notify_maintenance_created(maintenance: Any) -> None:
    renter = getattr(maintenance, "renter", None)
    owner = getattr(maintenance, "owner", None)
    if not renter and not owner:
        return

    title = "New Maintenance Request"
    message = (
        f"A new maintenance request '{maintenance.title}' has been created "
        f"for unit {getattr(getattr(maintenance, 'unit', None), 'unit', '')}."
    )

    if renter and getattr(renter, "user", None):
        dispatch_notification(
            user=renter.user,
            title=title,
            message=message,
            notification_type=Notification.MAINTENANCE_CREATED,
            resource_type="maintenance",
            resource_id=str(maintenance.id),
            priority=getattr(maintenance, "priority", Notification.PRIORITY_MEDIUM),
        )

    if owner:
        greeting = _owner_greeting_prefix(owner)
        dispatch_notification(
            user=owner,
            title=title,
            message=greeting + message,
            notification_type=Notification.MAINTENANCE_CREATED,
            resource_type="maintenance",
            resource_id=str(maintenance.id),
            priority=getattr(maintenance, "priority", Notification.PRIORITY_MEDIUM),
        )


def notify_maintenance_updated(
    maintenance: Any, old_status: str, new_status: str
) -> None:
    renter = getattr(maintenance, "renter", None)
    owner = getattr(maintenance, "owner", None)
    if not renter and not owner:
        return

    title = "Maintenance Update"
    message = (
        f"Maintenance request '{maintenance.title}' status changed "
        f"from {old_status} to {new_status}."
    )

    if renter and getattr(renter, "user", None):
        dispatch_notification(
            user=renter.user,
            title=title,
            message=message,
            notification_type=Notification.MAINTENANCE_UPDATED,
            resource_type="maintenance",
            resource_id=str(maintenance.id),
        )

    if owner:
        greeting = _owner_greeting_prefix(owner)
        dispatch_notification(
            user=owner,
            title=title,
            message=greeting + message,
            notification_type=Notification.MAINTENANCE_UPDATED,
            resource_type="maintenance",
            resource_id=str(maintenance.id),
        )


def notify_maintenance_assigned(maintenance: Any, caretaker: Any) -> None:
    renter = getattr(maintenance, "renter", None)
    owner = getattr(maintenance, "owner", None)

    title = "Maintenance Assigned"
    message = (
        f"Maintenance request '{maintenance.title}' has been assigned "
        f"to {getattr(caretaker, 'name', 'a caretaker')}."
    )

    if renter and getattr(renter, "user", None):
        dispatch_notification(
            user=renter.user,
            title=title,
            message=message,
            notification_type=Notification.MAINTENANCE_UPDATED,
            resource_type="maintenance",
            resource_id=str(maintenance.id),
        )

    if owner:
        greeting = _owner_greeting_prefix(owner)
        dispatch_notification(
            user=owner,
            title=title,
            message=greeting + message,
            notification_type=Notification.MAINTENANCE_UPDATED,
            resource_type="maintenance",
            resource_id=str(maintenance.id),
        )
