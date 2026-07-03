# from django.core.mail import send_mail
# from properties.models import PropertyTaxRecord, UserSubscription
# from datetime import timedelta
# from communication.utils import send_push_notification, send_whatsapp_message


#     def handle(self, *args, **options):
#         today = now().date()

#         # Sare active subscriptions lo
#         subscriptions = UserSubscription.objects.filter(is_active=True)

#         for sub in subscriptions:
#             user = sub.user
#             days_before = sub.tax_reminder_days_before or 7  # fallback to 7 if None
#             alert_date = today + timedelta(days=days_before)

#             due_records = PropertyTaxRecord.objects.filter(
#                 property__owner=user,
#                 is_paid=False,
#                 due_date__lte=alert_date,
#                 due_date__gte=today
#             )

#             for record in due_records:
#                 property_title = record.property.title
#                 due_date = record.due_date
#                 amount = record.amount

#                 subject = f"Upcoming Property Tax Due for {property_title}"
#                 message = (
#                     f"Dear {user.username},\n\n"
#                     f"Your property tax of ₹{amount} is due on {due_date} for your property '{property_title}'. "
#                     "Please make sure to complete the payment on time to avoid penalties.\n\n"
#                     "Thank you."
#                 )
#                 # Send email
#                 send_mail(subject, message, 'noreply@yourdomain.com', [user.email])

#                 # Send push notification
#                 send_push_notification(user, subject, message)

#                 if user.profile.whatsapp_number:  # Assuming you store this in profile
#                     send_whatsapp_message(
#                         to=user.profile.whatsapp_number,
#                         message=message
#                     )
