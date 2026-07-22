from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from shared.domain_events import BaseDomainEvent


@dataclass(frozen=True)
class PaymentLinkCreated(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "RentRecord"
    version: str = "1.0"
    rent_record_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    renter_id: UUID = field(default_factory=uuid4)
    amount: str = ""
    payment_link: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "rent_record_id": str(self.rent_record_id),
            "unit_id": str(self.unit_id),
            "renter_id": str(self.renter_id),
            "amount": self.amount,
            "payment_link": self.payment_link,
        }


@dataclass(frozen=True)
class PayoutProcessed(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "RentRecord"
    version: str = "1.0"
    rent_record_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    renter_id: UUID = field(default_factory=uuid4)
    amount: str = ""
    payout_status: str = ""
    payout_reference: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "rent_record_id": str(self.rent_record_id),
            "unit_id": str(self.unit_id),
            "renter_id": str(self.renter_id),
            "amount": self.amount,
            "payout_status": self.payout_status,
            "payout_reference": self.payout_reference,
        }


@dataclass(frozen=True)
class PayoutFailed(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "RentRecord"
    version: str = "1.0"
    rent_record_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    renter_id: UUID = field(default_factory=uuid4)
    amount: str = ""
    error: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "rent_record_id": str(self.rent_record_id),
            "unit_id": str(self.unit_id),
            "renter_id": str(self.renter_id),
            "amount": self.amount,
            "error": self.error,
        }


@dataclass(frozen=True)
class WebhookReceived(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "WebhookEvent"
    version: str = "1.0"
    provider: str = ""
    event_id: str = ""
    status: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "event_id": self.event_id,
            "status": self.status,
        }


__all__ = [
    "PaymentLinkCreated",
    "PayoutProcessed",
    "PayoutFailed",
    "WebhookReceived",
]
