"""Unit-related ViewSets and the Leegality webhook.

Views are kept thin; business logic lives in services. This module
also handles the Leegality webhook as a function-based view to keep
the surface area small.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any, cast

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q, QuerySet
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.models import User
from rentsecure_be.services.leegality_service import send_agreement_for_signature
from rentsecure_be.type_compat import override

from ..constants import UNITS_CACHE_TIMEOUT
from ..feature_enforcer import FeatureEnforcer
from ..models import RentAgreementDraft, Renter, Unit, UnitDocument, UnitImage
from ..serializers import (
    RentAgreementDraftSerializer,
    UnitDocumentSerializer,
    UnitImageSerializer,
    UnitSerializer,
)

logger = logging.getLogger(__name__)


class UnitViewSet(viewsets.ModelViewSet[Unit]):
    """CRUD for the :class:`Unit` model — owned by the authenticated user.

    Supports search, filtering, and ordering via query parameters:
      - search: icontains across unit, building_name, address_line,
                landmark, city, state
      - building: filter by building_id
      - city: filter by city
      - status: filter by status (VACANT/OCCUPIED)
      - unit_type: filter by unit_type
      - is_archived: filter by is_archived
      - ordering: field ordering (default: -created_at)
    """

    serializer_class = UnitSerializer
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    @override
    def get_queryset(self) -> QuerySet[Unit]:
        """Return cached, owned units (graceful fallback to free plan)."""
        user = cast(User, self.request.user)
        cache_key: str = f"units_user_{user.id}"
        enforcer = FeatureEnforcer(user)

        has_filters = self._has_active_unit_filters()

        if not has_filters:
            units: QuerySet[Unit] | None = cache.get(cache_key)
            if units is None:
                units = Unit.objects.filter(owner=user)
                cache.set(cache_key, units, timeout=UNITS_CACHE_TIMEOUT)
        else:
            units = Unit.objects.filter(owner=user)

        if enforcer.is_expired() and enforcer.is_past_grace_period():
            free_limit = enforcer.get_free_plan_limit("max_units")
            active_units = units.filter(is_archived=False)
            if free_limit == "unlimited":
                units = active_units
            else:
                units = active_units[:free_limit]

        return self._apply_unit_filters(units)

    def _has_active_unit_filters(self) -> bool:
        return any(
            self.request.GET.get(param)
            for param in (
                "search",
                "building",
                "city",
                "status",
                "unit_type",
                "is_archived",
                "ordering",
            )
        )

    def _apply_unit_filters(self, queryset: QuerySet[Unit]) -> QuerySet[Unit]:
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(unit__icontains=search)
                | Q(building_name__icontains=search)
                | Q(address_line__icontains=search)
                | Q(landmark__icontains=search)
                | Q(city__icontains=search)
                | Q(state__icontains=search)
            )

        building_param = self.request.GET.get("building")
        if building_param:
            queryset = queryset.filter(building_id=building_param)

        city = self.request.GET.get("city")
        if city:
            queryset = queryset.filter(city__icontains=city)

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        unit_type = self.request.GET.get("unit_type")
        if unit_type:
            queryset = queryset.filter(unit_type=unit_type)

        is_archived = self.request.GET.get("is_archived")
        if is_archived is not None:
            queryset = queryset.filter(is_archived=is_archived.lower() == "true")

        ordering = self.request.GET.get("ordering")
        if ordering:
            queryset = queryset.order_by(ordering)

        return queryset

    @override
    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        """Persist a new unit and update the cached queryset."""
        enforcer = FeatureEnforcer(self.request.user)
        if not enforcer.can_create("max_units"):
            raise PermissionDenied("Unit creation limit reached for your plan.")

        serializer.save(owner=self.request.user)
        enforcer.increment("max_units")
        cache.delete(f"units_user_{self.request.user.id}")

    @override
    def perform_update(self, serializer: BaseSerializer[Any]) -> None:
        """Persist unit updates after ownership check."""
        instance = serializer.instance
        if instance is None or instance.owner != self.request.user:
            raise PermissionDenied("You do not have permission to update this unit.")
        serializer.save()
        cache.delete(f"units_user_{self.request.user.id}")

    @override
    def perform_destroy(self, instance: Unit) -> None:
        """Delete a unit and decrement the owner's quota."""
        if instance.owner != self.request.user:
            raise PermissionDenied("You do not have permission to delete this unit.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement("max_units")
        cache.delete(f"units_user_{self.request.user.id}")

    @action(detail=False, methods=["get"], url_path="occupancy_stats")
    def occupancy_stats(self, request: Request) -> Response:
        user = cast(User, request.user)
        if isinstance(user, AnonymousUser):
            return Response({"total": 0, "occupied": 0, "vacant": 0})

        qs = Unit.objects.filter(owner=user)
        total = qs.count()
        occupied = qs.filter(status=Unit.VacancyStatus.OCCUPIED).count()
        vacant = total - occupied

        return Response(
            {
                "total": total,
                "occupied": occupied,
                "vacant": vacant,
            }
        )


class UnitImageViewSet(viewsets.ModelViewSet[UnitImage]):
    """CRUD for :class:`UnitImage` — images attached to a unit."""

    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]
    serializer_class = UnitImageSerializer

    @override
    def get_queryset(self) -> QuerySet[UnitImage]:
        """Return cached, owned unit images."""
        user = cast(User, self.request.user)
        cache_key: str = f"unit_images_user_{user.id}"
        images: QuerySet[UnitImage] | None = cache.get(cache_key)
        if images is None:
            images = UnitImage.objects.filter(unit__owner=user)
            cache.set(cache_key, images, timeout=300)
        return images

    @override
    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        """Persist a new image after ownership + quota check."""
        unit: Unit | None = serializer.validated_data.get("unit")
        if unit is None or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")  # noqa: S1192

        enforcer = FeatureEnforcer(self.request.user)
        if not enforcer.can_create("unit_images"):
            raise PermissionDenied("You have reached your image upload limit.")

        serializer.save()
        enforcer.increment("unit_images")
        cache.delete(f"unit_images_user_{self.request.user.id}")

    @override
    def perform_update(self, serializer: BaseSerializer[Any]) -> None:
        """Persist image updates after ownership check."""
        instance = serializer.instance
        unit: Unit | None = serializer.validated_data.get("unit") or (
            instance.unit if instance else None
        )
        if unit is None or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        serializer.save()
        cache.delete(f"unit_images_user_{self.request.user.id}")

    @override
    def perform_destroy(self, instance: UnitImage) -> None:
        """Delete an image and decrement the owner's quota."""
        if instance.unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement("unit_images")
        cache.delete(f"unit_images_user_{self.request.user.id}")


