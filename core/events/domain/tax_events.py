from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from shared.domain_events import BaseDomainEvent


@dataclass(frozen=True)
class PropertyTaxRecordCreated(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "PropertyTaxRecord"
    version: str = "1.0"
    tax_record_id: UUID = field(default_factory=uuid4)
    property_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)
    amount: str = ""
    due_date: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "tax_record_id": str(self.tax_record_id),
            "property_id": str(self.property_id),
            "owner_id": str(self.owner_id),
            "amount": self.amount,
            "due_date": self.due_date,
        }


@dataclass(frozen=True)
class ExtraChargeGenerated(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "ExtraCharge"
    version: str = "1.0"
    extra_charge_id: UUID = field(default_factory=uuid4)
    renter_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    name: str = ""
    amount: str = ""
    due_date: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "extra_charge_id": str(self.extra_charge_id),
            "renter_id": str(self.renter_id),
            "unit_id": str(self.unit_id),
            "name": self.name,
            "amount": self.amount,
            "due_date": self.due_date,
        }


__all__ = [
    "PropertyTaxRecordCreated",
    "ExtraChargeGenerated",
]
