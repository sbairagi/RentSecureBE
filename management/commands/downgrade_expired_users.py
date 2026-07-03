# # core/management/commands/downgrade_expired_users.py

# from properties.models import Building, Unit, Caretaker, Renter, UnitImage, UnitDocument

# # python manage.py downgrade_expired_users


#         now = timezone.now()
#         expired_users = UserSubscription.objects.filter(
#         ).exclude(plan__name=FREE_PLAN_NAME)

#         for sub in expired_users:
#             user = sub.user
#             print(f"Downgrading user: {user.phone}")
