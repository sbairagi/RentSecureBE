import os
import tempfile

from django.conf import settings
from django.template.loader import render_to_string
from PyPDF2 import PdfMerger
from weasyprint import HTML

from properties.models import RentAgreementDraft


def _read_pdf_if_exists(path):
    if not os.path.exists(path):
        return b""
    with open(path, 'rb') as output:
        return output.read()


def generate_unit_history_pdf(unit_obj):
    tax_records = []
    if hasattr(unit_obj, 'unittaxrecord_set'):
        tax_records = unit_obj.unittaxrecord_set.all()
    elif hasattr(unit_obj, 'tax_records'):
        tax_records = unit_obj.tax_records

    context = {
        'unit': unit_obj,
        'owner': unit_obj.owner,
        'caretakers': unit_obj.caretakers.all(),
        'renters': [],
        'tax_records': tax_records,
    }

    agreement_paths = []
    for renter in unit_obj.renters.all():
        rent_records = renter.rent_records.all()
        rent_agreement_url = renter.rent_agreement.url if renter.rent_agreement else None
        police_verification_url = renter.police_verification_pdf.url if renter.police_verification_pdf else None
        possession_images = unit_obj.images.filter(renter=renter)

        context['renters'].append({
            'renter': renter,
            'rent_records': rent_records,
            'rent_agreement_url': rent_agreement_url,
            'police_verification_url': police_verification_url,
            'images': [img.image.url for img in possession_images]
        })

        if renter.rent_agreement and hasattr(renter.rent_agreement, 'path'):
            agreement_path = renter.rent_agreement.path
            if agreement_path and os.path.exists(agreement_path):
                agreement_paths.append(agreement_path)

        drafts = RentAgreementDraft.objects.filter(
            renter=renter,
            owner_signed=True,
            renter_signed=True,
        )
        for draft in drafts:
            if draft.file and hasattr(draft.file, 'path'):
                draft_path = draft.file.path
                if draft_path and os.path.exists(draft_path):
                    agreement_paths.append(draft_path)

    html_string = render_to_string("pdf_templates/unit_history.html", context)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_pdf_path = os.path.join(tmpdir, 'unit_history_base.pdf')
        HTML(string=html_string, base_url=settings.BASE_DIR).write_pdf(base_pdf_path)

        if not agreement_paths:
            return _read_pdf_if_exists(base_pdf_path)

        merged_pdf_path = os.path.join(tmpdir, 'unit_history_full.pdf')
        merger = PdfMerger()
        merger.append(base_pdf_path)
        for agreement_path in agreement_paths:
            merger.append(agreement_path)
        merger.write(merged_pdf_path)
        merger.close()

        return _read_pdf_if_exists(merged_pdf_path)
