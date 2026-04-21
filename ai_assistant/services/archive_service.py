# services/archive_service.py

from django.forms import model_to_dict
from wealth_concierge_platform.models import ArchivedRenter, RentRecord, UnitImage


def archive_renter_data(renter):
    rent_records = list(RentRecord.objects.filter(renter=renter).values())
    image_paths = list(UnitImage.objects.filter(renter=renter).values_list("image", flat=True))

    archived = ArchivedRenter.objects.create(
        renter=renter,
        data={
            "profile": model_to_dict(renter),
            "rent_records": rent_records,
        },
        agreement_pdf=renter.rent_agreement_pdf,
        police_pdf=renter.police_verification_pdf,
        property_images=image_paths,
        final_invoice=renter.final_invoice_path,
    )
    return archived