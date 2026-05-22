# # management/commands/archive_expired_users_data.py
# from django.core.management.base import BaseCommand
# from core.models import UserSubscription, Building, Unit
# from django.utils import timezone
# from datetime import timedelta

# class Command(BaseCommand):
#     help = 'Archive user data whose plan expired more than 7 days ago'

#     def handle(self, *args, **kwargs):
#         threshold_date = timezone.now() - timedelta(days=7)
#         expired_users = UserSubscription.objects.filter(expiry_date__lt=threshold_date)

#         for sub in expired_users:
#             user = sub.user
#             Building.objects.filter(owner=user).update(is_archived=True)
#             Unit.objects.filter(owner=user).update(is_archived=True)

#         self.stdout.write(self.style.SUCCESS(f'Archived data for {expired_users.count()} users'))


# # python manage.py create_archived_data
