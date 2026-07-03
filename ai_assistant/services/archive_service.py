# mypy: ignore-errors

# services/archive_service.py

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from django.db.models.fields.files import FieldFile
from django.forms import model_to_dict

from properties.models import ArchivedRenter, RentRecord, UnitImage


def _serialize_value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, FieldFile):
        return str(value) if value else None
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize_value(v) for v in value]
    return value


def archive_renter_data(renter: Any) -> ArchivedRenter:  # type: ignore[misc]
    qs = RentRecord.objects.filter(renter=renter).values()
    rent_records = _serialize_value(list(qs))
    image_paths = list(
        UnitImage.objects.filter(renter=renter).values_list("image", flat=True)
    )

    renter_dict = model_to_dict(
        renter,
        exclude=["renter_image", "id_proof", "rent_agreement"],
    )
    renter_dict["renter_image"] = (
        str(renter.renter_image) if renter.renter_image else None
    )
    renter_dict["id_proof"] = str(renter.id_proof) if renter.id_proof else None
    renter_dict["rent_agreement"] = (
        str(renter.rent_agreement) if renter.rent_agreement else None
    )
    renter_dict = _serialize_value(renter_dict)

    archived = ArchivedRenter.objects.create(
        renter=renter,
        data={
            "profile": renter_dict,
            "rent_records": rent_records,
        },
        agreement_pdf=getattr(renter, "rent_agreement_pdf", None),
        police_pdf=getattr(renter, "police_verification_pdf", None),
        property_images=image_paths,
        final_invoice=renter.final_invoice_path,
    )
    return archived
