from django.core.cache import cache
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from notification.services.rent_notify_service import send_payout_notification
from notification.utils import send_whatsapp_message
from rentsecure_be.services.cashfree_service import process_rent_payout
from rentsecure_be.services.razorpay_service import create_payment_link

from ..feature_enforcer import FeatureEnforcer
from ..models import Renter, RentRecord
from ..serializers import RentRecordSerializer
from ..utils import generate_rent_invoice_pdf


class RentRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RentRecordSerializer

    def get_queryset(self):
        user = self.request.user
        cache_key = f'rent_records_user_{user.id}'
        rent_records = cache.get(cache_key)
        if rent_records is None:
            rent_records = RentRecord.objects.filter(unit__owner=user).select_related('unit', 'renter')
            cache.set(cache_key, rent_records, timeout=300)
        return rent_records

    def perform_create(self, serializer):
        unit = serializer.validated_data.get('unit')
        renter = serializer.validated_data.get('renter')
        user = self.request.user

        if unit.owner != user:
            raise PermissionDenied("You do not own this unit.")
        if renter.unit != unit:
            raise ValidationError("Renter does not belong to the selected unit.")
        if RentRecord.objects.filter(renter=renter, rent_month=serializer.validated_data.get('rent_month')).exists():
            raise ValidationError("Rent record for this month already exists.")

        enforcer = FeatureEnforcer(user)
        if not enforcer.can_create("rent_records"):
            raise PermissionDenied("You have reached your rent record creation limit.")

        rent = serializer.save(owner=user)

        try:
            link = create_payment_link(rent)
            rent.payment_link = link
            rent.save(update_fields=['payment_link'])
            send_whatsapp_message(rent.renter.phone, f"📩 Pay your rent: {link}")
        except Exception:
            pass

        enforcer.increment("rent_records")
        cache.delete(f'rent_records_user_{user.id}')

    def perform_update(self, serializer):
        instance = serializer.instance
        user = self.request.user

        if instance.unit.owner != user:
            raise PermissionDenied("You do not own this unit.")

        new_unit = serializer.validated_data.get('unit', instance.unit)
        new_renter = serializer.validated_data.get('renter', instance.renter)

        if new_unit.owner != user:
            raise PermissionDenied("You do not own the selected unit.")
        if new_renter.unit != new_unit:
            raise ValidationError("Renter does not belong to the selected unit.")

        serializer.save()
        cache.delete(f'rent_records_user_{user.id}')

    def perform_destroy(self, instance):
        if instance.unit.owner != self.request.user:
            raise PermissionDenied("You do not own this rent record.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement('rent_records')
        cache.delete(f'rent_records_user_{self.request.user.id}')


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def retry_payout_api(request, rent_id):
    rent = get_object_or_404(RentRecord, id=rent_id, owner=request.user)

    if rent.payment_status != "PAID" or rent.payout_status != "FAILED":
        return Response({"error": "Payout not retryable"}, status=400)

    try:
        response = process_rent_payout(rent)
        rent.refresh_from_db()
        if rent.payout_status == "SUCCESS":
            send_payout_notification(rent)
        return Response({
            "message": "Payout retry attempted",
            "status": rent.payout_status
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def owner_rent_records(request):
    owner = request.user
    rents = RentRecord.objects.filter(owner=owner).select_related('renter', 'unit')
    serializer = RentRecordSerializer(rents, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_rent_invoice(request, rent_id):
    rent = get_object_or_404(RentRecord, id=rent_id, owner=request.user)
    pdf_path = generate_rent_invoice_pdf(rent)
    return FileResponse(open(pdf_path, "rb"), content_type="application/pdf")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_latest_due_rent(request):
    renter = Renter.objects.filter(user=request.user, status__in=["active", "notice_period"]).first()

    if not renter:
        return Response({"error": "Not a renter"}, status=403)

    rent = RentRecord.objects.filter(renter=renter, payment_status="PENDING").order_by("-rent_due_date").first()
    if not rent:
        return Response({"message": "No pending rent"})

    return Response({
        "amount": rent.amount,
        "month": rent.month,
        "year": rent.year,
        "property": renter.property.name,
        "payment_link": rent.payment_link,
        "due_date": rent.due_date,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def rent_history(request):
    renter = Renter.objects.filter(user=request.user, status__in=["active", "notice_period"]).first()
    if not renter:
        return Response({"error": "Not a renter"}, status=403)

    rents = RentRecord.objects.filter(renter=renter).order_by("-rent_due_date")
    data = [{
        "month": r.month,
        "year": r.year,
        "amount": r.amount,
        "status": r.payment_status,
        "invoice_url": r.invoice_pdf.url if r.invoice_pdf else None,
        "payment_link": r.payment_link,
    } for r in rents]
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def owner_rent_overview(request):
    owner = request.user
    rents = RentRecord.objects.filter(owner=owner).select_related("renter", "unit")
    data = []
    for r in rents:
        data.append({
            "tenant": r.renter.name,
            "unit": r.renter.property.name,
            "amount": r.amount,
            "month": r.month,
            "year": r.year,
            "status": r.payment_status,
            "payout": r.payout_status,
            "invoice_url": r.invoice_pdf.url if r.invoice_pdf else None
        })
    return Response(data)
