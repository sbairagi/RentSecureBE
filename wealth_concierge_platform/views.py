from rest_framework import viewsets, permissions
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
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import (
    PropertyTaxRecord, SubscriptionPlan, UserSubscription,
    AddOnPurchase, PlanFeatureLimit, UsageLimit,
    RentAgreementDraft, PDFExportRecord,
    PropertyImage, PropertyDocument,
    Property, Caretaker, Renter, RentRecord
)
from .serializers import (
    PropertyTaxRecordSerializer, SubscriptionPlanSerializer, UserSubscriptionSerializer,
    AddOnPurchaseSerializer, PlanFeatureLimitSerializer, UsageLimitSerializer,
    RentAgreementDraftSerializer, PDFExportRecordSerializer,
    PropertyImageSerializer, PropertyDocumentSerializer, PropertySerializer, 
    CaretakerSerializer, RenterSerializer, RentRecordSerializer
)

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


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






# Records owned by a user
class PropertyTaxRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PropertyTaxRecordSerializer
    queryset = PropertyTaxRecord.objects.all()

    def get_queryset(self):
        return PropertyTaxRecord.objects.filter(property__owner=self.request.user)

class UserSubscriptionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSubscriptionSerializer
    queryset = UserSubscription.objects.all()

    def get_queryset(self):
        return UserSubscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AddOnPurchaseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AddOnPurchaseSerializer
    queryset = AddOnPurchase.objects.all()

    def get_queryset(self):
        return AddOnPurchase.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UsageLimitViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UsageLimitSerializer
    queryset = UsageLimit.objects.all()

    def get_queryset(self):
        return UsageLimit.objects.filter(user=self.request.user)

class RentAgreementDraftViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RentAgreementDraftSerializer
    queryset = RentAgreementDraft.objects.all()

    def get_queryset(self):
        return RentAgreementDraft.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PDFExportRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PDFExportRecordSerializer
    queryset = PDFExportRecord.objects.all()

    def get_queryset(self):
        return PDFExportRecord.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PropertyImageViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PropertyImageSerializer
    queryset = PropertyImage.objects.all()

    def get_queryset(self):
        return PropertyImage.objects.filter(property__owner=self.request.user)

class PropertyDocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PropertyDocumentSerializer
    queryset = PropertyDocument.objects.all()

    def get_queryset(self):
        return PropertyDocument.objects.filter(property__owner=self.request.user)

# Global Plans & Limits (public for listing)
class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer

class PlanFeatureLimitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PlanFeatureLimit.objects.all()
    serializer_class = PlanFeatureLimitSerializer

# class PropertyTaxRecordViewSet(viewsets.ModelViewSet):
#     queryset = PropertyTaxRecord.objects.all()
#     serializer_class = PropertyTaxRecordSerializer
#     permission_classes = [IsAuthenticated]

# class SubscriptionPlanViewSet(viewsets.ModelViewSet):
#     queryset = SubscriptionPlan.objects.all()
#     serializer_class = SubscriptionPlanSerializer
#     permission_classes = [IsAuthenticated]

# class UserSubscriptionViewSet(viewsets.ModelViewSet):
#     queryset = UserSubscription.objects.all()
#     serializer_class = UserSubscriptionSerializer
#     permission_classes = [IsAuthenticated]

# class AddOnPurchaseViewSet(viewsets.ModelViewSet):
#     queryset = AddOnPurchase.objects.all()
#     serializer_class = AddOnPurchaseSerializer
#     permission_classes = [IsAuthenticated]

# class PlanFeatureLimitViewSet(viewsets.ModelViewSet):
#     queryset = PlanFeatureLimit.objects.all()
#     serializer_class = PlanFeatureLimitSerializer
#     permission_classes = [IsAuthenticated]

# class UsageLimitViewSet(viewsets.ModelViewSet):
#     queryset = UsageLimit.objects.all()
#     serializer_class = UsageLimitSerializer
#     permission_classes = [IsAuthenticated]

# class RentAgreementDraftViewSet(viewsets.ModelViewSet):
#     queryset = RentAgreementDraft.objects.all()
#     serializer_class = RentAgreementDraftSerializer
#     permission_classes = [IsAuthenticated]

# class PDFExportRecordViewSet(viewsets.ModelViewSet):
#     queryset = PDFExportRecord.objects.all()
#     serializer_class = PDFExportRecordSerializer
#     permission_classes = [IsAuthenticated]

# class PropertyImageViewSet(viewsets.ModelViewSet):
#     queryset = PropertyImage.objects.all()
#     serializer_class = PropertyImageSerializer
#     permission_classes = [IsAuthenticated]

# class PropertyDocumentViewSet(viewsets.ModelViewSet):
#     queryset = PropertyDocument.objects.all()
#     serializer_class = PropertyDocumentSerializer
#     permission_classes = [IsAuthenticated]


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
    

