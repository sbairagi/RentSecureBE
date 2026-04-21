from expo_push_notifications import send_expo_notification

def push_user(user, title, message):
    from notifications.models import DeviceToken
    token_obj = DeviceToken.objects.filter(user=user).first()
    if not token_obj: return

    send_expo_notification(
        token_obj.token,
        title=title,
        body=message
    )


# Hook into Events

# For example, in rent created:

# push_user(user, title, msg)