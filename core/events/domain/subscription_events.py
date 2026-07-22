from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from shared.domain_events import BaseDomainEvent


@dataclass(frozen=True)
class SubscriptionActivated(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "UserSubscription"
    version: str = "1.0"
    user_id: UUID = field(default_factory=uuid4)
    plan_name: str = ""
    is_yearly: bool = False

    def to_payload(self) -> dict[str, Any]:
        return {
            "user_id": str(self.user_id),
            "plan_name": self.plan_name,
            "is_yearly": self.is_yearly,
        }


@dataclass(frozen=True)
class SubscriptionExpired(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "UserSubscription"
    version: str = "1.0"
    user_id: UUID = field(default_factory=uuid4)
    plan_name: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "user_id": str(self.user_id),
            "plan_name": self.plan_name,
        }


@dataclass(frozen=True)
class AddOnPurchased(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "AddOnPurchase"
    version: str = "1.0"
    user_id: UUID = field(default_factory=uuid4)
    addon_name: str = ""
    amount: str = ""
    is_recurring: bool = False

    def to_payload(self) -> dict[str, Any]:
        return {
            "user_id": str(self.user_id),
            "addon_name": self.addon_name,
            "amount": self.amount,
            "is_recurring": self.is_recurring,
        }


@dataclass(frozen=True)
class SubscriptionPlanCreated(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "SubscriptionPlan"
    version: str = "1.0"
    plan_id: int = 0
    plan_name: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "plan_name": self.plan_name,
        }


__all__ = [
    "SubscriptionActivated",
    "SubscriptionExpired",
    "AddOnPurchased",
    "SubscriptionPlanCreated",
]
