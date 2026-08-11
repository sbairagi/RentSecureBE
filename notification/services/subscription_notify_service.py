import logging

from django.utils import timezone

from core.models import UserSubscription
from notification.models import Notification
from notification.services.orchestrator import dispatch_notification

logger = logging.getLogger(__name__)


def check_subscription_expiry() -> None:
    today = timezone.now().date()
    for subscription in UserSubscription.objects.filter(is_active=True):
        if subscription.end_date and subscription.end_date <= today:
            _notify_subscription_expired(subscription)
        elif subscription.end_date:
            days_left = (subscription.end_date - today).days
            if days_left <= 7:
                _notify_subscription_expiring(subscription, days_left)


def _notify_subscription_expiring(
    subscription: UserSubscription, days_left: int
) -> None:
    user = subscription.user
    if not user:
        return
    dispatch_notification(
        user=user,
        title="Subscription Expiring Soon",
        message=(
            f"Your {subscription.plan.name} subscription expires in "
            f"{days_left} day(s). Renew now to avoid service interruption."
        ),
        notification_type=Notification.SUBSCRIPTION_EXPIRING,
        resource_type="subscription",
        resource_id=str(subscription.id),
        priority=Notification.PRIORITY_HIGH,
    )


def _notify_subscription_expired(subscription: UserSubscription) -> None:
    user = subscription.user
    if not user:
        return
    dispatch_notification(
        user=user,
        title="Subscription Expired",
        message=(
            f"Your {subscription.plan.name} subscription has expired. "
            "Please renew to continue using premium features."
        ),
        notification_type=Notification.SUBSCRIPTION_EXPIRED,
        resource_type="subscription",
        resource_id=str(subscription.id),
        priority=Notification.PRIORITY_URGENT,
    )
