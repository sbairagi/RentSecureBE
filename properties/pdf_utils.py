# utils/pdf_utils.py
import tempfile

from django.template.loader import render_to_string
from weasyprint import HTML


def generate_rent_invoice_pdf(rent):
    html = render_to_string("invoices/rent_invoice.html", {"rent": rent})

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as output:
        HTML(string=html).write_pdf(output.name)
        return output.name  # Return path to file
