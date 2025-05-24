from rest_framework import viewsets, permissions
from .models import Property, Caretaker, Renter, RentRecord, PropertyTaxRecord
from .serializers import PropertySerializer, CaretakerSerializer, RenterSerializer, RentRecordSerializer, PropertyTaxRecordSerializer
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from io import BytesIO
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound

class PropertyViewSet(viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    queryset = Property.objects.all()

    def get_queryset(self):
        return Property.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class CaretakerViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Caretaker.objects.all()
    serializer_class = CaretakerSerializer


class RenterViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Renter.objects.all()
    serializer_class = RenterSerializer


class RentRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = RentRecord.objects.all()
    serializer_class = RentRecordSerializer


class PropertyTaxRecordViewSet(viewsets.ModelViewSet):
    queryset = PropertyTaxRecord.objects.all()
    serializer_class = PropertyTaxRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Return only tax records of properties owned by the user
        return PropertyTaxRecord.objects.filter(property__owner=user)

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()


class GenerateRentAgreementPdfViewSet(viewsets.ViewSet):
    queryset = Renter.objects.all()

    @action(detail=True, methods=['get'], url_path='generate-rent-agreement-pdf')
    def generate_rent_agreement_pdf(self, request, pk=None):
        try:
            renter = Renter.objects.select_related('property', 'property__owner').get(pk=pk)
        except Renter.DoesNotExist:
            return Response({'detail': 'Renter not found.'}, status=status.HTTP_404_NOT_FOUND)

        html_string = render_to_string('rent_agreement_template.html', {
            'renter': renter,
            'property': renter.property,
            'owner': renter.property.owner,
            'today_date': now().date()
        })

        pdf_file = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename=rent_agreement_{renter.id}.pdf'
        return response

class GeneratePropertyDossierPdfViewSet(viewsets.ViewSet):
    @action(detail=True, methods=['get'], url_path='generate-dossier-pdf')
    def generate_dossier_pdf(self, request, pk=None):
        # Get property or return 404
        property_obj = get_object_or_404(Property, pk=pk)
        
        # Get related data
        caretakers = property_obj.caretakers.all()
        renters = property_obj.renters.all()
        taxes = getattr(property_obj, 'tax_records', None)
        if taxes is None:
            taxes = []

        context = {
            'property': property_obj,
            'caretakers': caretakers,
            'renters': renters,
            'taxes': taxes,
        }

        # Render HTML from template
        html_string = render_to_string('property_dossier_template.html', context)

        try:
            pdf_file = BytesIO()
            HTML(string=html_string).write_pdf(pdf_file)
        except Exception as e:
            return Response(
                {"error": "Failed to generate PDF", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        response = HttpResponse(pdf_file.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=property_dossier_{pk}.pdf'
        return response

class GenerateRentReceiptPdfViewSet(viewsets.ModelViewSet):
    queryset = RentRecord.objects.all()
    serializer_class = RentRecordSerializer

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