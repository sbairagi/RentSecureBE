from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from shared.domain_events import BaseDomainEvent


@dataclass(frozen=True)
class RentAgreementGenerated(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "RentAgreementDraft"
    version: str = "1.0"
    agreement_id: UUID = field(default_factory=uuid4)
    renter_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)

    def to_payload(self) -> dict[str, Any]:
        return {
            "agreement_id": str(self.agreement_id),
            "renter_id": str(self.renter_id),
            "unit_id": str(self.unit_id),
            "owner_id": str(self.owner_id),
        }


@dataclass(frozen=True)
class RentAgreementSigned(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "RentAgreementDraft"
    version: str = "1.0"
    agreement_id: UUID = field(default_factory=uuid4)
    renter_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)
    participant: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "agreement_id": str(self.agreement_id),
            "renter_id": str(self.renter_id),
            "unit_id": str(self.unit_id),
            "owner_id": str(self.owner_id),
            "participant": self.participant,
        }


@dataclass(frozen=True)
class UnitImageUploaded(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "UnitImage"
    version: str = "1.0"
    image_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)

    def to_payload(self) -> dict[str, Any]:
        return {
            "image_id": str(self.image_id),
            "unit_id": str(self.unit_id),
            "owner_id": str(self.owner_id),
        }


@dataclass(frozen=True)
class UnitDocumentUploaded(BaseDomainEvent):
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = "UnitDocument"
    version: str = "1.0"
    document_id: UUID = field(default_factory=uuid4)
    unit_id: UUID = field(default_factory=uuid4)
    owner_id: UUID = field(default_factory=uuid4)

    def to_payload(self) -> dict[str, Any]:
        return {
            "document_id": str(self.document_id),
            "unit_id": str(self.unit_id),
            "owner_id": str(self.owner_id),
        }


@dataclass(frozen=True)
class RentAgreementPDFGenerated(BaseDomainEvent):
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
class UnitDossierPDFGenerated(BaseDomainEvent):
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


__all__ = [
    "RentAgreementGenerated",
    "RentAgreementSigned",
    "UnitImageUploaded",
    "UnitDocumentUploaded",
    "RentAgreementPDFGenerated",
    "UnitDossierPDFGenerated",
]
