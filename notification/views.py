from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import DeviceToken


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    data = request.user.notifications.order_by("-created_at").values(
        "id", "title", "message", "is_read", "created_at"
    )
    return Response(list(data))


# Response

# [
#   {
#     "title": "📩 New Rent Due",
#     "message": "₹8000 rent due for May. Pay now",
#     "created_at": "2025-05-28T12:00:00Z",
#     "is_read": false
#   }
# ]


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    note = request.user.notifications.get(id=notification_id)
    note.is_read = True
    note.save()
    return Response({"status": "Marked as read"})


# API to receive from frontend
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_device_token(request):
    token = request.data.get("token")
    if token:
        DeviceToken.objects.update_or_create(
            user=request.user, defaults={"token": token}
        )
    return Response({"status": "saved"})


# React Native (Expo or Bare) Setup


# // app/_layout.tsx or root layout
# import * as Notifications from 'expo-notifications';
# import * as Device from 'expo-device';

# useEffect(() => {
#   const register = async () => {
#     const { status } = await Notifications.requestPermissionsAsync();
#     if (status !== 'granted') return;

#     const token = (await Notifications.getExpoPushTokenAsync()).data;

#     // Send this token to backend
#     await fetch('/api/save-device-token', {
#       method: 'POST',
#       headers: { Authorization: `Bearer ${jwt}` },
#       body: JSON.stringify({ token }),
#     });
#   };
#   register();
# }, []);


from fcm_django.models import FCMDevice
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_fcm_token(request):
    token = request.data.get("token")
    device_type = request.data.get("type", "android")  # or "ios", "web"

    if not token:
        return Response({"error": "Token required"}, status=400)

    FCMDevice.objects.update_or_create(
        user=request.user,
        registration_id=token,
        defaults={"type": device_type, "active": True},
    )
    return Response({"status": "Token registered"})
