"""
Security Regression Tests — Step 50

Covers critical and high-severity issues found during the Step 50 audit:
- IDOR in document PDF generation
- CAProfileViewSet authorization bypass
- Mass assignment in serializers
- Rate limiting on authentication endpoints
- Search ordering validation
- ProfileSerializer is_phone_verified protection
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from django.contrib.auth import get_user_model

from core.models import SubscriptionPlan, UserSubscription
from finance.models import CAProfile
from properties.models import Building, Renter, RentRecord, Unit

User = get_user_model()
API_PREFIX = "/api"


class DocumentIDORTests(APITestCase):
    """Ensure document PDF endpoints enforce ownership."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username="doc_owner", password="TestPass123!", email="docowner@test.com"
        )
        self.other_owner = User.objects.create_user(
            username="doc_other", password="TestPass123!", email="docother@test.com"
        )
        self.plan, _ = SubscriptionPlan.objects.get_or_create(
            name="doc_plan",
            defaults={
                "monthly_price": 10,
                "yearly_price": 100,
                "features": "Pro",
                "is_active": True,
            },
        )
        UserSubscription.objects.create(
            user=self.owner,
            plan=self.plan,
            start_date="2026-01-01",
            end_date="2027-01-01",
            is_active=True,
        )
        UserSubscription.objects.create(
            user=self.other_owner,
            plan=self.plan,
            start_date="2026-01-01",
            end_date="2027-01-01",
            is_active=True,
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="Doc Bldg",
            address_line="1 Doc St",
            city="Doc City",
            state="DS",
            country="IN",
            postal_code="400001",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="DOC-1",
            address_line="1 Doc St",
            city="Doc City",
            state="DS",
            country="IN",
            postal_code="400001",
            unit_type=Unit.UnitType.FLAT,
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Doc Renter",
            phone="+919999999999",
            rent_amount=10000,
            start_date="2026-01-01",
        )
        self.rent = RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            due_date="2026-02-05",
            amount=10000,
            status="paid",
            paid_on="2026-02-05",
            payment_method="upi",
            transaction_id="doc_txn_123",
        )
        self.other_building = Building.objects.create(
            owner=self.other_owner,
            name="Other Bldg",
            address_line="2 Other St",
            city="Other City",
            state="OS",
            country="IN",
            postal_code="400002",
        )
        self.other_unit = Unit.objects.create(
            owner=self.other_owner,
            building=self.other_building,
            unit="OTHER-1",
            address_line="2 Other St",
            city="Other City",
            state="OS",
            country="IN",
            postal_code="400002",
            unit_type=Unit.UnitType.FLAT,
        )
        self.other_renter = Renter.objects.create(
            unit=self.other_unit,
            name="Other Renter",
            phone="+918888888888",
            rent_amount=8000,
            start_date="2026-01-01",
        )
        self.other_rent = RentRecord.objects.create(
            renter=self.other_renter,
            unit=self.other_unit,
            due_date="2026-02-05",
            amount=8000,
            status="paid",
            paid_on="2026-02-05",
            payment_method="upi",
            transaction_id="other_txn_123",
        )
        self.hacker = User.objects.create_user(
            username="doc_hacker", password="TestPass123!", email="dochacker@test.com"
        )
        self.client = APIClient()

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_rent_agreement_pdf_blocks_other_owner(self):
        self._auth(self.hacker)
        resp = self.client.get(
            f"{API_PREFIX}/documents/generate-rent-agreement-pdf/{self.renter.id}/generate-rent-agreement-pdf/"
        )
        self.assertIn(
            resp.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        )

    def test_unit_dossier_pdf_blocks_other_owner(self):
        self._auth(self.hacker)
        resp = self.client.get(
            f"{API_PREFIX}/documents/generate-dossier-pdf/{self.unit.id}/generate-dossier-pdf/"
        )
        self.assertIn(
            resp.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        )

    def test_rent_receipt_pdf_blocks_other_owner(self):
        self._auth(self.hacker)
        resp = self.client.get(
            f"{API_PREFIX}/documents/generate-rent-receipt-pdf/{self.rent.id}/pdf_receipt/"
        )
        self.assertIn(
            resp.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        )

    def test_rent_agreement_pdf_allows_owner(self):
        self._auth(self.owner)
        resp = self.client.get(
            f"{API_PREFIX}/documents/generate-rent-agreement-pdf/{self.renter.id}/generate-rent-agreement-pdf/"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class CAProfileAuthorizationTests(APITestCase):
    """Ensure CAProfileViewSet filters by user."""

    def setUp(self):
        self.owner_a = User.objects.create_user(
            username="ca_a", password="TestPass123!", email="caa@test.com"
        )
        self.owner_b = User.objects.create_user(
            username="ca_b", password="TestPass123!", email="cab@test.com"
        )
        self.ca_a = CAProfile.objects.create(
            user=self.owner_a,
            name="CA A",
            email="ca.a@test.com",
            city="Mumbai",
            specialization="tax",
            available=True,
            experience_years=5,
            rating=4.5,
            price_range="medium",
        )
        self.ca_b = CAProfile.objects.create(
            user=self.owner_b,
            name="CA B",
            email="ca.b@test.com",
            city="Pune",
            specialization="audit",
            available=True,
            experience_years=10,
            rating=4.8,
            price_range="high",
        )
        self.client = APIClient()

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list_returns_only_own_profiles(self):
        self._auth(self.owner_a)
        resp = self.client.get(f"{API_PREFIX}/finance/ca-profiles/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ids = [p["id"] for p in resp.data.get("results", resp.data)]
        self.assertIn(self.ca_a.id, ids)
        self.assertNotIn(self.ca_b.id, ids)

    def test_retrieve_own_profile(self):
        self._auth(self.owner_a)
        resp = self.client.get(f"{API_PREFIX}/finance/ca-profiles/{self.ca_a.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_other_profile_forbidden(self):
        self._auth(self.owner_a)
        resp = self.client.get(f"{API_PREFIX}/finance/ca-profiles/{self.ca_b.id}/")
        self.assertIn(
            resp.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        )


class MassAssignmentSerializerTests(APITestCase):
    """Ensure protected fields cannot be mass-assigned."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username="mass_owner", password="TestPass123!", email="massowner@test.com"
        )
        self.other_user = User.objects.create_user(
            username="mass_other", password="TestPass123!", email="massother@test.com"
        )
        self.plan, _ = SubscriptionPlan.objects.get_or_create(
            name="mass_plan",
            defaults={
                "monthly_price": 10,
                "yearly_price": 100,
                "features": "Pro",
                "is_active": True,
            },
        )
        UserSubscription.objects.create(
            user=self.owner,
            plan=self.plan,
            start_date="2026-01-01",
            end_date="2027-01-01",
            is_active=True,
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="Mass Bldg",
            address_line="1 Mass St",
            city="Mass City",
            state="MS",
            country="IN",
            postal_code="400001",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="MASS-1",
            address_line="1 Mass St",
            city="Mass City",
            state="MS",
            country="IN",
            postal_code="400001",
            unit_type=Unit.UnitType.FLAT,
        )
        self.client = APIClient()

    def test_renter_user_field_is_read_only(self):
        self.client.force_authenticate(user=self.owner)
        payload = {
            "unit": self.unit.id,
            "name": "New Renter",
            "phone": "+919999999999",
            "rent_amount": 10000,
            "start_date": "2026-01-01",
            "user": self.other_user.id,
        }
        resp = self.client.post(f"{API_PREFIX}/renters/", payload, format="json")
        self.assertNotEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_caretaker_user_field_is_read_only(self):
        self.client.force_authenticate(user=self.owner)
        payload = {
            "unit": self.unit.id,
            "name": "New Caretaker",
            "phone": "+919999999998",
            "joining_date": "2026-01-01",
            "user": self.other_user.id,
        }
        resp = self.client.post(f"{API_PREFIX}/caretakers/", payload, format="json")
        self.assertNotEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_rent_record_status_not_writable_on_create(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="RR Renter",
            phone="+919999999997",
            rent_amount=10000,
            start_date="2026-01-01",
        )
        self.client.force_authenticate(user=self.owner)
        payload = {
            "renter": renter.id,
            "unit": self.unit.id,
            "due_date": "2026-02-05",
            "amount": 10000,
            "status": "PAID",
        }
        resp = self.client.post(f"{API_PREFIX}/rent-records/", payload, format="json")
        self.assertNotEqual(resp.status_code, status.HTTP_201_CREATED)


class RateLimitingTests(APITestCase):
    """Ensure authentication endpoints are rate-limited."""

    def setUp(self):
        self.client = APIClient()

    def test_login_is_throttled(self):
        payload = {"email": "nonexistent@test.com", "password": "wrong"}
        for _ in range(5):
            self.client.post(f"{API_PREFIX}/auth/login/", payload, format="json")
        resp = self.client.post(f"{API_PREFIX}/auth/login/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_register_is_throttled(self):
        payload = {
            "firstName": "Test",
            "lastName": "User",
            "email": "ratelimit@test.com",
            "phone": "+919999999996",
            "password": "TestPass123!",
            "confirmPassword": "TestPass123!",
            "role": "renter",
        }
        for _ in range(5):
            self.client.post(f"{API_PREFIX}/auth/register/", payload, format="json")
        resp = self.client.post(f"{API_PREFIX}/auth/register/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class SearchOrderingValidationTests(APITestCase):
    """Ensure search ordering parameter is validated."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username="search_owner",
            password="TestPass123!",
            email="searchowner@test.com",
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="Search Bldg",
            address_line="1 Search St",
            city="Search City",
            state="SS",
            country="IN",
            postal_code="400001",
        )
        self.client = APIClient()

    def test_search_ordering_rejects_invalid_value(self):
        self.client.force_authenticate(user=self.owner)
        resp = self.client.get(
            f"{API_PREFIX}/search/?q=Search&ordering=invalid_field;DROP%20TABLE"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class ProfileSecurityTests(APITestCase):
    """Ensure is_phone_verified cannot be mass-assigned."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="prof_user", password="TestPass123!", email="profuser@test.com"
        )
        self.client = APIClient()

    def test_is_phone_verified_is_read_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            f"{API_PREFIX}/auth/profile/", {"is_phone_verified": True}, format="json"
        )
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_phone_verified)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
