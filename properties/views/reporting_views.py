from __future__ import annotations

import logging
from typing import Any, cast

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from django.http import HttpResponse

from core.models import User
from properties.services.owner_reporting_service import OwnerReportingService

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def rent_inflow_summary(request: Request, /, *args: Any, **kwargs: Any) -> Response:
    owner: User = cast(User, request.user)
    return Response(OwnerReportingService.get_rent_inflow_summary(owner))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def owner_rent_records(request: Request, /, *args: Any, **kwargs: Any) -> Response:
    owner: User = cast(User, request.user)
    return Response(OwnerReportingService.get_owner_rent_records(owner))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_rent_excel(request: Request, /, *args: Any, **kwargs: Any) -> HttpResponse:
    from properties.utils.export_utils import generate_owner_rent_report

    file = generate_owner_rent_report(request.user)
    response = HttpResponse(file, content_type="application/vnd.ms-excel")
    response["Content-Disposition"] = 'attachment; filename="rent_report.xlsx"'
    return response
