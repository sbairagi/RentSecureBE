"""Tests for check_vacant_units management command."""

from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from core.models import User
from management.commands.check_vacant_units import Command
from properties.models import Building, Unit


class CheckVacantUnitsTests(TestCase):
    def setUp(self):
        self.command = Command()
        self.owner = User.objects.create_user(
            username="vacancy_cmd_owner",
            password="p",
            full_name="VacancyCmdOwner",
            phone="+1",
            email="cmd@test.com",
            whatsapp_number="+919876543210",
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="VacancyCmdB",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="VC1",
            unit_type="flat",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )

    def test_skips_when_no_vacant_units(self):
        Unit.objects.update(is_vacant=False)
        with patch.object(Command, "_send_whatsapp_alert") as mock_whatsapp:
            with patch.object(Command, "_send_email_alert") as mock_email:
                self.command.handle()
        mock_whatsapp.assert_not_called()
        mock_email.assert_not_called()

    def test_sends_7_day_vacancy_alert_with_suggestions(self):
        self.unit.is_vacant = True
        self.unit.last_vacated_at = timezone.now().date() - timedelta(days=10)
        self.unit.save(update_fields=["is_vacant", "last_vacated_at"])

        with patch.object(Command, "_send_whatsapp_alert") as mock_whatsapp:
            self.command.handle()

        mock_whatsapp.assert_called_once()
        call_args = mock_whatsapp.call_args[0][1]
        self.assertIn("Vacancy Alert", call_args)
        self.assertIn("Add a new renter", call_args)

    def test_skips_units_vacant_less_than_7_days(self):
        self.unit.is_vacant = True
        self.unit.last_vacated_at = timezone.now().date() - timedelta(days=3)
        self.unit.save(update_fields=["is_vacant", "last_vacated_at"])

        with patch.object(Command, "_send_whatsapp_alert") as mock_whatsapp:
            self.command.handle()

        mock_whatsapp.assert_not_called()

    def test_sends_30_day_long_term_alert(self):
        self.unit.is_vacant = True
        self.unit.last_vacated_at = timezone.now().date() - timedelta(days=45)
        self.unit.save(update_fields=["is_vacant", "last_vacated_at"])

        with patch.object(Command, "_send_whatsapp_alert") as mock_whatsapp:
            self.command.handle()

        mock_whatsapp.assert_called_once()
        call_args = mock_whatsapp.call_args[0][1]
        self.assertIn("Long-term vacancy", call_args)
