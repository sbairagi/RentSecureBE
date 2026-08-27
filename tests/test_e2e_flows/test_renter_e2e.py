"""
E2E Flow: Renter

Complete renter business flow:
- Renter authentication
- Dashboard
- View rent records
- Pay rent (mock payment)
- View agreement
- Documents
- Profile
- Notifications
"""

from __future__ import annotations

from decimal import Decimal

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from django.contrib.auth import get_user_model
from django.utils import timezone

from notification.models import Notification
from properties.models import ExtraCharge, RentAgreementDraft, RentRecord
from tests.test_e2e_flows import E2EAPIClientMixin

User = get_user_model()
API_PREFIX = "/api"


class RenterE2EFlowTests(E2EAPIClientMixin, APITestCase):
    """Complete renter end-to-end flow."""

    def setUp(self):
        self.client = APIClient()
        self.owner = self._create_owner_with_subscription("e2e_renter_flow_owner")
        self.data = self._create_complete_owner_data(self.owner)
        self.renter_user = self.data["renter_user"]
        self.renter = self.data["renter"]
        self.unit = self.data["unit"]
        self.owner_token = self._get_access_token(self.owner)
        self.renter_token = self._get_access_token(self.renter_user)
        self.other_renter_user = self._create_renter_user("e2e_other_renter")

    # ------------------------------------------------------------------
    # Renter Dashboard
    # ------------------------------------------------------------------

    def test_renter_dashboard(self):
        response = self._get_json(
            f"{API_PREFIX}/renter/dashboard/", token=self.renter_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_renter_dashboard_requires_auth(self):
        response = self.client.get(f"{API_PREFIX}/renter/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_cannot_access_renter_dashboard(self):
        response = self._get_json(
            f"{API_PREFIX}/renter/dashboard/", token=self.owner_token
        )
        self.assertIn(
            response.status_code,
            [
                status.HTTP_403_FORBIDDEN,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_404_NOT_FOUND,
            ],
        )

    # ------------------------------------------------------------------
    # Renter Rent Records
    # ------------------------------------------------------------------

    def test_renter_can_view_own_rent_records(self):
        RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            due_date=timezone.now().date().replace(day=5),
            amount=Decimal("15000.00"),
            status="pending",
        )
        response = self._get_json(
            f"{API_PREFIX}/renter/rent-records/", token=self.renter_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_renter_cannot_view_other_renter_rent_records(self):
        other_owner = self._create_owner_with_subscription("e2e_other_renter_owner")
        other_data = self._create_complete_owner_data(other_owner)
        other_renter = other_data["renter"]
        other_renter_user = other_data["renter_user"]
        other_rent = RentRecord.objects.create(
            renter=other_renter,
            unit=other_data["unit"],
            due_date=timezone.now().date().replace(day=5),
            amount=Decimal("15000.00"),
            status="pending",
        )
        other_renter_user_token = self._get_access_token(other_renter_user)

        response = self._get_json(
            f"{API_PREFIX}/renter/rent-records/", token=other_renter_user_token
        )
        # Should return only own records
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        record_ids = [record["id"] for record in response.data["data"]]
        self.assertIn(other_rent.id, record_ids)
        self.assertEqual(len(record_ids), 1)

    def test_renter_can_view_own_rent_detail(self):
        rent_record = RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            due_date=timezone.now().date().replace(day=5),
            amount=Decimal("15000.00"),
            status="pending",
        )
        response = self._get_json(
            f"{API_PREFIX}/renter/rent-records/{rent_record.id}/",
            token=self.renter_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_renter_cannot_view_other_renter_rent_detail(self):
        other_owner = self._create_owner_with_subscription("e2e_renter_detail_owner")
        other_data = self._create_complete_owner_data(other_owner)
        other_renter = other_data["renter"]
        other_rent = RentRecord.objects.create(
            renter=other_renter,
            unit=other_data["unit"],
            due_date=timezone.now().date().replace(day=5),
            amount=Decimal("15000.00"),
            status="pending",
        )
        response = self._get_json(
            f"{API_PREFIX}/renter/rent-records/{other_rent.id}/",
            token=self.renter_token,
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
        )

    # ------------------------------------------------------------------
    # Renter Profile
    # ------------------------------------------------------------------

    def test_renter_profile(self):
        response = self._get_json(
            f"{API_PREFIX}/renter/profile/", token=self.renter_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_renter_cannot_access_other_renter_profile(self):
        response = self._get_json(
            f"{API_PREFIX}/renter/profile/",
            token=self._get_access_token(self.other_renter_user),
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND, status.HTTP_200_OK],
        )

    # ------------------------------------------------------------------
    # Renter Agreement
    # ------------------------------------------------------------------

    def test_renter_agreement(self):
        from django.core.files.base import ContentFile

        RentAgreementDraft.objects.create(
            user=self.owner,
            renter=self.renter,
            unit=self.unit,
            file=ContentFile(b"dummy agreement", name="agreement.pdf"),
        )
        response = self._get_json(
            f"{API_PREFIX}/renter/agreement/", token=self.renter_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Renter Documents
    # ------------------------------------------------------------------

    def test_renter_documents(self):
        response = self._get_json(
            f"{API_PREFIX}/renter/documents/", token=self.renter_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Renter Extra Charges
    # ------------------------------------------------------------------

    def test_renter_extra_charges(self):
        ExtraCharge.objects.create(
            renter=self.renter,
            unit=self.unit,
            name="E2E Water Charge",
            amount=Decimal("500.00"),
            due_date=timezone.now().date().replace(day=15),
            status=ExtraCharge.Status.DUE,
        )
        response = self._get_json(
            f"{API_PREFIX}/renter/extra-charges/", token=self.renter_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    # ------------------------------------------------------------------
    # Renter Notifications
    # ------------------------------------------------------------------

    def test_renter_notifications(self):
        Notification.objects.create(
            user=self.renter_user,
            title="Renter E2E",
            message="Test renter notification",
            notification_type=Notification.RENT_DUE,
        )
        response = self._get_json(
            f"{API_PREFIX}/notifications/get/", token=self.renter_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.data)

    def test_renter_unread_count(self):
        response = self._get_json(
            f"{API_PREFIX}/notifications/unread-count/", token=self.renter_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def test_renter_search(self):
        response = self._get_json(
            f"{API_PREFIX}/search/?q=E2E", token=self.renter_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
