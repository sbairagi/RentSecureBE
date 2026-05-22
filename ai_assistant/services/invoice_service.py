# services/invoice_service.py

import tempfile

from django.template.loader import render_to_string
from weasyprint import HTML


def generate_final_invoice_pdf(renter, latest_rent):
    context = {
        "renter": renter,
        "unit": renter.unit,
        "building": renter.unit.building,
        "latest_rent": latest_rent,
        "deactivation_date": renter.updated_at.date(),
    }

    html_string = render_to_string("pdf_templates/final_invoice.html", context)
    html = HTML(string=html_string)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    html.write_pdf(target=temp_file.name)

    return temp_file.name


# from services.whatsapp_service import send_whatsapp_message

# send_whatsapp_message(
#     renter.phone,
#     f"📄 Your final rent invoice has been generated.",
#     media_path=pdf_path
# )
