from __future__ import annotations

from typing import Any

from core.services.base import BaseService, ServiceResult


class BankDetailsService(BaseService):
    """Service for bank details workflows.

    Expected responsibilities:
    - Bank detail validation
    - Secure storage coordination
    - Bank detail retrieval for payouts
    - Verification status management
    """

    def execute(self, *args: Any, **kwargs: Any) -> ServiceResult[Any]:
        raise NotImplementedError
