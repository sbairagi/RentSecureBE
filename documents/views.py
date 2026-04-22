
from properties.models import Renter, Unit, RentRecord
from properties.serializers import RentRecordSerializer
from rest_framework import viewsets
from django.http import HttpResponse
from weasyprint import HTML
from io import BytesIO
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from django.template.loader import render_to_string
from .utils import generate_unit_history_pdf
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action

# Create your views here.



class GenerateRentAgreementPdfViewSet(viewsets.ViewSet):
    queryset = Renter.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='generate-rent-agreement-pdf')
    def generate_rent_agreement_pdf(self, request, pk=None):
        try:
            renter = Renter.objects.select_related('unit', 'unit__owner').get(pk=pk)
        except Renter.DoesNotExist:
            return Response({'detail': 'Renter not found.'}, status=status.HTTP_404_NOT_FOUND)

        html_string = render_to_string('rent_agreement_template.html', {
            'renter': renter,
            'unit': renter.unit,
            'owner': renter.unit.owner,
            'today_date': now().date()
        })

        pdf_file = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename=rent_agreement_{renter.id}.pdf'
        return response

class GenerateUnitDossierPdfViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='generate-dossier-pdf')
    def generate_dossier_pdf(self, request, pk=None):
        # Get Unit or return 404
        unit_obj = get_object_or_404(Unit, pk=pk)
        
        # Get related data
        caretakers = unit_obj.caretakers.all()
        renters = unit_obj.renters.all()
        taxes = getattr(unit_obj, 'tax_records', None)
        if taxes is None:
            taxes = []

        context = {
            'unit': unit_obj,
            'caretakers': caretakers,
            'renters': renters,
            'taxes': taxes,
        }

        # Render HTML from template
        html_string = render_to_string('unit_dossier_template.html', context)

        try:
            pdf_file = BytesIO()
            HTML(string=html_string).write_pdf(pdf_file)
        except Exception as e:
            return Response(
                {"error": "Failed to generate PDF", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        response = HttpResponse(pdf_file.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=unit_dossier_{pk}.pdf'
        return response

class GenerateRentReceiptPdfViewSet(viewsets.ModelViewSet):
    queryset = RentRecord.objects.all()
    serializer_class = RentRecordSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='pdf_receipt')
    def pdf_receipt(self, request, pk=None):
        try:
            rent_record = self.get_object()
        except NotFound:
            return Response(
                {"error": "Rent record not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        html_string = render_to_string('rent_receipt.html', {'rent_record': rent_record})
        html = HTML(string=html_string)
        pdf_file = html.write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=rent_receipt_{rent_record.id}.pdf'
        return response
    

def download_unit_history(request, unit_id):
    unit_obj = Unit.objects.get(id=unit_id, owner=request.user)
    pdf_data = generate_unit_history_pdf(unit_obj)

    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="unit_{unit_id}_history.pdf"'
    return response