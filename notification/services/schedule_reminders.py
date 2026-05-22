# tasks/schedule_reminders.py
from django.utils.timezone import now, timedelta

from notification.services.voice_service import generate_voice_note
from notification.services.whatsapp_service import send_whatsapp_audio
from properties.models import PropertyTaxRecord, RentRecord


def get_upcoming_rent_dues():
    target_date = now().date() + timedelta(days=3)
    return RentRecord.objects.filter(due_date=target_date)

def get_upcoming_tax_dues():
    target_date = now().date() + timedelta(days=3)
    return PropertyTaxRecord.objects.filter(due_date=target_date, is_paid=False)


def generate_rent_reminder_msg(rent: RentRecord, lang="hi"):
    name = rent.renter.full_name
    amount = rent.amount
    date = rent.due_date.strftime("%d %B")
    return f"Namaste {name}! Aapka ₹{amount} rent {date} ko due hai. Kripya samay par jama karein."

def generate_tax_reminder_msg(tax: PropertyTaxRecord, lang="hi"):
    amount = tax.amount
    date = tax.due_date.strftime("%d %B")
    return f"Kripya dhyaan dein – property tax ₹{amount} {date} tak jama karna hai."


def process_rent_reminders():
    for rent in get_upcoming_rent_dues():
        phone = rent.renter.whatsapp_number
        lang = rent.renter.user.profile.language
        if phone:
            msg = generate_rent_reminder_msg(rent)
            audio_path = generate_voice_note(msg, lang)
            send_whatsapp_audio(rent.renter.whatsapp_number, audio_path)

def process_tax_reminders():
    for tax in get_upcoming_tax_dues():
        phone = tax.user.profile.whatsapp_number
        lang = tax.user.profile.language
        if phone:
            msg = generate_tax_reminder_msg(tax)
            audio_path = generate_voice_note(msg, lang)
            owner = tax.property.owner
            send_whatsapp_audio(owner.profile.whatsapp_number, audio_path)




# Step 4: Schedule Cron Job (Every Morning)

# cron: daily at 9AM
# 0 9 * * * /path/to/venv/bin/python /path/to/manage.py runscript schedule_reminders
