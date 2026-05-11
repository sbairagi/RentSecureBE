from datetime import timezone
from django.dispatch import receiver
from notification.services.voice_note_service import send_thank_you_voice_note
from notification.models import Notification
from notification.services.services import notify_owner_renter_flagged
from ai_assistant.services.archive_service import archive_renter_data
from ai_assistant.services.invoice_service import generate_final_invoice_pdf
from ..models import Unit, Caretaker, Renter, UnitImage, UnitDocument, Building, RentRecord
from django.db.models.signals import post_save, post_delete
from properties.scheduler import cancel_reminder_job
from properties.utils import update_usage_count


@receiver(post_save, sender=Building)
@receiver(post_delete, sender=Building)
def update_building_usage(sender, instance, **kwargs):
    update_usage_count(instance.owner, 'max_buldings', Building)


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
        owner = instance.unit.building.owner
        unit = instance.unit

        if not Renter.objects.filter(unit=unit, status="active").exists():
            from notification.services.whatsapp_service import send_whatsapp_message
            send_whatsapp_message(
                owner.profile.whatsapp_number,
                f"🏠 Unit {unit.unit_number} is now vacant. Please assign a new renter or mark it as intentionally vacant from your dashboard."
            )


@receiver(post_save, sender=Renter)
def generate_final_invoice_on_exit(sender, instance, **kwargs):
    if instance.status in ["notice_period", "deactivated", "revoked"]:
        latest_rent = RentRecord.objects.filter(renter=instance).last()
        if latest_rent:
            pdf_path = generate_final_invoice_pdf(instance, latest_rent)
            instance.final_invoice_path = pdf_path
            instance.save(update_fields=["final_invoice_path"])

        if instance.status in ["revoked", "deactivated"]:
            archive_renter_data(instance)
