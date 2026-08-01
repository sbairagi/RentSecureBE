"""Tests for vacancy alert system."""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from core.models import User
from properties.models import Building, Unit
from properties.services.vacancy_service import (
    build_vacancy_report,
    detect_vacant_units,
    get_vacancy_suggestions,
)


class VacancyServiceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="vacancy_owner",
            password="p",
            full_name="VacancyOwner",
            phone="+1",
            email="vacancy@test.com",
            whatsapp_number="+919876543210",
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="VacancyB",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="V1",
            unit_type="flat",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )

    def test_get_vacancy_suggestions_returns_add_renter(self):
        suggestions = get_vacancy_suggestions(self.unit, 1)
        self.assertIn("📋 Add a new renter from your dashboard", suggestions)

    def test_get_vacancy_suggestions_includes_marketplace_for_7_days(self):
        suggestions = get_vacancy_suggestions(self.unit, 7)
        self.assertIn(
            "📢 Consider posting this unit on rental marketplaces", suggestions
        )

    def test_get_vacancy_suggestions_includes_pricing_for_30_days(self):
        suggestions = get_vacancy_suggestions(self.unit, 30)
        self.assertIn(
            "💰 Review pricing or offer limited-time discounts to attract tenants",
            suggestions,
        )

    def test_detect_vacant_units_returns_vacant_units(self):
        self.unit.is_vacant = True
        self.unit.last_vacated_at = timezone.now().date()
        self.unit.save(update_fields=["is_vacant", "last_vacated_at"])

        vacant = detect_vacant_units()
        self.assertEqual(vacant.count(), 1)

    def test_build_vacancy_report_groups_by_duration(self):
        self.unit.is_vacant = True
        self.unit.last_vacated_at = timezone.now().date() - timedelta(days=10)
        self.unit.save(update_fields=["is_vacant", "last_vacated_at"])

        report = build_vacancy_report()
        self.assertEqual(report["total_vacant_units"], 1)
        self.assertEqual(len(report["recent_vacancies"]), 1)
        self.assertEqual(len(report["long_term_vacancies"]), 0)

    def test_build_vacancy_report_groups_long_term(self):
        self.unit.is_vacant = True
        self.unit.last_vacated_at = timezone.now().date() - timedelta(days=45)
        self.unit.save(update_fields=["is_vacant", "last_vacated_at"])

        report = build_vacancy_report()
        self.assertEqual(report["total_vacant_units"], 1)
        self.assertEqual(len(report["recent_vacancies"]), 0)
        self.assertEqual(len(report["long_term_vacancies"]), 1)

    def test_build_vacancy_report_filters_by_owner(self):
        other_owner = User.objects.create_user(
            username="other_owner",
            password="p",
            full_name="OtherOwner",
            phone="+1",
        )
        other_building = Building.objects.create(
            owner=other_owner,
            name="OtherB",
            address_line="1 Other St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        other_unit = Unit.objects.create(
            owner=other_owner,
            building=other_building,
            unit="O1",
            unit_type="flat",
            address_line="1 Other St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        other_unit.is_vacant = True
        other_unit.last_vacated_at = timezone.now().date() - timedelta(days=10)
        other_unit.save(update_fields=["is_vacant", "last_vacated_at"])

        self.unit.is_vacant = True
        self.unit.last_vacated_at = timezone.now().date() - timedelta(days=10)
        self.unit.save(update_fields=["is_vacant", "last_vacated_at"])

        report = build_vacancy_report(owner=self.owner)
        self.assertEqual(report["total_vacant_units"], 1)
        self.assertEqual(report["recent_vacancies"][0]["unit_id"], self.unit.pk)
