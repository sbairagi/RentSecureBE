from __future__ import annotations

from typing import Any

from core.services.base import BaseService, ServiceResult


class SubscriptionService(BaseService):
    """Service for subscription and usage-limit workflows.

    Expected responsibilities:
    - Subscription plan resolution
    - Usage limit checks
    - Feature flag evaluation
    - Subscription expiry handling
    """

    def execute(self, *args: Any, **kwargs: Any) -> ServiceResult[Any]:
        raise NotImplementedError
