from __future__ import annotations

from typing import Any

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from django.contrib.auth.models import AnonymousUser
from django.db.models import Count

from ..models import PoliceVerification
from ..serializers import PoliceVerificationSerializer


class PoliceVerificationViewSet(viewsets.ModelViewSet[PoliceVerification]):
    permission_classes = [IsAuthenticated]
    serializer_class = PoliceVerificationSerializer

    def get_queryset(self) -> Any:
        user = self.request.user
        if isinstance(user, AnonymousUser):
            return PoliceVerification.objects.none()
        return PoliceVerification.objects.filter(unit__owner=user)

    @action(detail=False, methods=["get"], url_path="dashboard_stats")
    def dashboard_stats(self, request: Request) -> Response:
        user = request.user
        if isinstance(user, AnonymousUser):
            return Response(
                {
                    "verified": 0,
                    "submitted": 0,
                    "not_started": 0,
                }
            )

        qs = PoliceVerification.objects.filter(unit__owner=user)
        data = {
            item["status"]: item["count"]
            for item in qs.values("status").annotate(count=Count("id"))
        }

        return Response(
            {
                "verified": data.get("verified", 0),
                "submitted": data.get("submitted", 0),
                "not_started": data.get("not_started", 0),
            }
        )
