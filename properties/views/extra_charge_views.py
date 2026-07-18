from typing import Any

from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import BaseSerializer

from django.contrib.auth.models import AnonymousUser

from shared.type_compat import override

from ..models import ExtraCharge
from ..serializers import ExtraChargeSerializer


class ExtraChargeViewSet(viewsets.ModelViewSet[ExtraCharge]):
    permission_classes = [IsAuthenticated]
    serializer_class = ExtraChargeSerializer

    @override
    def get_queryset(self) -> Any:
        user = self.request.user
        if isinstance(user, AnonymousUser):
            return ExtraCharge.objects.none()
        renter_profile = getattr(user, "renter_profile", None)

        if renter_profile:
            return ExtraCharge.objects.filter(renter=renter_profile).select_related(
                "renter", "unit"
            )

        return ExtraCharge.objects.filter(unit__owner=user).select_related(
            "renter", "unit"
        )

    @override
    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        unit = serializer.validated_data["unit"]
        renter = serializer.validated_data["renter"]

        if unit.owner != self.request.user:
            raise ValidationError("You do not own this unit.")
        if renter.unit != unit:
            raise ValidationError("Renter does not belong to the selected unit.")

        serializer.save()
