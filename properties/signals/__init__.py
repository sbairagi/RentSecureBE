import logging
from collections.abc import Iterable
from typing import cast

from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone

from notification.models import Notification
from properties.models import (
    ArchivedRenter,
    Building,
    Caretaker,
    CareTakerAssignmentLog,
    PropertyTaxRecord,
    Renter,
    RentRecord,
    Unit,
    UnitDocument,
    UnitImage,
)
from properties.scheduler import cancel_reminder_job
from properties.signals.renter_signals import renter_archived, renter_exited
from properties.utils.onboarding_utils import generate_onboarding_token
from properties.utils.utils import update_usage_count

from ..services.unit_service import update_unit_status

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Renter)
def update_last_vacated_date_on_renter_exit(
    sender: type[Renter], instance: Renter, **kwargs: object
) -> None:
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
                unit.save(update_fields=["last_vacated_at"])


@receiver(post_save, sender=Renter)
def generate_renter_onboarding_token(
    sender: type[Renter], instance: Renter, created: bool, **kwargs: object
) -> None:
    """Generate onboarding token for new renters."""
    if created and not instance.onboarding_token:
        generate_onboarding_token(instance)


@receiver(post_save, sender=Renter)
def update_unit_status_on_renter_save(
    sender: type[Renter], instance: Renter, **kwargs: object
) -> None:
    """
    Auto-update unit status whenever a renter is created or updated.

    Triggered when:
    - New renter is created (created=True)
    - Renter status changes (e.g., active → notice_period → deactivated)
    - Renter is revoked

    This ensures unit occupancy status stays in sync with renter records.
    """
    update_unit_status(instance.unit)


@receiver(post_delete, sender=Renter)
def update_unit_status_on_renter_delete(
    sender: type[Renter], instance: Renter, **kwargs: object
) -> None:
    """
    Auto-update unit status when a renter is deleted.

    This handles cases where:
    - A renter record is permanently deleted
    - The unit should revert to vacant if this was the only renter
    """
    update_unit_status(instance.unit)


@receiver(post_save, sender=Building)
@receiver(post_delete, sender=Building)
def update_building_usage(
    sender: type[Building], instance: Building, **kwargs: object
) -> None:
    update_usage_count(instance.owner, "max_buildings", Building)


@receiver(post_save, sender=Unit)
@receiver(post_delete, sender=Unit)
def update_unit_usage(sender: type[Unit], instance: Unit, **kwargs: object) -> None:
    update_usage_count(instance.owner, "max_units", Unit)


@receiver(post_save, sender=Caretaker)
@receiver(post_delete, sender=Caretaker)
def update_caretaker_usage(
    sender: type[Caretaker], instance: Caretaker, **kwargs: object
) -> None:
    update_usage_count(instance.unit.owner, "max_caretakers", Caretaker)


@receiver(post_save, sender=Caretaker)
def log_caretaker_assignment(
    sender: type[Caretaker], instance: Caretaker, created: bool, **kwargs: object
) -> None:
    if created:
        CareTakerAssignmentLog.objects.create(
            caretaker=instance,
            action="assigned",
            notes=f"Assigned to unit {instance.unit_id}",
        )
    else:
        CareTakerAssignmentLog.objects.create(
            caretaker=instance,
            action="assigned",
            notes=f"Reassigned to unit {instance.unit_id}",
        )


@receiver(pre_delete, sender=Caretaker)
def log_caretaker_unassignment(
    sender: type[Caretaker], instance: Caretaker, **kwargs: object
) -> None:
    CareTakerAssignmentLog.objects.create(
        caretaker=instance,
        action="unassigned",
        notes=f"Unassigned from unit {instance.unit_id}",
    )


@receiver(post_save, sender=Renter)
@receiver(post_delete, sender=Renter)
def update_renter_usage(
    sender: type[Renter], instance: Renter, **kwargs: object
) -> None:
    update_usage_count(instance.unit.owner, "max_renters", Renter)


