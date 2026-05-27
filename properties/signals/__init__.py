from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from ai_assistant.services.archive_service import archive_renter_data
from ai_assistant.services.invoice_service import generate_final_invoice_pdf
from notification.models import Notification
from notification.services.services import notify_owner_renter_flagged
from notification.services.voice_note_service import send_thank_you_voice_note
from properties.scheduler import cancel_reminder_job
from properties.utils import update_usage_count
from properties.utils.onboarding_utils import generate_onboarding_token

from ..models import (
    Building,
    Caretaker,
    ArchivedRenter,
    Renter,
    RentRecord,
    Unit,
    UnitDocument,
    UnitImage,
)
from ..services.unit_service import update_unit_status


@receiver(post_save, sender=Renter)
def generate_renter_onboarding_token(sender, instance, created, **kwargs):
    if created and not instance.onboarding_token:
        generate_onboarding_token(instance)


@receiver(post_save, sender=Renter)
def update_unit_status_on_renter_save(sender, instance, **kwargs):
    update_unit_status(instance.unit)


@receiver(post_delete, sender=Renter)
def update_unit_status_on_renter_delete(sender, instance, **kwargs):
    update_unit_status(instance.unit)


@receiver(post_save, sender=Building)
@receiver(post_delete, sender=Building)
def update_building_usage(sender, instance, **kwargs):
    update_usage_count(instance.owner, 'max_buildings', Building)


@receiver(post_save, sender=Unit)
@receiver(post_delete, sender=Unit)
def update_unit_usage(sender, instance, **kwargs):
    update_usage_count(instance.owner, 'max_units', Unit)


@receiver(post_save, sender=Caretaker)
@receiver(post_delete, sender=Caretaker)
def update_caretaker_usage(sender, instance, **kwargs):
    update_usage_count(instance.unit.owner, 'max_caretakers', Caretaker)


@receiver(post_save, sender=Renter)
@receiver(post_delete, sender=Renter)
def update_renter_usage(sender, instance, **kwargs):
    update_usage_count(instance.unit.owner, 'max_renters', Renter)


@receiver(post_save, sender=UnitImage)
@receiver(post_delete, sender=UnitImage)
def update_unit_images_usage(sender, instance, **kwargs):
    update_usage_count(instance.unit.owner, 'max_unit_images', UnitImage)


@receiver(post_save, sender=UnitDocument)
@receiver(post_delete, sender=UnitDocument)
def update_unit_document_usage(sender, instance, **kwargs):
    update_usage_count(instance.unit.owner, 'max_documents_uploads', UnitDocument)


@receiver(post_save, sender=RentRecord)
def handle_rent_payment(sender, instance, **kwargs):
    if instance.payment_status == "PAID":
        cancel_reminder_job(f"rent_{instance.id}")
        send_thank_you_voice_note(instance)

        if instance.renter.user:
            Notification.objects.create(
                user=instance.renter.user,
                title="Thanks for Early Rent Payment",
                message="We appreciate your on-time rent payment. Keep it up! 🏆"
            )

        # Send rent receipt email to renter
        try:
            from properties.services.receipt_service import send_rent_receipt_on_payment
            send_rent_receipt_on_payment(instance)
        except Exception as exc:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(
                f"Failed to send receipt email for rent {instance.id}: {exc}"
            )


def update_renter_defaulter_status(rent: RentRecord):
    if rent.status == "UNPAID" and rent.due_date < timezone.now().date():
        renter = rent.renter
        renter.missed_rents += 1
        if renter.missed_rents >= 3 and not renter.is_flagged:
            renter.is_flagged = True
            renter.flagged_reason = "Missed 3 or more rent payments."
            renter.active_agreement = None
            notify_owner_renter_flagged(renter)
        renter.save()


@receiver(post_save, sender=Renter)
def notify_owner_if_unit_vacant(sender, instance, **kwargs):
    if instance.status in ["deactivated", "revoked"]:
        owner = instance.unit.owner
        unit = instance.unit

        if not Renter.objects.filter(unit=unit, status="active").exists():
            from notification.services.whatsapp_service import send_whatsapp_message
            phone = getattr(
                getattr(owner, "userprofile", None),
                "whatsapp_number",
                getattr(owner, "whatsapp_number", ""),
            )
            if phone:
                send_whatsapp_message(
                    phone,
                    (
                        f"Unit {unit.unit_number} is now vacant. "
                        f"Please assign a new renter or mark it as "
                        f"intentionally vacant from your dashboard."
                    ),
                )


@receiver(post_save, sender=Renter)
def generate_final_invoice_on_exit(sender, instance, **kwargs):
    update_fields = kwargs.get("update_fields")
    if update_fields and set(update_fields).issubset(
        {"onboarding_token", "onboarding_link_sent_at"}
    ):
        return

    if instance.status in ["notice_period", "deactivated", "revoked"]:
        latest_rent = RentRecord.objects.filter(renter=instance).last()
        if latest_rent:
            pdf_path = generate_final_invoice_pdf(instance, latest_rent)
            instance.final_invoice_path = pdf_path
            instance.save(update_fields=["final_invoice_path"])

        if instance.status in ["revoked", "deactivated"]:
            if not ArchivedRenter.objects.filter(renter=instance).exists():
                archive_renter_data(instance)
