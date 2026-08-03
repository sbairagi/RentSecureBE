"""Tests for rent_monitor_service and auto_flag_defaulters command."""

from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from properties.management.commands.auto_flag_defaulters import Command
from properties.models import Building, Renter, RentRecord, Unit
from properties.services.rent_monitor_service import check_renter_defaulter_status

User = get_user_model()


class RentMonitorServiceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="monitor_owner",
            password="p",
            full_name="MonitorOwner",
            phone="+1",
            email="monitor_owner@test.com",
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="MonitorB",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="M1",
            unit_type="flat",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        self.renter_user = User.objects.create_user(
            username="monitor_renter",
            password="p",
            full_name="MonitorRenter",
            phone="+1",
            email="renter@test.com",
            whatsapp_number="+919876543210",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            user=self.renter_user,
            name="TestRenter",
            phone="+911234567890",
            email="renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
        )

    def _create_pending_rent(self, days_ago: int):
        return RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("10000"),
            due_date=timezone.now().date() - timezone.timedelta(days=days_ago),
            status=RentRecord.Status.PENDING,
            payout_status="PENDING",
        )

    def test_marks_notice_period_at_two_missed(self):
        self._create_pending_rent(1)
        self._create_pending_rent(2)

        updated = check_renter_defaulter_status()
        self.assertEqual(updated, 1)
        self.renter.refresh_from_db()
        self.assertEqual(self.renter.status, Renter.RenterStatus.NOTICE_PERIOD)
        self.assertTrue(self.renter.is_flagged)

    def test_revokes_at_three_missed(self):
        self._create_pending_rent(1)
        self._create_pending_rent(2)
        self._create_pending_rent(3)

        updated = check_renter_defaulter_status()
        self.assertEqual(updated, 1)
        self.renter.refresh_from_db()
        self.assertEqual(self.renter.status, Renter.RenterStatus.REVOKED)
        self.assertTrue(self.renter.is_agreement_revoked)

    def test_skips_already_revoked_renter(self):
        self._create_pending_rent(1)
        self._create_pending_rent(2)
        self._create_pending_rent(3)
        self.renter.status = Renter.RenterStatus.REVOKED
        self.renter.save(update_fields=["status"])

        updated = check_renter_defaulter_status()
        self.assertEqual(updated, 0)

    @patch("properties.services.rent_monitor_service._notify_all_parties")
    def test_notifies_on_revoke(self, mock_notify):
        self._create_pending_rent(1)
        self._create_pending_rent(2)
        self._create_pending_rent(3)

        check_renter_defaulter_status()
        mock_notify.assert_called_once()

    @patch("properties.services.rent_monitor_service._notify_all_parties")
    def test_notifies_on_notice_period(self, mock_notify):
        self._create_pending_rent(1)
        self._create_pending_rent(2)

        check_renter_defaulter_status()
        mock_notify.assert_called_once()


class AutoFlagDefaultersCommandTests(TestCase):
    def test_command_runs(self):
        from io import StringIO

        command = Command()
        out = StringIO()
        command.stdout = out
        command.handle()
        output = out.getvalue()
        self.assertIn("Checked renter default status", output)