@receiver(post_save, sender=UnitImage)
@receiver(post_delete, sender=UnitImage)
def update_unit_images_usage(
    sender: type[UnitImage], instance: UnitImage, **kwargs: object
) -> None:
    update_usage_count(instance.unit.owner, "max_unit_images", UnitImage)


@receiver(post_save, sender=UnitDocument)
@receiver(post_delete, sender=UnitDocument)
def update_unit_documents_usage(
    sender: type[UnitDocument], instance: UnitDocument, **kwargs: object
) -> None:
    update_usage_count(instance.unit.owner, "max_unit_images", UnitDocument)


@receiver(post_save, sender=RentRecord)
def handle_rent_payment(
    sender: type[RentRecord], instance: RentRecord, **kwargs: object
) -> None:
    if instance.status == RentRecord.Status.PAID:
        from notification.services.voice_note_service import send_thank_you_voice_note

        cancel_reminder_job(f"rent_{instance.id}")
        send_thank_you_voice_note(instance)

        if instance.renter and instance.renter.user:
            Notification.objects.create(
                user=instance.renter.user,
                title="Thanks for Early Rent Payment",
                message="We appreciate your on-time rent payment. Keep it up! 🏆",
            )

        # Send multilingual rent paid confirmation via WhatsApp
        try:
            from notification.services.voice_service import generate_voice_note
            from notification.services.whatsapp_service import (
                send_whatsapp_audio,
                send_whatsapp_message,
            )
            from rentsecure_be.services.message_template_service import (
                get_rent_paid_confirmation_msg,
            )

            renter = instance.renter
            if renter and renter.whatsapp_number:
                user_profile = getattr(getattr(renter, "user", None), "profile", None)
                lang = getattr(user_profile, "language_preference", None) or "en"
                msg = get_rent_paid_confirmation_msg(
                    name=renter.full_name,
                    amount=instance.amount,
                    paid_date=instance.updated_at,
                    lang=lang,
                )
                send_whatsapp_message(
                    renter.whatsapp_number,
                    msg,
                    user=getattr(renter, "user", None),
                    rent_record=instance,
                )

                try:
                    audio_path = generate_voice_note(msg, lang)
                    if audio_path:
                        send_whatsapp_audio(
                            renter.whatsapp_number,
                            audio_path,
                            user=getattr(renter, "user", None),
                            rent_record=instance,
                        )
                except Exception:
                    logger.exception(
                        "Failed to send rent-paid audio for rent %s",
                        instance.id,
                    )
        except Exception as exc:
            logger.exception(
                "Failed to send rent-paid confirmation for rent %s: %s",
                instance.id,
                exc,
            )

        # Send rent receipt email to renter
        try:
            from properties.services.receipt_service import send_rent_receipt_on_payment

            send_rent_receipt_on_payment(instance)
        except Exception as exc:
            logger.exception(
                f"Failed to send receipt email for rent {instance.id}: {exc}"
            )


def update_renter_defaulter_status(rent: RentRecord) -> None:
    if (
        rent.status == RentRecord.Status.PENDING
        and rent.due_date < timezone.now().date()
    ):
        from notification.services.services import notify_owner_renter_flagged

        renter = rent.renter
        if renter is None:
            return
        renter.missed_rents += 1
        if renter.missed_rents >= 3 and not renter.is_flagged:
            renter.is_flagged = True
            renter.flagged_reason = "Missed 3 or more rent payments."
            try:
                notify_owner_renter_flagged(renter)
            except Exception as e:
                logger.warning(
                    f"Failed to notify owner about flagged renter {renter.id}: {e}"
                )
        renter.save(
            update_fields=["missed_rents", "is_flagged", "flagged_reason", "updated_at"]
        )


