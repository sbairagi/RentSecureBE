"""The renter facing part of the portal.

Everything a renter can do lives behind these endpoints:

* the home they live in and its rent ledger,
* the maintenance of their flat,
* the agreement they have to sign,
* the police verification they have to submit,
* the homes they can rent next and the viewing they can book.

The renter is the user who is linked to a :class:`~properties.models.Renter`
record. A renter without a lease (a prospective tenant) can still browse
the listings and book a viewing.
"""

from __future__ import annotations

from typing import Any, cast

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.models import User
from documents.receipt import receipt_filename
from rentsecure_be.type_compat import override

from ..models import (
    MaintenanceRequest,
    PoliceVerification,
    RentAgreementDraft,
    Renter,
    RentRecord,
    Unit,
    ViewingAppointment,
)
from ..serializers.rent_record_serializers import (
    PartPaymentSerializer,
    RentRecordPartSerializer,
)
from ..serializers.renter_portal_serializers import (
    RenterAgreementSerializer,
    RenterListingSerializer,
    RenterMaintenanceSerializer,
    RenterVerificationSerializer,
    ViewingAppointmentSerializer,
)
from ..serializers.renter_serializers import RenterRentRecordDetailSerializer
from ..services.rent_collection_service import record_part_payment

RENTER_STATUSES = ("active", "notice_period")


def _current_renter(request: Request) -> Renter | None:
    """Return the renter record of the authenticated user, when there is one."""
    user = cast(User, request.user)
    if isinstance(user, AnonymousUser):
        return None
    return (
        Renter.objects.select_related("unit", "unit__building", "user")
        .filter(user=user, status__in=RENTER_STATUSES)
        .first()
    )


def _require_renter(request: Request) -> Renter:
    """Return the renter record or refuse the request."""
    renter = _current_renter(request)
    if renter is None:
        raise NotFound("No active tenancy is linked to this account.")
    return renter


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def renter_listings(request: Request) -> Response:
    """Return the homes that are available to rent, across every owner."""
    query = Unit.objects.filter(
        is_archived=False, status=Unit.VacancyStatus.VACANT
    ).select_related("building", "owner")

    search = request.query_params.get("search", "").strip()
    if search:
        query = query.filter(
            Q(unit__icontains=search)
            | Q(building_name__icontains=search)
            | Q(building__name__icontains=search)
            | Q(address_line__icontains=search)
            | Q(city__icontains=search)
            | Q(landmark__icontains=search)
        )
    city = request.query_params.get("city", "").strip()
    if city:
        query = query.filter(city__iexact=city)
    unit_type = request.query_params.get("unit_type", "").strip()
    if unit_type:
        query = query.filter(unit_type=unit_type)
    max_rent = request.query_params.get("max_rent", "").strip()
    if max_rent:
        try:
            query = query.filter(rent_amount__lte=float(max_rent))
        except (TypeError, ValueError) as error:
            raise ValidationError("The maximum rent has to be a number.") from error

    try:
        page = max(int(request.query_params.get("page", 1)), 1)
        limit = max(min(int(request.query_params.get("limit", 20)), 50), 1)
    except (TypeError, ValueError):
        page = 1
        limit = 20

    total = query.count()
    start = (page - 1) * limit
    results = query.order_by("city", "building_name", "unit")[start : start + limit]

    return Response(
        {
            "data": RenterListingSerializer(results, many=True).data,
            "meta": {
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit if total else 1,
            },
        }
    )


