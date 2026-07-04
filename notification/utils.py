#     from notifications.models import DeviceToken
#     token_obj = DeviceToken.objects.filter(user=user).first()
#     if not token_obj: return


from typing import Any

from fcm_django.models import FCMDevice  # type: ignore[import-untyped]
from twilio.rest import Client

from django.conf import settings


def send_push_notification(user: Any, title: str, body: str) -> None:
    devices = FCMDevice.objects.filter(user=user, active=True)
    if devices.exists():
        devices.send_message(title=title, body=body)


def send_whatsapp_message(to: str, message: str) -> Any:
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    from_whatsapp = settings.TWILIO_WHATSAPP_NUMBER
    to_whatsapp = f"whatsapp:{to}"

    msg = client.messages.create(body=message, from_=from_whatsapp, to=to_whatsapp)
    return msg.sid


# Hook into Events

# For example, in rent created:

# push_user(user, title, msg)
