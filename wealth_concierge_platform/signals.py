from django.dispatch import receiver
from wealth_concierge_platform.models import Property, Caretaker, Renter, PropertyImage, PropertyDocument
from django.db.models.signals import post_save, post_delete
from wealth_concierge_platform.utils import update_usage_count


# Property usage update
@receiver(post_save, sender=Property)
@receiver(post_delete, sender=Property)
def update_property_usage(sender, instance, **kwargs):
    update_usage_count(instance.owner, 'max_properties', Property)

# Caretaker usage update
@receiver(post_save, sender=Caretaker)
@receiver(post_delete, sender=Caretaker)
def update_caretaker_usage(sender, instance, **kwargs):
    update_usage_count(instance.property.owner, 'max_caretakers', Caretaker)

# Renter usage update
@receiver(post_save, sender=Renter)
@receiver(post_delete, sender=Renter)
def update_renter_usage(sender, instance, **kwargs):
    update_usage_count(instance.property.owner, 'max_renters', Renter)

# Property Images usage update
@receiver(post_save, sender=PropertyImage)
@receiver(post_delete, sender=PropertyImage)
def update_property_images_usage(sender, instance, **kwargs):
    update_usage_count(instance.property.owner, 'max_property_images', PropertyImage)

# Property Document usage update
@receiver(post_save, sender=PropertyDocument)
@receiver(post_delete, sender=PropertyDocument)
def update_property_document_usage(sender, instance, **kwargs):
    update_usage_count(instance.property.owner, 'max_document_uploads', PropertyDocument)