"""Tests for finance serializers and URL import coverage."""

from django.test import TestCase

from finance import urls as finance_urls_module
from finance.models import CAProfile, TaxSubmissionToCA
from finance.serializers import CAProfileSerializer, TaxSubmissionToCASerializer


class FinanceSerializerTest(TestCase):
    def setUp(self):
        self.user = self._create_user()

    def _create_user(self):
        from django.contrib.auth import get_user_model

        django_user_model = get_user_model()
        return django_user_model.objects.create_user(
            username="fin_serializer",
            email="fs@test.com",
            password="p",
            full_name="FS",
            phone="+1",
        )

    def test_ca_profile_serializer_fields(self):
        ca = CAProfile.objects.create(
            user=self.user,
            firm_name="Tax Firm",
            contact_email="ca@firm.com",
            phone="+919999999999",
        )
        data = CAProfileSerializer(ca).data
        self.assertIn("firm_name", data)
        self.assertEqual(data["firm_name"], "Tax Firm")

    def test_tax_submission_serializer_fields(self):
        submission = TaxSubmissionToCA.objects.create(
            user=self.user,
            financial_year="2024-25",
            sent_to_email="ca@firm.com",
        )
        data = TaxSubmissionToCASerializer(submission).data
        self.assertIn("financial_year", data)
        self.assertEqual(data["financial_year"], "2024-25")
        self.assertIn("sent_at", data)


class FinanceURLImportTest(TestCase):
    def test_finance_urls_import(self):
        self.assertIsNotNone(finance_urls_module.urlpatterns)
        self.assertTrue(len(finance_urls_module.urlpatterns) > 0)
