"""DRF views for the finance app — strict-typed and thin.

Views are intentionally kept small. All business logic lives in
:mod:`finance.utils` or in dedicated service modules. Each view handler
has full type annotations including the ``Request`` and ``Response``
shapes it produces.
"""

from __future__ import annotations

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

from core.models import User
from properties.models import Unit
from rentsecure_be.services.ca_matchmaking_service import match_ca
from rentsecure_be.type_compat import override

from .models import CAConnectionRequest, CAProfile, TaxSubmissionToCA
from .serializers import CAProfileSerializer, TaxSubmissionToCASerializer
from .utils import create_tax_zip, generate_tax_excel, generate_tax_pdf


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
    CAConnectionRequest.objects.create(user=user, ca=ca, message=message)

    return Response(
        {
            "message": "CA callback requested successfully.",
            "ca_name": ca.name,
            "ca_phone": ca.phone,
            "ca_email": ca.email,
        },
        status=status.HTTP_201_CREATED,
    )
