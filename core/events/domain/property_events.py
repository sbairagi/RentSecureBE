from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from shared.domain_events import BaseDomainEvent


@dataclass(frozen=True)
class BuildingCreated(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "Building"
    version: str = "1.0"
    building_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)
    name: str = ""
    city: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "building_id": str(self.building_id),
            "owner_id": str(self.owner_id),
            "name": self.name,
            "city": self.city,
        }


@dataclass(frozen=True)
class BuildingUpdated(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "Building"
    version: str = "1.0"
    building_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)
    changed_fields: list[str] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        return {
            "building_id": str(self.building_id),
            "owner_id": str(self.owner_id),
            "changed_fields": self.changed_fields,
        }


@dataclass(frozen=True)
class BuildingArchived(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "Building"
    version: str = "1.0"
    building_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)

    def to_payload(self) -> dict[str, Any]:
        return {
            "building_id": str(self.building_id),
            "owner_id": str(self.owner_id),
        }


@dataclass(frozen=True)
class UnitCreated(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "Unit"
    version: str = "1.0"
    unit_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)
    building_id: UUID = field(default_factory=uuid4)
    unit_number: str = ""
    unit_type: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "unit_id": str(self.unit_id),
            "owner_id": str(self.owner_id),
            "building_id": str(self.building_id),
            "unit_number": self.unit_number,
            "unit_type": self.unit_type,
        }


@dataclass(frozen=True)
class UnitUpdated(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "Unit"
    version: str = "1.0"
    unit_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)
    changed_fields: list[str] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        return {
            "unit_id": str(self.unit_id),
            "owner_id": str(self.owner_id),
            "changed_fields": self.changed_fields,
        }


@dataclass(frozen=True)
class UnitArchived(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "Unit"
    version: str = "1.0"
    unit_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)

    def to_payload(self) -> dict[str, Any]:
        return {
            "unit_id": str(self.unit_id),
            "owner_id": str(self.owner_id),
        }


@dataclass(frozen=True)
class UnitOccupied(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "Unit"
    version: str = "1.0"
    unit_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)
    renter_id: UUID = field(default_factory=uuid4)

    def to_payload(self) -> dict[str, Any]:
        return {
            "unit_id": str(self.unit_id),
            "owner_id": str(self.owner_id),
            "renter_id": str(self.renter_id),
        }


@dataclass(frozen=True)
class UnitVacated(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "Unit"
    version: str = "1.0"
    unit_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)
    renter_id: UUID = field(default_factory=uuid4)

    def to_payload(self) -> dict[str, Any]:
        return {
            "unit_id": str(self.unit_id),
            "owner_id": str(self.owner_id),
            "renter_id": str(self.renter_id),
        }


__all__ = [
    "BuildingCreated",
    "BuildingUpdated",
    "BuildingArchived",
    "UnitCreated",
    "UnitUpdated",
    "UnitArchived",
    "UnitOccupied",
    "UnitVacated",
]
