"""Tests for ai_assistant views."""

from unittest.mock import patch

from rest_framework.test import APIRequestFactory, force_authenticate

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from ai_assistant.views import (
    ai_assistant_insights,
    chat_with_assistant,
    financial_health_report,
    rent_analytics_data,
)

User = get_user_model()


class AiAssistantInsightsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="ai_user",
            email="ai@test.com",
            password="p",
            full_name="AI User",
            phone="+1",
        )

    def _make_request(self, user=None):
        request = self.factory.get("/api/ai-assistant/insights/")
        if user is not None:
            force_authenticate(request, user=user)
        return request

    def test_anonymous_user_returns_403(self):
        request = self._make_request(user=AnonymousUser())
        response = ai_assistant_insights(request)
        self.assertEqual(response.status_code, 403)

    @patch("ai_assistant.views.RentRecord")
    @patch("ai_assistant.views.Renter")
    @patch("ai_assistant.views.PropertyTaxRecord")
    def test_ai_assistant_insights_success(self, mock_tax, mock_renter, mock_rent):
        mock_rent.objects.filter.return_value.count.return_value = 0
        mock_rent.objects.filter.return_value.filter.return_value.count.return_value = 0
        mock_renter.objects.filter.return_value.count.return_value = 0
        mock_tax.objects.filter.return_value.order_by.return_value = []
        request = self._make_request(user=self.user)
        response = ai_assistant_insights(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("total_rent_this_month", response.data)


class RentAnalyticsDataTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="analytics_user",
            email="an@test.com",
            password="p",
            full_name="Analytics User",
            phone="+1",
        )

    def _make_request(self, user=None):
        request = self.factory.get("/api/ai-assistant/rent-analytics/")
        if user is not None:
            force_authenticate(request, user=user)
        return request

    def test_anonymous_user_returns_403(self):
        request = self._make_request(user=AnonymousUser())
        response = rent_analytics_data(request)
        self.assertEqual(response.status_code, 403)

    @patch("ai_assistant.views.RentRecord")
    def test_rent_analytics_data_success(self, mock_rent):
        mock_rent.objects.filter.return_value.annotate.return_value.values.return_value.annotate.return_value.order_by.return_value = (
            []
        )
        mock_rent.objects.filter.return_value.aggregate.return_value = {"total": 0}
        request = self._make_request(user=self.user)
        response = rent_analytics_data(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("monthly_rent", response.data)
        self.assertIn("paid", response.data)
        self.assertIn("unpaid", response.data)


class FinancialHealthReportTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="health_user",
            email="health@test.com",
            password="p",
            full_name="Health User",
            phone="+1",
        )

    def _make_request(self, user=None):
        request = self.factory.get("/api/ai-assistant/financial-health/")
        if user is not None:
            force_authenticate(request, user=user)
        return request

    def test_anonymous_user_returns_403(self):
        request = self._make_request(user=AnonymousUser())
        response = financial_health_report(request)
        self.assertEqual(response.status_code, 403)

    @patch("ai_assistant.views.analyze_financial_health")
    @patch("ai_assistant.views.RentRecord")
    @patch("ai_assistant.views.PropertyTaxRecord")
    def test_financial_health_report_success(self, mock_tax, mock_rent, mock_analyze):
        mock_rent.objects.filter.return_value = []
        mock_tax.objects.filter.return_value = []
        mock_analyze.return_value = {"score": 85}
        request = self._make_request(user=self.user)
        response = financial_health_report(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["score"], 85)


class ChatWithAssistantTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="chat_user",
            email="chat@test.com",
            password="p",
            full_name="Chat User",
            phone="+1",
        )

    def _make_request(self, data=None, user=None):
        request = self.factory.post("/api/ai-assistant/chat/", data=data or {})
        if user is not None:
            force_authenticate(request, user=user)
        return request

    def test_anonymous_user_returns_403(self):
        request = self._make_request(user=AnonymousUser())
        response = chat_with_assistant(request)
        self.assertEqual(response.status_code, 403)

    @patch("ai_assistant.views.handle_chat_message")
    def test_chat_with_assistant_success(self, mock_handle):
        mock_handle.return_value = "Hello! How can I help?"
        request = self._make_request(data={"message": "Hello"}, user=self.user)
        response = chat_with_assistant(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["reply"], "Hello! How can I help?")
        mock_handle.assert_called_once_with(user=self.user, message="Hello")
