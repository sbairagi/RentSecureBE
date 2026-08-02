"""Rent reminder resend views."""

from __future__ import annotations

import logging
from typing import Any

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.shortcuts import get_object_or_404

from notification.services.voice_service import generate_voice_note  # nosonar
from notification.services.whatsapp_service import send_whatsapp_audio  # nosonar
from notification.services.whatsapp_service import (
    send_whatsapp_message,  # nosonar; nosonar
)
from properties.models import RentRecord
from rentsecure_be.services.message_template_service import (
    get_rent_paid_confirmation_msg,
)

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def resend_rent_confirmation(request: Any, rent_id: int) -> Response:
    """Resend rent paid confirmation WhatsApp message and optional voice note.

    Only the owner of the rent record's unit may trigger this action.
    """
    rent = get_object_or_404(RentRecord, id=rent_id)

    if rent.unit.owner != request.user:
        return Response(
            {"error": "Not authorized to resend this confirmation."},
            status=403,
        )

    renter = rent.renter
    if renter is None:
        return Response(
            {"error": "No renter associated with this rent record."},
            status=400,
        )

    phone = renter.whatsapp_number or renter.phone or ""
    if not phone:
        return Response(
            {"error": "Renter has no phone number configured."},
            status=400,
        )

    user_profile = getattr(getattr(renter, "user", None), "profile", None)
    lang: str = getattr(user_profile, "language_preference", None) or "en"

    msg = get_rent_paid_confirmation_msg(
        name=renter.full_name,
        amount=rent.amount,
        paid_date=rent.updated_at,
        lang=lang,
    )

    send_whatsapp_message(
        phone,
        msg,
        user=getattr(renter, "user", None),
        rent_record=rent,
    )

    try:
        audio_path = generate_voice_note(msg, lang)
        if audio_path:
            send_whatsapp_audio(
                phone,
                audio_path,
                user=getattr(renter, "user", None),
                rent_record=rent,
            )
    except Exception:
        logger.exception("Failed to send resend voice note for rent %s", rent_id)

    return Response({"status": "Resent successfully."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def rent_whatsapp_logs(request: Any, rent_id: int) -> Response:
    """Return WhatsApp delivery logs for a rent record."""
    rent = get_object_or_404(RentRecord, id=rent_id)
    if rent.unit.owner != request.user:
        return Response({"detail": "Not authorized."}, status=403)

    logs = rent.whatsapp_logs.select_related("user").order_by("-timestamp")[:100]
    data = [
        {
            "id": log.id,
            "phone": log.phone,
            "message_type": log.message_type,
            "message_content": log.message_content,
            "media_url": log.media_url,
            "status": log.status,
            "retry_count": log.retry_count,
            "timestamp": log.timestamp.isoformat(),
            "user": log.user.username if log.user else None,
        }
        for log in logs
    ]
    return Response(data)
