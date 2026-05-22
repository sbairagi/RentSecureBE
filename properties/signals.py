"""
Django Signals for Properties App

Handles automated business logic triggers:
- Auto-update unit status when renters are created/updated/deactivated
- Sync denormalized fields
- Trigger notifications
"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Renter
from .services.unit_service import update_unit_status
from .utils.onboarding_utils import generate_onboarding_token


@receiver(post_save, sender=Renter)
def generate_renter_onboarding_token(sender, instance, created, **kwargs):
    """Generate onboarding token for new renters."""
    if created and not instance.onboarding_token:
        generate_onboarding_token(instance)


@receiver(post_save, sender=Renter)
def update_unit_status_on_renter_save(sender, instance, created, **kwargs):
    """
    Auto-update unit status whenever a renter is created or updated.

    Triggered when:
    - New renter is created (created=True)
    - Renter status changes (e.g., active → notice_period → deactivated)
    - Renter is revoked

    This ensures unit occupancy status stays in sync with renter records.
    """
    update_unit_status(instance.unit)


@receiver(post_save, sender=Renter)
def update_last_vacated_date_on_renter_exit(sender, instance, **kwargs):
    """Track the date the unit became vacant when the renter is exiting."""
    if instance.status in [
        Renter.RenterStatus.NOTICE_PERIOD,
        Renter.RenterStatus.REVOKED,
        Renter.RenterStatus.DEACTIVATED,
    ]:
        unit = instance.unit
        if not unit.current_renter:
            today = timezone.now().date()
            if unit.last_vacated_at != today:
                unit.last_vacated_at = today
                unit.save(update_fields=['last_vacated_at'])


@receiver(post_delete, sender=Renter)
def update_unit_status_on_renter_delete(sender, instance, **kwargs):
    """
    Auto-update unit status when a renter is deleted.

    This handles cases where:
    - A renter record is permanently deleted
    - The unit should revert to vacant if this was the only renter
    """
    update_unit_status(instance.unit)
