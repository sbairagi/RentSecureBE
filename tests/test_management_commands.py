"""Tests for management commands."""

from io import StringIO
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from notification.management.commands.send_extra_charge_reminders import (
    Command as ExtraChargeRemindersCommand,
)
from properties.management.commands.generate_monthly_extra_charges import (
    Command as GenerateExtraChargesCommand,
)
from properties.management.commands.send_monthly_rent_summary import (
    Command as SendMonthlyRentSummaryCommand,
)

User = get_user_model()


class SendMonthlyRentSummaryCommandTest(TestCase):
    def test_no_owners(self):
        cmd = SendMonthlyRentSummaryCommand()
        out = StringIO()
        cmd.stdout = out
        cmd._send_to_all_owners(send_whatsapp=True)
        self.assertIn("No property owners found", out.getvalue())

    def test_single_user_not_found(self):
        cmd = SendMonthlyRentSummaryCommand()
        out = StringIO()
        cmd.stdout = out
        cmd._send_to_single_user(user_id=9999, send_whatsapp=True)
        self.assertIn("not found", out.getvalue())

    def test_single_user_success(self):
        owner = User.objects.create_user(
            username="summary_owner",
            email="so@test.com",
            password="p",
            full_name="Summary Owner",
            phone="+91",
        )
        cmd = SendMonthlyRentSummaryCommand()
        out = StringIO()
        cmd.stdout = out
        with patch(
            "properties.management.commands.send_monthly_rent_summary.send_monthly_rent_summary_email",
            return_value=True,
        ):
            cmd._send_to_single_user(user_id=owner.id, send_whatsapp=True)
        self.assertIn("✅", out.getvalue())
        self.assertIn(owner.username, out.getvalue())

    def test_single_user_failure(self):
        owner = User.objects.create_user(
            username="fail_owner",
            email="fo@test.com",
            password="p",
            full_name="Fail Owner",
            phone="+91",
        )
        cmd = SendMonthlyRentSummaryCommand()
        out = StringIO()
        cmd.stdout = out
        with patch(
            "properties.management.commands.send_monthly_rent_summary.send_monthly_rent_summary_email",
            return_value=False,
        ):
            cmd._send_to_single_user(user_id=owner.id, send_whatsapp=True)
        self.assertIn("❌", out.getvalue())

    def test_send_summary_to_owner_exception(self):
        owner = User.objects.create_user(
            username="exc_owner",
            email="eo@test.com",
            password="p",
            full_name="Exc Owner",
            phone="+91",
        )
        cmd = SendMonthlyRentSummaryCommand()
        out = StringIO()
        cmd.stdout = out
        with patch(
            "properties.management.commands.send_monthly_rent_summary.send_monthly_rent_summary_email",
            side_effect=RuntimeError("SMTP down"),
        ):
            cmd._send_summary_to_owner(owner, send_whatsapp=True)
        self.assertIn("❌", out.getvalue())


class GenerateMonthlyExtraChargesCommandTest(TestCase):
    def test_no_new_charges(self):
        cmd = GenerateExtraChargesCommand()
        out = StringIO()
        cmd.stdout = out
        with patch(
            "properties.management.commands.generate_monthly_extra_charges.generate_monthly_extra_charges",
            return_value=None,
        ):
            cmd.handle()
        self.assertIn("No new extra charges", out.getvalue())

    def test_charges_generated(self):
        cmd = GenerateExtraChargesCommand()
        out = StringIO()
        cmd.stdout = out
        mock_charge = MagicMock()
        with patch(
            "properties.management.commands.generate_monthly_extra_charges.generate_monthly_extra_charges",
            return_value=[mock_charge, mock_charge],
        ):
            cmd.handle()
        self.assertIn("Created 2 extra charge(s)", out.getvalue())


class SendExtraChargeRemindersCommandTest(TestCase):
    def test_handle_calls_service(self):
        cmd = ExtraChargeRemindersCommand()
        out = StringIO()
        cmd.stdout = out
        with patch(
            "notification.management.commands.send_extra_charge_reminders.send_due_extra_charge_reminders",
            return_value=3,
        ):
            cmd.handle(days_ahead=0)
        self.assertIn("Sent reminders for 3 extra charge(s)", out.getvalue())

    def test_handle_with_days_ahead(self):
        cmd = ExtraChargeRemindersCommand()
        out = StringIO()
        cmd.stdout = out
        with patch(
            "notification.management.commands.send_extra_charge_reminders.send_due_extra_charge_reminders",
            return_value=0,
        ):
            cmd.handle(days_ahead=7)
        self.assertIn("Sent reminders for 0 extra charge(s)", out.getvalue())
