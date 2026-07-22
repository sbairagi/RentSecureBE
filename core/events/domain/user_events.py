from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from shared.domain_events import BaseDomainEvent


@dataclass(frozen=True)
class UserCreated(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "User"
    version: str = "1.0"
    user_id: UUID = field(default_factory=uuid4)
    phone: str = ""
    email: str = ""
    full_name: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "user_id": str(self.user_id),
            "phone": self.phone,
            "email": self.email,
            "full_name": self.full_name,
        }


@dataclass(frozen=True)
class UserLoggedIn(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "User"
    version: str = "1.0"
    user_id: UUID = field(default_factory=uuid4)
    phone: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "user_id": str(self.user_id),
            "phone": self.phone,
        }


@dataclass(frozen=True)
class UserPreferencesCreated(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "NotificationPreference"
    version: str = "1.0"
    user_id: UUID = field(default_factory=uuid4)

    def to_payload(self) -> dict[str, Any]:
        return {
            "user_id": str(self.user_id),
        }


@dataclass(frozen=True)
class ReferralCreated(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "Referral"
    version: str = "1.0"
    user_id: UUID = field(default_factory=uuid4)
    referral_code: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "user_id": str(self.user_id),
            "referral_code": self.referral_code,
        }


@dataclass(frozen=True)
class ReferralRewardGranted(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "Referral"
    version: str = "1.0"
    referrer_id: UUID = field(default_factory=uuid4)
    referred_user_id: UUID = field(default_factory=uuid4)
    bonus_amount: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "referrer_id": str(self.referrer_id),
            "referred_user_id": str(self.referred_user_id),
            "bonus_amount": self.bonus_amount,
        }


__all__ = [
    "UserCreated",
    "UserLoggedIn",
    "UserPreferencesCreated",
    "ReferralCreated",
    "ReferralRewardGranted",
]
