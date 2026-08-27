"""
E2E Flow: Owner

Complete Owner business flow:
- Dashboard
- Building CRUD
- Unit CRUD
- Renter management
- Caretaker management
- Rent record management
- Payments
- Extra charges
- Notifications
- Profile management
- Subscription
- AI assistant
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import OwnerBankDetails
from notification.models import DeviceToken, Notification
from properties.models import Building, ExtraCharge, Renter, Unit
from tests.test_e2e_flows import OWNER_USERNAME, E2EAPIClientMixin

User = get_user_model()
API_PREFIX = "/api"


class OwnerE2EFlowTests(E2EAPIClientMixin, APITestCase):
    """Complete Owner end-to-end flow."""

    def setUp(self):
        self.client = APIClient()
        self.owner = self._create_owner_with_subscription(OWNER_USERNAME)
        self.data = self._create_complete_owner_data(self.owner)
        self.token = self._get_access_token(self.owner)
        self.other_owner = self._create_owner_with_subscription("e2e_other_owner")
        self.other_building = Building.objects.create(
            owner=self.other_owner,
            name="Other Owner Building",
            address_line="456 Other St",
            city="Other City",
            state="OT",
            country="IN",
            postal_code="400002",
        )
        self.other_unit = Unit.objects.create(
            owner=self.other_owner,
            building=self.other_building,
            unit="OTHER-101",
            address_line="456 Other St",
            city="Other City",
            state="OT",
            country="IN",
            postal_code="400002",
            unit_type=Unit.UnitType.FLAT,
        )

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    def test_owner_dashboard_summary(self):
        response = self._get_json(
            f"{API_PREFIX}/owner/dashboard-summary/", token=self.token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_rent_collected", response.data)
        self.assertIn("pending_rent", response.data)
        self.assertIn("rent_defaulters", response.data)

    def test_owner_dashboard_redirects_unauthenticated(self):
        response = self.client.get(f"{API_PREFIX}/owner/dashboard-summary/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ------------------------------------------------------------------
    # Building CRUD
    # ------------------------------------------------------------------

    def test_create_building(self):
        payload = {
            "name": "E2E New Building",
            "address_line": "456 Oak Avenue",
            "city": "Mumbai",
            "state": "MH",
            "country": "IN",
            "postal_code": "400050",
        }
        response = self._post_json(
            f"{API_PREFIX}/buildings/", payload, token=self.token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "E2E New Building")
        self.assertEqual(response.data["owner"], self.owner.id)

    def test_list_buildings(self):
        self._create_complete_owner_data(self.owner)
        response = self._get_json(f"{API_PREFIX}/buildings/", token=self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_retrieve_building(self):
        building = self.data["building"]
        response = self._get_json(
            f"{API_PREFIX}/buildings/{building.id}/", token=self.token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], building.id)

    def test_update_building(self):
        building = self.data["building"]
        response = self._patch_json(
            f"{API_PREFIX}/buildings/{building.id}/",
            {"name": "Updated E2E Building"},
            token=self.token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        building.refresh_from_db()
        self.assertEqual(building.name, "Updated E2E Building")

    def test_delete_building(self):
        building = Building.objects.create(
            owner=self.owner,
            name="To Delete",
            address_line="789 Delete St",
            city="Test City",
            state="TS",
            country="IN",
            postal_code="400001",
        )
        response = self._delete_json(
            f"{API_PREFIX}/buildings/{building.id}/", token=self.token
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Building.objects.filter(id=building.id).exists())

    def test_cannot_access_other_owner_building(self):
        response = self._get_json(
            f"{API_PREFIX}/buildings/{self.other_building.id}/",
            token=self.token,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ------------------------------------------------------------------
    # Unit CRUD
    # ------------------------------------------------------------------

    def test_create_unit(self):
        payload = {
            "building": self.data["building"].id,
            "unit": "E2E-201",
            "address_line": "456 Oak Avenue",
            "city": "Mumbai",
            "state": "MH",
            "country": "IN",
            "postal_code": "400050",
            "unit_type": Unit.UnitType.FLAT,
            "status": "vacant",
            "is_vacant": True,
            "rent_amount": "18000.00",
        }
        response = self._post_json(f"{API_PREFIX}/units/", payload, token=self.token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["unit"], "E2E-201")

    def test_list_units(self):
        response = self._get_json(f"{API_PREFIX}/units/", token=self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_unit(self):
        unit = self.data["unit"]
        response = self._patch_json(
            f"{API_PREFIX}/units/{unit.id}/",
            {"status": "occupied", "is_vacant": False},
            token=self.token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        unit.refresh_from_db()
        self.assertEqual(unit.status, "occupied")

    def test_delete_unit(self):
        unit = Unit.objects.create(
            owner=self.owner,
            building=self.data["building"],
            unit="E2E-DEL-101",
            address_line="123 Test",
            city="Test",
            state="TS",
            country="IN",
            postal_code="400001",
            unit_type=Unit.UnitType.FLAT,
        )
        response = self._delete_json(f"{API_PREFIX}/units/{unit.id}/", token=self.token)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_access_other_owner_unit(self):
        other_unit = Unit.objects.create(
            owner=self.other_owner,
            building=self.other_building,
            unit="OTHER-101",
            address_line="Other",
            city="Other",
            state="OT",
            country="IN",
            postal_code="400001",
            unit_type=Unit.UnitType.FLAT,
        )
        response = self._get_json(
            f"{API_PREFIX}/units/{other_unit.id}/", token=self.token
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ------------------------------------------------------------------
    # Renter management
    # ------------------------------------------------------------------

    def test_create_renter(self):
        payload = {
            "unit": self.data["unit"].id,
            "name": "E2E New Renter",
            "phone": "+919876543999",
            "email": "newrenter@test.com",
            "rent_amount": "12000.00",
            "start_date": str(timezone.now().date()),
        }
        response = self._post_json(f"{API_PREFIX}/renters/", payload, token=self.token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "E2E New Renter")

    def test_list_renters(self):
        response = self._get_json(f"{API_PREFIX}/renters/", token=self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_update_renter_status(self):
        renter = self.data["renter"]
        response = self._patch_json(
            f"{API_PREFIX}/renters/{renter.id}/",
            {"status": Renter.RenterStatus.NOTICE_PERIOD},
            token=self.token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        renter.refresh_from_db()
        self.assertEqual(renter.status, Renter.RenterStatus.NOTICE_PERIOD)

    def test_renter_status_transitions(self):
        renter = self.data["renter"]
        for status_val in [
            Renter.RenterStatus.ACTIVE,
            Renter.RenterStatus.NOTICE_PERIOD,
            Renter.RenterStatus.REVOKED,
            Renter.RenterStatus.DEACTIVATED,
        ]:
            with self.subTest(status=status_val):
                response = self._patch_json(
                    f"{API_PREFIX}/renters/{renter.id}/",
                    {"status": status_val},
                    token=self.token,
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_access_other_owner_renter(self):
        other_building = Building.objects.create(
            owner=self.other_owner,
            name="Other Bldg",
            address_line="Other",
            city="Other",
            state="OT",
            country="IN",
            postal_code="400001",
        )
        other_unit = Unit.objects.create(
            owner=self.other_owner,
            building=other_building,
            unit="OTHER-101",
            address_line="Other",
            city="Other",
            state="OT",
            country="IN",
            postal_code="400001",
            unit_type=Unit.UnitType.FLAT,
        )
        other_renter = Renter.objects.create(
            unit=other_unit,
            name="Other Renter",
            phone="+919876543000",
            rent_amount=Decimal("10000.00"),
            start_date=timezone.now().date(),
        )
        response = self._get_json(
            f"{API_PREFIX}/renters/{other_renter.id}/", token=self.token
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ------------------------------------------------------------------
    # Caretaker management
    # ------------------------------------------------------------------

    def test_create_caretaker(self):
        payload = {
            "unit": self.data["unit"].id,
            "name": "E2E Caretaker 2",
            "phone": "+919876543888",
            "email": "caretaker2@test.com",
            "address": "456 Oak Avenue, Mumbai, MH, 400050",
            "joining_date": str(timezone.now().date()),
        }
        response = self._post_json(
            f"{API_PREFIX}/caretakers/", payload, token=self.token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "E2E Caretaker 2")

    def test_list_caretakers(self):
        response = self._get_json(f"{API_PREFIX}/caretakers/", token=self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_cannot_create_caretaker_for_other_owner_unit(self):
        payload = {
            "unit": self.other_unit.id,
            "name": "Hacked Caretaker",
            "phone": "+919876543777",
            "address": "Hacked",
            "joining_date": str(timezone.now().date()),
        }
        response = self._post_json(
            f"{API_PREFIX}/caretakers/", payload, token=self.token
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN],
        )

    # ------------------------------------------------------------------
    # Rent records
    # ------------------------------------------------------------------

    def test_create_rent_record(self):
        payload = {
            "renter": self.data["renter"].id,
            "unit": self.data["unit"].id,
            "due_date": str((timezone.now() + timedelta(days=5)).date().replace(day=5)),
            "amount": "15000.00",
            "payment_method": "upi",
        }
        with patch(
            "properties.views.rent_record_views.create_payment_link",
            return_value="https://payments.test/rent/1",
        ):
            response = self._post_json(
                f"{API_PREFIX}/rent-records/", payload, token=self.token
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_rent_records(self):
        response = self._get_json(f"{API_PREFIX}/rent-records/", token=self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_owner_rent_records_endpoint(self):
        response = self._get_json(f"{API_PREFIX}/owner/rent-records/", token=self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_owner_rent_overview(self):
        response = self._get_json(f"{API_PREFIX}/owner/rents/", token=self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Extra charges
    # ------------------------------------------------------------------

    def test_create_extra_charge(self):
        payload = {
            "name": "E2E Electricity",
            "description": "Monthly electricity",
            "renter": self.data["renter"].id,
            "unit": self.data["unit"].id,
            "amount": "2000.00",
            "due_date": str(timezone.now().date().replace(day=15)),
            "status": ExtraCharge.Status.DUE,
        }
        response = self._post_json(
            f"{API_PREFIX}/extra-charges/", payload, token=self.token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_extra_charges(self):
        response = self._get_json(f"{API_PREFIX}/extra-charges/", token=self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    def test_get_notifications(self):
        Notification.objects.create(
            user=self.owner,
            title="E2E Test",
            message="Test notification",
            notification_type=Notification.SYSTEM_ALERT,
        )
        response = self._get_json(f"{API_PREFIX}/notifications/get/", token=self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.data)
        self.assertIn("meta", response.data)

    def test_unread_count(self):
        response = self._get_json(
            f"{API_PREFIX}/notifications/unread-count/", token=self.token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)

    def test_mark_all_notifications_read(self):
        response = self._post_json(
            f"{API_PREFIX}/notifications/mark-all-read/", token=self.token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_save_device_token(self):
        response = self._post_json(
            f"{API_PREFIX}/notifications/save-token/",
            {
                "token": "e2e-expo-token-12345",
                "platform": "android",
                "device_id": "e2e-device-001",
                "fcm_token": "e2e-fcm-token",
            },
            token=self.token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            DeviceToken.objects.filter(token="e2e-expo-token-12345").exists()
        )

    def test_notification_preferences(self):
        response = self._get_json(
            f"{API_PREFIX}/notifications/preferences/", token=self.token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Profile
    # ------------------------------------------------------------------

    def test_get_profile(self):
        response = self._get_json(f"{API_PREFIX}/auth/profile/", token=self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["username"], self.owner.username)

    def test_update_profile(self):
        response = self._patch_json(
            f"{API_PREFIX}/auth/profile/",
            {"full_name": "Updated E2E Owner Profile"},
            token=self.token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def test_list_subscription_plans(self):
        response = self.client.get(f"{API_PREFIX}/subscription-plans/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_user_subscription(self):
        response = self._get_json(f"{API_PREFIX}/user-subscriptions/", token=self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_usage_limits(self):
        response = self._get_json(f"{API_PREFIX}/usage-limits/", token=self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Search (owner scoped)
    # ------------------------------------------------------------------

    def test_owner_search(self):
        response = self._get_json(f"{API_PREFIX}/search/?q=E2E", token=self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_owner_search_empty(self):
        response = self._get_json(
            f"{API_PREFIX}/search/?q=ZZZNONEXISTENT", token=self.token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Bank details
    # ------------------------------------------------------------------

    def test_update_bank_details(self):
        with (
            patch(
                "core.views.add_beneficiary",
                return_value={"subCode": "200"},
            ),
            patch(
                "core.views.delete_beneficiary",
                return_value={"subCode": "200"},
            ),
        ):
            response = self._post_json(
                f"{API_PREFIX}/owner/update-bank-details/",
                {
                    "account_number": "1234567890",
                    "ifsc_code": "HDFC0001234",
                    "account_holder_name": self.owner.full_name,
                },
                token=self.token,
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(OwnerBankDetails.objects.filter(owner=self.owner).exists())
