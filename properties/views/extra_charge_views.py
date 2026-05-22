from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from ..models import ExtraCharge
from ..serializers import ExtraChargeSerializer


class ExtraChargeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ExtraChargeSerializer

    def get_queryset(self):
        user = self.request.user
        renter_profile = getattr(user, 'renter_profile', None)

        if renter_profile:
            return ExtraCharge.objects.filter(renter=renter_profile).select_related('renter', 'unit')

        return ExtraCharge.objects.filter(unit__owner=user).select_related('renter', 'unit')

    def perform_create(self, serializer):
        unit = serializer.validated_data['unit']
        renter = serializer.validated_data['renter']

        if unit.owner != self.request.user:
            raise ValidationError('You do not own this unit.')
        if renter.unit != unit:
            raise ValidationError('Renter does not belong to the selected unit.')

        serializer.save()
