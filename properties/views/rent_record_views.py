import logging
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from typing import Any, cast

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import (
    MethodNotAllowed,
    PermissionDenied,
    ValidationError,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.db.models import Count, Q, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.models import User
from documents.receipt import receipt_filename
from notification.services.rent_notify_service import send_payout_notification
from notification.services.whatsapp_service import send_whatsapp_message
from rentsecure_be.services.cashfree_service import process_rent_payout
from rentsecure_be.services.razorpay_service import create_payment_link
from rentsecure_be.type_compat import override

from ..feature_enforcer import FeatureEnforcer
from ..models import Renter, RentRecord, Unit
from ..serializers import (
    PartPaymentSerializer,
    RentRecordPartSerializer,
    RentRecordSerializer,
)
from ..services.rent_collection_service import (
    cancel_rent_record,
    record_part_payment,
    send_rent_receipt,
    send_rent_reminder,
)
from ..services.rent_rules import build_rent_rules
from ..utils.utils import generate_rent_invoice_pdf

logger = logging.getLogger(__name__)


class RentRecordViewSet(viewsets.ModelViewSet[RentRecord]):
    """CRUD for rent records owned by the authenticated user.

    Supports search, filtering, and ordering via query parameters:
      - search: icontains across renter__name, unit__unit, transaction_id, notes
      - status: filter by status (PENDING/PAID/OVERDUE/CANCELLED)
      - unit: filter by unit_id
      - ordering: field ordering (default: -due_date)
    """

    permission_classes = [IsAuthenticated]
    serializer_class = RentRecordSerializer

    @override
    def get_queryset(self) -> Any:
        user = self.request.user
        if isinstance(user, AnonymousUser):
            return RentRecord.objects.none()

        has_filters = any(
            self.request.GET.get(param)
            for param in ("search", "status", "unit", "ordering")
        )

        if not has_filters:
            cache_key = f"rent_records_user_{user.id}"
            rent_records = cache.get(cache_key)
            if rent_records is None:
                rent_records = (
                    RentRecord.objects.filter(unit__owner=user)
                    .select_related("unit", "renter")
                    .prefetch_related("parts")
                )
                cache.set(cache_key, rent_records, timeout=300)
        else:
            rent_records = (
                RentRecord.objects.filter(unit__owner=user)
                .select_related("unit", "renter")
                .prefetch_related("parts")
            )

        search = self.request.GET.get("search")
        if search:
            rent_records = rent_records.filter(
                Q(renter__name__icontains=search)
                | Q(unit__unit__icontains=search)
                | Q(transaction_id__icontains=search)
                | Q(notes__icontains=search)
            )

        status_param = self.request.GET.get("status")
        if status_param:
            rent_records = rent_records.filter(status=status_param)

        unit_param = self.request.GET.get("unit")
        if unit_param:
            rent_records = rent_records.filter(unit_id=unit_param)

        ordering = self.request.GET.get("ordering")
        if ordering:
            rent_records = rent_records.order_by(ordering)
        else:
            rent_records = rent_records.order_by("-due_date")

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
        if renter.status in {
            Renter.RenterStatus.REVOKED,
            Renter.RenterStatus.DEACTIVATED,
        }:
            raise ValidationError(
                "Rent cannot be paid for revoked or deactivated renters."
            )
        if RentRecord.objects.filter(
            renter=renter, due_date=serializer.validated_data.get("due_date")
        ).exists():
            raise ValidationError("Rent record for this month already exists.")

        enforcer = FeatureEnforcer(user)
        if not enforcer.can_create("rent_records"):
            raise PermissionDenied("You have reached your rent record creation limit.")

        rent = serializer.save()

        try:
            link = create_payment_link(rent)
            rent.payment_link = link
            rent.save(update_fields=["payment_link"])
            send_whatsapp_message(
                rent.renter.phone if rent.renter else "",
                f"📩 Pay your rent: {link}",
                user=user,
                rent_record=rent,
            )
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
        """Rent records are never deleted.

        The ledger keeps every record for the audit trail — a record leaves
        the books only through ``POST /rent-records/{id}/cancel/``, which
        needs a reason and keeps the row visible.
        """
        raise MethodNotAllowed(
            "Rent records are never deleted. Cancel the record instead so the "
            "ledger history stays intact."
        )

    def _owned_record(self, pk: Any) -> RentRecord:
        """Fetch a rent record owned by the caller or raise 404/403."""
        rent = get_object_or_404(RentRecord, pk=pk)
        if rent.unit.owner != self.request.user:
            raise PermissionDenied("You do not own this rent record.")
        return rent

    def _invalidate_caches(self) -> None:
        cache.delete(f"rent_records_user_{self.request.user.id}")

    @action(detail=False, methods=["get"], url_path="rules")
    def rules(self, request: DRFRequest) -> Response:
        """The rent-collection rules the clients check their forms against.

        The limits and the wording live on the server, so the web client and
        the API always agree on what a valid rent record is.
        """
        return Response(build_rent_rules(), status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request: DRFRequest, pk: Any = None) -> Response:
        """Cancel a rent record — the only way to take one out of the books.

        Body: ``{"reason": "..."}`` — the reason is mandatory.
        """
        rent = self._owned_record(pk)
        reason = request.data.get("reason", "") if hasattr(request, "data") else ""
        rent = cancel_rent_record(rent, reason, request.user)
        self._invalidate_caches()
        return Response(self.get_serializer(rent).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="send-receipt")
    def send_receipt(self, request: DRFRequest, pk: Any = None) -> Response:
        """Send the settlement receipt of a settled month to the renter.

        A month that is still open does not need a manual receipt: every
        part payment already carries its own receipt, and the settlement
        receipt unlocks once the balance reaches zero.
        """
        rent = self._owned_record(pk)
        status_value = str(rent.status or "").lower()
        if status_value != RentRecord.Status.PAID:
            if (rent.amount_paid or Decimal("0")) <= 0:
                raise ValidationError(
                    {
                        "error": (
                            "The rent receipt is generated once a payment is "
                            "confirmed. Use Remind to follow up on the pending "
                            "payment."
                        )
                    }
                )
            raise ValidationError(
                {
                    "error": (
                        "This month is not settled yet. The receipt of every part "
                        "payment is sent automatically, and the settlement receipt "
                        "can be sent once the month is fully paid."
                    )
                }
            )
        delivered = send_rent_receipt(rent, request.user)
        self._invalidate_caches()
        return Response(
            {
                "sent": delivered,
                "receipt_sent_at": rent.receipt_sent_at,
                "record": self.get_serializer(rent).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="send-reminder")
    def send_reminder(self, request: DRFRequest, pk: Any = None) -> Response:
        """Send a WhatsApp reminder for whatever balance is still due."""
        rent = self._owned_record(pk)
        sent = send_rent_reminder(rent, request.user)
        self._invalidate_caches()
        return Response(
            {
                "sent": sent,
                "balance": str(rent.balance),
                "last_reminded_at": rent.last_reminded_at,
                "record": self.get_serializer(rent).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="payments")
    def payments(self, request: DRFRequest, pk: Any = None) -> Response:
        """Record one part payment against the month."""
        rent = self._owned_record(pk)
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
        )
        part.refresh_from_db()
        part.receipt_no = receipt_filename(rent, part)
        part.save(update_fields=["receipt_no"])

        self._invalidate_caches()
        rent.refresh_from_db()
        serializer = self.get_serializer(rent)
        return Response(
            {
                "part": RentRecordPartSerializer(part).data,
                "record": serializer.data,
                "status": rent.status,
                "amount_paid": str(rent.amount_paid),
                "balance": str(rent.balance),
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="monthly_rent_summary")
    def monthly_rent_summary(self, request: DRFRequest) -> Response:
        user = cast(User, request.user)
        if isinstance(user, AnonymousUser):
            return Response(
                {
                    "month": "",
                    "collected_amount": 0,
                    "collected_count": 0,
                    "pending_count": 0,
                }
            )

        today = timezone.now()
        this_month_start = today.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        rent_records = RentRecord.objects.filter(
            unit__owner=user,
            created_at__gte=this_month_start,
        )

        collected = rent_records.filter(status=RentRecord.Status.PAID).aggregate(
            total=Sum("amount_paid"), count=Count("id")
        )

        pending = rent_records.filter(status=RentRecord.Status.PENDING).count()

        return Response(
            {
                "month": today.strftime("%B %Y"),
                "collected_amount": collected["total"] or 0,
                "collected_count": collected["count"] or 0,
                "pending_count": pending,
            }
        )

    @action(detail=False, methods=["get"], url_path="itr_summary")
    def itr_summary(self, request: DRFRequest) -> Response:
        user = cast(User, request.user)
        if isinstance(user, AnonymousUser):
            return Response(
                {
                    "fy": "",
                    "total_rent": 0,
                    "record_count": 0,
                }
            )

        today = timezone.now().date()
        fy_start_year = today.year if today.month >= 4 else today.year - 1
        fy_start = datetime(fy_start_year, 4, 1).date()
        fy_end = datetime(fy_start_year + 1, 3, 31).date()

        rent_records = RentRecord.objects.filter(
            unit__owner=user,
            created_at__date__gte=fy_start,
            created_at__date__lte=fy_end,
            payout_status="SUCCESS",
        )

        totals = rent_records.aggregate(total=Sum("amount_paid"), count=Count("id"))

        return Response(
            {
                "fy": f"{fy_start.year}-{fy_end.year}",
                "total_rent": totals["total"] or 0,
                "record_count": totals["count"] or 0,
            }
        )

    @action(detail=False, methods=["post"], url_path="send_itr_summary")
    def send_itr_summary(self, request: DRFRequest) -> Response:
        user = cast(User, request.user)
        if isinstance(user, AnonymousUser):
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            from notification.services.itr_notify_service import notify_itr_summary

            notify_itr_summary(user)
        except Exception:
            logger.exception(
                "Failed to send ITR summary notification for user %s", user.id
            )
            return Response(
                {"error": "Failed to send ITR summary."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({"message": "ITR summary sent successfully."})

    @action(detail=False, methods=["get"], url_path="download_itr_summary")
    def download_itr_summary(self, request: DRFRequest) -> FileResponse:
        user = cast(User, request.user)
        if isinstance(user, AnonymousUser):
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        today = timezone.now().date()
        fy_start_year = today.year if today.month >= 4 else today.year - 1
        fy_start = date(fy_start_year, 4, 1)
        fy_end = date(fy_start_year + 1, 3, 31)

        try:
            from properties.services.itr_pdf_service import generate_itr_summary_pdf

            pdf_bytes = generate_itr_summary_pdf(user, fy_start, fy_end)
        except Exception:
            logger.exception("Failed to generate ITR summary PDF for user %s", user.id)
            return Response(
                {"error": "Failed to generate ITR summary PDF."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response = FileResponse(
            BytesIO(pdf_bytes),
            content_type="application/pdf",
        )
        response["Content-Disposition"] = (
            f"attachment; filename=ITR_Summary_{fy_start_year}-{fy_start_year + 1}.pdf"
        )
        return response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def retry_payout_api(request: DRFRequest, rent_id: int) -> Any:
    rent = get_object_or_404(RentRecord, id=rent_id, renter__unit__owner=request.user)

    if rent.payment_status != "PAID" or rent.payout_status != "FAILED":
        return Response({"error": "Payout not retryable"}, status=400)

    try:
        process_rent_payout(rent)
        rent.refresh_from_db()
        if rent.payout_status == "SUCCESS":
            send_payout_notification(rent)
        return Response(
            {"message": "Payout retry attempted", "status": rent.payout_status}
        )
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def owner_rent_records(request: DRFRequest) -> Any:
    owner = cast(User, request.user)
    rents = (
        RentRecord.objects.filter(unit__owner=owner)
        .select_related("renter", "unit")
        .prefetch_related("parts")
    )
    serializer = RentRecordSerializer(rents, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_rent_invoice(request: DRFRequest, rent_id: int) -> Any:
    user = cast(User, request.user)
    renter = Renter.objects.filter(user=user).first()

    if renter:
        rent = get_object_or_404(RentRecord, id=rent_id, renter=renter)
    else:
        rent = get_object_or_404(RentRecord, id=rent_id, unit__owner=user)

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
