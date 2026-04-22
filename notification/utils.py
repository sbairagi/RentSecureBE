# from expo_push_notifications import send_expo_notification

# def push_user(user, title, message):
#     from notifications.models import DeviceToken
#     token_obj = DeviceToken.objects.filter(user=user).first()
#     if not token_obj: return

#     send_expo_notification(
#         token_obj.token,
#         title=title,
#         body=message
#     )


from fcm_django.models import FCMDevice
from django.conf import settings
from twilio.rest import Client

def send_push_notification(user, title, body):
    devices = FCMDevice.objects.filter(user=user, active=True)
    if devices.exists():
        devices.send_message(title=title, body=body)


def send_whatsapp_message(to, message):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    from_whatsapp = settings.TWILIO_WHATSAPP_NUMBER
    to_whatsapp = f'whatsapp:{to}'

    message = client.messages.create(
        body=message,
        from_=from_whatsapp,
        to=to_whatsapp
    )
    return message.sid


# Hook into Events

# For example, in rent created:

# push_user(user, title, msg)