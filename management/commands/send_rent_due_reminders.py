# from django.core.management.base import BaseCommand
# from django.core.mail import send_mail
# from django.utils import timezone
# from datetime import timedelta
# from wealth_concierge_platform.models import Renter
# from django.conf import settings
# from communication.utils import send_whatsapp_message


# class Command(BaseCommand):
#     help = 'Send rent due reminders'

#     def handle(self, *args, **kwargs):
#         today = timezone.now().date()
#         renters = Renter.objects.filter(rent_due_date__isnull=False)

#         for renter in renters:
#             user = renter.property.owner
#             subscription = getattr(user, 'usersubscription', None)
#             if not subscription or not subscription.plan:
#                 continue

#             days_before = subscription.plan.rent_reminder_days_before or 7
#             due_date = renter.rent_due_date
#             reminder_date = due_date - timedelta(days=days_before)

#             if reminder_date == today:
#                 subject = "Upcoming Rent Due Reminder"
#                 message = (
#                     f"Hello {user.username},\n\n"
#                     f"This is a reminder that rent is due for renter '{renter.name}' on {due_date} "
#                     f"for the property: {renter.property.name}.\n\n"
#                     f"Please ensure payment is tracked or received in time.\n\n"
#                     f"- Your Concierge Team"
#                 )

#                 # Send email
#                 if user.email:
#                     send_mail(
#                         subject,
#                         message,
#                         settings.DEFAULT_FROM_EMAIL,
#                         [user.email],
#                         fail_silently=False,
#                     )

#                 if user.profile.whatsapp_number:  # Assuming you store this in profile
#                     send_whatsapp_message(
#                         to=user.profile.whatsapp_number,
#                         message=message
#                     )

#                 self.stdout.write(self.style.SUCCESS(
#                     f"Sent rent due reminder to {user.username} for renter {renter.name} (due on {due_date})"
#                 ))