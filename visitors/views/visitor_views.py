import logging
from typing import Any

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone

from rentsecure_be.type_compat import override
from visitors.models import Visitor, VisitorHistory
from visitors.serializers.visitor_serializers import (
    VisitorApprovalSerializer,
    VisitorCheckInSerializer,
    VisitorCreateSerializer,
    VisitorHistorySerializer,
    VisitorOTPVerifySerializer,
    VisitorSerializer,
    VisitorStatsSerializer,
)
from visitors.services.visitor_services import get_visitor_stats, mark_expired_visitors
from visitors.signals import _log_history
from visitors.utils.permissions import (
    CanApproveVisitor,
    CanCheckInVisitor,
    CanCheckOutVisitor,
)

logger = logging.getLogger(__name__)

VISITOR_CACHE_TIMEOUT = 300


class VisitorViewSet(viewsets.ModelViewSet[Visitor]):
    """CRUD + workflow actions for visitor requests.

    Supports:
    - List / Create / Retrieve / Update / Delete visitors
    - Approve / Reject visitor requests
    - Check in / Check out visitors
    - Generate QR code
    - Generate / Verify OTP
    """

    permission_classes = [IsAuthenticated]
    serializer_class = VisitorSerializer
    filterset_fields = [
        "status",
        "building",
        "unit",
        "renter",
        "visit_date",
        "created_by",
        "approved_by",
        "verified_by",
    ]
    search_fields = ["visitor_name", "phone_number", "vehicle_number"]
    ordering_fields = ["created_at", "visit_date", "expected_arrival", "status"]
    ordering = ["-created_at"]

    def get_queryset(self) -> Any:
        user = self.request.user
        cache_key = f"visitors_user_{user.id}"

        if user.is_staff or user.is_superuser:
            queryset = Visitor.objects.all()
        else:
            queryset = Visitor.objects.filter(
                Q(created_by=user) | Q(building__owner=user)
            ).distinct()

        queryset = queryset.select_related(
            "renter",
            "unit",
            "building",
            "renter__user",
            "created_by",
            "approved_by",
            "verified_by",
        )

        cached = cache.get(cache_key)
        if cached is not None and self.action == "list":
            return cached

        result = queryset
        if self.action == "list":
            cache.set(cache_key, result, timeout=VISITOR_CACHE_TIMEOUT)
        return result

    @override
    def get_serializer_class(self) -> type[VisitorSerializer | VisitorCreateSerializer]:
        if self.action == "create":
            return VisitorCreateSerializer
        return VisitorSerializer

    @override
    def perform_create(self, serializer: Any) -> None:
        user = self.request.user
        unit = serializer.validated_data.get("unit")
        building = serializer.validated_data.get("building")
        renter = serializer.validated_data.get("renter")

        if unit and unit.owner != user:
            raise PermissionDenied("You do not own the selected unit.")
        if building and building.owner != user:
            raise PermissionDenied("You do not own the selected building.")
        if renter and renter.unit.owner != user:
            raise PermissionDenied("You do not own the renter's unit.")

        instance = serializer.save(created_by=user)
        cache.delete(f"visitors_user_{user.id}")
        logger.info("Visitor request created: ID=%s by user=%s", instance.id, user.id)

    @override
    def perform_update(self, serializer: Any) -> None:
        instance = serializer.instance
        user = self.request.user

        if instance.created_by != user and instance.building.owner != user:
            raise PermissionDenied(
                "You do not have permission to update this visitor request."
            )

        if instance.status not in [
            Visitor.Status.REQUESTED,
            Visitor.Status.PENDING_APPROVAL,
        ]:
            raise ValidationError(
                f"Cannot update visitor in '{instance.status}' status."
            )

        serializer.save()
        cache.delete(f"visitors_user_{user.id}")

    @override
    def perform_destroy(self, instance: Visitor) -> None:
        user = self.request.user
        if instance.created_by != user:
            raise PermissionDenied("You can only delete your own visitor requests.")
        if instance.status in [Visitor.Status.CHECKED_IN, Visitor.Status.CHECKED_OUT]:
            raise ValidationError(
                "Cannot delete a visitor who has already checked in or out."
            )
        instance.delete()
        cache.delete(f"visitors_user_{user.id}")

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request: Request, pk: int) -> Response:
        visitor = self.get_object()
        serializer = VisitorApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not CanApproveVisitor(request.user, visitor).has_permission():
            raise PermissionDenied("You do not have permission to approve visitors.")

        visitor.approve(
            approved_by_user=request.user,
            notes=serializer.validated_data.get("notes", ""),
        )
        cache.delete(f"visitors_user_{visitor.created_by.id}")
        return Response({"message": "Visitor approved successfully."})

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request: Request, pk: int) -> Response:
        visitor = self.get_object()
        serializer = VisitorApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not CanApproveVisitor(request.user, visitor).has_permission():
            raise PermissionDenied("You do not have permission to reject visitors.")

        visitor.reject(
            rejected_by_user=request.user,
            reason=serializer.validated_data.get("reason", ""),
        )
        cache.delete(f"visitors_user_{visitor.created_by.id}")
        return Response({"message": "Visitor rejected."})

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request: Request, pk: int) -> Response:
        visitor = self.get_object()

        if visitor.created_by != request.user:
            raise PermissionDenied("You can only cancel your own visitor requests.")

        visitor.cancel()
        cache.delete(f"visitors_user_{visitor.created_by.id}")
        return Response({"message": "Visitor request cancelled."})

    @action(detail=True, methods=["post"], url_path="block")
    def block(self, request: Request, pk: int) -> Response:
        visitor = self.get_object()

        if not CanApproveVisitor(request.user, visitor).has_permission():
            raise PermissionDenied("You do not have permission to block visitors.")

        visitor.block()
        cache.delete(f"visitors_user_{visitor.created_by.id}")
        return Response({"message": "Visitor blocked."})

    @action(detail=True, methods=["post"], url_path="generate-qr")
    def generate_qr(self, request: Request, pk: int) -> Response:
        visitor = self.get_object()

        if (
            visitor.created_by != request.user
            and visitor.building.owner != request.user
        ):
            raise PermissionDenied(
                "You do not have permission to generate QR for this visitor."
            )

        if visitor.status not in [Visitor.Status.APPROVED, Visitor.Status.CHECKED_IN]:
            raise ValidationError("QR can only be generated for approved visitors.")

        if visitor.qr_token and not visitor.is_qr_expired:
            return Response(
                {
                    "message": "QR code already generated.",
                    "qr_token": visitor.qr_token,
                    "qr_expires_at": visitor.qr_expires_at,
                }
            )

        token = visitor.generate_qr_token()
        _log_history(
            visitor=visitor,
            action=VisitorHistory.Action.QR_GENERATED,
            description="QR code generated",
            performed_by=request.user,
        )
        return Response(
            {
                "message": "QR code generated successfully.",
                "qr_token": token,
                "qr_generated_at": visitor.qr_generated_at,
                "qr_expires_at": visitor.qr_expires_at,
                "qr_max_uses": visitor.qr_max_uses,
            }
        )

    @action(detail=True, methods=["post"], url_path="verify-qr")
    def verify_qr(self, request: Request, pk: int) -> Response:
        visitor = self.get_object()

        token = request.data.get("qr_token", "")
        if visitor.qr_token != token:
            return Response(
                {"error": "Invalid QR code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if visitor.is_qr_expired:
            return Response(
                {"error": "QR code has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if visitor.qr_used_count >= visitor.qr_max_uses:
            return Response(
                {"error": "QR code has exceeded maximum uses."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not CanCheckInVisitor(request.user, visitor).has_permission():
            raise PermissionDenied("You do not have permission to verify QR codes.")

        visitor.qr_verified = True
        visitor.qr_verified_at = timezone.now()
        visitor.qr_used_count += 1
        visitor.save(update_fields=["qr_verified", "qr_verified_at", "qr_used_count"])

        _log_history(
            visitor=visitor,
            action=VisitorHistory.Action.QR_VERIFIED,
            description="QR code verified at gate",
            performed_by=request.user,
        )
        return Response(
            {
                "message": "QR code verified successfully.",
                "visitor_name": visitor.visitor_name,
                "unit": visitor.unit_identifier,
                "purpose": visitor.get_purpose_display(),
                "status": visitor.status,
            }
        )

    @action(detail=True, methods=["post"], url_path="generate-otp")
    def generate_otp(self, request: Request, pk: int) -> Response:
        visitor = self.get_object()

        if visitor.created_by != request.user:
            raise PermissionDenied(
                "You can only generate OTP for your own visitor requests."
            )

        if visitor.status not in [Visitor.Status.APPROVED, Visitor.Status.CHECKED_IN]:
            raise ValidationError("OTP can only be generated for approved visitors.")

        if visitor.otp_code and not visitor.is_otp_expired:
            return Response(
                {
                    "message": "OTP already generated.",
                    "otp_expires_at": visitor.otp_expires_at,
                    "otp_attempts_remaining": visitor.OTP_MAX_ATTEMPTS
                    - visitor.otp_attempts,
                }
            )

        visitor.generate_otp()
        _log_history(
            visitor=visitor,
            action=VisitorHistory.Action.OTP_GENERATED,
            description="OTP generated for visitor verification",
            performed_by=request.user,
        )
        return Response(
            {
                "message": "OTP generated successfully.",
                "otp_expires_at": visitor.otp_expires_at,
                "otp_attempts_remaining": visitor.OTP_MAX_ATTEMPTS,
            }
        )

    @action(detail=True, methods=["post"], url_path="verify-otp")
    def verify_otp(self, request: Request, pk: int) -> Response:
        visitor = self.get_object()
        serializer = VisitorOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not CanCheckInVisitor(request.user, visitor).has_permission():
            raise PermissionDenied("You do not have permission to verify OTP codes.")

        entered_code = serializer.validated_data["otp_code"]
        is_valid = visitor.verify_otp(entered_code)

        if not is_valid:
            attempts_remaining = visitor.OTP_MAX_ATTEMPTS - visitor.otp_attempts
            if visitor.is_otp_expired:
                return Response(
                    {"error": "OTP has expired. Please request a new one."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if visitor.otp_attempts >= visitor.OTP_MAX_ATTEMPTS:
                return Response(
                    {
                        "error": (
                            "Maximum OTP attempts exceeded."
                            " Please request a new OTP."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {
                    "error": f"Invalid OTP. {attempts_remaining} attempts remaining.",
                    "attempts_remaining": attempts_remaining,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        _log_history(
            visitor=visitor,
            action=VisitorHistory.Action.OTP_VERIFIED,
            description="OTP verified successfully",
            performed_by=request.user,
        )
        return Response(
            {
                "message": "OTP verified successfully.",
                "visitor_name": visitor.visitor_name,
                "status": visitor.status,
            }
        )

    @action(detail=True, methods=["post"], url_path="check-in")
    def check_in(self, request: Request, pk: int) -> Response:
        visitor = self.get_object()
        serializer = VisitorCheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not CanCheckInVisitor(request.user, visitor).has_permission():
            raise PermissionDenied("You do not have permission to check in visitors.")

        if not visitor.can_check_in:
            if visitor.is_visit_expired and visitor.status == Visitor.Status.APPROVED:
                visitor.mark_expired()
                return Response(
                    {"error": "Visit has expired."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            raise ValidationError(
                f"Visitor cannot be checked in (current status: {visitor.status})."
            )

        visitor.check_in(
            verified_by_user=request.user,
            vehicle_details=serializer.validated_data.get("vehicle_details", ""),
        )
        cache.delete(f"visitors_user_{visitor.created_by.id}")

        _log_history(
            visitor=visitor,
            action=VisitorHistory.Action.CHECKED_IN,
            description="Visitor checked in",
            performed_by=request.user,
            metadata={
                "vehicle_details": serializer.validated_data.get("vehicle_details", "")
            },
        )
        return Response({"message": "Visitor checked in successfully."})

    @action(detail=True, methods=["post"], url_path="check-out")
    def check_out(self, request: Request, pk: int) -> Response:
        visitor = self.get_object()

        if not CanCheckOutVisitor(request.user, visitor).has_permission():
            raise PermissionDenied("You do not have permission to check out visitors.")

        if not visitor.can_check_out:
            raise ValidationError(
                f"Visitor cannot be checked out (current status: {visitor.status})."
            )

        visitor.check_out()
        cache.delete(f"visitors_user_{visitor.created_by.id}")

        _log_history(
            visitor=visitor,
            action=VisitorHistory.Action.CHECKED_OUT,
            description="Visitor checked out",
            performed_by=request.user,
            metadata={"duration_minutes": visitor.visit_duration_minutes},
        )
        return Response(
            {
                "message": "Visitor checked out successfully.",
                "visit_duration_minutes": visitor.visit_duration_minutes,
            }
        )

    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request: Request, pk: int) -> Response:
        visitor = self.get_object()
        visitor_history = visitor.history.select_related("performed_by").order_by(
            "-created_at"
        )
        page = self.paginate_queryset(visitor_history)
        if page is not None:
            serializer = VisitorHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = VisitorHistorySerializer(visitor_history, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request: Request) -> Response:
        user = self.request.user
        stats = get_visitor_stats(user)
        serializer = VisitorStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="mark-expired")
    def mark_expired(self, request: Request) -> Response:
        count = mark_expired_visitors()
        return Response({"message": f"{count} visitors marked as expired."})


class VisitorPublicVerifyView(viewsets.GenericViewSet):
    """Public endpoint for QR/OTP verification at gate kiosks.

    This endpoint does NOT require authentication — it is designed
    for use by gate hardware / caretaker kiosk devices.
    """

    permission_classes = []  # No auth required
    serializer_class = VisitorSerializer
    queryset = Visitor.objects.all()

    @action(detail=False, methods=["post"], url_path="verify-qr")
    def verify_qr_public(self, request: Request) -> Response:
        token = request.data.get("qr_token", "")
        if not token:
            return Response(
                {"error": "qr_token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            visitor = Visitor.objects.select_related("renter", "unit", "building").get(
                qr_token=token, is_archived=False
            )
        except Visitor.DoesNotExist:
            return Response(
                {"error": "Invalid QR code."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if visitor.is_qr_expired:
            return Response(
                {"error": "QR code has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if visitor.qr_used_count >= visitor.qr_max_uses:
            return Response(
                {"error": "QR code has exceeded maximum uses."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if visitor.status not in [Visitor.Status.APPROVED, Visitor.Status.CHECKED_IN]:
            return Response(
                {
                    "error": (
                        f"Visitor is not in an approvable state "
                        f"(status: {visitor.status})."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = VisitorSerializer(visitor, context={"request": request})
        return Response(
            {
                "message": "QR code is valid.",
                "visitor": serializer.data,
            }
        )
