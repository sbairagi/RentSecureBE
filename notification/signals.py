import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from notification.models import Notification
from notification.services.notifications import send_fcm_notification

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Notification)
def dispatch_push_on_notification_create(
    sender: type[Notification], instance: Notification, created: bool, **kwargs: object
) -> None:
    if not created:
        return

    try:
        from core.models import NotificationPreference

        pref, _ = NotificationPreference.objects.get_or_create(owner=instance.user)
        if not pref.push_enabled:
            return

        type_pref_map = {
            Notification.RENT_DUE: "rent_alerts_push",
            Notification.RENT_PAYMENT_SUCCESS: "rent_alerts_push",
            Notification.RENT_PAYMENT_FAILED: "rent_alerts_push",
            Notification.AGREEMENT_EXPIRING: "agreement_push",
            Notification.AGREEMENT_SIGNED: "agreement_push",
            Notification.MAINTENANCE_CREATED: "maintenance_push",
            Notification.MAINTENANCE_UPDATED: "maintenance_push",
            Notification.VISITOR_REQUEST: "visitor_push",
            Notification.VISITOR_APPROVED: "visitor_push",
            Notification.SUBSCRIPTION_EXPIRING: "subscription_push",
            Notification.SUBSCRIPTION_EXPIRED: "subscription_push",
            Notification.DOCUMENT_SHARED: "system_push",
            Notification.SYSTEM_ALERT: "system_push",
            Notification.PAYOUT_SUCCESS: "payout_alerts_whatsapp",
            Notification.PAYOUT_FAILED: "payout_alerts_whatsapp",
            Notification.RENTER_STATUS_CHANGE: "rent_alerts_push",
            Notification.ITR_REMINDER: "system_push",
            Notification.TAX_REMINDER: "system_push",
            Notification.EXTRA_CHARGE_REMINDER: "rent_alerts_push",
        }

        pref_key = type_pref_map.get(instance.notification_type)
        if pref_key and not getattr(pref, pref_key, False):
            return

        data = {
            "notification_id": str(instance.id),
            "type": instance.notification_type,
            "resource_type": instance.resource_type,
            "resource_id": instance.resource_id,
            "action": instance.action_url or "view",
        }
        if instance.data:
            data.update(instance.data)

        send_fcm_notification(
            user=instance.user,
            title=instance.title,
            body=instance.message,
            data=data,
            notification_type=instance.notification_type,
        )
    except Exception:
        logger.exception("Failed to dispatch push for notification %s", instance.id)
