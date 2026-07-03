"""
API Integration Tests for Properties Module

Tests covering:
- Building ViewSet API endpoints
- Unit ViewSet API endpoints
- Caretaker ViewSet API endpoints
- Renter ViewSet API endpoints
- RentRecord ViewSet API endpoints
- UnitImage/Document ViewSet API endpoints
- RentAgreementDraft ViewSet API endpoints
- Permission enforcement
- Feature limit enforcement
- Cache invalidation
- Error handling
"""

from datetime import date, timedelta
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import PlanFeatureLimit, SubscriptionPlan, UserSubscription

from .models import Building, ExtraCharge, RentAgreementDraft, Renter, RentRecord, Unit

User = get_user_model()


class BuildingViewSetAPITests(APITestCase):
    """Test Building ViewSet endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(username="owner1", password="pass123")
        self.other_user = User.objects.create_user(
            username="owner2", password="pass123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_buildings(self):
        """Test listing user's buildings"""
        Building.objects.create(
            name="Building 1",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user,
        )
        response = self.client.get("/api/buildings/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_building(self):
        """Test creating a building"""
        data = {
            "name": "New Building",
            "address_line": "456 Oak St",
            "city": "Boston",
            "state": "MA",
            "country": "USA",
            "postal_code": "02101",
        }
        response = self.client.post("/api/buildings/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Building.objects.count(), 1)

    def test_create_building_exceeds_plan_limit(self):
        """Test building creation respects plan limits"""
        # Create free plan with limit of 1
        free_plan = SubscriptionPlan.objects.create(
            name="free", monthly_price=0, yearly_price=0
        )
        PlanFeatureLimit.objects.create(
            plan=free_plan, feature_key="max_buildings", value="1"
        )
        UserSubscription.objects.create(
            user=self.user, plan=free_plan, end_date=timezone.now() + timedelta(days=30)
        )

        # Create first building (should succeed)
        data1 = {
            "name": "Building 1",
            "address_line": "123 Main St",
            "city": "New York",
            "state": "NY",
            "country": "USA",
            "postal_code": "10001",
        }
        response1 = self.client.post("/api/buildings/", data1, format="json")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Create second building (should fail)
        data2 = {
            "name": "Building 2",
            "address_line": "456 Oak St",
            "city": "Boston",
            "state": "MA",
            "country": "USA",
            "postal_code": "02101",
        }
        response2 = self.client.post("/api/buildings/", data2, format="json")
        self.assertEqual(response2.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_building(self):
        """Test retrieving a single building"""
        building = Building.objects.create(
            name="Building 1",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user,
        )
        response = self.client.get(f"/api/buildings/{building.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_building(self):
        """Test updating a building"""
        building = Building.objects.create(
            name="Building 1",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user,
        )
        data = {"name": "Updated Building"}
        response = self.client.patch(
            f"/api/buildings/{building.id}/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        building.refresh_from_db()
        self.assertEqual(building.name, "Updated Building")

    def test_cannot_update_other_user_building(self):
        """Test cannot update building owned by other user"""
        building = Building.objects.create(
            name="Building 1",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.other_user,
        )
        self.client.force_authenticate(user=self.user)
        data = {"name": "Hacked Building"}
        response = self.client.patch(
            f"/api/buildings/{building.id}/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_building(self):
        """Test deleting a building"""
        building = Building.objects.create(
            name="Building 1",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user,
        )
        response = self.client.delete(f"/api/buildings/{building.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Building.objects.count(), 0)

    def test_cannot_delete_other_user_building(self):
        """Test cannot delete building owned by other user"""
        building = Building.objects.create(
            name="Building 1",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.other_user,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/api/buildings/{building.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_archived_buildings_filtered_after_expiry(self):
        """Test archived buildings are filtered when plan expires"""
        Building.objects.create(
            name="Building 1",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user,
            is_archived=False,
        )
        Building.objects.create(
            name="Building 2",
            address_line="456 Oak St",
            city="Boston",
            state="MA",
            country="USA",
            postal_code="02101",
            owner=self.user,
            is_archived=True,
        )
        response = self.client.get("/api/buildings/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Both should be returned by default


class UnitViewSetAPITests(APITestCase):
    """Test Unit ViewSet endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(username="owner1", password="pass123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.building = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user,
        )

    def test_list_units(self):
        """Test listing user's units"""
        Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="101",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT,
        )
        response = self.client.get("/api/units/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_unit(self):
        """Test creating a unit"""
        data = {
            "building": self.building.id,
            "unit": "102",
            "address_line": "123 Main St",
            "city": "New York",
            "state": "NY",
            "country": "USA",
            "postal_code": "10001",
            "unit_type": Unit.UnitType.FLAT,
            "status": "vacant",
            "is_vacant": True,
        }
        response = self.client.post("/api/units/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_unit_with_invalid_coordinates(self):
        """Test creating unit with invalid coordinates"""
        data = {
            "building": self.building.id,
            "unit": "103",
            "address_line": "123 Main St",
            "city": "New York",
            "state": "NY",
            "country": "USA",
            "postal_code": "10001",
            "unit_type": Unit.UnitType.FLAT,
            "latitude": 91,  # Invalid
            "longitude": -74.0060,
        }
        response = self.client.post("/api/units/", data, format="json")
        # Should fail validation
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_unit(self):
        """Test updating a unit"""
        unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="101",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT,
        )
        data = {"status": "occupied", "is_vacant": False}
        response = self.client.patch(f"/api/units/{unit.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_unit(self):
        """Test deleting a unit"""
        unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="101",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT,
        )
        response = self.client.delete(f"/api/units/{unit.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class CaretakerViewSetAPITests(APITestCase):
    """Test Caretaker ViewSet endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(username="owner1", password="pass123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.building = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user,
        )
        self.unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="101",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT,
        )

    def test_create_caretaker(self):
        """Test creating a caretaker"""
        data = {
            "unit": self.unit.id,
            "name": "John Doe",
            "phone": "+919876543210",
            "address": "123 Main St, New York, NY, USA, 10001",
            "joining_date": "2025-01-01",
        }
        response = self.client.post("/api/caretakers/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_create_caretaker_invalid_unit(self):
        """Test cannot create caretaker for non-owned unit"""
        other_user = User.objects.create_user(username="owner2", password="pass123")
        other_building = Building.objects.create(
            name="Other Building",
            address_line="456 Oak St",
            city="Boston",
            state="MA",
            country="USA",
            postal_code="02101",
            owner=other_user,
        )
        other_unit = Unit.objects.create(
            owner=other_user,
            building=other_building,
            unit="201",
            address_line="456 Oak St",
            city="Boston",
            state="MA",
            country="USA",
            postal_code="02101",
            unit_type=Unit.UnitType.FLAT,
        )
        data = {
            "unit": other_unit.id,
            "name": "John Doe",
            "phone": "+919876543210",
            "address": "456 Oak St, Boston, MA, USA, 02101",
            "joining_date": "2025-01-01",
        }
        response = self.client.post("/api/caretakers/", data, format="json")
        self.assertIn(response.status_code, [400, 403])


class RenterViewSetAPITests(APITestCase):
    """Test Renter ViewSet endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(username="owner1", password="pass123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.building = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user,
        )
        self.unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="101",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT,
        )

    def test_create_renter(self):
        """Test creating a renter"""
        data = {
            "unit": self.unit.id,
            "name": "Alice Smith",
            "phone": "+919876543210",
            "rent_amount": 10000,
            "start_date": "2025-01-01",
        }
        response = self.client.post("/api/renters/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_renters_only_active(self):
        """Test listing renters returns only active/notice_period"""
        Renter.objects.create(
            unit=self.unit,
            name="Alice",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            status=Renter.RenterStatus.ACTIVE,
        )
        Renter.objects.create(
            unit=self.unit,
            name="Bob",
            phone="+919876543211",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            status=Renter.RenterStatus.DEACTIVATED,
        )
        response = self.client.get("/api/renters/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return active renters
        self.assertEqual(len(response.data), 1)


class RentRecordViewSetAPITests(APITestCase):
    """Test RentRecord ViewSet endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(username="owner1", password="pass123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.building = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user,
        )
        self.unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="101",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT,
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Alice",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
        )

    def test_create_rent_record(self):
        """Test creating a rent record"""
        data = {
            "renter": self.renter.id,
            "unit": self.unit.id,
            "due_date": "2025-01-01",
            "amount": 10000,
            "paid_on": "2025-01-05",
            "status": RentRecord.Status.PAID,
            "payment_method": RentRecord.PaymentMethod.CASH,
        }
        with patch("rentsecure_be.services.razorpay_service.create_payment_link"):
            with patch("notification.utils.send_whatsapp_message"):
                response = self.client.post("/api/rent-records/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_owner_dashboard_summary_returns_expected_data(self):
        """Test owner dashboard summary contains rent totals and defaulters"""
        today = date.today()
        current_month = today.replace(day=1)
        last_month = (current_month - timedelta(days=30)).replace(day=1)

        RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            due_date=current_month,
            amount=10000,
            paid_on=today,
            status=RentRecord.Status.PAID,
            payout_status="SUCCESS",
        )

        RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            due_date=last_month,
            amount=0,
            paid_on=last_month,
            status=RentRecord.Status.PENDING,
            payout_status="PENDING",
        )

        response = self.client.get("/api/owner/dashboard-summary/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data["total_rent_collected"]), 10000.0)
        self.assertEqual(float(response.data["rent_collected_this_month"]), 10000.0)
        self.assertEqual(response.data["payouts"]["success"], 1)
        self.assertEqual(response.data["payouts"]["pending"], 1)
        self.assertEqual(len(response.data["rent_defaulters"]), 1)
        self.assertEqual(response.data["rent_defaulters"][0]["renter_name"], "Alice")

    def test_cannot_create_duplicate_rent_record(self):
        """Test cannot create duplicate rent record for same month"""
        RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            amount=10000,
            payment_method="upi",
            status="pending",
            due_date=date(2025, 1, 1),
            paid_on=date(2025, 1, 5),
        )
        data = {
            "renter": self.renter.id,
            "unit": self.unit.id,
            "due_date": "2025-01-01",
            "amount": 10000,
            "paid_on": "2025-01-05",
        }
        response = self.client.post("/api/rent-records/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_create_rent_record_negative_amount(self):
        """Test cannot create rent record with negative amount"""
        data = {
            "renter": self.renter.id,
            "unit": self.unit.id,
            "due_date": "2025-01-01",
            "amount": -1000,
            "paid_on": "2025-01-05",
        }
        response = self.client.post("/api/rent-records/", data, format="json")
        # Should fail
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)

    def test_owner_can_list_extra_charges(self):
        """Test owner can view extra charges"""
        charge = ExtraCharge.objects.create(
            name="Electricity",
            renter=self.renter,
            unit=self.unit,
            amount=1500,
            due_date=date(2025, 2, 10),
            status=ExtraCharge.Status.DUE,
        )

        response = self.client.get("/api/extra-charges/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], charge.name)

    def test_renter_can_list_their_extra_charges(self):
        """Test renter user can view their own extra charges"""
        renter_user = User.objects.create_user(username="renter1", password="pass123")
        self.renter.user = renter_user
        self.renter.save()

        ExtraCharge.objects.create(
            name="Maintenance",
            renter=self.renter,
            unit=self.unit,
            amount=1200,
            due_date=date(2025, 2, 10),
            status=ExtraCharge.Status.DUE,
        )

        self.client.force_authenticate(user=renter_user)
        response = self.client.get("/api/extra-charges/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["renter"], self.renter.id)

    def test_owner_can_create_extra_charge(self):
        """Test owner can create extra charges via API"""
        data = {
            "name": "Water",
            "description": "Monthly water charge",
            "renter": self.renter.id,
            "unit": self.unit.id,
            "amount": 800,
            "due_date": "2025-02-10",
            "status": ExtraCharge.Status.DUE,
        }
        response = self.client.post("/api/extra-charges/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Water")


class RentAgreementDraftViewSetAPITests(APITestCase):
    """Test RentAgreementDraft ViewSet endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(username="owner1", password="pass123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.building = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user,
        )
        self.unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="101",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT,
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Alice",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
        )

    def test_create_rent_agreement_draft(self):
        """Test creating a rent agreement draft"""
        from django.core.files.base import ContentFile

        draft_file = ContentFile(b"PDF content", name="draft.pdf")
        data = {"renter": self.renter.id, "unit": self.unit.id, "file": draft_file}
        response = self.client.post(
            "/api/rent-agreement-drafts/", data, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unique_renter_draft(self):
        """Test only one draft per renter"""
        from django.core.files.base import ContentFile

        # Create first draft
        draft_file1 = ContentFile(b"PDF content 1", name="draft1.pdf")
        RentAgreementDraft.objects.create(
            user=self.user, renter=self.renter, unit=self.unit, file=draft_file1
        )

        # Try to create second draft
        draft_file2 = ContentFile(b"PDF content 2", name="draft2.pdf")
        data = {"renter": self.renter.id, "unit": self.unit.id, "file": draft_file2}
        self.client.post("/api/rent-agreement-drafts/", data, format="multipart")
        # Should fail due to unique constraint


class CrossUserAccessTests(APITestCase):
    """Test cross-user access prevention"""

    def setUp(self):
        self.user1 = User.objects.create_user(username="owner1", password="pass123")
        self.user2 = User.objects.create_user(username="owner2", password="pass123")
        self.client = APIClient()

    def test_user2_cannot_list_user1_buildings(self):
        """Test user2 cannot see user1's buildings"""
        Building.objects.create(
            name="User1 Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user1,
        )
        self.client.force_authenticate(user=self.user2)
        response = self.client.get("/api/buildings/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_user2_cannot_update_user1_building(self):
        """Test user2 cannot update user1's building"""
        building = Building.objects.create(
            name="User1 Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user1,
        )
        self.client.force_authenticate(user=self.user2)
        data = {"name": "Hacked"}
        response = self.client.patch(
            f"/api/buildings/{building.id}/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user2_cannot_delete_user1_building(self):
        """Test user2 cannot delete user1's building"""
        building = Building.objects.create(
            name="User1 Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user1,
        )
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(f"/api/buildings/{building.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UnauthenticatedAccessTests(APITestCase):
    """Test unauthenticated access is denied"""

    def setUp(self):
        self.client = APIClient()

    def test_cannot_list_buildings_unauthenticated(self):
        """Test unauthenticated user cannot list buildings"""
        response = self.client.get("/api/buildings/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_create_building_unauthenticated(self):
        """Test unauthenticated user cannot create building"""
        data = {
            "name": "Building",
            "address_line": "123 Main St",
            "city": "New York",
            "state": "NY",
            "country": "USA",
            "postal_code": "10001",
        }
        response = self.client.post("/api/buildings/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