class UnitDocumentViewSet(viewsets.ModelViewSet[UnitDocument]):
    """CRUD for :class:`UnitDocument` — documents attached to a unit."""

    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]
    serializer_class = UnitDocumentSerializer

    @override
    def get_queryset(self) -> QuerySet[UnitDocument]:
        """Return cached, owned unit documents."""
        if isinstance(self.request.user, AnonymousUser):
            return UnitDocument.objects.none()
        user = self.request.user
        cache_key: str = f"unit_docs_user_{user.id}"
        docs: QuerySet[UnitDocument] | None = cache.get(cache_key)
        if docs is None:
            docs = UnitDocument.objects.filter(unit__owner=user)
            cache.set(cache_key, docs, timeout=300)
        return docs

    @override
    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        """Persist a new document after ownership + quota check."""
        unit: Unit | None = serializer.validated_data.get("unit")
        if unit is None or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")

        enforcer = FeatureEnforcer(self.request.user)
        if not enforcer.can_create("unit_documents"):
            raise PermissionDenied("You have reached your document upload limit.")

        serializer.save()
        enforcer.increment("unit_documents")
        cache.delete(f"unit_docs_user_{self.request.user.id}")

    @override
    def perform_update(self, serializer: BaseSerializer[Any]) -> None:
        """Persist document updates after ownership check."""
        instance = serializer.instance
        unit: Unit | None = serializer.validated_data.get("unit") or (
            instance.unit if instance else None
        )
        if unit is None or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        serializer.save()
        cache.delete(f"unit_docs_user_{self.request.user.id}")

    @override
    def perform_destroy(self, instance: UnitDocument) -> None:
        """Delete a document and decrement the owner's quota."""
        if instance.unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement("unit_documents")
        cache.delete(f"unit_docs_user_{self.request.user.id}")


