from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated

from notification.services.rent_notify_service import send_payout_notification

from .feature_enforcer import FeatureEnforcer
from .models import (
    Building,
    Caretaker,
    RentAgreementDraft,
    Renter,
    RentRecord,
    Unit,
    UnitDocument,
    UnitImage,
)
from .serializers import (
    BuildingSerializer,
    CaretakerSerializer,
    RentAgreementDraftSerializer,
    RenterSerializer,
    RentRecordSerializer,
    UnitDocumentSerializer,
    UnitImageSerializer,
    UnitSerializer,
)


class BuildingViewSet(viewsets.ModelViewSet):
    serializer_class = BuildingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        cache_key = f"buildings_user_{user.id}"
        enforcer = FeatureEnforcer(user)

        buildings = cache.get(cache_key)
        if buildings is None:
            buildings = Building.objects.filter(owner=user)
            cache.set(cache_key, buildings, timeout=300)

        if enforcer.is_expired() and enforcer.is_past_grace_period():
            free_limit = enforcer.get_free_plan_limit('max_buildings')
            active_buildings = buildings.filter(is_archived=False)
            if free_limit == 'unlimited':
                return active_buildings
            return active_buildings[:free_limit]

        return buildings


    def perform_create(self, serializer):
        user = self.request.user
        enforcer = FeatureEnforcer(user)

        if not enforcer.can_create('max_buildings'):
            raise PermissionDenied("Building creation limit reached for your plan.")

        serializer.save(owner=user)
        enforcer.increment('max_buildings')
        cache.delete(f"buildings_user_{user.id}")

    def perform_update(self, serializer):
        if serializer.instance.owner != self.request.user:
            raise PermissionDenied("You do not have permission to update this building.")
        serializer.save()
        cache.delete(f"buildings_user_{self.request.user.id}")

    def perform_destroy(self, instance):
        if instance.owner != self.request.user:
            raise PermissionDenied("You do not have permission to delete this building.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement('max_buildings')
        cache.delete(f"buildings_user_{self.request.user.id}")

class UnitViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        cache_key = f'units_user_{user.id}'
        enforcer = FeatureEnforcer(user)

        units = cache.get(cache_key)
        if units is None:
            units = Unit.objects.filter(owner=user)
            cache.set(cache_key, units, timeout=300)

        if enforcer.is_expired() and enforcer.is_past_grace_period():
            free_limit = enforcer.get_free_plan_limit('max_units')
            active_units = units.filter(is_archived=False)
            if free_limit == 'unlimited':
                return active_units
            return active_units[:free_limit]

        return units


    def perform_create(self, serializer):
        enforcer = FeatureEnforcer(self.request.user)
        if not enforcer.can_create('max_units'):
            raise PermissionDenied("Unit creation limit reached for your plan.")

        serializer.save(owner=self.request.user)
        enforcer.increment('max_units')
        cache.delete(f'units_user_{self.request.user.id}')

    def perform_update(self, serializer):
        if serializer.instance.owner != self.request.user:
            raise PermissionDenied("You do not have permission to update this unit.")
        serializer.save()
        cache.delete(f'units_user_{self.request.user.id}')

    def perform_destroy(self, instance):
        if instance.owner != self.request.user:
            raise PermissionDenied("You do not have permission to delete this unit.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement('max_units')
        cache.delete(f'units_user_{self.request.user.id}')

class CaretakerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CaretakerSerializer

    def get_queryset(self):
        cache_key = f'caretakers_user_{self.request.user.id}'
        caretakers = cache.get(cache_key)
        if caretakers is None:
            caretakers = Caretaker.objects.filter(unit__owner=self.request.user)
            cache.set(cache_key, caretakers, timeout=300)
        return caretakers

    def perform_create(self, serializer):
        unit = serializer.validated_data.get('unit')
        if not unit or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")

        enforcer = FeatureEnforcer(self.request.user)
        if not enforcer.can_create('max_caretakers'):
            raise PermissionDenied("Caretaker limit reached for your plan.")

        serializer.save()
        enforcer.increment('max_caretakers')
        cache.delete(f'caretakers_user_{self.request.user.id}')


    def perform_update(self, serializer):
        unit = serializer.validated_data.get('unit') or serializer.instance.unit
        if unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        serializer.save()
        cache.delete(f'caretakers_user_{self.request.user.id}')

    def perform_destroy(self, instance):
        if instance.unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement('max_caretakers')
        cache.delete(f'caretakers_user_{self.request.user.id}')

class RenterViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RenterSerializer

    def get_queryset(self):
        cache_key = f'renters_user_{self.request.user.id}'
        renters = cache.get(cache_key)
        if renters is None:
            renters = Renter.objects.filter(unit__owner=self.request.user, status__in=["active", "notice_period"])
            cache.set(cache_key, renters, timeout=300)
        return renters

    def perform_create(self, serializer):
        unit = serializer.validated_data.get('unit')
        if not unit or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")

        enforcer = FeatureEnforcer(self.request.user)
        if not enforcer.can_create('max_renters'):
            raise PermissionDenied("Renter limit reached for your plan.")

        serializer.save()
        enforcer.increment('max_renters')
        cache.delete(f'renters_user_{self.request.user.id}')


    def perform_update(self, serializer):
        unit = serializer.validated_data.get('unit') or serializer.instance.unit
        if unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        serializer.save()
        cache.delete(f'renters_user_{self.request.user.id}')

    def perform_destroy(self, instance):
        if instance.unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement('max_renters')
        cache.delete(f'renters_user_{self.request.user.id}')

from notification.utils import send_whatsapp_message
from rentsecure_be.services.razorpay_service import create_payment_link


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
            # Keep the rent record if payment link generation fails, but do not block the resource creation.
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


class UnitImageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UnitImageSerializer

    def get_queryset(self):
        cache_key = f'unit_images_user_{self.request.user.id}'
        images = cache.get(cache_key)
        if images is None:
            images = UnitImage.objects.filter(unit__owner=self.request.user)
            cache.set(cache_key, images, timeout=300)
        return images

    def perform_create(self, serializer):
        unit = serializer.validated_data.get('unit')
        if not unit or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")

        enforcer = FeatureEnforcer(self.request.user)
        if not enforcer.can_create("unit_images"):
            raise PermissionDenied("You have reached your image upload limit.")

        serializer.save()
        enforcer.increment("unit_images")
        cache.delete(f'unit_images_user_{self.request.user.id}')


    def perform_update(self, serializer):
        unit = serializer.validated_data.get('unit') or serializer.instance.unit
        if unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        serializer.save()
        cache.delete(f'unit_images_user_{self.request.user.id}')

    def perform_destroy(self, instance):
        if instance.unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement('unit_images')
        cache.delete(f'unit_images_user_{self.request.user.id}')


class UnitDocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UnitDocumentSerializer

    def get_queryset(self):
        cache_key = f'unit_docs_user_{self.request.user.id}'
        docs = cache.get(cache_key)
        if docs is None:
            docs = UnitDocument.objects.filter(unit__owner=self.request.user)
            cache.set(cache_key, docs, timeout=300)
        return docs

    def perform_create(self, serializer):
        unit = serializer.validated_data.get('unit')
        if not unit or unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")

        enforcer = FeatureEnforcer(self.request.user)
        if not enforcer.can_create("unit_documents"):
            raise PermissionDenied("You have reached your document upload limit.")

        serializer.save()
        enforcer.increment("unit_documents")
        cache.delete(f'unit_docs_user_{self.request.user.id}')


    def perform_update(self, serializer):
        unit = serializer.validated_data.get('unit') or serializer.instance.unit
        if unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        serializer.save()
        cache.delete(f'unit_docs_user_{self.request.user.id}')

    def perform_destroy(self, instance):
        if instance.unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement('unit_documents')
        cache.delete(f'unit_docs_user_{self.request.user.id}')


class RentAgreementDraftViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RentAgreementDraftSerializer

    def get_queryset(self):
        cache_key = f'rent_drafts_user_{self.request.user.id}'
        drafts = cache.get(cache_key)
        if drafts is None:
            drafts = RentAgreementDraft.objects.filter(user=self.request.user)
            cache.set(cache_key, drafts, timeout=300)
        return drafts

    def perform_create(self, serializer):
        enforcer = FeatureEnforcer(self.request.user)

        renter = serializer.validated_data.get('renter')
        unit = serializer.validated_data.get('unit')

        if not enforcer.can_create("rent_agreement_drafts"):
            raise PermissionDenied("You have reached your draft creation limit.")

        if unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        if renter.unit != unit:
            raise PermissionDenied("Renter does not belong to this unit.")

        serializer.save(user=self.request.user)
        enforcer.increment("rent_agreement_drafts")
        cache.delete(f'rent_drafts_user_{self.request.user.id}')


    def perform_update(self, serializer):
        instance = serializer.instance
        if instance.user != self.request.user:
            raise PermissionDenied("You do not own this draft.")

        unit = serializer.validated_data.get('unit', instance.unit)
        renter = serializer.validated_data.get('renter', instance.renter)

        if unit.owner != self.request.user:
            raise PermissionDenied("You do not own the selected unit.")
        if renter.unit != unit:
            raise PermissionDenied("Renter does not belong to this unit.")

        serializer.save()
        cache.delete(f'rent_drafts_user_{self.request.user.id}')

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You do not own this draft.")
        enforcer = FeatureEnforcer(self.request.user)
        instance.delete()
        enforcer.decrement('rent_agreement_drafts')
        cache.delete(f'rent_drafts_user_{self.request.user.id}')















# rent/api.py or views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rentsecure_be.services.cashfree_service import process_rent_payout


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def retry_payout_api(request, rent_id):
    rent = RentRecord.objects.get(id=rent_id, owner=request.user)

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


# Optional Owner Notification

# After successful retry:

#if rent.payout_status == "SUCCESS":
    # send_whatsapp_message(
    #     owner.profile.whatsapp_number,
    #     f"✅ Your payout for ₹{rent.amount} has been successfully retried and credited."
    # )

# {% if rent.payment_status == 'PAID' and rent.payout_status == 'FAILED' %}
# <form method="POST" action="{% url 'retry_payout_api' rent.id %}">
#   {% csrf_token %}
#   <button type="submit">🔁 Retry Payout</button>
# </form>
# {% endif %}



# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from properties.models import RentRecord
from properties.serializers import RentRecordSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def owner_rent_records(request):
    owner = request.user
    rents = RentRecord.objects.filter(owner=owner).select_related('renter', 'unit')
    serializer = RentRecordSerializer(rents, many=True)
    return Response(serializer.data)


# views.py
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from properties.utils import generate_rent_invoice_pdf


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_rent_invoice(request, rent_id):
    rent = get_object_or_404(RentRecord, id=rent_id, owner=request.user)
    pdf_path = generate_rent_invoice_pdf(rent)
    return FileResponse(open(pdf_path, "rb"), content_type="application/pdf")



# views.py
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



# views.py
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


# views/renter.py
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
from .serializers import RenterRentRecordSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_rent_records(request):
    renter = request.user.renter_profile
    rents = RentRecord.objects.filter(renter=renter).order_by('-due_date')
    return Response(RenterRentRecordSerializer(rents, many=True).data)



# views/property.py
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_late_fee_policy(request, property_id):
    prop = RentRecord.objects.get(id=property_id, owner=request.user)
    prop.grace_days = request.data.get('grace_days', prop.grace_days)
    prop.late_fee = request.data.get('late_fee_amount', prop.late_fee)
    prop.save(update_fields=['grace_days', 'late_fee'])
    return Response({"msg": "Updated"})


# views/revoke_agreement.py

from django.utils import timezone


@api_view(['POST'])
def revoke_rent_agreement(request, renter_id):
    renter = Renter.objects.get(id=renter_id, unit__owner=request.user)

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


# views.py

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


