# services/agreement_service.py

import tempfile
from typing import Any

from django.template.loader import render_to_string


def generate_agreement_pdf(rent_record: Any) -> str:
    html_string = render_to_string("pdf/rent_agreement.html", {"rent": rent_record})
    pdf_file = tempfile.NamedTemporaryFile(
        delete=False,
        prefix=f"rent_agreement_{rent_record.id}_",
        suffix=".pdf",
    )
    pdf_file_path = pdf_file.name
    pdf_file.close()
    from weasyprint import HTML

    HTML(string=html_string).write_pdf(pdf_file_path)
    return pdf_file_path
