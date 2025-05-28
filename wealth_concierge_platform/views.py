from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import ( RentAgreementDraft, UnitImage, UnitDocument, Unit, 
                     Caretaker, Renter, RentRecord, Building )
from .serializers import ( RentAgreementDraftSerializer, UnitImageSerializer, 
                          UnitDocumentSerializer, UnitSerializer, CaretakerSerializer, RenterSerializer, 
                          RentRecordSerializer, BuildingSerializer )
from django.core.cache import cache
from .feature_enforcer import FeatureEnforcer

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
            # Free plan active, show only allowed active buildings
            free_limit = enforcer.get_free_plan_limit('max_buildings')
            return buildings.filter(is_archived=False)[:free_limit]

        return buildings

    
    def perform_create(self, serializer):
        user = self.request.user
        enforcer = FeatureEnforcer(user)

        current_buildings = Building.objects.filter(owner=user).count()
        try:
            enforcer.check_limit('max_buildings', current_buildings)
        except ValidationError as e:
            raise ValidationError({"detail": str(e)})

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
            free_limit = enforcer.get_free_plan_limit('max_units')  # Assuming this is correct key
            return units.filter(is_archived=False)[:free_limit]

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
            renters = Renter.objects.filter(unit__owner=self.request.user)
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

        # OPTIONAL: enforce if limit exists
        enforcer = FeatureEnforcer(user)
        if not enforcer.can_create("rent_records"):
            raise PermissionDenied("You have reached your rent record creation limit.")
        serializer.save()
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
