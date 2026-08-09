from datetime import date

from rest_framework.test import APIClient

from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import User
from properties.models import (
    Building,
    Caretaker,
    RentAgreementDraft,
    Renter,
    RentRecord,
    Unit,
)


@override_settings(REST_FRAMEWORK={"DEFAULT_AUTHENTICATION_CLASSES": []})
class GlobalSearchAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username="owner",
            password="testpass123",
            full_name="Test Owner",
        )
        self.other_owner = User.objects.create_user(
            username="other",
            password="testpass123",
            full_name="Other Owner",
        )
        self.building = Building.objects.create(
            name="Sunshine Complex",
            address_line="123 Main St",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400001",
            owner=self.owner,
        )
        self.unit = Unit.objects.create(
            unit="101",
            building=self.building,
            building_name="Sunshine Complex",
            address_line="123 Main St",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400001",
            owner=self.owner,
            status=Unit.VacancyStatus.OCCUPIED,
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Test Renter",
            phone="+919999999999",
            email="renter@example.com",
            rent_amount=5000,
            start_date=date(2024, 1, 1),
            status=Renter.RenterStatus.ACTIVE,
        )
        self.caretaker = Caretaker.objects.create(
            unit=self.unit,
            name="Test Caretaker",
            phone="+919999999998",
            email="caretaker@example.com",
            joining_date=date(2024, 1, 1),
            is_active=True,
        )
        self.rent_record = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=5000,
            payment_method="online",
            status=RentRecord.Status.PAID,
            due_date=date(2024, 5, 1),
        )
        self.agreement = RentAgreementDraft.objects.create(
            user=self.owner,
            renter=self.renter,
            unit=self.unit,
        )

    def test_search_requires_auth(self):
        url = reverse("search:global-search")
        response = self.client.get(url, {"q": "test"})
        self.assertIn(response.status_code, [401, 403])

    def test_empty_query_returns_available_types(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse("search:global-search")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data["total_results"], 0)
        self.assertIn("buildings", data["available_resource_types"])

    def test_search_buildings(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse("search:global-search")
        response = self.client.get(url, {"q": "Sunshine"})
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertGreaterEqual(data["total_results"], 1)
        types = [r["resource_type"] for r in data["results"]]
        self.assertIn("buildings", types)

    def test_search_does_not_leak_other_owners(self):
        self.client.force_authenticate(user=self.other_owner)
        url = reverse("search:global-search")
        response = self.client.get(url, {"q": "Sunshine"})
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data["total_results"], 0)

    def test_search_suggestions(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse("search:search-suggestions")
        response = self.client.get(url, {"q": "Sun"})
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn("Sunshine Complex", data["suggestions"])

    def test_search_suggestions_min_length(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse("search:search-suggestions")
        response = self.client.get(url, {"q": "S"})
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data["suggestions"], [])

    def test_search_pagination(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse("search:global-search")
        response = self.client.get(url, {"q": "Test", "page": 1, "page_size": 1})
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(len(data["results"]), 1)
        self.assertGreaterEqual(data["total_pages"], 1)

    def test_search_resource_type_filter(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse("search:global-search")
        response = self.client.get(url, {"q": "Test", "resource_type": "buildings"})
        self.assertEqual(response.status_code, 200)
        data = response.data
        for result in data["results"]:
            self.assertEqual(result["resource_type"], "buildings")
