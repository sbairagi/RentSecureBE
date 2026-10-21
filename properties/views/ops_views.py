"""The RentSecure Ops desk.

Ops is the internal team that runs the trust side of the portal: they review
the police verifications of the renters, they step in when an agreement could
not be generated and they keep an eye on the agreements that expired without
a renewal.

Only users with ``is_ops`` (or Django staff) can reach these endpoints.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from rentsecure_be.type_compat import override

from ..models import PoliceVerification, RentAgreementDraft
from ..services.agreement_document_service import generate_agreement_document


class IsOpsUser(BasePermission):
    """Allow only the RentSecure Ops team."""

    def has_permission(self, request: Request, view: Any) -> bool:
        """Return ``True`` for an authenticated member of the ops team."""
        user = request.user
        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            return False
        return bool(user.is_ops or user.is_staff)


class OpsPoliceVerificationSerializer(serializers.ModelSerializer):
    """A police verification in the review queue."""

    renter_name = serializers.CharField(source="renter.name", read_only=True)
    renter_email = serializers.CharField(source="renter.email", read_only=True)
    renter_phone = serializers.CharField(source="renter.phone", read_only=True)
    unit_label = serializers.CharField(source="unit.unit", read_only=True)
    building_name = serializers.CharField(source="unit.building.name", read_only=True)
    owner_name = serializers.CharField(source="user.full_name", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = PoliceVerification
        fields = [
            "id",
            "status",
            "status_label",
            "renter_name",
            "renter_email",
            "renter_phone",
            "unit_label",
            "building_name",
            "owner_name",
            "file",
            "submitted_at",
            "verified_at",
            "reviewed_at",
            "review_notes",
            "rejection_reason",
        ]


class OpsAgreementSerializer(serializers.ModelSerializer):
    """An agreement in the exception queue."""

    renter_name = serializers.CharField(source="renter.name", read_only=True)
    unit_label = serializers.CharField(source="unit.unit", read_only=True)
    building_name = serializers.CharField(source="unit.building.name", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = RentAgreementDraft
        fields = [
            "id",
            "agreement_number",
            "status",
            "status_label",
            "renter_name",
            "unit_label",
            "building_name",
            "generation_error",
            "document_generated_at",
            "owner_signed",
            "renter_signed",
            "start_date",
            "end_date",
        ]


class OpsPoliceVerificationViewSet(viewsets.ViewSet):
    """The police verification review queue."""

    permission_classes = [IsAuthenticated, IsOpsUser]

    def get_queryset(self) -> Any:
        """Return the verifications of every owner."""
        return PoliceVerification.objects.select_related(
            "renter", "unit", "unit__building", "user"
        ).order_by("-submitted_at")

    @override
    def list(self, request: Request) -> Response:
        """Return the review queue."""
        queryset = self.get_queryset()
        status_filter = request.query_params.get("status", "").strip()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        else:
            queryset = queryset.filter(
                status=PoliceVerification.PoliceVerificationStatus.SUBMITTED
            )
        serializer = OpsPoliceVerificationSerializer(queryset, many=True)
        return Response({"data": serializer.data})

    @action(detail=True, methods=["post"], url_path="decision")
    def decision(self, request: Request, pk: int | None = None) -> Response:
        """Approve or reject a verification."""
        verification = self.get_queryset().filter(pk=pk).first()
        if verification is None:
            raise NotFound("That verification does not exist.")

        decision = str(request.data.get("decision", "")).lower()
        notes = str(request.data.get("notes", "")).strip()
        if decision not in ("approve", "reject"):
            raise ValidationError("The decision must be 'approve' or 'reject'.")
        if decision == "reject" and not notes:
            raise ValidationError("A rejection needs a reason for the renter.")

        verification.reviewed_by = request.user
        verification.reviewed_at = timezone.now()
        verification.review_notes = notes
        if decision == "approve":
            verification.status = PoliceVerification.PoliceVerificationStatus.VERIFIED
            verification.verified_at = timezone.now()
            verification.rejection_reason = ""
        else:
            verification.status = PoliceVerification.PoliceVerificationStatus.REJECTED
            verification.rejection_reason = notes[:255]
        verification.save()
        serializer = OpsPoliceVerificationSerializer(verification)
        return Response(serializer.data)


class OpsAgreementViewSet(viewsets.ViewSet):
    """The agreements that need a hand from the ops team."""

    permission_classes = [IsAuthenticated, IsOpsUser]

    def get_queryset(self) -> Any:
        """Return the agreements that are not in a healthy state."""
        return RentAgreementDraft.objects.select_related(
            "renter", "unit", "unit__building"
        ).order_by("-generated_at")

    @override
    def list(self, request: Request) -> Response:
        """Return the exception queue."""
        queryset = self.get_queryset()
        status_filter = request.query_params.get("status", "").strip()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        serializer = OpsAgreementSerializer(queryset, many=True)
        return Response({"data": serializer.data})

    @action(detail=True, methods=["post"], url_path="regenerate")
    def regenerate(self, request: Request, pk: int | None = None) -> Response:
        """Generate the document of an agreement again."""
        agreement = self.get_queryset().filter(pk=pk).first()
        if agreement is None:
            raise NotFound("That agreement does not exist.")
        generate_agreement_document(agreement)
        serializer = OpsAgreementSerializer(agreement)
        return Response(serializer.data, status=status.HTTP_200_OK)
