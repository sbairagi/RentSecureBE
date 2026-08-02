"""Tests for multi-language message template service."""

from datetime import date

from django.test import TestCase

from rentsecure_be.services.message_template_service import (
    get_rent_reminder_msg,
    get_tax_reminder_msg,
)


class MessageTemplateServiceTests(TestCase):
    def test_get_rent_reminder_msg_english(self):
        msg = get_rent_reminder_msg(
            name="John",
            amount=5000,
            due_date=date(2026, 6, 5),
            lang="en",
        )
        self.assertIn("John", msg)
        self.assertIn("5000", msg)
        self.assertIn("05-06-2026", msg)

    def test_get_rent_reminder_msg_hindi(self):
        msg = get_rent_reminder_msg(
            name="रजत",
            amount=5000,
            due_date=date(2026, 6, 5),
            lang="hi",
        )
        self.assertIn("रजत", msg)
        self.assertIn("5000", msg)
        self.assertIn("05-06-2026", msg)

    def test_get_rent_reminder_msg_marathi(self):
        msg = get_rent_reminder_msg(
            name="अमित",
            amount=5000,
            due_date=date(2026, 6, 5),
            lang="mr",
        )
        self.assertIn("अमित", msg)
        self.assertIn("5000", msg)
        self.assertIn("05-06-2026", msg)

    def test_get_rent_reminder_msg_falls_back_to_english(self):
        msg = get_rent_reminder_msg(
            name="John",
            amount=5000,
            due_date=date(2026, 6, 5),
            lang="fr",
        )
        self.assertIn("John", msg)
        self.assertIn("5000", msg)

    def test_get_tax_reminder_msg_english(self):
        msg = get_tax_reminder_msg(
            name="John",
            amount=10000,
            due_date=date(2026, 6, 5),
            lang="en",
        )
        self.assertIn("John", msg)
        self.assertIn("10000", msg)
        self.assertIn("05-06-2026", msg)

    def test_get_tax_reminder_msg_hindi(self):
        msg = get_tax_reminder_msg(
            name="रजत",
            amount=10000,
            due_date=date(2026, 6, 5),
            lang="hi",
        )
        self.assertIn("रजत", msg)
        self.assertIn("10000", msg)
        self.assertIn("05-06-2026", msg)
