# # core/management/commands/downgrade_expired_users.py

# from django.core.management.base import BaseCommand
# from django.utils import timezone
# from datetime import timedelta
# from core.models import UserSubscription, PlanFeatureLimit, UsageLimit, SubscriptionPlan
# from wealth_concierge_platform.models import Building, Unit, Caretaker, Renter, UnitImage, UnitDocument

# # python manage.py downgrade_expired_users

# FREE_PLAN_NAME = 'free'

# class Command(BaseCommand):
#     help = 'Downgrade users whose subscription expired 7+ days ago and trim their resources.'

#     def handle(self, *args, **kwargs):
#         now = timezone.now()
#         expired_users = UserSubscription.objects.filter(
#             expiry_date__lt=now - timedelta(days=7)
#         ).exclude(plan__name=FREE_PLAN_NAME)

#         for sub in expired_users:
#             user = sub.user
#             print(f"Downgrading user: {user.phone}")

#             # Get free plan limits
#             free_limits = {
#                 x.feature_key: int(x.value)
#                 for x in PlanFeatureLimit.objects.filter(plan__name=FREE_PLAN_NAME)
#             }

#             # Truncate buildings
#             buildings = Building.objects.filter(owner=user)
#             if buildings.count() > free_limits.get('max_properties', 0):
#                 to_delete = buildings.order_by('-id')[free_limits['max_properties']:]
#                 print(f"  Deleting {to_delete.count()} buildings")
#                 to_delete.delete()

#             # Truncate units
#             units = Unit.objects.filter(owner=user)
#             if units.count() > free_limits.get('max_units', 0):
#                 to_delete = units.order_by('-id')[free_limits['max_units']:]
#                 print(f"  Deleting {to_delete.count()} units")
#                 to_delete.delete()

#             # Truncate caretakers
#             caretakers = Caretaker.objects.filter(owner=user)
#             if caretakers.count() > free_limits.get('max_caretakers', 0):
#                 to_delete = caretakers.order_by('-id')[free_limits['max_caretakers']:]
#                 print(f"  Deleting {to_delete.count()} caretakers")
#                 to_delete.delete()

#             # Truncate renters
#             renters = Renter.objects.filter(owner=user)
#             if renters.count() > free_limits.get('max_renters', 0):
#                 to_delete = renters.order_by('-id')[free_limits['max_renters']:]
#                 print(f"  Deleting {to_delete.count()} renters")
#                 to_delete.delete()

#             # Truncate uploads
#             uploads = UnitDocument.objects.filter(owner=user)
#             if uploads.count() > free_limits.get('max_uploads', 0):
#                 to_delete = uploads.order_by('-id')[free_limits['max_uploads']:]
#                 print(f"  Deleting {to_delete.count()} uploads")
#                 to_delete.delete()

#             images = UnitImage.objects.filter(owner=user)
#             if images.count() > free_limits.get('max_unit_images', 0):
#                 to_delete = images.order_by('-id')[free_limits['max_unit_images']:]
#                 print(f"  Deleting {to_delete.count()} images")
#                 to_delete.delete()

#             # Downgrade user to Free plan
#             sub.plan = SubscriptionPlan.objects.get(name=FREE_PLAN_NAME)
#             sub.expiry_date = None  # Free plan doesn't expire
#             sub.save()
#             print(f"  Downgraded to Free plan.\n")

