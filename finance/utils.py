import os
import tempfile
import zipfile

from django.template.loader import render_to_string
from openpyxl import Workbook
from weasyprint import HTML


def generate_tax_excel(user, properties, fy):
    wb = Workbook()
    ws = wb.active
    ws.title = f"FY {fy}"

    headers = ["Property", "Address", "Renter", "Rent Received", "Tax Paid", "Net Income"]
    ws.append(headers)

    for p in properties:
        row = [
            p.title,
            p.address_line,
            p.renter.name if hasattr(p, 'renter') else '—',
            p.rent_income_for_fy(fy),
            p.tax_paid_for_fy(fy),
            p.net_income_for_fy(fy),
        ]
        ws.append(row)

    fd, path = tempfile.mkstemp(suffix=".xlsx", prefix=f"{user.username}_tax_{fy}_")
    os.close(fd)
    wb.save(path)
    return path


def generate_tax_pdf(user, properties, fy):
    html_string = render_to_string("templates/pdf_templates/tax_summary_template.html", {
        "user": user,
        "properties": properties,
        "fy": fy,
    })
    fd, pdf_file = tempfile.mkstemp(suffix=".pdf", prefix=f"{user.username}_tax_{fy}_")
    os.close(fd)
    HTML(string=html_string).write_pdf(pdf_file)
    return pdf_file


def create_tax_zip(user, excel_path, pdf_path, extra_docs):
    fd, zip_path = tempfile.mkstemp(suffix=".zip", prefix=f"{user.username}_tax_docs_")
    os.close(fd)
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write(excel_path, os.path.basename(excel_path))
        zipf.write(pdf_path, os.path.basename(pdf_path))

        for doc in extra_docs:
            if doc and os.path.exists(doc.path):
                zipf.write(doc.path, os.path.basename(doc.path))

    return zip_path