class RentAgreementDraftViewSet(viewsets.ModelViewSet[RentAgreementDraft]):
    """CRUD for :class:`RentAgreementDraft` — also dispatches to Leegality."""

    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]
    serializer_class = RentAgreementDraftSerializer

    @override
    def get_queryset(self) -> QuerySet[RentAgreementDraft]:
        """Return cached, owned agreement drafts with search/filter/ordering."""
        if isinstance(self.request.user, AnonymousUser):
            return RentAgreementDraft.objects.none()
        user = self.request.user

        if not self._agreement_has_active_filters():
            cache_key: str = f"rent_drafts_user_{user.id}"
            drafts: QuerySet[RentAgreementDraft] | None = cache.get(cache_key)
            if drafts is None:
                drafts = RentAgreementDraft.objects.filter(user=user).select_related(
                    "renter", "unit", "unit__building"
                )
                cache.set(cache_key, drafts, timeout=300)
            return drafts

        return self._apply_agreement_filters(
            RentAgreementDraft.objects.filter(user=user).select_related(
                "renter", "unit", "unit__building"
            )
        )

    def _agreement_has_active_filters(self) -> bool:
        return any(
            self.request.GET.get(param)
            for param in (
                "search",
                "status",
                "building",
                "unit",
                "renter",
                "is_signed",
                "ordering",
            )
        )

    def _apply_agreement_filters(
        self, queryset: QuerySet[RentAgreementDraft]
    ) -> QuerySet[RentAgreementDraft]:
        queryset = self._apply_agreement_search(queryset)
        queryset = self._apply_agreement_status_filter(queryset)
        queryset = self._apply_agreement_relation_filters(queryset)
        return self._apply_agreement_ordering(queryset)

    def _apply_agreement_search(
        self, queryset: QuerySet[RentAgreementDraft]
    ) -> QuerySet[RentAgreementDraft]:
        search = self.request.GET.get("search")
        if not search:
            return queryset
        return queryset.filter(
            Q(renter__name__icontains=search)
            | Q(unit__unit__icontains=search)
            | Q(leegality_document_id__icontains=search)
        )

    def _apply_agreement_status_filter(
        self, queryset: QuerySet[RentAgreementDraft]
    ) -> QuerySet[RentAgreementDraft]:
        status_param = self.request.GET.get("status")
        if not status_param:
            return queryset

        status_map: dict[str, QuerySet[RentAgreementDraft]] = {
            "draft": queryset.filter(owner_signed=False, renter_signed=False),
            "pending_signature": queryset.filter(
                owner_signed=False, renter_signed=False
            ),
            "partially_signed": queryset.filter(
                Q(owner_signed=True, renter_signed=False)
                | Q(owner_signed=False, renter_signed=True)
            ),
            "fully_signed": queryset.filter(owner_signed=True, renter_signed=True),
            "active": queryset.filter(owner_signed=True, renter_signed=True),
        }
        return status_map.get(status_param, queryset)

    def _apply_agreement_relation_filters(
        self, queryset: QuerySet[RentAgreementDraft]
    ) -> QuerySet[RentAgreementDraft]:
        building_param = self.request.GET.get("building")
        if building_param:
            queryset = queryset.filter(unit__building_id=building_param)

        unit_param = self.request.GET.get("unit")
        if unit_param:
            queryset = queryset.filter(unit_id=unit_param)

        renter_param = self.request.GET.get("renter")
        if renter_param:
            queryset = queryset.filter(renter_id=renter_param)

        is_signed = self.request.GET.get("is_signed")
        if is_signed is not None:
            signed = is_signed.lower() == "true"
            if signed:
                queryset = queryset.filter(owner_signed=True, renter_signed=True)
            else:
                queryset = queryset.filter(
                    Q(owner_signed=False) | Q(renter_signed=False)
                )

        return queryset

    def _apply_agreement_ordering(
        self, queryset: QuerySet[RentAgreementDraft]
    ) -> QuerySet[RentAgreementDraft]:
        ordering = self.request.GET.get("ordering")
        if ordering:
            return queryset.order_by(ordering)
        return queryset.order_by("-generated_at")

    @override
    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        """Persist a new draft and send it for digital signature."""
        enforcer = FeatureEnforcer(self.request.user)
        renter: Renter | None = serializer.validated_data.get("renter")
        unit: Unit | None = serializer.validated_data.get("unit")

        if not enforcer.can_create("rent_agreement_drafts"):
            raise PermissionDenied("You have reached your draft creation limit.")

        if unit is None or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        if renter is None or renter.unit != unit:
            raise PermissionDenied("Renter does not belong to this unit.")

        agreement: RentAgreementDraft = serializer.save(user=self.request.user)
        enforcer.increment("rent_agreement_drafts")
        cache.delete(f"rent_drafts_user_{self.request.user.id}")

        try:
            user_obj = cast(User, self.request.user)
            owner_email: str | None = getattr(user_obj, "email", None)
            renter_email: str | None = agreement.renter.email
            if not owner_email:
                raise PermissionDenied("Owner email is required for digital signature.")
            send_agreement_for_signature(
                agreement,
                owner_email=owner_email,
                renter_email=renter_email,
            )
        except Exception as exc:
            logger.warning("Failed to send agreement for signature: %s", exc)

    @override
    def perform_update(self, serializer: BaseSerializer[Any]) -> None:
        """Persist draft updates after ownership + integrity checks."""
        instance = serializer.instance
        if instance is None or instance.user != self.request.user:
            raise PermissionDenied("You do not own this draft.")

        unit: Unit | None = serializer.validated_data.get("unit") or (
            instance.unit if instance else None
        )
        renter: Renter | None = serializer.validated_data.get("renter") or (
            instance.renter if instance else None
        )

        if unit is None or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        if renter is None or renter.unit != unit:
            raise PermissionDenied("Renter does not belong to this unit.")

        serializer.save()
        cache.delete(f"rent_drafts_user_{self.request.user.id}")

    @override
    def perform_destroy(self, instance: RentAgreementDraft) -> None:
        """Delete a draft and free up plan quota."""
        if instance.user != self.request.user:
            raise PermissionDenied("You do not own this draft.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement("rent_agreement_drafts")


# Webhook endpoint: CSRF is exempted. This endpoint receives inbound callbacks
# from external agreement providers. Those callers do not have browser
# sessions and therefore cannot supply a CSRF token.
# Security: Leegality webhook signature is verified inline below (hmac + sha256)
# before any business logic executes. The LEEGALITY_WEBHOOK_SECRET setting must
# be configured in production; the endpoint refuses all requests if it is absent.


def _apply_signature_status(
    agreement: RentAgreementDraft | None,
    status_value: str | None,
    participant: str | None,
) -> None:
    if agreement is None or status_value is None or status_value.upper() != "SIGNED":
        return
    if participant and participant.upper() == "OWNER":
        agreement.owner_signed = True
    elif participant and participant.upper() == "RENTER":
        agreement.renter_signed = True
    else:
        agreement.owner_signed = True
        agreement.renter_signed = True
    agreement.save(update_fields=["owner_signed", "renter_signed"])


@csrf_exempt
def leegality_webhook(request: HttpRequest) -> JsonResponse:
    """Process Leegality signing-status callbacks.

    Updates ``owner_signed`` / ``renter_signed`` flags based on the
    document state. The endpoint is intentionally permissive — it
    always returns ``200`` so Leegality does not retry indefinitely.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    webhook_secret = getattr(settings, "LEEGALITY_WEBHOOK_SECRET", None)
    if not webhook_secret:
        raise ImproperlyConfigured("LEEGALITY_WEBHOOK_SECRET is not set")
    signature = request.headers.get("X-Leegality-Signature")
    if not signature:
        return JsonResponse({"error": "Missing signature!"}, status=400)
    if not hmac.compare_digest(
        hmac.new(
            webhook_secret.encode("utf-8"), request.body, hashlib.sha256
        ).hexdigest(),
        signature,
    ):
        logger.warning("Leegality webhook: invalid signature")
        return JsonResponse({"error": "Invalid signature!"}, status=400)

    try:
        payload: dict[str, Any] = json.loads(request.body.decode("utf-8"))
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid payload"}, status=400)

    doc_id: str | None = (
        payload.get("document_id")
        or payload.get("documentId")
        or payload.get("documentKey")
    )
    status_value: str | None = payload.get("status") or payload.get("state")
    participant: str | None = payload.get("participant") or payload.get("identifier")

    agreement: RentAgreementDraft | None = RentAgreementDraft.objects.filter(
        leegality_document_id=doc_id
    ).first()
    _apply_signature_status(agreement, status_value, participant)

    return JsonResponse({"status": "ok"})
