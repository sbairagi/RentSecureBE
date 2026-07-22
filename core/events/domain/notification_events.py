from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from shared.domain_events import BaseDomainEvent


@dataclass(frozen=True)
class NotificationSent(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "Notification"
    version: str = "1.0"
    notification_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    channel: str = ""
    title: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "notification_id": str(self.notification_id),
            "user_id": str(self.user_id),
            "channel": self.channel,
            "title": self.title,
        }


@dataclass(frozen=True)
class RentReminderSent(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "RentRecord"
    version: str = "1.0"
    rent_record_id: UUID = field(default_factory=uuid4)
    renter_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)

    def to_payload(self) -> dict[str, Any]:
        return {
            "rent_record_id": str(self.rent_record_id),
            "renter_id": str(self.renter_id),
            "unit_id": str(self.unit_id),
        }


@dataclass(frozen=True)
class TaxReminderSent(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "PropertyTaxRecord"
    version: str = "1.0"
    tax_record_id: UUID = field(default_factory=uuid4)
    property_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)

    def to_payload(self) -> dict[str, Any]:
        return {
            "tax_record_id": str(self.tax_record_id),
            "property_id": str(self.property_id),
            "owner_id": str(self.owner_id),
        }


@dataclass(frozen=True)
class MonthlySummarySent(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "User"
    version: str = "1.0"
    owner_id: UUID = field(default_factory=uuid4)
    month: int = 0
    year: int = 0

    def to_payload(self) -> dict[str, Any]:
        return {
            "owner_id": str(self.owner_id),
            "month": self.month,
            "year": self.year,
        }


__all__ = [
    "NotificationSent",
    "RentReminderSent",
    "TaxReminderSent",
    "MonthlySummarySent",
]
