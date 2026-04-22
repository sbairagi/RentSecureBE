from weasyprint import HTML
from django.template.loader import render_to_string
from django.conf import settings
import tempfile

def generate_unit_history_pdf(unit_obj):
    context = {
        'unit': unit_obj,
        'owner': unit_obj.owner,
        'caretakers': unit_obj.caretaker_set.all(),
        'renters': [],
        'tax_records': unit_obj.unittaxrecord_set.all(),
    }

    for renter in unit_obj.renter_set.all():
        rent_records = renter.rentrecord_set.all()
        rent_agreement_url = renter.rent_agreement.url if renter.rent_agreement else None
        police_verification_url = renter.police_verification.url if renter.police_verification else None
        possession_images = unit_obj.unitimage_set.filter(renter=renter)

        context['renters'].append({
            'renter': renter,
            'rent_records': rent_records,
            'rent_agreement_url': rent_agreement_url,
            'police_verification_url': police_verification_url,
            'images': [img.image.url for img in possession_images]
        })

    html_string = render_to_string("pdf_templates/unit_history.html", context)

    with tempfile.NamedTemporaryFile(delete=True, suffix='.pdf') as output:
        HTML(string=html_string, base_url=settings.BASE_DIR).write_pdf(output.name)
        output.seek(0)
        return output.read()