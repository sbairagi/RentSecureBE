from __future__ import annotations

from typing import Any

from core.services.base import BaseService, ServiceResult


class UsageLimitService(BaseService):
    """Service for usage-limit enforcement.

    Expected responsibilities:
    - Current usage calculation
    - Limit comparison
    - Limit-exceeded handling
    - Reset scheduling
    """

    def execute(self, *args: Any, **kwargs: Any) -> ServiceResult[Any]:
        raise NotImplementedError
