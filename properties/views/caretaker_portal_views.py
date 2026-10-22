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

from datetime import date
from typing import Any, cast

from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from django.contrib.auth.models import AnonymousUser
from django.db.models import Count, Max, Q
from django.utils import timezone

from core.models import User

from ..models import (
    Building,
    CareTaker,
    CareTakerActivity,
    MaintenanceRequest,
    Renter,
    Unit,
)
from ..serializers.caretaker_portal_serializers import (
    CareTakerAssignmentSummarySerializer,
    CareTakerBuildingSerializer,
    CareTakerHomeSerializer,
    CareTakerMaintenanceSerializer,
    CareTakerMaintenanceUpdateSerializer,
    CareTakerProfileSerializer,
    CareTakerProfileUpdateSerializer,
    CareTakerTenantSerializer,
    CareTakerUnitSerializer,
)
from ..serializers.caretaker_serializers import CareTakerActivitySerializer
from ..services.caretaker_scope import (
    assigned_building_ids,
    assigned_unit_ids,
    directly_assigned_unit_ids,
)

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


def _record_caretaker_actions(
    *,
    caretaker: CareTaker,
    maintenance: MaintenanceRequest,
    actor: Any,
    previous_status: str,
    previous_caretaker_id: int | None,
    note: str = "",
) -> None:
    """Write the trail of the caretaker — what the owner reads.

    One row per action: taking the job, moving the status and leaving a note.
    A request that changed nothing writes nothing.
    """
    from ..services.caretaker_activity import record_activity

    status_labels = dict(MaintenanceRequest.Status.choices)
    title = maintenance.title
    unit = getattr(maintenance, "unit", None)
    building = getattr(unit, "building", None)
    property_label = " · ".join(
        part
        for part in (
            getattr(building, "name", "") or "",
            getattr(unit, "unit", "") or "",
        )
        if part
    )

    if previous_caretaker_id != caretaker.id:
        record_activity(
            caretaker=caretaker,
            action=CareTakerActivity.Action.TOOK_JOB,
            summary=f"Took the job “{title}”",
            detail=property_label,
            maintenance_request=maintenance,
            actor=actor,
        )

    if maintenance.status != previous_status:
        record_activity(
            caretaker=caretaker,
            action=CareTakerActivity.Action.STATUS_CHANGE,
            summary=(
                f"Moved “{title}” from "
                f"{status_labels.get(previous_status, previous_status or '—')} to "
                f"{status_labels.get(maintenance.status, maintenance.status)}"
            ),
            detail=property_label,
            maintenance_request=maintenance,
            from_status=previous_status,
            to_status=maintenance.status,
            actor=actor,
        )

    if note:
        record_activity(
            caretaker=caretaker,
            action=CareTakerActivity.Action.NOTE,
            summary=f"Left a note on “{title}”",
            detail=note,
            maintenance_request=maintenance,
            from_status=previous_status,
            to_status=maintenance.status,
            actor=actor,
        )


