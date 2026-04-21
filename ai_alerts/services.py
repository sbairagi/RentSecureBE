from rent.models import Renter, RentRecord
from datetime import date, timedelta
from .models import AIAlert

def generate_ai_alerts(owner):
    today = date.today()
    six_months_ago = today - timedelta(days=180)

    renters = Renter.objects.filter(property__owner=owner, status__in=["active", "notice_period"])

    for renter in renters:
        rents = RentRecord.objects.filter(renter=renter).order_by("-month", "-year")

        # 1. Missed 2+ consecutive months
        recent = list(rents[:3])
        if all(r.payment_status == "UNPAID" for r in recent[:2]):
            AIAlert.objects.get_or_create(
                owner=owner,
                alert_type="Missed Rent",
                message=f"{renter.name} missed last 2+ months rent."
            )

        # 2. Irregular rent pattern
        past_six = rents.filter(created_at__gte=six_months_ago)
        delayed = [r for r in past_six if r.payment_status == "PAID" and r.paid_date and r.paid_date > r.due_date]
        if len(delayed) >= 3:
            AIAlert.objects.get_or_create(
                owner=owner,
                alert_type="Irregular Rent",
                message=f"{renter.name} has delayed rent 3+ times recently."
            )


# Cron or Command to Run Alerts Weekly

# cron weekly
# python manage.py run_ai_alerts

# ai/management/commands/run_ai_alerts.py

# from django.core.management.base import BaseCommand
# from django.contrib.auth import get_user_model
# from ai.services import generate_ai_alerts

# class Command(BaseCommand):
#     def handle(self, *args, **kwargs):
#         for user in get_user_model().objects.all():
#             generate_ai_alerts(user)

# Show Alerts on Dashboard


# <FlatList
#   data={alerts}
#   renderItem={({ item }) => (
#     <View>
#       <Text>⚠️ {item.message}</Text>
#     </View>
#   )}
# />


# (Optional): WhatsApp Alerts

# from services.whatsapp_service import send_whatsapp_message

# send_whatsapp_message(owner.profile.whatsapp_number, alert.message)