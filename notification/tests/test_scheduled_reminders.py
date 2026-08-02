"""Tests for scheduled reminder management command."""

from unittest.mock import patch

from django.test import TestCase

from management.commands.send_scheduled_reminders import Command


class SendScheduledRemindersCommandTest(TestCase):
    def test_command_calls_rent_and_tax_processors(self):
        cmd = Command()
        with patch(
            "management.commands.send_scheduled_reminders.process_rent_reminders"
        ) as mock_rent:
            with patch(
                "management.commands.send_scheduled_reminders.process_tax_reminders"
            ) as mock_tax:
                cmd.handle()
                mock_rent.assert_called_once()
                mock_tax.assert_called_once()
