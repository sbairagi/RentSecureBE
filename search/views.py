"""Global search across all user-owned resources.

The search endpoint is the single source of truth for cross-resource
search. All authorization is enforced at the database level — no
frontend-side filtering is trusted for security.
"""

from __future__ import annotations

import logging
from typing import Any

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.db.models import Q, QuerySet

from core.models import User
from properties.models import (
    Building,
    Caretaker,
    RentAgreementDraft,
    Renter,
    RentRecord,
    Unit,
)
from properties.serializers import (
    BuildingSerializer,
    CaretakerSerializer,
    RenterSerializer,
    RentRecordSerializer,
    UnitSerializer,
)
from visitors.models import Visitor
from visitors.serializers.visitor_serializers import VisitorSerializer

from .serializers import SearchResponseSerializer

logger = logging.getLogger(__name__)


SEARCHABLE_RESOURCE_TYPES: dict[str, dict[str, Any]] = {
    "buildings": {
        "label": "Buildings",
        "fields": ["name", "address_line", "city", "state", "country", "postal_code"],
        "queryset_fn": lambda user: Building.objects.filter(
            owner=user, is_archived=False
        ),
        "serializer": BuildingSerializer,
        "detail_route": "buildings-detail",
        "title_fn": lambda obj: obj.name,
        "subtitle_fn": lambda obj: f"{obj.address_line}, {obj.city}",
        "status_fn": lambda obj: "Active" if not obj.is_archived else "Archived",
        "updated_fn": lambda obj: (
            getattr(obj, "updated_at", None) or getattr(obj, "created_at", None)
        ),
        "order_field": "-created_at",
    },
    "units": {
        "label": "Units",
        "fields": [
            "unit",
            "building_name",
            "address_line",
            "landmark",
            "city",
            "state",
        ],
        "queryset_fn": lambda user: Unit.objects.filter(owner=user, is_archived=False),
        "serializer": UnitSerializer,
        "detail_route": "units-detail",
        "title_fn": lambda obj: obj.building_name or obj.unit,
        "subtitle_fn": lambda obj: f"{obj.address_line}, {obj.city}",
        "status_fn": lambda obj: obj.get_status_display(),
        "updated_fn": lambda obj: (
            getattr(obj, "updated_at", None) or getattr(obj, "created_at", None)
        ),
        "order_field": "-created_at",
    },
    "renters": {
        "label": "Renters",
        "fields": ["name", "email", "phone", "alternate_phone"],
        "queryset_fn": lambda user: Renter.objects.filter(
            unit__owner=user, status__in=["active", "notice_period"]
        ),
        "serializer": RenterSerializer,
        "detail_route": "renters-detail",
        "title_fn": lambda obj: obj.name,
        "subtitle_fn": lambda obj: (
            f"{obj.unit.building.name if obj.unit and obj.unit.building else ''}"
            f" - {obj.unit.unit if obj.unit else ''}"
        ),
        "status_fn": lambda obj: obj.get_status_display(),
        "updated_fn": lambda obj: (
            getattr(obj, "updated_at", None) or getattr(obj, "created_at", None)
        ),
        "order_field": "-start_date",
    },
    "caretakers": {
        "label": "Caretakers",
        "fields": ["name", "email", "phone", "alternate_phone", "address"],
        "queryset_fn": lambda user: Caretaker.objects.filter(
            unit__owner=user, is_active=True
        ),
        "serializer": CaretakerSerializer,
        "detail_route": "caretakers-detail",
        "title_fn": lambda obj: obj.name,
        "subtitle_fn": lambda obj: (
            f"{obj.unit.building.name if obj.unit and obj.unit.building else ''}"
            f" - {obj.unit.unit if obj.unit else ''}"
        ),
        "status_fn": lambda obj: "Active" if obj.is_active else "Inactive",
        "updated_fn": lambda obj: (
            getattr(obj, "updated_at", None) or getattr(obj, "created_at", None)
        ),
        "order_field": "-joining_date",
    },
    "rent_records": {
        "label": "Rent Records",
        "fields": ["renter__name", "unit__unit", "transaction_id", "notes"],
        "queryset_fn": lambda user: RentRecord.objects.filter(unit__owner=user),
        "serializer": RentRecordSerializer,
        "detail_route": "rent-records-detail",
        "title_fn": lambda obj: (
            f"{obj.renter.name if obj.renter else 'Unknown'} - {obj.due_date}"
        ),
        "subtitle_fn": lambda obj: (
            f"{obj.unit.unit if obj.unit else ''} | {obj.get_status_display()}"
        ),
        "status_fn": lambda obj: obj.get_status_display(),
        "updated_fn": lambda obj: (
            getattr(obj, "updated_at", None) or getattr(obj, "created_at", None)
        ),
        "order_field": "-due_date",
    },
    "visitors": {
        "label": "Visitors",
        "fields": ["visitor_name", "phone_number", "vehicle_number", "purpose"],
        "queryset_fn": lambda user: Visitor.objects.filter(
            Q(created_by=user) | Q(building__owner=user)
        ).distinct(),
        "serializer": VisitorSerializer,
        "detail_route": "visitors-detail",
        "title_fn": lambda obj: obj.visitor_name,
        "subtitle_fn": lambda obj: (
            f"{obj.building.name if obj.building else ''}"
            f" - {obj.unit.unit if obj.unit else ''}"
        ),
        "status_fn": lambda obj: obj.get_status_display(),
        "updated_fn": lambda obj: (
            getattr(obj, "updated_at", None) or getattr(obj, "created_at", None)
        ),
        "order_field": "-created_at",
    },
    "agreements": {
        "label": "Rent Agreements",
        "fields": ["renter__name", "unit__unit", "leegality_document_id"],
        "queryset_fn": lambda user: RentAgreementDraft.objects.filter(user=user),
        "serializer": None,
        "detail_route": None,
        "title_fn": lambda obj: (
            f"Agreement - {obj.renter.name if obj.renter else 'Unknown'}"
        ),
        "subtitle_fn": lambda obj: f"{obj.unit.unit if obj.unit else ''}",
        "status_fn": lambda obj: (
            "Signed" if obj.owner_signed and obj.renter_signed else "Pending"
        ),
        "updated_fn": lambda obj: obj.generated_at,
        "order_field": "-generated_at",
    },
}


