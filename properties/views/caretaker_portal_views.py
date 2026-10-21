"""The caretaker facing part of the portal.

A caretaker works for one owner and looks after the buildings and the
standalone units the owner assigned to them. Everything the caretaker does
on the ground lives behind these endpoints:

* the work of today,
* the properties in the scope of the caretaker,
* the maintenance requests of those properties,
* the tenants of those properties.

The caretaker never sees the owner financials, never edits a rent and never
signs an agreement — the owner keeps those. A caretaker only sees what is
assigned to them.
"""

from __future__ import annotations

from typing import Any, cast

from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from django.contrib.auth.models import AnonymousUser
from django.db.models import Count, Q
from django.utils import timezone

from core.models import User

from ..models import Building, CareTaker, MaintenanceRequest, Renter, Unit
from ..serializers.caretaker_portal_serializers import (
    CareTakerAssignmentSummarySerializer,
    CareTakerBuildingSerializer,
    CareTakerMaintenanceSerializer,
    CareTakerMaintenanceUpdateSerializer,
    CareTakerTenantSerializer,
    CareTakerUnitSerializer,
)
from ..services.caretaker_scope import assigned_building_ids, assigned_unit_ids

OPEN_STATUSES = (
    MaintenanceRequest.Status.OPEN,
    MaintenanceRequest.Status.IN_PROGRESS,
    MaintenanceRequest.Status.WAITING,
)
CLOSED_STATUSES = (
    MaintenanceRequest.Status.RESOLVED,
    MaintenanceRequest.Status.CLOSED,
)
PRIORITY_ORDER = {"urgent": 0, "high": 1, "medium": 2, "low": 3}


def _current_caretaker(request: Request) -> CareTaker | None:
    """Return the caretaker record of the authenticated user, when there is one."""
    user = cast(User, request.user)
    if isinstance(user, AnonymousUser):
        return None
    return (
        CareTaker.objects.select_related("owner")
        .filter(user=user, is_active=True)
        .first()
    )


def _require_caretaker(request: Request) -> CareTaker:
    """Return the caretaker record or refuse the request."""
    caretaker = _current_caretaker(request)
    if caretaker is None:
        raise NotFound("No caretaker profile is linked to this account.")
    return caretaker


def _scope(caretaker: CareTaker) -> tuple[set[int], set[int]]:
    """Return the building ids and the unit ids in the scope of the caretaker."""
    return assigned_building_ids(caretaker), assigned_unit_ids(caretaker)


