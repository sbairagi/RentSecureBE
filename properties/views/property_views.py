from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from notification.utils import send_whatsapp_message

from ..models import Building, Renter, RentRecord
from ..serializers import RenterRentRecordSerializer
from ..services.unit_service import get_owner_analytics, update_unit_status


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_rent_records(request):
    renter = Renter.objects.filter(
        user=request.user, status__in=["active", "notice_period"]
    ).first()
    rents = RentRecord.objects.filter(renter=renter).order_by("-due_date")
    return Response(RenterRentRecordSerializer(rents, many=True).data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_late_fee_policy(request, property_id):
    prop = RentRecord.objects.get(id=property_id, owner=request.user)
    prop.grace_days = request.data.get("grace_days", prop.grace_days)
    prop.late_fee = request.data.get("late_fee_amount", prop.late_fee)
    prop.save(update_fields=["grace_days", "late_fee"])
    return Response({"msg": "Updated"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def revoke_rent_agreement(request, renter_id):
    renter = get_object_or_404(Renter, id=renter_id, unit__owner=request.user)
    renter.is_agreement_revoked = True
    renter.revoked_by_owner = True
    renter.revoked_on = timezone.now()
    renter.revocation_reason = request.data.get("reason", "Manually revoked by owner")
    if hasattr(renter, "active_agreement"):
        renter.active_agreement = None
    renter.save()

    # Auto-update unit status (unit should revert to vacant if renter is revoked)
    update_unit_status(renter.unit)

    send_whatsapp_message(
        renter.phone,
        (
            "⚠️ Your rent agreement has been revoked by the owner. "
            f"Reason: {renter.revocation_reason}"
        ),
    )

    return Response({"success": True, "message": "Agreement revoked successfully"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def unit_analytics(request):
    """
    Get comprehensive unit occupancy analytics for all buildings.

    Returns aggregated and per-building metrics including:
    - Total units, occupied, and vacant counts
    - Occupancy rates (percentage)
    - Per-building breakdown

    Query Parameters:
        - building_id (optional): Filter to specific building

    Returns:
        dict: Analytics with total, vacant, occupied counts and rates
    """
    user = request.user
    building_id = request.query_params.get("building_id")

    if building_id:
        # Get analytics for specific building
        building = Building.objects.get(id=building_id, owner=user)
        from ..services.unit_service import get_building_analytics

        analytics = get_building_analytics(building)
        return Response({"data": analytics})

    # Get analytics for all buildings
    analytics = get_owner_analytics(user)
    return Response(analytics)
