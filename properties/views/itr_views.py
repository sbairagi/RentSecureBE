"""ITR CA contact API."""

from __future__ import annotations

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response

from django.contrib.auth.models import AnonymousUser

from ..models import ITRCAContactRequest


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def contact_ca(request: DRFRequest) -> Response:
    """Submit a CA contact request for ITR filing assistance."""
    user = request.user
    if isinstance(user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=401)

    data = request.data or {}
    phone = data.get("phone")
    email = data.get("email")
    pan_number = data.get("pan_number")

    if not phone or not email or not pan_number:
        return Response(
            {"error": "phone, email, and pan_number are required."},
            status=400,
        )

    ITRCAContactRequest.objects.create(
        user=user,
        phone=phone,
        email=email,
        pan_number=pan_number,
        message=data.get("message", ""),
    )

    return Response({"status": "submitted"})
