from fcm_django.models import FCMDevice
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_fcm_token(request):
    token = request.data.get("token")
    device_type = request.data.get("type", "android")  # or "ios", "web"
    
    if not token:
        return Response({"error": "Token required"}, status=400)

    FCMDevice.objects.update_or_create(
        user=request.user,
        registration_id=token,
        defaults={"type": device_type, "active": True}
    )
    return Response({"status": "Token registered"})