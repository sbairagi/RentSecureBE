"""DRF views for the finance app — strict-typed and thin.

Views are intentionally kept small. All business logic lives in
:mod:`finance.utils` or in dedicated service modules. Each view handler
has full type annotations including the ``Request`` and ``Response``
shapes it produces.
"""

from __future__ import annotations

from typing import Any, override

from django.http import FileResponse
from rest_framework import permissions, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from core.models import User
from properties.models import Unit

from .models import CAProfile, TaxSubmissionToCA
from .serializers import CAProfileSerializer, TaxSubmissionToCASerializer
from .utils import create_tax_zip, generate_tax_excel, generate_tax_pdf


class CAProfileViewSet(viewsets.ModelViewSet[CAProfile]):
    """CRUD for the ``CAProfile`` model — used by owners to onboard their CA."""

    queryset: Any = CAProfile.objects.all()
    serializer_class = CAProfileSerializer
    permission_classes: list[type[permissions.BasePermission]] = [
        permissions.IsAuthenticated
    ]


class TaxSubmissionToCAViewSet(viewsets.ModelViewSet[TaxSubmissionToCA]):
    """CRUD for tax submissions belonging to the authenticated user only."""

    serializer_class = TaxSubmissionToCASerializer
    permission_classes: list[type[permissions.BasePermission]] = [
        permissions.IsAuthenticated
    ]
    queryset: Any = TaxSubmissionToCA.objects.all()

    @override
    def get_queryset(self) -> Any:
        """Return only the current user's tax submissions.

        ``TaxSubmissionToCA`` has a direct ``user`` FK (not a
        ``tax_summary`` reverse), so we filter on that.
        """
        return TaxSubmissionToCA.objects.filter(user=self.request.user)

    @override
    def perform_create(self, serializer: TaxSubmissionToCASerializer) -> None:
        """Persist the submission; ownership is bound by the related tax summary."""
        serializer.save()


class DownloadTaxFilesView(APIView):
    """Build a zip containing the user's tax Excel, PDF, and rent-agreement files."""

    permission_classes: list[type[permissions.BasePermission]] = [IsAuthenticated]

    def get(self, request: Request) -> FileResponse:
        """Generate and return a downloadable tax-document zip."""
        user: User = request.user
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
