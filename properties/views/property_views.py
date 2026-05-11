from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from ..models import Renter, RentRecord, Building, Unit
from ..serializers import RenterRentRecordSerializer
from notification.utils import send_whatsapp_message


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_rent_records(request):
    renter = Renter.objects.filter(user=request.user, status__in=["active", "notice_period"]).first()
    rents = RentRecord.objects.filter(renter=renter).order_by('-due_date')
    return Response(RenterRentRecordSerializer(rents, many=True).data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_late_fee_policy(request, property_id):
    prop = RentRecord.objects.get(id=property_id, owner=request.user)
    prop.grace_days = request.data.get('grace_days', prop.grace_days)
    prop.late_fee = request.data.get('late_fee_amount', prop.late_fee)
    prop.save(update_fields=['grace_days', 'late_fee'])
    return Response({"msg": "Updated"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_rent_agreement(request, renter_id):
    renter = get_object_or_404(Renter, id=renter_id, unit__owner=request.user)
    renter.is_agreement_revoked = True
    renter.revoked_by_owner = True
    renter.revoked_on = timezone.now()
    renter.revocation_reason = request.data.get("reason", "Manually revoked by owner")
    if hasattr(renter, 'active_agreement'):
        renter.active_agreement = None
    renter.save()

    send_whatsapp_message(
        renter.phone,
        f"⚠️ Your rent agreement has been revoked by the owner. Reason: {renter.revocation_reason}"
    )

    return Response({"success": True, "message": "Agreement revoked successfully"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def unit_analytics(request):
    user = request.user
    buildings = Building.objects.filter(owner=user)
    response = []
    for building in buildings:
        total_units = Unit.objects.filter(building=building).count()
        vacant_units = Unit.objects.filter(building=building, status="vacant").count()
        occupied_units = total_units - vacant_units
        response.append({
            "building": building.name,
            "total": total_units,
            "vacant": vacant_units,
            "occupied": occupied_units,
        })
    return Response(response)
