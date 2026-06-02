"""Comprehensive tests for finance app"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from finance.models import CAProfile, TaxSubmissionToCA

User = get_user_model()


class FinanceModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="fm@t.com",
            email="fm@t.com",
            password="p",
            full_name="FM",
            phone="+1",
        )

    def test_create_ca_profile(self):
        ca = CAProfile.objects.create(
            user=self.user,
            firm_name="Tax Firm",
            contact_email="ca@firm.com",
            phone="+919999999999",
        )
        self.assertEqual(ca.firm_name, "Tax Firm")
        self.assertFalse(ca.verified)

    def test_ca_profile_verified(self):
        ca = CAProfile.objects.create(
            user=self.user,
            firm_name="Verified CA",
            contact_email="v@firm.com",
            phone="+918888888888",
            verified=True,
        )
        self.assertIn("Verified", str(ca))

    def test_create_tax_submission(self):
        s = TaxSubmissionToCA.objects.create(
            user=self.user, financial_year="2024-25", sent_to_email="ca@firm.com"
        )
        self.assertEqual(s.financial_year, "2024-25")
        self.assertIsNotNone(str(s))

    def test_tax_submission_with_ca(self):
        ca = CAProfile.objects.create(
            user=self.user,
            firm_name="My CA",
            contact_email="my@firm.com",
            phone="+917777777777",
        )
        s = TaxSubmissionToCA.objects.create(
            user=self.user, ca=ca, financial_year="2023-24", sent_to_email="my@firm.com"
        )
        self.assertEqual(s.ca.firm_name, "My CA")
