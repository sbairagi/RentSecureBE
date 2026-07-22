from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from shared.domain_events import BaseDomainEvent


@dataclass(frozen=True)
class RenterCreated(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "Renter"
    version: str = "1.0"
    renter_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)
    name: str = ""
    phone: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "renter_id": str(self.renter_id),
            "unit_id": str(self.unit_id),
            "owner_id": str(self.owner_id),
            "name": self.name,
            "phone": self.phone,
        }


@dataclass(frozen=True)
class RenterStatusChanged(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "Renter"
    version: str = "1.0"
    renter_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)
    old_status: str = ""
    new_status: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "renter_id": str(self.renter_id),
            "unit_id": str(self.unit_id),
            "owner_id": str(self.owner_id),
            "old_status": self.old_status,
            "new_status": self.new_status,
        }


@dataclass(frozen=True)
class RenterOnboardingInvited(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "Renter"
    version: str = "1.0"
    renter_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)
    phone: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "renter_id": str(self.renter_id),
            "unit_id": str(self.unit_id),
            "owner_id": str(self.owner_id),
            "phone": self.phone,
        }


@dataclass(frozen=True)
class RenterKYCCompleted(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "Renter"
    version: str = "1.0"
    renter_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)

    def to_payload(self) -> dict[str, Any]:
        return {
            "renter_id": str(self.renter_id),
            "unit_id": str(self.unit_id),
            "owner_id": str(self.owner_id),
        }


@dataclass(frozen=True)
class RenterAgreementRevoked(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "Renter"
    version: str = "1.0"
    renter_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)
    reason: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "renter_id": str(self.renter_id),
            "unit_id": str(self.unit_id),
            "owner_id": str(self.owner_id),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class RenterExited(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "Renter"
    version: str = "1.0"
    renter_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)

    def to_payload(self) -> dict[str, Any]:
        return {
            "renter_id": str(self.renter_id),
            "unit_id": str(self.unit_id),
            "owner_id": str(self.owner_id),
        }


@dataclass(frozen=True)
class RenterArchived(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "Renter"
    version: str = "1.0"
    renter_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)

    def to_payload(self) -> dict[str, Any]:
        return {
            "renter_id": str(self.renter_id),
            "unit_id": str(self.unit_id),
            "owner_id": str(self.owner_id),
        }


__all__ = [
    "RenterCreated",
    "RenterStatusChanged",
    "RenterOnboardingInvited",
    "RenterKYCCompleted",
    "RenterAgreementRevoked",
    "RenterExited",
    "RenterArchived",
]
