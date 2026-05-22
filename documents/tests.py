from datetime import date
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PyPDF2 import PdfReader
from weasyprint import HTML

from documents.utils import generate_unit_history_pdf
from properties.models import RentAgreementDraft, Renter, Unit


class GenerateUnitHistoryPdfTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username='owner',
            password='ownerpass',
            full_name='Owner User',
            whatsapp_number='+919876543210',
        )

        self.unit = Unit.objects.create(
            owner=self.owner,
            unit='101',
            unit_type=Unit.UnitType.FLAT,
            address_line='123 Main St',
            city='Mumbai',
            state='Maharashtra',
            country='India',
            postal_code='400001',
        )

        agreement_bytes = HTML(string='<p>Signed agreement</p>').write_pdf()

        self.renter = Renter.objects.create(
            unit=self.unit,
            user=self.owner,
            name='Renter Name',
            email='renter@example.com',
            phone='+919999999999',
            whatsapp_number='+919999999999',
            rent_amount=10000,
            start_date=date.today(),
            id_proof=SimpleUploadedFile('id_proof.pdf', b'%PDF-1.4\n%%EOF', content_type='application/pdf'),
            rent_agreement=SimpleUploadedFile('agreement.pdf', agreement_bytes, content_type='application/pdf'),
        )

        self.renter.refresh_from_db()

    def test_generate_unit_history_pdf_merges_signed_agreement(self):
        pdf_data = generate_unit_history_pdf(self.unit)

        self.assertTrue(pdf_data.startswith(b'%PDF'))

        reader = PdfReader(BytesIO(pdf_data))
        self.assertGreaterEqual(len(reader.pages), 2)

    def test_generate_unit_history_pdf_includes_signed_draft_agreement(self):
        draft_bytes = HTML(string='<p>Signed draft agreement</p>').write_pdf()
        RentAgreementDraft.objects.create(
            user=self.owner,
            renter=self.renter,
            unit=self.unit,
            file=SimpleUploadedFile('draft_agreement.pdf', draft_bytes, content_type='application/pdf'),
            owner_signed=True,
            renter_signed=True,
        )

        pdf_data = generate_unit_history_pdf(self.unit)
        self.assertTrue(pdf_data.startswith(b'%PDF'))

        reader = PdfReader(BytesIO(pdf_data))
        self.assertGreaterEqual(len(reader.pages), 2)