def _previous_month(today: date) -> tuple[int, int]:
    """Return the year and the month before the given day."""
    if today.month == 1:
        return today.year - 1, 12
    return today.year, today.month - 1


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def caretaker_today(request: Request) -> Response:
    """Return the work of the day of the caretaker."""
    caretaker = _require_caretaker(request)
    building_ids, unit_ids = _scope(caretaker)
    requests_qs = _maintenance_scope(caretaker)

    today = timezone.localdate()
    last_year, last_month = _previous_month(today)
    closed = requests_qs.filter(status__in=CLOSED_STATUSES)

    counts = {
        "buildings": len(building_ids),
        "homes": len(unit_ids),
        "units": len(unit_ids),
        "tenants": Renter.objects.filter(
            unit_id__in=unit_ids, status__in=("active", "notice_period")
        ).count(),
        "open": requests_qs.filter(status__in=OPEN_STATUSES).count(),
        "new": requests_qs.filter(status=MaintenanceRequest.Status.OPEN).count(),
        "in_progress": requests_qs.filter(
            status=MaintenanceRequest.Status.IN_PROGRESS
        ).count(),
        "waiting": requests_qs.filter(status=MaintenanceRequest.Status.WAITING).count(),
        "closed": closed.count(),
        "closed_this_month": closed.filter(
            resolved_at__year=today.year, resolved_at__month=today.month
        ).count(),
        "closed_last_month": closed.filter(
            resolved_at__year=last_year, resolved_at__month=last_month
        ).count(),
        "urgent": requests_qs.filter(
            status__in=OPEN_STATUSES, priority=MaintenanceRequest.Priority.URGENT
        ).count(),
    }

    todo = list(requests_qs.filter(status__in=OPEN_STATUSES).order_by("reported_at"))
    todo.sort(key=lambda item: (PRIORITY_ORDER.get(item.priority, 9), item.reported_at))

    serializer = CareTakerMaintenanceSerializer(
        todo[:10],
        many=True,
        context={"request": request, "caretaker_id": caretaker.id},
    )
    assignments = caretaker.assignments.filter(is_active=True).select_related(
        "building", "unit"
    )
    activity = CareTakerActivity.objects.filter(caretaker=caretaker).select_related(
        "maintenance_request",
        "maintenance_request__unit",
        "maintenance_request__unit__building",
    )[:5]
    return Response(
        {
            "data": {
                "date": today.isoformat(),
                "caretaker": {
                    "id": caretaker.id,
                    "name": caretaker.name,
                    "owner": getattr(caretaker.owner, "full_name", "")
                    or getattr(caretaker.owner, "username", ""),
                    "owner_phone": getattr(caretaker.owner, "phone", "") or "",
                    "joining_date": caretaker.joining_date.isoformat(),
                },
                "counts": counts,
                "assignments": CareTakerAssignmentSummarySerializer(
                    assignments, many=True
                ).data,
                "todo": serializer.data,
                "recent_activity": CareTakerActivitySerializer(
                    activity, many=True, context={"request": request}
                ).data,
            }
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def caretaker_properties(request: Request) -> Response:
    """Return the buildings and the units the caretaker looks after.

    The cards of the screen are the properties of the scope — the buildings
    and the standalone homes. The table below them lists every home of the
    scope, including the homes that belong to an assigned building.
    """
    caretaker = _require_caretaker(request)
    building_ids, unit_ids = _scope(caretaker)
    standalone_ids = directly_assigned_unit_ids(caretaker)

    buildings = (
        Building.objects.filter(id__in=building_ids, is_archived=False)
        .select_related("owner")
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
        Renter.objects.filter(
            unit__building_id__in=building_ids,
            status__in=("active", "notice_period"),
        )
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
        Unit.objects.filter(id__in=standalone_ids, is_archived=False)
        .select_related("building", "owner")
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
            unit_id__in=standalone_ids, status__in=("active", "notice_period")
        ).select_related("unit")
    }
    unit_data = CareTakerUnitSerializer(units, many=True, context={"request": request})
    for item, unit in zip(unit_data.data, units, strict=False):
        renter = tenant_by_unit.get(unit.id)
        item["tenant_name"] = getattr(renter, "name", None)
        item["tenant_phone"] = getattr(renter, "phone", None)

    homes = (
        Unit.objects.filter(id__in=unit_ids, is_archived=False)
        .select_related("building")
        .annotate(
            open_requests=Count(
                "maintenance_requests",
                filter=Q(maintenance_requests__status__in=OPEN_STATUSES),
                distinct=True,
            ),
            last_update=Max("maintenance_requests__reported_at"),
        )
        .order_by("building__name", "unit")
    )
    home_tenants = {
        renter.unit_id: renter
        for renter in Renter.objects.filter(
            unit_id__in=unit_ids, status__in=("active", "notice_period")
        ).select_related("unit")
    }
    home_data = CareTakerHomeSerializer(homes, many=True, context={"request": request})
    for item, home in zip(home_data.data, homes, strict=False):
        renter = home_tenants.get(home.id)
        item["tenant_name"] = getattr(renter, "name", None)
        item["tenant_phone"] = getattr(renter, "phone", None)
        item["last_update"] = home.last_update.isoformat() if home.last_update else ""
        item["scope"] = "building" if home.building_id in building_ids else "standalone"

    return Response(
        {
            "data": {
                "buildings": building_data.data,
                "units": unit_data.data,
                "homes": home_data.data,
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
        requests_qs,
        many=True,
        context={"request": request, "caretaker_id": caretaker.id},
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
            maintenance,
            context={"request": request, "caretaker_id": caretaker.id},
        )
        return Response({"data": serializer.data})

    payload = CareTakerMaintenanceUpdateSerializer(data=request.data)
    payload.is_valid(raise_exception=True)
    data = payload.validated_data

    previous_status = maintenance.status
    previous_caretaker_id = maintenance.assigned_caretaker_id

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
    _record_caretaker_actions(
        caretaker=caretaker,
        maintenance=maintenance,
        actor=request.user,
        previous_status=previous_status,
        previous_caretaker_id=previous_caretaker_id,
        note=data.get("notes", ""),
    )
    serializer = CareTakerMaintenanceSerializer(
        maintenance, context={"request": request, "caretaker_id": caretaker.id}
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
    owner_total = (
        Building.objects.filter(owner=caretaker.owner, is_archived=False).count()
        + Unit.objects.filter(
            owner=caretaker.owner, is_archived=False, building__isnull=True
        ).count()
    )
    mine = len(building_ids) + len(directly_assigned_unit_ids(caretaker))
    return Response(
        {
            "data": {
                "name": caretaker.name,
                "owner": getattr(caretaker.owner, "full_name", "")
                or getattr(caretaker.owner, "username", ""),
                "owner_phone": getattr(caretaker.owner, "phone", "") or "",
                "since": caretaker.joining_date.isoformat(),
                "properties": len(building_ids) + len(unit_ids),
                "buildings": len(building_ids),
                "units": len(unit_ids),
                "homes": len(unit_ids),
                "tenants": Renter.objects.filter(
                    unit_id__in=unit_ids, status__in=("active", "notice_period")
                ).count(),
                "open_requests": requests_qs.filter(status__in=OPEN_STATUSES).count(),
                "scope_percent": round(mine * 100 / owner_total) if owner_total else 0,
            }
        }
    )


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def caretaker_profile(request: Request) -> Response:
    """Return the profile of the caretaker and the scope of the owner.

    The caretaker reads his own details and the properties the owner gave
    him. He may correct his own contact details — the scope itself is never
    changed from here, only the owner does that.
    """
    caretaker = _require_caretaker(request)
    building_ids, unit_ids = _scope(caretaker)

    if request.method == "PATCH":
        payload = CareTakerProfileUpdateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        for field, value in payload.validated_data.items():
            setattr(caretaker, field, value)
        try:
            caretaker.full_clean(exclude=["owner", "unit"])
        except ValidationError as error:
            raise ValidationError(error.message_dict) from error
        caretaker.save()
        return Response(
            {
                "data": {
                    "profile": CareTakerProfileSerializer(
                        caretaker, context={"request": request}
                    ).data
                }
            }
        )

    assignments = caretaker.assignments.filter(is_active=True).select_related(
        "building", "unit", "unit__building"
    )
    return Response(
        {
            "data": {
                "profile": CareTakerProfileSerializer(
                    caretaker, context={"request": request}
                ).data,
                "scope": {
                    "owner": getattr(caretaker.owner, "full_name", "")
                    or getattr(caretaker.owner, "username", ""),
                    "owner_phone": getattr(caretaker.owner, "phone", "") or "",
                    "since": caretaker.joining_date.isoformat(),
                    "buildings": len(building_ids),
                    "homes": len(unit_ids),
                },
                "assignments": CareTakerAssignmentSummarySerializer(
                    assignments, many=True, context={"request": request}
                ).data,
            }
        }
    )
