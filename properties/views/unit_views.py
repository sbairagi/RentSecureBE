import json
import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from rentsecure_be.services.leegality_service import send_agreement_for_signature

from ..constants import UNITS_CACHE_TIMEOUT
from ..feature_enforcer import FeatureEnforcer
from ..models import RentAgreementDraft, Unit, UnitDocument, UnitImage
from ..serializers import (
    RentAgreementDraftSerializer,
    UnitDocumentSerializer,
    UnitImageSerializer,
    UnitSerializer,
)


class UnitViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        cache_key = f"units_user_{user.id}"
        enforcer = FeatureEnforcer(user)

        units = cache.get(cache_key)
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

    def perform_create(self, serializer):
        enforcer = FeatureEnforcer(self.request.user)
        if not enforcer.can_create("max_units"):
            raise PermissionDenied("Unit creation limit reached for your plan.")

        serializer.save(owner=self.request.user)
        enforcer.increment("max_units")
        cache.delete(f"units_user_{self.request.user.id}")

    def perform_update(self, serializer):
        if serializer.instance.owner != self.request.user:
            raise PermissionDenied("You do not have permission to update this unit.")
        serializer.save()
        cache.delete(f"units_user_{self.request.user.id}")

    def perform_destroy(self, instance):
        if instance.owner != self.request.user:
            raise PermissionDenied("You do not have permission to delete this unit.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement("max_units")
        cache.delete(f"units_user_{self.request.user.id}")


class UnitImageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UnitImageSerializer

    def get_queryset(self):
        cache_key = f"unit_images_user_{self.request.user.id}"
        images = cache.get(cache_key)
        if images is None:
            images = UnitImage.objects.filter(unit__owner=self.request.user)
            cache.set(cache_key, images, timeout=300)
        return images

    def perform_create(self, serializer):
        unit = serializer.validated_data.get("unit")
        if not unit or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")

        enforcer = FeatureEnforcer(self.request.user)
        if not enforcer.can_create("unit_images"):
            raise PermissionDenied("You have reached your image upload limit.")

        serializer.save()
        enforcer.increment("unit_images")
        cache.delete(f"unit_images_user_{self.request.user.id}")

    def perform_update(self, serializer):
        unit = serializer.validated_data.get("unit") or serializer.instance.unit
        if unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        serializer.save()
        cache.delete(f"unit_images_user_{self.request.user.id}")

    def perform_destroy(self, instance):
        if instance.unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement("unit_images")
        cache.delete(f"unit_images_user_{self.request.user.id}")


class UnitDocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UnitDocumentSerializer

    def get_queryset(self):
        cache_key = f"unit_docs_user_{self.request.user.id}"
        docs = cache.get(cache_key)
        if docs is None:
            docs = UnitDocument.objects.filter(unit__owner=self.request.user)
            cache.set(cache_key, docs, timeout=300)
        return docs

    def perform_create(self, serializer):
        unit = serializer.validated_data.get("unit")
        if not unit or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")

        enforcer = FeatureEnforcer(self.request.user)
        if not enforcer.can_create("unit_documents"):
            raise PermissionDenied("You have reached your document upload limit.")

        serializer.save()
        enforcer.increment("unit_documents")
        cache.delete(f"unit_docs_user_{self.request.user.id}")

    def perform_update(self, serializer):
        unit = serializer.validated_data.get("unit") or serializer.instance.unit
        if unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        serializer.save()
        cache.delete(f"unit_docs_user_{self.request.user.id}")

    def perform_destroy(self, instance):
        if instance.unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement("unit_documents")
        cache.delete(f"unit_docs_user_{self.request.user.id}")


class RentAgreementDraftViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RentAgreementDraftSerializer

    def get_queryset(self):
        cache_key = f"rent_drafts_user_{self.request.user.id}"
        drafts = cache.get(cache_key)
        if drafts is None:
            drafts = RentAgreementDraft.objects.filter(user=self.request.user)
            cache.set(cache_key, drafts, timeout=300)
        return drafts

    def perform_create(self, serializer):
        enforcer = FeatureEnforcer(self.request.user)
        renter = serializer.validated_data.get("renter")
        unit = serializer.validated_data.get("unit")

        if not enforcer.can_create("rent_agreement_drafts"):
            raise PermissionDenied("You have reached your draft creation limit.")

        if unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        if renter.unit != unit:
            raise PermissionDenied("Renter does not belong to this unit.")

        agreement = serializer.save(user=self.request.user)
        enforcer.increment("rent_agreement_drafts")
        cache.delete(f"rent_drafts_user_{self.request.user.id}")

        try:
            owner_email = self.request.user.email
            renter_email = agreement.renter.email
            if not owner_email:
                raise PermissionDenied("Owner email is required for digital signature.")
            send_agreement_for_signature(
                agreement, owner_email=owner_email, renter_email=renter_email
            )
        except Exception as e:
            logger.warning(f"Failed to send agreement for signature: {e}")

    def perform_update(self, serializer):
        instance = serializer.instance
        if instance.user != self.request.user:
            raise PermissionDenied("You do not own this draft.")

        unit = serializer.validated_data.get("unit", instance.unit)
        renter = serializer.validated_data.get("renter", instance.renter)

        if unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        if renter.unit != unit:
            raise PermissionDenied("Renter does not belong to this unit.")

        serializer.save()
        cache.delete(f"rent_drafts_user_{self.request.user.id}")

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You do not own this draft.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement("rent_agreement_drafts")


@csrf_exempt
def leegality_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid payload"}, status=400)

    doc_id = (
        payload.get("document_id")
        or payload.get("documentId")
        or payload.get("documentKey")
    )
    status_value = payload.get("status") or payload.get("state")
    participant = payload.get("participant") or payload.get("identifier")

    agreement = RentAgreementDraft.objects.filter(leegality_document_id=doc_id).first()
    if agreement and status_value:
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
