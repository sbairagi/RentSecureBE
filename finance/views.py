from django.http import FileResponse
from rest_framework import permissions, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from properties.models import Unit

from .models import CAProfile, TaxSubmissionToCA
from .serializers import CAProfileSerializer, TaxSubmissionToCASerializer
from .utils import create_tax_zip, generate_tax_excel, generate_tax_pdf


class CAProfileViewSet(viewsets.ModelViewSet):
    queryset = CAProfile.objects.all()
    serializer_class = CAProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

class TaxSubmissionToCAViewSet(viewsets.ModelViewSet):
    serializer_class = TaxSubmissionToCASerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = TaxSubmissionToCA.objects.all()

    def get_queryset(self):
        return TaxSubmissionToCA.objects.filter(tax_summary__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()


class DownloadTaxFilesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        fy = request.query_params.get('fy', '2024-25')

        properties = Unit.objects.filter(owner=user)
        excel = generate_tax_excel(user, properties, fy)
        pdf = generate_tax_pdf(user, properties, fy)

        # Assuming your model has FileFields like rent_agreement, police_verification
        extra_files = []
        for p in properties:
            if p.renter and p.renter.rent_agreement:
                extra_files.append(p.renter.rent_agreement)
            if p.renter and p.renter.police_verification:
                extra_files.append(p.renter.police_verification)

        zip_file = create_tax_zip(user, excel, pdf, extra_files)

        return FileResponse(open(zip_file, 'rb'), as_attachment=True, filename="tax_documents.zip")
