# services/agreement_service.py


from django.template.loader import render_to_string
from weasyprint import HTML


def generate_agreement_pdf(rent_record):
    html_string = render_to_string("pdf/rent_agreement.html", {"rent": rent_record})
    pdf_file_path = f"/tmp/rent_agreement_{rent_record.id}.pdf"
    HTML(string=html_string).write_pdf(pdf_file_path)
    return pdf_file_path