@receiver(pre_save, sender=Renter)
def notify_renter_status_change(
    sender: type[Renter], instance: Renter, **kwargs: object
) -> None:
    if not instance.pk:
        return

    try:
        old = Renter.objects.get(pk=instance.pk)
    except Renter.DoesNotExist:
        return

    if old.status == instance.status:
        return

    if instance.status not in {
        Renter.RenterStatus.NOTICE_PERIOD,
        Renter.RenterStatus.REVOKED,
        Renter.RenterStatus.DEACTIVATED,
    }:
        return

    from notification.services.renter_status_notify_service import (
        send_renter_status_change_notification,
    )

    try:
        send_renter_status_change_notification(instance, old.status, instance.status)
    except Exception:
        logger.exception(
            "Failed to send status change notification for renter %s",
            instance.id,
        )


@receiver(pre_save, sender=Renter)
def update_renter_status_changed_at(
    sender: type[Renter], instance: Renter, **kwargs: object
) -> None:
    if not instance.pk:
        return

    try:
        old = Renter.objects.get(pk=instance.pk)
    except Renter.DoesNotExist:
        return

    if old.status != instance.status:
        instance.status_changed_at = timezone.now()


@receiver(post_save, sender=Renter)
def notify_owner_if_unit_vacant(
    sender: type[Renter], instance: Renter, **kwargs: object
) -> None:
    if instance.status in ["deactivated", "revoked"]:
        owner = instance.unit.owner
        unit = instance.unit

        if not Renter.objects.filter(unit=unit, status="active").exists():
            from notification.services.whatsapp_service import send_whatsapp_message

            profile = getattr(owner, "userprofile", None)
            phone = (
                getattr(profile, "whatsapp_number", None) if profile else None
            ) or getattr(owner, "whatsapp_number", "")
            if phone:
                send_whatsapp_message(
                    phone,
                    (
                        f"Unit {unit.unit} is now vacant. "
                        f"Please assign a new renter or mark it as "
                        f"intentionally vacant from your dashboard."
                    ),
                    user=owner,
                    rent_record=None,
                )


@receiver(post_save, sender=Renter)
def generate_final_invoice_on_exit(
    sender: type[Renter], instance: Renter, **kwargs: object
) -> None:
    update_fields = kwargs.get("update_fields")
    if _is_onboarding_update(update_fields):
        return

    if instance.status not in {"notice_period", "deactivated", "revoked"}:
        return

    _generate_final_invoice_if_needed(instance)

    if instance.status in {"revoked", "deactivated"}:
        _archive_renter_if_needed(instance)


def _is_onboarding_update(update_fields: object) -> bool:
    if update_fields is None:
        return False
    allowed = {"onboarding_token", "onboarding_link_sent_at"}
    return set(cast(Iterable[str], update_fields)).issubset(allowed)


def _generate_final_invoice_if_needed(instance: Renter) -> None:
    latest_rent = RentRecord.objects.filter(renter=instance).last()
    if not latest_rent:
        return

    renter_exited.send(sender=Renter, instance=instance, latest_rent=latest_rent)


def _archive_renter_if_needed(instance: Renter) -> None:
    if ArchivedRenter.objects.filter(renter=instance).exists():
        return
    renter_archived.send(sender=Renter, instance=instance)


@receiver(post_save, sender=PropertyTaxRecord)
def notify_owner_on_tax_paid(
    sender: type[PropertyTaxRecord], instance: PropertyTaxRecord, **kwargs: object
) -> None:
    if not instance.paid:
        return

    owner = instance.property.owner
    phone = getattr(owner, "whatsapp_number", None) or ""
    if not phone:
        return

    try:
        from notification.services.rent_notify_service import notify_owner

        msg = (
            f"✅ Property tax of ₹{instance.amount} has been paid for "
            f"{instance.property.name} on {instance.paid_date}."
        )
        notify_owner(owner, msg)
    except Exception as exc:
        logger.exception(
            "Failed to send tax-paid notification for tax %s: %s",
            instance.id,
            exc,
        )
