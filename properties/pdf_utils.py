# utils/pdf_utils.py
import tempfile
from typing import Any

from django.template.loader import render_to_string


def generate_rent_invoice_pdf(rent: Any) -> str:
    html = render_to_string("invoices/rent_invoice.html", {"rent": rent})

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as output:
        from weasyprint import HTML

        HTML(string=html).write_pdf(output.name)
        return output.name
