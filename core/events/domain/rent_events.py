from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from shared.domain_events import BaseDomainEvent


@dataclass(frozen=True)
class RentRecordCreated(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "RentRecord"
    version: str = "1.0"
    rent_record_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    renter_id: UUID = field(default_factory=uuid4)
    amount: str = ""
    due_date: str = ""
    payment_method: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "rent_record_id": str(self.rent_record_id),
            "unit_id": str(self.unit_id),
            "renter_id": str(self.renter_id),
            "amount": self.amount,
            "due_date": self.due_date,
            "payment_method": self.payment_method,
        }


@dataclass(frozen=True)
class RentPaid(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "RentRecord"
    version: str = "1.0"
    rent_record_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    renter_id: UUID = field(default_factory=uuid4)
    amount: str = ""
    paid_on: str = ""
    payment_method: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "rent_record_id": str(self.rent_record_id),
            "unit_id": str(self.unit_id),
            "renter_id": str(self.renter_id),
            "amount": self.amount,
            "paid_on": self.paid_on,
            "payment_method": self.payment_method,
        }


@dataclass(frozen=True)
class RentOverdue(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "RentRecord"
    version: str = "1.0"
    rent_record_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    renter_id: UUID = field(default_factory=uuid4)
    amount: str = ""
    due_date: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "rent_record_id": str(self.rent_record_id),
            "unit_id": str(self.unit_id),
            "renter_id": str(self.renter_id),
            "amount": self.amount,
            "due_date": self.due_date,
        }


@dataclass(frozen=True)
class RenterFlagged(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "Renter"
    version: str = "1.0"
    renter_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)
    missed_rents: int = 0
    reason: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "renter_id": str(self.renter_id),
            "unit_id": str(self.unit_id),
            "owner_id": str(self.owner_id),
            "missed_rents": self.missed_rents,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class RentReceiptGenerated(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "RentRecord"
    version: str = "1.0"
    rent_record_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    renter_id: UUID = field(default_factory=uuid4)

    def to_payload(self) -> dict[str, Any]:
        return {
            "rent_record_id": str(self.rent_record_id),
            "unit_id": str(self.unit_id),
            "renter_id": str(self.renter_id),
        }


__all__ = [
    "RentRecordCreated",
    "RentPaid",
    "RentOverdue",
    "RenterFlagged",
    "RentReceiptGenerated",
]