class RenterAppointmentViewSet(viewsets.ViewSet):
    """The viewing appointments a renter books."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> Any:
        """Return the appointments of the authenticated renter."""
        user = cast(User, self.request.user)
        return ViewingAppointment.objects.filter(renter_user=user).select_related(
            "unit", "unit__building", "unit__owner"
        )

    @override
    def list(self, request: Request) -> Response:
        """Return the appointments of the renter."""
        appointments = self.get_queryset()
        status_filter = request.query_params.get("status", "").strip()
        if status_filter:
            appointments = appointments.filter(status=status_filter)
        serializer = ViewingAppointmentSerializer(
            appointments, many=True, context={"request": request}
        )
        return Response({"data": serializer.data})

    @override
    def create(self, request: Request) -> Response:
        """Book a viewing for a unit of any owner."""
        unit_id = request.data.get("unit")
        if not unit_id:
            raise ValidationError("Choose the unit you want to see.")
        unit = (
            Unit.objects.filter(id=unit_id, is_archived=False)
            .select_related("building", "owner")
            .first()
        )
        if unit is None:
            raise NotFound("That home is not available any more.")
        if unit.owner_id == request.user.id:
            raise ValidationError("You cannot book a viewing of your own home.")

        scheduled_for = request.data.get("scheduled_for")
        if not scheduled_for:
            raise ValidationError("Choose a date and a time for the viewing.")
        from django.utils.dateparse import parse_datetime

        parsed = parse_datetime(str(scheduled_for))
        if parsed is None:
            raise ValidationError("The appointment date could not be read.")
        if parsed.tzinfo is None:
            parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
        if parsed < timezone.now():
            raise ValidationError("The appointment has to be in the future.")

        mode = str(request.data.get("mode", ViewingAppointment.Mode.IN_PERSON))
        if mode not in ViewingAppointment.Mode.values:
            raise ValidationError("Choose either an in person or a video viewing.")

        renter = _current_renter(request)
        appointment = ViewingAppointment.objects.create(
            renter_user=request.user,
            renter=renter,
            unit=unit,
            scheduled_for=parsed,
            mode=mode,
            notes=str(request.data.get("notes", ""))[:1000],
        )
        serializer = ViewingAppointmentSerializer(
            appointment, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch", "post"], url_path="cancel")
    def cancel(self, request: Request, pk: int | None = None) -> Response:
        """Cancel an appointment the renter booked."""
        appointment = self.get_queryset().filter(pk=pk).first()
        if appointment is None:
            raise NotFound("That appointment does not exist.")
        if appointment.status in (
            ViewingAppointment.Status.COMPLETED,
            ViewingAppointment.Status.CANCELLED,
        ):
            raise ValidationError("This appointment is already closed.")
        appointment.status = ViewingAppointment.Status.CANCELLED
        appointment.save(update_fields=["status"])
        serializer = ViewingAppointmentSerializer(
            appointment, context={"request": request}
        )
        return Response(serializer.data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def renter_maintenance(request: Request) -> Response:
    """The maintenance of the flat the renter lives in."""
    renter = _require_renter(request)

    if request.method == "GET":
        requests_qs = MaintenanceRequest.objects.filter(
            Q(renter=renter) | Q(unit=renter.unit)
        ).select_related("unit", "unit__building", "assigned_caretaker")
        status_filter = request.query_params.get("status", "").strip()
        if status_filter:
            requests_qs = requests_qs.filter(status=status_filter)
        serializer = RenterMaintenanceSerializer(
            requests_qs, many=True, context={"request": request}
        )
        return Response({"data": serializer.data})

    title = str(request.data.get("title", "")).strip()
    if not title:
        raise ValidationError("Describe the issue in a short title.")
    request_obj = MaintenanceRequest.objects.create(
        owner=renter.unit.owner,
        unit=renter.unit,
        renter=renter,
        title=title[:180],
        description=str(request.data.get("description", ""))[:4000],
        category=str(request.data.get("category", MaintenanceRequest.Category.OTHER)),
        priority=str(request.data.get("priority", MaintenanceRequest.Priority.MEDIUM)),
    )
    serializer = RenterMaintenanceSerializer(request_obj, context={"request": request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def renter_verification(request: Request) -> Response:
    """The police verification of the renter."""
    renter = _require_renter(request)

    verification = PoliceVerification.objects.filter(renter=renter).first()

    if request.method == "GET":
        if verification is None:
            return Response(
                {
                    "id": None,
                    "status": PoliceVerification.PoliceVerificationStatus.NOT_STARTED,
                    "status_label": "Not started",
                    "renter_name": renter.name,
                    "unit_label": renter.unit.unit,
                    "file": None,
                    "submitted_at": None,
                    "verified_at": None,
                    "reviewed_at": None,
                    "review_notes": "",
                    "rejection_reason": "",
                }
            )
        serializer = RenterVerificationSerializer(
            verification, context={"request": request}
        )
        return Response(serializer.data)

    upload = request.FILES.get("file")
    if upload is None:
        raise ValidationError("Attach the police verification document.")
    if verification is None:
        verification = PoliceVerification.objects.create(
            user=renter.unit.owner,
            renter=renter,
            unit=renter.unit,
        )
    if verification.status == PoliceVerification.PoliceVerificationStatus.VERIFIED:
        raise ValidationError("This verification is already approved.")

    verification.file = upload
    verification.status = PoliceVerification.PoliceVerificationStatus.SUBMITTED
    verification.submitted_at = timezone.now()
    verification.reviewed_by = None
    verification.reviewed_at = None
    verification.review_notes = ""
    verification.rejection_reason = ""
    verification.save()
    serializer = RenterVerificationSerializer(
        verification, context={"request": request}
    )
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def renter_agreements(request: Request) -> Response:
    """The agreements of the renter, ready to be signed."""
    renter = _require_renter(request)
    agreements = RentAgreementDraft.objects.filter(renter=renter).select_related(
        "unit", "unit__building", "user"
    )
    serializer = RenterAgreementSerializer(
        agreements, many=True, context={"request": request}
    )
    return Response({"data": serializer.data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def renter_rent_payment(request: Request, rent_id: int) -> Response:
    """Record a payment against a month of the renter's own rent.

    The renter pays the balance of their own month; the backend records the
    part, issues the receipt number and settles the month when the balance
    reaches zero. The rules are the owner's rules — the same service records
    the payment for both sides.
    """
    renter = _require_renter(request)
    rent = get_object_or_404(
        RentRecord.objects.select_related("unit", "renter"),
        pk=rent_id,
        renter=renter,
    )
    if rent.status == RentRecord.Status.CANCELLED:
        raise ValidationError("This month was cancelled, there is nothing to pay.")

    payload = PartPaymentSerializer(data=request.data)
    payload.is_valid(raise_exception=True)
    data = payload.validated_data

    part = record_part_payment(
        rent,
        amount=data["amount"],
        paid_on=data["paid_on"],
        payment_method=data.get("payment_method") or RentRecord.PaymentMethod.CASH,
        transaction_id=data.get("transaction_id", ""),
        note=data.get("note", ""),
        user=request.user,
        split_allowed=bool(getattr(rent.unit, "allow_partial_payments", False)),
    )
    part.refresh_from_db()
    part.receipt_no = receipt_filename(rent, part)
    part.save(update_fields=["receipt_no"])

    rent.refresh_from_db()
    return Response(
        {
            "part": RentRecordPartSerializer(part).data,
            "record": RenterRentRecordDetailSerializer(
                rent, context={"request": request}
            ).data,
            "status": rent.status,
            "amount_paid": str(rent.amount_paid),
            "balance": str(rent.balance),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def renter_sign_agreement(request: Request) -> Response:
    """Sign an agreement as the renter."""
    renter = _require_renter(request)
    agreement_id = request.data.get("agreement")
    agreement = RentAgreementDraft.objects.filter(
        id=agreement_id, renter=renter
    ).first()
    if agreement is None:
        raise NotFound("That agreement does not exist.")
    if not agreement.document_generated_at:
        raise ValidationError(
            "The agreement document is still being generated. Try again in a moment."
        )
    if agreement.status in (
        RentAgreementDraft.AgreementStatus.TERMINATED,
        RentAgreementDraft.AgreementStatus.EXPIRED,
    ):
        raise ValidationError("This agreement can no longer be signed.")

    agreement.renter_signed = True
    agreement.renter_signed_at = agreement.renter_signed_at or timezone.now()
    agreement.status = agreement.refresh_status()
    agreement.save(update_fields=["renter_signed", "renter_signed_at", "status"])
    serializer = RenterAgreementSerializer(agreement, context={"request": request})
    return Response(serializer.data)
