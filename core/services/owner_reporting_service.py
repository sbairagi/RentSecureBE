from __future__ import annotations

from typing import Any

from django.db.models import Sum

from core.services.base import BaseService, ServiceResult
from properties.models.rent_record_models import RentRecord


class OwnerReportingService(BaseService):
    """Service for owner reporting workflows.

    Expected responsibilities:
    - Report data aggregation
    - Report generation orchestration
    - Export format handling
    - Delivery scheduling
    """

    @staticmethod
    def get_rent_inflow_summary(owner: Any) -> dict[str, Any]:
        total_received = (
            RentRecord.objects.filter(unit__owner=owner, status="PAID").aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        pending_count = RentRecord.objects.filter(
            unit__owner=owner, status="PENDING"
        ).count()

        failed_payouts = RentRecord.objects.filter(
            unit__owner=owner, payout_status="FAILED"
        ).count()

        return {
            "total_received": total_received,
            "pending_payments": pending_count,
            "failed_payouts": failed_payouts,
        }

    @staticmethod
    def get_owner_rent_records(owner: Any) -> list[dict[str, Any]]:
        rents = (
            RentRecord.objects.filter(unit__owner=owner)
            .select_related("renter", "unit")
            .order_by("-due_date")
        )

        return [
            {
                "property": r.unit.unit,
                "renter": r.renter.name if r.renter else "",
                "month": r.due_date.strftime("%B %Y"),
                "rent": float(r.amount),
                "status": r.status,
                "payout_status": r.payout_status,
            }
            for r in rents
        ]

    def execute(self, *args: Any, **kwargs: Any) -> ServiceResult[Any]:
        raise NotImplementedError
