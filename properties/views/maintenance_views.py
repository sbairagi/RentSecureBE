from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth.models import AnonymousUser
from django.db.models import Q, QuerySet
from django.utils import timezone

from properties.models import MaintenanceRequest
from properties.serializers import MaintenanceRequestSerializer
from rentsecure_be.type_compat import override


class MaintenanceRequestViewSet(viewsets.ModelViewSet[MaintenanceRequest]):
    """Authenticated CRUD for maintenance requests belonging to the owner."""

    permission_classes = [IsAuthenticated]
    serializer_class = MaintenanceRequestSerializer

    @override
    def get_queryset(self) -> QuerySet[MaintenanceRequest]:
        if isinstance(self.request.user, AnonymousUser):
            return MaintenanceRequest.objects.none()
        queryset = MaintenanceRequest.objects.filter(
            owner=self.request.user
        ).select_related("unit", "unit__building", "renter", "assigned_caretaker")
        status_value = self.request.query_params.get("status")
        priority = self.request.query_params.get("priority")
        category = self.request.query_params.get("category")
        building = self.request.query_params.get("building")
        unit = self.request.query_params.get("unit")
        search = self.request.query_params.get("search")
        ordering = self.request.query_params.get("ordering", "-reported_at")
        if status_value:
            queryset = queryset.filter(status=status_value)
        if priority:
            queryset = queryset.filter(priority=priority)
        if category:
            queryset = queryset.filter(category=category)
        if building:
            queryset = queryset.filter(unit__building_id=building)
        if unit:
            queryset = queryset.filter(unit_id=unit)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(unit__unit__icontains=search)
                | Q(renter__name__icontains=search)
            )
        allowed_orderings = {
            "reported_at",
            "-reported_at",
            "priority",
            "status",
            "title",
        }
        return queryset.order_by(
            ordering if ordering in allowed_orderings else "-reported_at"
        )

    @override
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @override
    def perform_update(self, serializer):
        instance = serializer.instance
        if instance is None or instance.owner_id != self.request.user.id:
            raise PermissionDenied("You do not own this maintenance request.")
        next_status = serializer.validated_data.get("status", instance.status)
        if next_status in {
            MaintenanceRequest.Status.RESOLVED,
            MaintenanceRequest.Status.CLOSED,
        }:
            serializer.save(resolved_at=instance.resolved_at or timezone.now())
        elif instance.resolved_at:
            serializer.save(resolved_at=None)
        else:
            serializer.save()

    @override
    def perform_destroy(self, instance):
        if instance.owner_id != self.request.user.id:
            raise PermissionDenied("You do not own this maintenance request.")
        instance.delete()
