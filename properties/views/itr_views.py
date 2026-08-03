"""ITR CA contact, deduction suggestion, and Form 16 OCR APIs."""

from __future__ import annotations

import logging

from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response

from django.contrib.auth.models import AnonymousUser

from ..models import ITRCAContactRequest
from ..services.ocr_service import extract_form16_data as extract_form16_data_service
from ..services.tax_calculator_service import build_deduction_suggestions

logger = logging.getLogger(__name__)


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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_itr_deduction_suggestions(request: DRFRequest) -> Response:
    """Return smart deduction suggestions based on salary, rent, HRA, and city."""
    user = request.user
    if isinstance(user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=401)

    data = request.data or {}
    try:
        monthly_salary = data.get("monthly_salary", 0) or 0
        monthly_rent = data.get("monthly_rent", 0) or 0
        monthly_hra = data.get("monthly_hra", 0) or 0
        city = data.get("city", "non_metro") or "non_metro"
    except Exception as exc:
        return Response({"error": str(exc)}, status=400)

    try:
        suggestions = build_deduction_suggestions(
            monthly_salary=monthly_salary,
            monthly_rent=monthly_rent,
            monthly_hra=monthly_hra,
            city=city,
        )
    except Exception as exc:
        return Response({"error": str(exc)}, status=400)

    return Response(suggestions)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, JSONParser])
def extract_form16_data(request: DRFRequest) -> Response:
    """Extract ITR data from an uploaded Form 16 or rent receipt PDF."""
    user = request.user
    if isinstance(user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=401)

    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return Response(
            {"error": "A PDF file is required in the 'file' field."},
            status=400,
        )

    try:
        extracted = extract_form16_data_service(uploaded_file)
    except Exception as exc:
        logger.exception("Form 16 extraction failed for user %s", user.id)
        return Response({"error": str(exc)}, status=400)

    return Response(extracted)
