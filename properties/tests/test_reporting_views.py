"""Tests for property reporting views."""

from decimal import Decimal
from unittest.mock import patch

from django.test import RequestFactory

from properties.models import Renter, RentRecord
from properties.views.reporting_views import (
    download_rent_excel,
    owner_rent_records,
    rent_inflow_summary,
)


def _make_django_request(user=None, method="get"):
    factory = RequestFactory()
    if method == "get":
        req = factory.get("/test")
    else:
        req = factory.post("/test")
    if user is not None:
        req.user = user
    return req


def _create_renter(unit):
    return Renter.objects.create(
        unit=unit,
        name="Test Renter",
        phone="+919876543210",
        email="renter@test.com",
        rent_amount=10000,
        start_date="2025-01-01",
        end_date="2025-12-31",
    )


class TestRentInflowSummaryView:
    def test_returns_summary(self, owner, building, unit):
        renter = _create_renter(unit)
        RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("15000"),
            payment_method="upi",
            status="PAID",
            due_date="2025-01-05",
        )
        RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("15000"),
            payment_method="upi",
            status="PENDING",
            due_date="2025-02-05",
        )
        RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("15000"),
            payment_method="upi",
            status="PAID",
            payout_status="FAILED",
            due_date="2025-03-05",
        )
        req = _make_django_request(user=owner, method="get")
        with patch("rest_framework.request.Request.user", owner):
            response = rent_inflow_summary(req)
        assert response.status_code == 200
        assert response.data["total_received"] == Decimal("30000")
        assert response.data["pending_payments"] == 1
        assert response.data["failed_payouts"] == 1

    def test_empty_summary(self, owner):
        req = _make_django_request(user=owner, method="get")
        with patch("rest_framework.request.Request.user", owner):
            response = rent_inflow_summary(req)
        assert response.status_code == 200
        assert response.data["total_received"] == 0
        assert response.data["pending_payments"] == 0
        assert response.data["failed_payouts"] == 0


class TestOwnerRentRecordsView:
    def test_lists_own_records(self, owner, building, unit):
        renter = _create_renter(unit)
        RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("12000"),
            payment_method="upi",
            status="PAID",
            payout_status="SUCCESS",
            due_date="2025-01-05",
        )
        req = _make_django_request(user=owner, method="get")
        with patch("rest_framework.request.Request.user", owner):
            response = owner_rent_records(req)
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["rent"] == float(Decimal("12000"))
        assert response.data[0]["renter"] == renter.name

    def test_empty_records(self, owner):
        req = _make_django_request(user=owner, method="get")
        with patch("rest_framework.request.Request.user", owner):
            response = owner_rent_records(req)
        assert response.status_code == 200
        assert response.data == []


class TestDownloadRentExcelView:
    @patch("properties.utils.export_utils.generate_owner_rent_report")
    def test_returns_excel_response(self, mock_generate, owner):
        mock_generate.return_value = b"fake_excel_content"
        req = _make_django_request(user=owner, method="get")
        with patch("rest_framework.request.Request.user", owner):
            response = download_rent_excel(req)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/vnd.ms-excel"
        assert "attachment" in response["Content-Disposition"]
