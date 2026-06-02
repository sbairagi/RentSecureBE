# services/agreement_service.py

import tempfile

from django.template.loader import render_to_string
from weasyprint import HTML


def generate_agreement_pdf(rent_record):
    html_string = render_to_string("pdf/rent_agreement.html", {"rent": rent_record})
    pdf_file = tempfile.NamedTemporaryFile(
        delete=False,
        prefix=f"rent_agreement_{rent_record.id}_",
        suffix=".pdf",
    )
    pdf_file_path = pdf_file.name
    pdf_file.close()
    HTML(string=html_string).write_pdf(pdf_file_path)
    return pdf_file_path
