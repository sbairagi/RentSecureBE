from django.dispatch import receiver
from wealth_concierge_platform.models import Unit, Caretaker, Renter, UnitImage, UnitDocument, Building
from django.db.models.signals import post_save, post_delete
from wealth_concierge_platform.utils import update_usage_count

# Building usage update
@receiver(post_save, sender=Building)
@receiver(post_delete, sender=Building)
def update_building_usage(sender, instance, **kwargs):
    update_usage_count(instance.owner, 'max_buldings', Building)

# Unit usage update
@receiver(post_save, sender=Unit)
@receiver(post_delete, sender=Unit)
def update_unit_usage(sender, instance, **kwargs):
    update_usage_count(instance.owner, 'max_units', Unit)

# Caretaker usage update
@receiver(post_save, sender=Caretaker)
@receiver(post_delete, sender=Caretaker)
def update_caretaker_usage(sender, instance, **kwargs):
    update_usage_count(instance.unit.owner, 'max_caretakers', Caretaker)

# Renter usage update
@receiver(post_save, sender=Renter)
@receiver(post_delete, sender=Renter)
def update_renter_usage(sender, instance, **kwargs):
    update_usage_count(instance.unit.owner, 'max_renters', Renter)

# Unit Images usage update
@receiver(post_save, sender=UnitImage)
@receiver(post_delete, sender=UnitImage)
def update_unit_images_usage(sender, instance, **kwargs):
    update_usage_count(instance.unit.owner, 'max_unit_images', UnitImage)

# Unit Document usage update
@receiver(post_save, sender=UnitDocument)
@receiver(post_delete, sender=UnitDocument)
def update_unit_document_usage(sender, instance, **kwargs):
    update_usage_count(instance.unit.owner, 'max_documents_uploads', UnitDocument)