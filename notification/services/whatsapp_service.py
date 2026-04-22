# services/whatsapp_service.py

from notification.utils import send_whatsapp_message
from twilio.rest import Client
from django.conf import settings

def send_whatsapp_message(phone, text):
    client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
    client.messages.create(
        body=text,
        from_='whatsapp:+1415XXXXXXX',
        to=f'whatsapp:{phone}'
    )

def send_whatsapp_audio(phone, audio_path):
    media_url = upload_to_s3(audio_path)  # This must return a public URL

    client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
    client.messages.create(
        media_url=[media_url],
        from_='whatsapp:+1415XXXXXXX',
        to=f'whatsapp:{phone}'
    )


def upload_to_s3(file_path):
    s3 = boto3.client('s3')
    filename = os.path.basename(file_path)
    key = f"voice_notes/{filename}"
    
    s3.upload_file(file_path, 'your-bucket-name', key, ExtraArgs={'ContentType': 'audio/mpeg'})
    url = f"https://your-bucket-name.s3.amazonaws.com/{key}"
    return url


def send_agreement_via_whatsapp(renter, pdf_url):
    msg = f"📄 Your rent agreement is ready.\nDownload: {pdf_url}"
    send_whatsapp_message(renter.phone, msg)