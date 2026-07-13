from __future__ import annotations

from typing import Any

from core.services.base import BaseService, ServiceResult


class OwnerReportingService(BaseService):
    """Service for owner reporting workflows.

    Expected responsibilities:
    - Report data aggregation
    - Report generation orchestration
    - Export format handling
    - Delivery scheduling
    """

    def execute(self, *args: Any, **kwargs: Any) -> ServiceResult[Any]:
        raise NotImplementedError
