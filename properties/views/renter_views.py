from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.models import User
from notification.models import Notification
from rentsecure_be.type_compat import override

from ..feature_enforcer import FeatureEnforcer
from ..models import ExtraCharge, RentAgreementDraft, Renter, RentRecord, Unit
from ..serializers import (
    RenterAgreementSerializer,
    RenterDocumentSerializer,
    RenterExtraChargeSerializer,
    RenterProfileSerializer,
    RenterRentRecordDetailSerializer,
    RenterRentRecordSerializer,
    RenterSerializer,
)
from ..services.unit_service import update_unit_status
from ..utils.utils import check_feature_limit

if TYPE_CHECKING:
    from django.db.models import QuerySet

logger = logging.getLogger(__name__)


class RenterViewSet(viewsets.ModelViewSet[Renter]):
    """CRUD for renters owned by the authenticated user.

    Uses a per-user cache (5 minute TTL) for list views to reduce
    database pressure on the dashboard.
    """

    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]
    serializer_class = RenterSerializer
    search_fields = ["name", "phone", "email"]
    ordering_fields = [
        "name",
        "rent_amount",
        "start_date",
        "status",
        "-start_date",
        "-created_at",
    ]
    ordering = ["-start_date"]

    @override
    def get_queryset(self) -> QuerySet[Renter]:
        """Return all renters owned by the user."""
        if isinstance(self.request.user, AnonymousUser):
            return Renter.objects.none()
        user = self.request.user
        cache_key: str = f"renters_user_{user.id}"
        renters: QuerySet[Renter] | None = cache.get(cache_key)
        if renters is None:
            renters = Renter.objects.filter(unit__owner=user)
            cache.set(cache_key, renters, timeout=300)
        return renters

    @override
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new renter, enforcing the per-plan limit first."""
        user = cast(User, request.user)
        allowed, current_usage, subscription_limit, add_on_limit = check_feature_limit(
            user, "max_renters"
        )
        if not allowed:
            payload: dict[str, Any] = {
                "error": "You've reached your renter limit.",
                "required_add_on": "max_renters",
                "subscription_limit": subscription_limit,
                "add_on_limit": add_on_limit,
                "current_usage": current_usage,
            }
            return Response(payload, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    @override
    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        """Persist a new renter, enforce ownership, and update unit state."""
        unit: Unit | None = serializer.validated_data.get("unit")
        if unit is None or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")  # noqa: S1192

        enforcer = FeatureEnforcer(self.request.user)
        if not enforcer.can_create("max_renters"):
            raise PermissionDenied("Renter limit reached for your plan.")

        serializer.save()
        enforcer.increment("max_renters")
        update_unit_status(unit)
        cache.delete(f"renters_user_{self.request.user.id}")

    @override
    def perform_update(self, serializer: BaseSerializer[Any]) -> None:
        """Persist updates and refresh unit state."""
        instance = serializer.instance
        unit: Unit | None = serializer.validated_data.get("unit") or (
            instance.unit if instance else None
        )
        if unit is None or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        serializer.save()
        update_unit_status(unit)
        cache.delete(f"renters_user_{self.request.user.id}")

    @override
    def perform_destroy(self, instance: Renter) -> None:
        """Delete a renter and free up plan quota."""
        if instance.unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        unit: Unit = instance.unit
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement("max_renters")
        update_unit_status(unit)
        cache.delete(f"renters_user_{self.request.user.id}")

    @action(detail=True, methods=["post"], url_path="rate")
    def submit_rating(self, request: Request, pk: int) -> Response:
        renter = get_object_or_404(
            Renter.objects.select_related("unit"), pk=pk, unit__owner=request.user
        )

        allowed_statuses = ["deactivated", "revoked", "notice_period"]
        if renter.status not in allowed_statuses:
            return Response(
                {"error": "Rating allowed only after move-out."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rating = request.data.get("rating")
        feedback = request.data.get("feedback", "")

        if rating is None:
            return Response(
                {"error": "Rating is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rating_value = int(rating)
        except (TypeError, ValueError):
            return Response(
                {"error": "Rating must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not 1 <= rating_value <= 5:
            return Response(
                {"error": "Rating must be between 1 and 5"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        renter.rating = rating_value
        renter.feedback = feedback or ""
        renter.rated_at = timezone.now()
        renter.save(update_fields=["rating", "feedback", "rated_at"])

        return Response({"message": "Thank you for your feedback!"})

    @action(detail=True, methods=["post"], url_path="assign-unit")
    def assign_unit(self, request: Request, pk: int) -> Response:
        renter = get_object_or_404(
            Renter.objects.select_related("unit"), pk=pk, unit__owner=request.user
        )

        unit_id = request.data.get("unit_id")
        if not unit_id:
            return Response(
                {"error": "unit_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_unit = get_object_or_404(Unit, pk=unit_id, owner=request.user)

        if renter.unit_id == new_unit.id:
            return Response(
                {"error": "Renter is already assigned to this unit."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing = Renter.objects.filter(
            unit=new_unit, status__in=["active", "notice_period"]
        ).exclude(pk=renter.pk)
        if existing.exists():
            return Response(
                {"error": "The selected unit already has an active renter."},
                status=status.HTTP_409_CONFLICT,
            )

        old_unit = renter.unit
        renter.unit = new_unit
        renter.save(update_fields=["unit", "updated_at"])

        try:
            update_unit_status(old_unit)
        except Exception:
            logger.exception(
                "Failed to update status for old unit %s after renter reassignment",
                old_unit.id,
            )

        try:
            update_unit_status(new_unit)
        except Exception:
            logger.exception(
                "Failed to update status for new unit %s after renter reassignment",
                new_unit.id,
            )

        cache.delete(f"renters_user_{request.user.id}")

        serializer = RenterSerializer(renter, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="update-status")
    def update_status(self, request: Request, pk: int) -> Response:
        renter = get_object_or_404(
            Renter.objects.select_related("unit"), pk=pk, unit__owner=request.user
        )

        new_status = request.data.get("status")
        allowed_statuses = [
            Renter.RenterStatus.ACTIVE,
            Renter.RenterStatus.NOTICE_PERIOD,
            Renter.RenterStatus.REVOKED,
            Renter.RenterStatus.DEACTIVATED,
        ]
        if new_status not in allowed_statuses:
            return Response(
                {"error": "Invalid status."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        renter.status = new_status
        if new_status == Renter.RenterStatus.ACTIVE:
            renter.is_flagged = False
            renter.flagged_reason = ""
            renter.is_agreement_revoked = False
            renter.revocation_reason = ""
            renter.revoked_by_owner = False
            renter.revoked_on = None
            renter.notice_start_date = None
        elif new_status == Renter.RenterStatus.NOTICE_PERIOD:
            renter.notice_start_date = timezone.now().date()
        renter.save(
            update_fields=[
                "status",
                "notice_start_date",
                "is_flagged",
                "flagged_reason",
                "is_agreement_revoked",
                "revocation_reason",
                "revoked_by_owner",
                "revoked_on",
                "updated_at",
            ]
        )

        return Response({"message": "Status updated successfully."})

    @action(detail=True, methods=["post"], url_path="vacate")
    def vacate(self, request: Request, pk: int) -> Response:
        renter = get_object_or_404(
            Renter.objects.select_related("unit"), pk=pk, unit__owner=request.user
        )

        if renter.status != Renter.RenterStatus.NOTICE_PERIOD:
            return Response(
                {"error": "Renter is not in notice period."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        renter.status = Renter.RenterStatus.DEACTIVATED
        renter.vacated_on = timezone.now().date()
        renter.is_active = False
        renter.save()

        try:
            from notification.services.rent_notify_service import (
                notify_owner,
                notify_renter,
            )

            renter_msg = (
                "You have been vacated from the property. "
                "All records have been archived successfully."
            )
            owner_msg = (
                f"Renter {renter.name} has been vacated from unit "
                f"{renter.unit.unit}. The unit is now marked as vacant."
            )

            notify_renter(renter, renter_msg)
            notify_owner(renter.unit.owner, owner_msg)
        except Exception:
            logger.exception(
                "Failed to send vacate notifications for renter %s",
                renter.id,
            )

        return Response({"message": "Renter vacated and archived successfully."})

    @action(detail=False, methods=["get"], url_path="status_summary")
    def status_summary(self, request: Request) -> Response:
        user = cast(User, request.user)
        if isinstance(user, AnonymousUser):
            return Response(
                {
                    "active": 0,
                    "notice_period": 0,
                    "revoked": 0,
                    "deactivated": 0,
                }
            )

        summary = (
            Renter.objects.filter(unit__owner=user)
            .values("status")
            .annotate(count=Count("id"))
        )
        data = {item["status"]: item["count"] for item in summary}

        return Response(
            {
                "active": data.get("active", 0),
                "notice_period": data.get("notice_period", 0),
                "revoked": data.get("revoked", 0),
                "deactivated": data.get("deactivated", 0),
            }
        )

    @action(detail=False, methods=["get"], url_path="recent_activity")
    def recent_activity(self, request: Request) -> Response:
        user = cast(User, request.user)
        if isinstance(user, AnonymousUser):
            return Response([])

        recent_renters = Renter.objects.filter(
            unit__owner=user, status_changed_at__isnull=False
        ).order_by("-status_changed_at")[:10]

        data = [
            {
                "name": renter.name,
                "status": renter.status,
                "changed_at": (
                    renter.status_changed_at.strftime("%d %b %Y")
                    if renter.status_changed_at
                    else None
                ),
            }
            for renter in recent_renters
        ]

        return Response(data)


# ---------------------------------------------------------------------------
# Renter-scoped endpoints (current authenticated renter)
# ---------------------------------------------------------------------------


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def renter_profile(request: Request) -> Response:
    user = cast(User, request.user)
    if isinstance(user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    renter = get_object_or_404(
        Renter.objects.select_related("unit", "unit__building"),
        user=user,
        status__in=["active", "notice_period"],
    )

    cache_key = f"renter_profile_user_{user.id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)

    serializer = RenterProfileSerializer(renter, context={"request": request})
    data = serializer.data
    cache.set(cache_key, data, timeout=120)
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def renter_rent_records(request: Request) -> Response:
    user = cast(User, request.user)
    if isinstance(user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    renter = get_object_or_404(
        Renter.objects.select_related("unit", "unit__building"),
        user=user,
        status__in=["active", "notice_period"],
    )

    try:
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 20))
    except (ValueError, TypeError):
        page = 1
        limit = 20

    page = max(page, 1)
    limit = max(min(limit, 100), 1)

    rents_qs = (
        RentRecord.objects.filter(renter=renter)
        .select_related("unit", "renter", "renter__unit", "renter__unit__building")
        .order_by("-due_date")
    )

    total = rents_qs.count()
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    start = (page - 1) * limit
    end = start + limit
    page_qs = rents_qs[start:end]

    serializer = RenterRentRecordDetailSerializer(
        page_qs, many=True, context={"request": request}
    )
    return Response(
        {
            "data": serializer.data,
            "meta": {
                "total": total,
                "page": page,
                "limit": limit,
                "totalPages": total_pages,
            },
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def renter_rent_record_detail(request: Request, rent_id: int) -> Response:
    user = cast(User, request.user)
    if isinstance(user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    renter = get_object_or_404(
        Renter.objects.select_related("unit", "unit__building"),
        user=user,
        status__in=["active", "notice_period"],
    )

    rent = get_object_or_404(
        RentRecord.objects.select_related("unit", "renter"),
        pk=rent_id,
        renter=renter,
    )

    serializer = RenterRentRecordDetailSerializer(rent, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def renter_agreement(request: Request) -> Response:
    user = cast(User, request.user)
    if isinstance(user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    renter = get_object_or_404(
        Renter.objects.select_related("unit", "unit__building"),
        user=user,
        status__in=["active", "notice_period"],
    )

    agreement = get_object_or_404(
        RentAgreementDraft.objects.select_related("renter", "unit", "unit__building"),
        renter=renter,
    )

    cache_key = f"renter_agreement_user_{user.id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)

    serializer = RenterAgreementSerializer(agreement, context={"request": request})
    data = serializer.data
    cache.set(cache_key, data, timeout=300)
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def renter_documents(request: Request) -> Response:
    user = cast(User, request.user)
    if isinstance(user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    renter = get_object_or_404(
        Renter.objects.select_related("unit", "unit__building"),
        user=user,
        status__in=["active", "notice_period"],
    )

    cache_key = f"renter_documents_user_{user.id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)

    serializer = RenterDocumentSerializer(renter, context={"request": request})
    data = serializer.data
    cache.set(cache_key, data, timeout=300)
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def renter_extra_charges(request: Request) -> Response:
    user = cast(User, request.user)
    if isinstance(user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    renter = get_object_or_404(
        Renter.objects.select_related("unit", "unit__building"),
        user=user,
        status__in=["active", "notice_period"],
    )

    try:
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 20))
    except (ValueError, TypeError):
        page = 1
        limit = 20

    page = max(page, 1)
    limit = max(min(limit, 100), 1)

    charges_qs = (
        ExtraCharge.objects.filter(renter=renter)
        .select_related("renter", "unit")
        .order_by("-due_date")
    )

    total = charges_qs.count()
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    start = (page - 1) * limit
    end = start + limit
    page_qs = charges_qs[start:end]

    serializer = RenterExtraChargeSerializer(page_qs, many=True)
    return Response(
        {
            "data": serializer.data,
            "meta": {
                "total": total,
                "page": page,
                "limit": limit,
                "totalPages": total_pages,
            },
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def renter_dashboard(request: Request) -> Response:
    user = cast(User, request.user)
    if isinstance(user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    renter = get_object_or_404(
        Renter.objects.select_related("unit", "unit__building"),
        user=user,
        status__in=["active", "notice_period"],
    )

    cache_key = f"renter_dashboard_user_{user.id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)

    profile_serializer = RenterProfileSerializer(renter, context={"request": request})
    profile_data = profile_serializer.data

    current_rent = (
        RentRecord.objects.filter(renter=renter, status__in=["pending", "overdue"])
        .select_related("unit", "renter")
        .order_by("-due_date")
        .first()
    )
    current_rent_data = None
    if current_rent:
        current_rent_data = RenterRentRecordDetailSerializer(
            current_rent, context={"request": request}
        ).data

    recent_payments = (
        RentRecord.objects.filter(renter=renter)
        .select_related("unit", "renter")
        .order_by("-due_date")[:5]
    )
    recent_payments_data = RenterRentRecordSerializer(recent_payments, many=True).data

    agreement = RentAgreementDraft.objects.filter(renter=renter).first()
    agreement_data = None
    if agreement:
        agreement_data = RenterAgreementSerializer(
            agreement, context={"request": request}
        ).data

    notifications_unread_count = Notification.objects.filter(
        user=user, is_read=False, archived=False
    ).count()

    extra_charges_count = ExtraCharge.objects.filter(
        renter=renter, status=ExtraCharge.Status.DUE
    ).count()

    dashboard_data = {
        "profile": profile_data,
        "current_rent": current_rent_data,
        "recent_payments": recent_payments_data,
        "agreement": agreement_data,
        "notifications_unread_count": notifications_unread_count,
        "extra_charges_count": extra_charges_count,
    }

    cache.set(cache_key, dashboard_data, timeout=60)
    return Response(dashboard_data)
