# send_tax_reminders.py
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils.timezone import now
from datetime import timedelta

from wealth_concierge_platform.models import PropertyTaxRecord

class Command(BaseCommand):
    help = "Send upcoming property tax reminders"

    def handle(self, *args, **kwargs):
        upcoming_due_date = now().date() + timedelta(days=7)
        records = PropertyTaxRecord.objects.filter(
            is_paid=False,
            due_date__lte=upcoming_due_date,
            due_date__gte=now().date()
        ).select_related('property', 'property__owner')

        for record in records:
            user = record.property.owner
            subject = f"Upcoming Property Tax Due - {record.property.title}"
            message = f"Reminder: Your property tax of ₹{record.amount} is due on {record.due_date} for {record.property.title}."
            send_mail(subject, message, 'noreply@yourdomain.com', [user.email])
        
        self.stdout.write(self.style.SUCCESS(f"Sent {records.count()} reminders."))