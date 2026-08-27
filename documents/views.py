import os
import tempfile
from io import BytesIO
from typing import Any, cast

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.timezone import now

from core.models import User
from properties.models import Renter, RentRecord, Unit
from properties.serializers import RentRecordSerializer

from .utils import generate_unit_history_pdf

# Create your views here.


class GenerateRentAgreementPdfViewSet(viewsets.ViewSet):
    queryset: Any = Renter.objects.all()
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    @action(detail=True, methods=["get"], url_path="generate-rent-agreement-pdf")
    def generate_rent_agreement_pdf(
        self, request: HttpRequest, pk: int
    ) -> HttpResponse:
        from weasyprint import HTML

        try:
            renter = Renter.objects.select_related("unit", "unit__owner").get(pk=pk)
        except Renter.DoesNotExist:
            return Response(
                {"detail": "Renter not found."}, status=status.HTTP_404_NOT_FOUND
            )

        if renter.unit.owner != request.user:
            return Response(
                {"detail": "You do not have permission to access this document."},
                status=status.HTTP_403_FORBIDDEN,
            )

        html_string = render_to_string(
            "rent_agreement.html",
            {
                "renter": renter,
                "unit": renter.unit,
                "owner": renter.unit.owner,
                "today_date": now().date(),
            },
        )

        pdf_file = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf_file, content_type="application/pdf")  # noqa: S1192
        response["Content-Disposition"] = (
            f"inline; filename=rent_agreement_{renter.id}.pdf"
        )
        return response


class GenerateUnitDossierPdfViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["get"], url_path="generate-dossier-pdf")
    def generate_dossier_pdf(self, request: HttpRequest, pk: int) -> HttpResponse:
        from weasyprint import HTML

        unit_obj = get_object_or_404(Unit, pk=pk)

        if unit_obj.owner != request.user:
            return Response(
                {"detail": "You do not have permission to access this document."},
                status=status.HTTP_403_FORBIDDEN,
            )

        caretakers = unit_obj.caretakers.all()
        renters = unit_obj.renters.all()
        taxes = getattr(unit_obj, "tax_records", None)
        if taxes is None:
            taxes = []

        context = {
            "unit": unit_obj,
            "caretakers": caretakers,
            "renters": renters,
            "taxes": taxes,
        }

        html_string = render_to_string("property_dossier.html", context)

        try:
            pdf_file = BytesIO()
            HTML(string=html_string).write_pdf(pdf_file)
        except Exception as e:
            return Response(
                {"error": "Failed to generate PDF", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response = HttpResponse(pdf_file.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename=unit_dossier_{pk}.pdf"
        return response


class GenerateRentReceiptPdfViewSet(viewsets.ModelViewSet):
    serializer_class = RentRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return RentRecord.objects.filter(unit__owner=user)

    @action(detail=True, methods=["get"], url_path="pdf_receipt")
    def pdf_receipt(self, request: HttpRequest, pk: int) -> HttpResponse:
        from weasyprint import HTML

        try:
            rent_record = self.get_object()
        except NotFound:
            return Response(
                {"error": "Rent record not found."}, status=status.HTTP_404_NOT_FOUND
            )

        html_string = render_to_string("rent_recept.html", {"rent_record": rent_record})
        html = HTML(string=html_string)
        pdf_file = html.write_pdf()

        response = HttpResponse(pdf_file, content_type="application/pdf")
        response["Content-Disposition"] = (
            f"attachment; filename=rent_receipt_{rent_record.id}.pdf"
        )
        return response


class GenerateIncomeSummaryPdfViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="download")
    def download_income_summary(self, request: HttpRequest) -> HttpResponse:
        period = request.query_params.get("period", "monthly")
        owner = cast(User, request.user)
        try:
            from properties.services.income_summary_service import (
                generate_income_summary_pdf,
            )

            pdf_bytes = generate_income_summary_pdf(owner, period=period)
        except Exception as e:
            return Response(
                {"error": "Failed to generate income summary", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        filename = f"income_summary_{period}_{now().date()}.pdf"
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response

    @action(detail=False, methods=["post"], url_path="send-whatsapp")
    def send_income_summary_whatsapp(self, request: HttpRequest) -> Response:
        from notification.services.whatsapp_service import send_whatsapp_file
        from properties.services.income_summary_service import (
            generate_income_summary_pdf,
        )

        period = request.data.get("period", "monthly")
        owner = cast(User, request.user)
        phone = getattr(owner, "whatsapp_number", None)

        if not phone:
            return Response(
                {"detail": "WhatsApp number not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            pdf_bytes = generate_income_summary_pdf(owner, period=period)
            fd, path = tempfile.mkstemp(
                suffix=".pdf", prefix=f"income_summary_{period}_"
            )
            try:
                with os.fdopen(fd, "wb") as pdf_file:
                    pdf_file.write(pdf_bytes)
            except Exception:
                os.close(fd)
                raise

            sent = send_whatsapp_file(phone, path, "application/pdf")
        except Exception as exc:
            return Response(
                {"error": "Failed to send WhatsApp", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            if "path" in locals() and os.path.exists(path):
                os.unlink(path)

        if sent:
            return Response(
                {"detail": "Income summary sent via WhatsApp."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"detail": "Failed to send WhatsApp."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def download_unit_history(request: HttpRequest, unit_id: int) -> HttpResponse:
    owner = cast("User", request.user)
    unit_obj = Unit.objects.get(id=unit_id, owner=owner)
    pdf_data = generate_unit_history_pdf(unit_obj)

    response = HttpResponse(pdf_data, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="unit_{unit_id}_history.pdf"'
    )
    return response
