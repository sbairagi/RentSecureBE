from __future__ import annotations

import logging
from typing import Any, cast

from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from core.models import User
from properties.services.payment_orchestrator import PaymentOrchestrator
from shared.type_compat import override

from ..feature_enforcer import FeatureEnforcer
from ..models import Renter, RentRecord, Unit
from ..serializers import RentRecordSerializer
from ..utils.utils import generate_rent_invoice_pdf

logger = logging.getLogger(__name__)


class RentRecordViewSet(viewsets.ModelViewSet[RentRecord]):
    permission_classes = [IsAuthenticated]
    serializer_class = RentRecordSerializer

    @override
    def get_queryset(self) -> Any:
        user = self.request.user
        if isinstance(user, AnonymousUser):
            return RentRecord.objects.none()
        cache_key = f"rent_records_user_{user.id}"
        rent_records = cache.get(cache_key)
        if rent_records is None:
            rent_records = RentRecord.objects.filter(unit__owner=user).select_related(
                "unit", "renter"
            )
            cache.set(cache_key, rent_records, timeout=300)
        return rent_records

    @override
    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        unit: Unit | None = serializer.validated_data.get("unit")
        renter = serializer.validated_data.get("renter")
        user = self.request.user

        if unit is None or unit.owner != user:
            raise PermissionDenied("You do not own this unit.")
        if renter is None or renter.unit != unit:
            raise ValidationError("Renter does not belong to the selected unit.")
        if RentRecord.objects.filter(
            renter=renter, due_date=serializer.validated_data.get("due_date")
        ).exists():
            raise ValidationError("Rent record for this month already exists.")

        enforcer = FeatureEnforcer(user)
        if not enforcer.can_create("rent_records"):
            raise PermissionDenied("You have reached your rent record creation limit.")

        rent = serializer.save()

        try:
            PaymentOrchestrator.create_payment_link(rent)
        except Exception as e:
            logger.warning(f"Failed to create payment link for rent {rent.id}: {e}")

        enforcer.increment("rent_records")
        cache.delete(f"rent_records_user_{user.id}")

    @override
    def perform_update(self, serializer: BaseSerializer[Any]) -> None:
        instance = serializer.instance
        user = self.request.user
        if instance is None or instance.unit is None or instance.unit.owner != user:
            raise PermissionDenied("You do not own this rent record.")

        new_unit: Unit | None = serializer.validated_data.get("unit") or (
            instance.unit if instance else None
        )
        if new_unit is None or new_unit.owner != user:
            raise PermissionDenied("You do not own the selected unit.")

        serializer.save()
        cache.delete(f"rent_records_user_{user.id}")

    @override
    def perform_destroy(self, instance: RentRecord) -> None:
        if instance.unit.owner != self.request.user:
            raise PermissionDenied("You do not own this rent record.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement("rent_records")
        cache.delete(f"rent_records_user_{self.request.user.id}")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def retry_payout_api(request: DRFRequest, rent_id: int) -> Any:
    rent = get_object_or_404(RentRecord, id=rent_id, renter__unit__owner=request.user)

    if rent.payment_status != "PAID" or rent.payout_status != "FAILED":
        return Response({"error": "Payout not retryable"}, status=400)

    try:
        PaymentOrchestrator.retry_payout(rent)
        rent.refresh_from_db()
        return Response(
            {"message": "Payout retry attempted", "status": rent.payout_status}
        )
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def owner_rent_records(request: DRFRequest) -> Any:
    owner = cast(User, request.user)
    rents = RentRecord.objects.filter(unit__owner=owner).select_related(
        "renter", "unit"
    )
    serializer = RentRecordSerializer(rents, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_rent_invoice(request: DRFRequest, rent_id: int) -> Any:
    rent = get_object_or_404(RentRecord, id=rent_id, owner=cast(User, request.user))
    pdf_path = generate_rent_invoice_pdf(rent)
    return FileResponse(open(pdf_path, "rb"), content_type="application/pdf")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_latest_due_rent(request: DRFRequest) -> Any:
    renter = Renter.objects.filter(
        user=cast(User, request.user), status__in=["active", "notice_period"]
    ).first()

    if not renter:
        return Response({"error": "Not a renter"}, status=403)

    rent = (
        RentRecord.objects.filter(renter=renter, status="PENDING")
        .order_by("-due_date")
        .first()
    )
    if not rent:
        return Response({"message": "No pending rent"})

    return Response(
        {
            "amount": float(rent.amount),
            "month": rent.due_date.month,
            "year": rent.due_date.year,
            "property": renter.unit.unit,
            "building": renter.unit.building.name if renter.unit.building else None,
            "payment_link": rent.payment_link,
            "due_date": rent.due_date,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def rent_history(request: DRFRequest) -> Any:
    renter = Renter.objects.filter(
        user=cast(User, request.user), status__in=["active", "notice_period"]
    ).first()
    if not renter:
        return Response({"error": "Not a renter"}, status=403)

    rents = RentRecord.objects.filter(renter=renter).order_by("-due_date")
    data = [
        {
            "month": r.due_date.month,
            "year": r.due_date.year,
            "amount": r.amount,
            "status": r.payment_status,
            "invoice_url": r.invoice_pdf.url if r.invoice_pdf else None,
            "payment_link": r.payment_link,
        }
        for r in rents
    ]
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def owner_rent_overview(request: DRFRequest) -> Any:
    owner = cast(User, request.user)
    rents = RentRecord.objects.filter(unit__owner=owner).select_related(
        "renter", "unit"
    )
    data = []
    for r in rents:
        data.append(
            {
                "tenant": r.renter.name if r.renter else "",
                "unit": r.unit.unit,
                "building": r.unit.building.name if r.unit.building else None,
                "amount": float(r.amount),
                "month": r.due_date.month,
                "year": r.due_date.year,
                "status": r.status,
                "payout": r.payout_status,
                "invoice_url": r.invoice_pdf.url if r.invoice_pdf else None,
            }
        )
    return Response(data)
