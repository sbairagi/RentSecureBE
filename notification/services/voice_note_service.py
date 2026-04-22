# services/voice_note_service.py

from notification.services.voice_service import generate_voice_note
from notification.services.whatsapp_service import send_whatsapp_audio, send_whatsapp_message
from properties.models import RentRecord


def send_thank_you_voice_note(rent: RentRecord):
    name = rent.renter.full_name
    amount = rent.amount
    date = rent.payment_date.strftime("%d %B")
    msg = f"Shukriya {name}! Aapne ₹{amount} rent {date} ko time se pehle jama kiya. Aapki samay par payment ki hum sarahna karte hain."

    audio_path = generate_voice_note(msg, lang="hi")
    send_whatsapp_audio(rent.renter.whatsapp_number, audio_path)


def send_late_rent_reminder(rent: RentRecord):
    name = rent.renter.full_name
    amount = rent.amount
    due_date = rent.due_date.strftime("%d %B")

    msg = f"Namaste {name}, aapka ₹{amount} rent {due_date} ko due tha. Kripya jald se jald jama karein. Dhanyawaad."

    audio_path = generate_voice_note(msg, lang="hi")
    send_whatsapp_audio(rent.renter.whatsapp_number, audio_path)

    # Mark reminder sent
    rent.reminder_sent = True
    rent.save()


def alert_owner_about_delay(rent: RentRecord):
    owner = rent.renter.property.owner
    msg = (
        f"⚠️ Alert: Your renter {rent.renter.full_name} "
        f"has not paid rent ₹{rent.amount} due on {rent.due_date}."
    )
    send_whatsapp_message(owner.profile.whatsapp_number, msg)