def _build_search_query(
    queryset: QuerySet, query: str, search_fields: list[str]
) -> QuerySet:
    """Build a Q-object search query across multiple fields."""
    if not query or not search_fields:
        return queryset
    q_objects = Q()
    for field in search_fields:
        q_objects |= Q(**{f"{field}__icontains": query})
    return queryset.filter(q_objects)


def _normalize_result(
    resource_type: str,
    obj: Any,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Normalize a model instance into the unified search result shape."""
    serializer_cls = config.get("serializer")
    serialized_data = {}
    if serializer_cls:
        try:
            serialized_data = serializer_cls(obj).data
        except Exception:
            serialized_data = {}

    return {
        "resource_type": resource_type,
        "id": obj.pk,
        "title": config["title_fn"](obj),
        "subtitle": config["subtitle_fn"](obj),
        "status": config["status_fn"](obj),
        "metadata": serialized_data,
        "last_updated": (
            config["updated_fn"](obj).isoformat() if config["updated_fn"](obj) else None
        ),
        "navigation_target": config.get("detail_route", ""),
    }


def _search_resource_type(
    resource_type: str,
    user: User,
    query: str,
    include_archived: bool,
    ordering: str,
    page_size: int,
) -> tuple[list[dict[str, Any]], bool]:
    """Search a single resource type and return normalized results."""
    config = SEARCHABLE_RESOURCE_TYPES.get(resource_type)
    if config is None:
        return [], False

    try:
        base_qs = config["queryset_fn"](user)
    except Exception as exc:
        logger.warning("Search queryset failed for %s: %s", resource_type, exc)
        return [], False

    if not include_archived and resource_type in ("buildings", "units"):
        base_qs = base_qs.filter(is_archived=False)

    search_qs = _build_search_query(base_qs, query, config["fields"])

    order_field = config["order_field"]
    if ordering == "oldest":
        order_field = order_field.lstrip("-")
    elif ordering == "relevance":
        order_field = order_field

    allowed_ordering = {
        "newest",
        "oldest",
        "relevance",
    }
    if ordering not in allowed_ordering:
        order_field = config["order_field"]

    search_qs = search_qs.order_by(order_field)

    results = [
        _normalize_result(resource_type, obj, config)
        for obj in search_qs[: page_size * 3]
    ]

    return results, search_qs.exists()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def global_search(request):
    """Search across all user-owned resources.

    Query Parameters:
        q (str): Search query string (required for meaningful results).
        resource_type (str): Optional resource type filter (comma-separated).
        page (int): Page number (default 1).
        page_size (int): Results per page (default 20, max 50).
        ordering (str): Field to order by (default: relevance/newest).
        include_archived (bool): Include archived items (default false).

    Returns:
        Normalized search results across all searchable resources.
    """
    user: User = request.user
    query = (request.query_params.get("q") or "").strip()
    resource_type_filter = request.query_params.get("resource_type", "")
    page = max(1, int(request.query_params.get("page", 1) or 1))
    page_size = min(50, max(1, int(request.query_params.get("page_size", 20) or 20)))
    ordering = request.query_params.get("ordering", "newest")
    include_archived = (
        request.query_params.get("include_archived", "false").lower() == "true"
    )

    if not query:
        return Response(
            {
                "query": query,
                "total_results": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "results": [],
                "available_resource_types": list(SEARCHABLE_RESOURCE_TYPES.keys()),
            }
        )

    requested_types = (
        [t.strip() for t in resource_type_filter.split(",") if t.strip()]
        if resource_type_filter
        else []
    )
    if not requested_types:
        requested_types = list(SEARCHABLE_RESOURCE_TYPES.keys())

    available_types = []
    all_results = []

    for resource_type in requested_types:
        resource_results, has_results = _search_resource_type(
            resource_type, user, query, include_archived, ordering, page_size
        )
        all_results.extend(resource_results)
        if has_results:
            available_types.append(resource_type)

    total_results = len(all_results)
    total_pages = (
        max(1, (total_results + page_size - 1) // page_size) if total_results else 0
    )
    start = (page - 1) * page_size
    end = start + page_size
    page_results = all_results[start:end]

    response_data = {
        "query": query,
        "total_results": total_results,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "results": page_results,
        "available_resource_types": available_types,
    }

    serializer = SearchResponseSerializer(data=response_data)
    serializer.is_valid(raise_exception=True)
    return Response(serializer.validated_data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_suggestions(request):
    """Return lightweight search suggestions based on partial query.

    Query Parameters:
        q (str): Partial query string (min 2 chars).
        limit (int): Max suggestions to return (default 10).

    Returns:
        List of suggestion strings derived from existing data.
    """
    user: User = request.user
    query = (request.query_params.get("q") or "").strip().lower()
    limit = min(20, max(1, int(request.query_params.get("limit", 10) or 10)))

    if len(query) < 2:
        return Response({"query": query, "suggestions": []})

    suggestions: set[str] = set()

    building_names = Building.objects.filter(owner=user, is_archived=False).values_list(
        "name", flat=True
    )
    for name in building_names:
        if query in name.lower():
            suggestions.add(name)

    unit_identifiers = Unit.objects.filter(owner=user, is_archived=False).values_list(
        "unit", flat=True
    )
    for unit in unit_identifiers:
        if query in unit.lower():
            suggestions.add(unit)

    renter_names = Renter.objects.filter(
        unit__owner=user, status__in=["active", "notice_period"]
    ).values_list("name", flat=True)
    for name in renter_names:
        if query in name.lower():
            suggestions.add(name)

    visitor_names = Visitor.objects.filter(
        Q(created_by=user) | Q(building__owner=user)
    ).values_list("visitor_name", flat=True)
    for name in visitor_names:
        if query in name.lower():
            suggestions.add(name)

    return Response(
        {
            "query": query,
            "suggestions": list(suggestions)[:limit],
        }
    )
