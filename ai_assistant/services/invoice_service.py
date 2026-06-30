# services/invoice_service.py

import tempfile
from typing import TYPE_CHECKING

from django.template.loader import render_to_string

if TYPE_CHECKING:
    from properties.models import Renter, RentRecord


def generate_final_invoice_pdf(
    renter: "Renter",
    latest_rent: "RentRecord",
) -> str:
    from weasyprint import HTML

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
