"""DRF views for the finance app — strict-typed and thin.

Views are intentionally kept small. All business logic lives in
:mod:`finance.utils` or in dedicated service modules. Each view handler
has full type annotations including the ``Request`` and ``Response``
shapes it produces.
"""

from __future__ import annotations

import logging
from typing import Any, cast

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from django.contrib.auth.models import AnonymousUser
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from core.models import User
from notification.services.whatsapp_service import send_whatsapp_message
from properties.models import Unit
from rentsecure_be.services.ca_matchmaking_service import match_ca
from rentsecure_be.type_compat import override

from .models import CAConnectionRequest, CAPartner, CAProfile, TaxSubmissionToCA
from .serializers import (
    CAConnectionRequestSerializer,
    CAProfileSerializer,
    TaxSubmissionToCASerializer,
)
from .utils import create_tax_zip, generate_tax_excel, generate_tax_pdf

logger = logging.getLogger(__name__)


class CAProfileViewSet(viewsets.ModelViewSet[CAProfile]):
    """CRUD for the ``CAProfile`` model — used by owners to onboard their CA."""

    queryset: Any = CAProfile.objects.all()
    serializer_class = CAProfileSerializer
    permission_classes: list[type[permissions.BasePermission]] = [
        permissions.IsAuthenticated
    ]

    @override
    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        serializer.save(user=self.request.user)


class TaxSubmissionToCAViewSet(viewsets.ModelViewSet[TaxSubmissionToCA]):
    """CRUD for tax submissions belonging to the authenticated user only."""

    serializer_class = TaxSubmissionToCASerializer
    permission_classes: list[type[permissions.BasePermission]] = [
        permissions.IsAuthenticated
    ]
    queryset: Any = TaxSubmissionToCA.objects.all()

    @override
    def get_queryset(self) -> Any:
        """Return only the current user's tax submissions."""
        if isinstance(self.request.user, AnonymousUser):
            return self.queryset.none()
        return TaxSubmissionToCA.objects.filter(user=self.request.user)

    @override
    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        """Persist the submission; ownership is bound by the related tax summary."""
        serializer.save(user=self.request.user)