def _maintenance_scope(caretaker: CareTaker) -> Any:
    """Return the maintenance requests of the assigned properties."""
    _building_ids, unit_ids = _scope(caretaker)
    return MaintenanceRequest.objects.filter(
        Q(unit_id__in=unit_ids) | Q(assigned_caretaker=caretaker)
    ).select_related("unit", "unit__building", "renter", "assigned_caretaker")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def caretaker_today(request: Request) -> Response:
    """Return the work of the day of the caretaker."""
    caretaker = _require_caretaker(request)
    building_ids, unit_ids = _scope(caretaker)
    requests_qs = _maintenance_scope(caretaker)

    counts = {
        "buildings": len(building_ids),
        "units": len(unit_ids),
        "tenants": Renter.objects.filter(unit_id__in=unit_ids).count(),
        "open": requests_qs.filter(status=MaintenanceRequest.Status.OPEN).count(),
        "in_progress": requests_qs.filter(
            status=MaintenanceRequest.Status.IN_PROGRESS
        ).count(),
        "waiting": requests_qs.filter(status=MaintenanceRequest.Status.WAITING).count(),
        "closed": requests_qs.filter(status__in=CLOSED_STATUSES).count(),
        "urgent": requests_qs.filter(
            status__in=OPEN_STATUSES, priority=MaintenanceRequest.Priority.URGENT
        ).count(),
    }

    todo = list(requests_qs.filter(status__in=OPEN_STATUSES).order_by("reported_at"))
    todo.sort(key=lambda item: (PRIORITY_ORDER.get(item.priority, 9), item.reported_at))

    serializer = CareTakerMaintenanceSerializer(
        todo[:10], many=True, context={"request": request}
    )
    assignments = caretaker.assignments.filter(is_active=True).select_related(
        "building", "unit"
    )
    return Response(
        {
            "data": {
                "date": timezone.localdate().isoformat(),
                "caretaker": {
                    "id": caretaker.id,
                    "name": caretaker.name,
                    "owner": getattr(caretaker.owner, "full_name", "")
                    or getattr(caretaker.owner, "username", ""),
                },
                "counts": counts,
                "assignments": CareTakerAssignmentSummarySerializer(
                    assignments, many=True
                ).data,
                "todo": serializer.data,
            }
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def caretaker_properties(request: Request) -> Response:
    """Return the buildings and the units the caretaker looks after."""
    caretaker = _require_caretaker(request)
    building_ids, unit_ids = _scope(caretaker)

    buildings = (
        Building.objects.filter(id__in=building_ids, is_archived=False)
        .annotate(
            unit_count=Count("units", distinct=True),
            open_requests=Count(
                "units__maintenance_requests",
                filter=Q(units__maintenance_requests__status__in=OPEN_STATUSES),
                distinct=True,
            ),
        )
        .order_by("name")
    )
    tenant_counts = dict(
        Renter.objects.filter(unit__building_id__in=building_ids)
        .values_list("unit__building_id")
        .annotate(total=Count("id"))
    )
    building_data = CareTakerBuildingSerializer(
        buildings,
        many=True,
        context={"request": request},
    )
    for item, building in zip(building_data.data, buildings, strict=False):
        item["tenant_count"] = tenant_counts.get(building.id, 0)

    units = (
        Unit.objects.filter(id__in=unit_ids, is_archived=False)
        .select_related("building")
        .annotate(
            open_requests=Count(
                "maintenance_requests",
                filter=Q(maintenance_requests__status__in=OPEN_STATUSES),
                distinct=True,
            )
        )
        .order_by("building__name", "unit")
    )
    tenant_by_unit = {
        renter.unit_id: renter
        for renter in Renter.objects.filter(
            unit_id__in=unit_ids, status__in=("active", "notice_period")
        ).select_related("unit")
    }
    unit_data = CareTakerUnitSerializer(units, many=True, context={"request": request})
    for item, unit in zip(unit_data.data, units, strict=False):
        renter = tenant_by_unit.get(unit.id)
        item["tenant_name"] = getattr(renter, "name", None)

    return Response(
        {
            "data": {
                "buildings": building_data.data,
                "units": unit_data.data,
            }
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def caretaker_maintenance(request: Request) -> Response:
    """Return the maintenance requests of the assigned properties."""
    caretaker = _require_caretaker(request)
    requests_qs = _maintenance_scope(caretaker)

    status_filter = request.query_params.get("status", "").strip()
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)
    priority_filter = request.query_params.get("priority", "").strip()
    if priority_filter:
        requests_qs = requests_qs.filter(priority=priority_filter)
    unit_id = request.query_params.get("unit", "").strip()
    if unit_id:
        requests_qs = requests_qs.filter(unit_id=unit_id)

    serializer = CareTakerMaintenanceSerializer(
        requests_qs, many=True, context={"request": request}
    )
    return Response({"data": serializer.data})


@api_view(["GET", "PATCH", "POST"])
@permission_classes([IsAuthenticated])
def caretaker_maintenance_detail(request: Request, pk: int) -> Response:
    """Read one maintenance request and move it forward.

    The caretaker may take a job, put it on hold or close it. That is the
    only change the caretaker may make.
    """
    caretaker = _require_caretaker(request)
    maintenance = _maintenance_scope(caretaker).filter(pk=pk).first()
    if maintenance is None:
        raise NotFound("That maintenance request is not in your scope.")

    if request.method == "GET":
        serializer = CareTakerMaintenanceSerializer(
            maintenance, context={"request": request}
        )
        return Response({"data": serializer.data})

    payload = CareTakerMaintenanceUpdateSerializer(data=request.data)
    payload.is_valid(raise_exception=True)
    data = payload.validated_data

    new_status = data.get("status")
    if new_status is not None:
        maintenance.status = new_status
        if new_status in CLOSED_STATUSES and maintenance.resolved_at is None:
            maintenance.resolved_at = timezone.now()
        elif new_status in OPEN_STATUSES:
            maintenance.resolved_at = None

    if "notes" in data and data["notes"]:
        existing_notes = maintenance.description or ""
        stamp = timezone.localtime().strftime("%d %b %Y, %H:%M")
        maintenance.description = f"{existing_notes}\n[{stamp}] {data['notes']}".strip()

    if "assigned_caretaker" in data:
        requested = data["assigned_caretaker"]
        if requested is not None and int(requested) != caretaker.id:
            raise ValidationError("You can only take the job yourself.")
        maintenance.assigned_caretaker = caretaker

    if maintenance.assigned_caretaker_id is None:
        maintenance.assigned_caretaker = caretaker

    maintenance.save(
        update_fields=[
            "status",
            "resolved_at",
            "description",
            "assigned_caretaker",
            "updated_at",
        ]
    )
    serializer = CareTakerMaintenanceSerializer(
        maintenance, context={"request": request}
    )
    return Response({"data": serializer.data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def caretaker_tenants(request: Request) -> Response:
    """Return the tenants of the assigned properties."""
    caretaker = _require_caretaker(request)
    _building_ids, unit_ids = _scope(caretaker)

    renters = (
        Renter.objects.filter(unit_id__in=unit_ids)
        .select_related("unit", "unit__building")
        .order_by("unit__building__name", "unit__unit")
    )
    status_filter = request.query_params.get("status", "").strip()
    if status_filter:
        renters = renters.filter(status=status_filter)

    serializer = CareTakerTenantSerializer(
        renters, many=True, context={"request": request}
    )
    return Response({"data": serializer.data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def caretaker_dashboard(request: Request) -> Response:
    """Return the small summary shown on the caretaker home screen."""
    caretaker = _require_caretaker(request)
    building_ids, unit_ids = _scope(caretaker)
    requests_qs = _maintenance_scope(caretaker)
    return Response(
        {
            "data": {
                "name": caretaker.name,
                "owner": getattr(caretaker.owner, "full_name", "")
                or getattr(caretaker.owner, "username", ""),
                "properties": len(building_ids) + len(unit_ids),
                "buildings": len(building_ids),
                "units": len(unit_ids),
                "tenants": Renter.objects.filter(unit_id__in=unit_ids).count(),
                "open_requests": requests_qs.filter(status__in=OPEN_STATUSES).count(),
            }
        }
    )
