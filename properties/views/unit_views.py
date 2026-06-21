"""Unit-related ViewSets and the Leegality webhook.

Views are kept thin; business logic lives in services. This module
also handles the Leegality webhook as a function-based view to keep
the surface area small.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, cast

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import BaseSerializer

from core.models import User
from rentsecure_be.services.leegality_service import send_agreement_for_signature
from rentsecure_be.type_compat import override

from ..constants import UNITS_CACHE_TIMEOUT
from ..feature_enforcer import FeatureEnforcer
from ..models import (
    RentAgreementDraft,
    Renter,
    Unit,
    UnitDocument,
    UnitImage,
)
from ..serializers import (
    RentAgreementDraftSerializer,
    UnitDocumentSerializer,
    UnitImageSerializer,
    UnitSerializer,
)

if TYPE_CHECKING:
    from django.db.models import QuerySet


logger = logging.getLogger(__name__)


class UnitViewSet(viewsets.ModelViewSet[Unit]):
    """CRUD for the :class:`Unit` model — owned by the authenticated user."""

    serializer_class = UnitSerializer
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    @override
    def get_queryset(self) -> QuerySet[Unit]:
        """Return cached, owned units (graceful fallback to free plan)."""
        user = cast(User, self.request.user)
        cache_key: str = f"units_user_{user.id}"
        enforcer = FeatureEnforcer(user)

        units: QuerySet[Unit] | None = cache.get(cache_key)
        if units is None:
            units = Unit.objects.filter(owner=user)
            cache.set(cache_key, units, timeout=UNITS_CACHE_TIMEOUT)

        if enforcer.is_expired() and enforcer.is_past_grace_period():
            free_limit = enforcer.get_free_plan_limit("max_units")
            active_units = units.filter(is_archived=False)
            if free_limit == "unlimited":
                return active_units
            return active_units[:free_limit]

        return units

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
        if serializer.instance.owner != self.request.user:
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
            raise PermissionDenied("You do not own the selected unit.")

        enforcer = FeatureEnforcer(self.request.user)
        if not enforcer.can_create("unit_images"):
            raise PermissionDenied("You have reached your image upload limit.")

        serializer.save()
        enforcer.increment("unit_images")
        cache.delete(f"unit_images_user_{self.request.user.id}")

    @override
    def perform_update(self, serializer: BaseSerializer[Any]) -> None:
        """Persist image updates after ownership check."""
        unit: Unit | None = (
            serializer.validated_data.get("unit") or serializer.instance.unit
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
        unit: Unit | None = (
            serializer.validated_data.get("unit") or serializer.instance.unit
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
        """Return cached, owned agreement drafts."""
        if isinstance(self.request.user, AnonymousUser):
            return RentAgreementDraft.objects.none()
        user = self.request.user
        cache_key: str = f"rent_drafts_user_{user.id}"
        drafts: QuerySet[RentAgreementDraft] | None = cache.get(cache_key)
        if drafts is None:
            drafts = RentAgreementDraft.objects.filter(user=user)
            cache.set(cache_key, drafts, timeout=300)
        return drafts

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
            owner_email: str | None = self.request.user.email
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
        if instance.user != self.request.user:
            raise PermissionDenied("You do not own this draft.")

        unit: Unit | None = serializer.validated_data.get("unit", instance.unit)
        renter: Renter | None = serializer.validated_data.get("renter", instance.renter)

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


@csrf_exempt
def leegality_webhook(request: HttpRequest) -> JsonResponse:
    """Process Leegality signing-status callbacks.

    Updates ``owner_signed`` / ``renter_signed`` flags based on the
    document state. The endpoint is intentionally permissive — it
    always returns ``200`` so Leegality does not retry indefinitely.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload: dict[str, Any] = json.loads(request.body.decode("utf-8"))
    except Exception:
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
    if agreement is not None and status_value is not None:
        if status_value.upper() == "SIGNED":
            if participant and participant.upper() == "OWNER":
                agreement.owner_signed = True
            elif participant and participant.upper() == "RENTER":
                agreement.renter_signed = True
            else:
                agreement.owner_signed = True
                agreement.renter_signed = True
            agreement.save(update_fields=["owner_signed", "renter_signed"])

    return JsonResponse({"status": "ok"})
