"""Project-wide type aliases and TypedDicts.

Centralising shared types here keeps modules thin and consistent. New
typed payloads should be added here, not scattered across modules.
"""

from __future__ import annotations

from typing import Literal, TypedDict, Union

# ---------------------------------------------------------------------------
# Status / state literals
# ---------------------------------------------------------------------------

RenterStatus = Literal["active", "notice_period", "revoked", "deactivated"]
PaymentStatus = Literal["PENDING", "PAID", "FAILED", "UNPAID"]
VacancyStatus = Literal["OCCUPIED", "VACANT"]
SubscriptionState = Literal["active", "expired", "grace_period", "cancelled"]

# ---------------------------------------------------------------------------
# API response shapes
# ---------------------------------------------------------------------------


class ErrorPayload(TypedDict):
    """Standard error envelope used by all DRF error responses."""

    error: str
    code: str
    detail: str | None


class FeatureLimitError(ErrorPayload):
    """Specialised error for feature-limit violations."""

    required_add_on: str
    subscription_limit: Union[int, Literal["unlimited"]]
    add_on_limit: int
    current_usage: int


# ---------------------------------------------------------------------------
# Export all
# ---------------------------------------------------------------------------

__all__ = [
    "RenterStatus",
    "PaymentStatus",
    "VacancyStatus",
    "SubscriptionState",
    "ErrorPayload",
    "FeatureLimitError",
]
