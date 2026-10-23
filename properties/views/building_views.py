from typing import Any

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from django.core.cache import cache
from django.db.models import Count, Q, QuerySet

from rentsecure_be.type_compat import override

from ..constants import BUILDINGS_CACHE_TIMEOUT
from ..feature_enforcer import FeatureEnforcer
from ..models import Building
from ..serializers import BuildingSerializer
from ..services.unit_service import get_building_analytics


def _paginate(queryset, request, serializer_class, context=None):
    """Return a paginated response shaped as { data, meta }.

    The frontend ``rows()`` helper already extracts ``payload.data`` when it
    is a list, so this shape is drop-in compatible with existing consumers.
    """
    try:
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 50))
    except (ValueError, TypeError):
        page = 1
        limit = 50
    page = max(page, 1)
    limit = max(min(limit, 200), 1)

    total = queryset.count()
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    start = (page - 1) * limit
    end = start + limit
    page_qs = queryset[start:end]

    serializer = serializer_class(page_qs, many=True, context=context or {})
    return Response(
        {
            "data": serializer.data,
            "meta": {
                "total": total,
                "page": page,
                "limit": limit,
                "totalPages": total_pages,
            },
        }
    )


class BuildingViewSet(viewsets.ModelViewSet[Building]):
    serializer_class = BuildingSerializer
    permission_classes = [IsAuthenticated]

    @override
    def get_queryset(self) -> QuerySet[Building]:
        user = self.request.user
        cache_key = f"buildings_user_{user.id}"
        enforcer = FeatureEnforcer(user)

        has_filters = self._has_active_filters()

        if not has_filters:
            buildings = cache.get(cache_key)
            if buildings is None:
                buildings = Building.objects.filter(owner=user).annotate(
                    _occupied_units_count=Count(
                        "units", filter=Q(units__is_vacant=False), distinct=True
                    )
                )
                cache.set(cache_key, buildings, timeout=BUILDINGS_CACHE_TIMEOUT)
        else:
            buildings = Building.objects.filter(owner=user).annotate(
                _occupied_units_count=Count(
                    "units", filter=Q(units__is_vacant=False), distinct=True
                )
            )

        if enforcer.is_expired() and enforcer.is_past_grace_period():
            free_limit = enforcer.get_free_plan_limit("max_buildings")
            active_buildings = buildings.filter(is_archived=False)
            if free_limit == "unlimited":
                buildings = active_buildings
            else:
                buildings = active_buildings[:free_limit]

        return self._apply_building_filters(buildings)

    @override
    def list(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        return _paginate(
            queryset, request, BuildingSerializer, context={"request": request}
        )

    def _has_active_filters(self) -> bool:
        return any(
            self.request.GET.get(param)
            for param in (
                "search",
                "city",
                "state",
                "country",
                "is_archived",
                "ordering",
            )
        )

    def _apply_building_filters(
        self, queryset: QuerySet[Building]
    ) -> QuerySet[Building]:
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(address_line__icontains=search)
                | Q(city__icontains=search)
                | Q(state__icontains=search)
                | Q(country__icontains=search)
                | Q(postal_code__icontains=search)
            )

        city = self.request.GET.get("city")
        if city:
            queryset = queryset.filter(city__icontains=city)

        state = self.request.GET.get("state")
        if state:
            queryset = queryset.filter(state__icontains=state)

        country = self.request.GET.get("country")
        if country:
            queryset = queryset.filter(country__icontains=country)

        is_archived = self.request.GET.get("is_archived")
        if is_archived is not None:
            queryset = queryset.filter(is_archived=is_archived.lower() == "true")

        ordering = self.request.GET.get("ordering")
        if ordering:
            queryset = queryset.order_by(ordering)

        return queryset

    @override
    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        user = self.request.user
        enforcer = FeatureEnforcer(user)

        if not enforcer.can_create("max_buildings"):
            raise PermissionDenied("Building creation limit reached for your plan.")

        serializer.save(owner=user)
        cache.delete(f"buildings_user_{user.id}")

    @override
    def perform_update(self, serializer: BaseSerializer[Any]) -> None:
        if serializer.instance.owner != self.request.user:
            raise PermissionDenied(
                "You do not have permission to update this building."
            )
        serializer.save()
        cache.delete(f"buildings_user_{self.request.user.id}")

    @override
    def perform_destroy(self, instance: Building) -> None:
        if instance.owner != self.request.user:
            raise PermissionDenied(
                "You do not have permission to delete this building."
            )
        instance.delete()
        cache.delete(f"buildings_user_{self.request.user.id}")

    @action(detail=True, methods=["get"], url_path="analytics")
    def analytics(self, request: Any, pk: str | None = None) -> Response:
        building = self.get_object()
        data = get_building_analytics(building)
        return Response({"data": data})