class DownloadTaxFilesView(APIView):
    """Build a zip containing the user's tax Excel, PDF, and rent-agreement files."""

    permission_classes: list[type[permissions.BasePermission]] = [IsAuthenticated]

    def get(self, request: Request) -> FileResponse:
        """Generate and return a downloadable tax-document zip."""
        user: User = cast(User, request.user)
        fy: str = request.query_params.get("fy", "2024-25")

        properties: Any = Unit.objects.filter(owner=user)
        excel: str = generate_tax_excel(user, properties, fy)
        pdf: str = generate_tax_pdf(user, properties, fy)

        extra_files: list[Any] = []
        for p in properties:
            renter = getattr(p, "renter", None)
            if renter is None:
                continue
            agreement = getattr(renter, "rent_agreement", None)
            police_verification = getattr(renter, "police_verification", None)
            if agreement:
                extra_files.append(agreement)
            if police_verification:
                extra_files.append(police_verification)

        zip_file: str = create_tax_zip(user, excel, pdf, extra_files)

        return FileResponse(
            open(zip_file, "rb"), as_attachment=True, filename="tax_documents.zip"
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ca_leads_list(request: Request, /, *args: Any, **kwargs: Any) -> Response:
    """Return all leads for the authenticated CA partner."""
    try:
        ca = request.user.ca_partner_profile
    except CAPartner.DoesNotExist:
        return Response(
            {"error": "CA partner profile not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    leads = CAConnectionRequest.objects.filter(ca_partner=ca).order_by("-requested_at")
    serializer = CAConnectionRequestSerializer(leads, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_lead_status(
    request: Request, lead_id: int, /, *args: Any, **kwargs: Any
) -> Response:
    """Update the status and notes for a specific lead."""
    try:
        ca = request.user.ca_partner_profile
    except CAPartner.DoesNotExist:
        return Response(
            {"error": "CA partner profile not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    lead = get_object_or_404(CAConnectionRequest, id=lead_id, ca_partner=ca)
    new_status = request.data.get("status")
    notes = request.data.get("notes", "")

    if new_status not in dict(CAConnectionRequest.STATUS_CHOICES):
        return Response(
            {"error": "Invalid status."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    lead.status = new_status
    lead.notes = notes
    if new_status == "CLOSED":
        mark_conversion(lead)
    lead.save()
    return Response({"message": "Lead updated successfully."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_whatsapp_followup(
    request: Request, lead_id: int, /, *args: Any, **kwargs: Any
) -> Response:
    """Send a WhatsApp follow-up message to the user linked to a lead."""
    try:
        ca = request.user.ca_partner_profile
    except CAPartner.DoesNotExist:
        return Response(
            {"error": "CA partner profile not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    lead = get_object_or_404(CAConnectionRequest, id=lead_id, ca_partner=ca)
    message = request.data.get("message")
    if not message:
        return Response(
            {"error": "Message content required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    phone = getattr(lead.user, "whatsapp_number", None) or getattr(
        lead.user, "userprofile", None
    )
    if hasattr(phone, "whatsapp_number"):
        phone = phone.whatsapp_number
    if not phone:
        return Response(
            {"error": "User does not have a WhatsApp number."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    sent = send_whatsapp_message(phone, message, user=lead.user)
    if sent:
        lead.status = "CONTACTED"
        lead.contacted_at = timezone.now()
        lead.save(update_fields=["status", "contacted_at"])
        return Response({"message": "WhatsApp message sent successfully."})
    return Response(
        {"error": "Failed to send WhatsApp message."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_matched_ca(request: Request, /, *args: Any, **kwargs: Any) -> Response:
    """Return the best available CA partner for the authenticated user."""
    user: User = cast(User, request.user)
    ca = match_ca(user)

    if not ca:
        return Response(
            {"message": "No CA available in your city at the moment."},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(
        {
            "name": ca.name,
            "firm": ca.firm_name,
            "city": ca.city,
            "email": ca.email,
            "phone": ca.phone,
            "specialization": ca.get_specialization_display(),
            "experience": ca.experience_years,
            "rating": ca.rating,
            "price_range": ca.price_range,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_ca_callback(request: Request, /, *args: Any, **kwargs: Any) -> Response:
    """Create a CA connection request for the authenticated user."""
    user: User = cast(User, request.user)
    ca = match_ca(user)

    if not ca:
        return Response(
            {"message": "No CA available in your city at the moment."},
            status=status.HTTP_404_NOT_FOUND,
        )

    message = request.data.get("message", "")
    CAConnectionRequest.objects.create(user=user, ca_partner=ca, message=message)

    return Response(
        {
            "message": "CA callback requested successfully.",
            "ca_name": ca.name,
            "ca_phone": ca.phone,
            "ca_email": ca.email,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ca_partner_analytics(request: Request, /, *args: Any, **kwargs: Any) -> Response:
    """Return lead analytics for the authenticated CA partner."""
    try:
        ca = request.user.ca_partner_profile
    except CAPartner.DoesNotExist:
        return Response(
            {"error": "CA partner profile not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    from_str = request.query_params.get("from")
    to_str = request.query_params.get("to")

    try:
        to_dt = timezone.make_aware(parse_datetime(to_str)) if to_str else None
    except Exception:
        to_dt = None

    try:
        from_dt = timezone.make_aware(parse_datetime(from_str)) if from_str else None
    except Exception:
        from_dt = None

    # Default date range: last 30 days
    if not to_dt:
        to_dt = timezone.now()
    if not from_dt:
        from_dt = to_dt - timezone.timedelta(days=30)

    # Ensure from_date <= to_date
    if from_dt > to_dt:
        from_dt, to_dt = to_dt, from_dt

    leads = CAConnectionRequest.objects.filter(
        ca_partner=ca,
        requested_at__gte=from_dt,
        requested_at__lte=to_dt,
    )

    total_leads = leads.count()
    contacted = leads.filter(contacted_at__isnull=False).count()
    converted = leads.filter(converted_at__isnull=False).count()
    conversion_rate = (converted / total_leads * 100) if total_leads > 0 else 0.0

    # CA partner joined count in date range
    ca_joined = 0
    if ca.joined_at and from_dt <= ca.joined_at <= to_dt:
        ca_joined = 1

    return Response(
        {
            "total_leads": total_leads,
            "contacted_leads": contacted,
            "converted_leads": converted,
            "conversion_rate": round(conversion_rate, 2),
            "total_ca_partners": ca_joined,
            "total_clients": total_leads,
        }
    )


def mark_conversion(ca_connection_request: CAConnectionRequest) -> None:
    """Mark a CA connection request as converted."""
    ca_connection_request.converted_at = timezone.now()
    ca_connection_request.save(update_fields=["converted_at"])
