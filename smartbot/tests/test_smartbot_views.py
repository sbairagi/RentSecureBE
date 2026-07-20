"""Tests for smartbot views."""

from unittest.mock import patch

from rest_framework.test import APIRequestFactory, force_authenticate

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from smartbot.views import smart_bot_reply

User = get_user_model()


class SmartBotReplyTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="bot_user",
            email="bot@test.com",
            password="p",
            full_name="Bot User",
            phone="+1",
        )

    def _make_request(self, data=None, user=None, method="post"):
        request = getattr(self.factory, method)(
            "/api/smart-bot/reply/", data=data or {}
        )
        if user is not None:
            force_authenticate(request, user=user)
        return request

    def test_anonymous_user_returns_403(self):
        request = self._make_request(user=AnonymousUser())
        response = smart_bot_reply(request)
        self.assertEqual(response.status_code, 403)

    @patch("smartbot.views.gpt_smart_reply")
    @patch("smartbot.views.extract_intent")
    @patch("smartbot.views.SmartBotChat")
    def test_smart_bot_reply_success(self, mock_chat, mock_extract, mock_gpt):
        mock_gpt.return_value = "Hello! How can I help?"
        mock_extract.return_value = None
        request = self._make_request(data={"query": "Hello"}, user=self.user)
        response = smart_bot_reply(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["answer"], "Hello! How can I help?")
        mock_chat.objects.create.assert_called_once()

    @patch("smartbot.views.gpt_smart_reply")
    @patch("smartbot.views.extract_intent")
    @patch("smartbot.views.send_rent_reminder")
    def test_smart_bot_reply_with_send_rent_reminder(
        self, mock_send_reminder, mock_extract, mock_gpt
    ):
        mock_gpt.return_value = "Sending reminder"
        mock_extract.return_value = "send_rent_reminder"
        request = self._make_request(
            data={"query": "send rent reminder to Test Renter"}, user=self.user
        )
        response = smart_bot_reply(request)
        self.assertEqual(response.status_code, 200)
        mock_send_reminder.assert_called_once_with("Test Renter")

    @patch("smartbot.views.gpt_smart_reply")
    @patch("smartbot.views.extract_intent")
    @patch("smartbot.views.retry_payout")
    def test_smart_bot_reply_with_retry_payout(
        self, mock_retry, mock_extract, mock_gpt
    ):
        mock_gpt.return_value = "Retrying payout"
        mock_extract.return_value = "retry_payout"
        request = self._make_request(
            data={"query": "retry payout for Test Renter"}, user=self.user
        )
        response = smart_bot_reply(request)
        self.assertEqual(response.status_code, 200)
        mock_retry.assert_called_once_with("Test Renter")

    @patch("smartbot.views.gpt_smart_reply")
    @patch("smartbot.views.extract_intent")
    @patch("smartbot.views.send_rent_agreement")
    def test_smart_bot_reply_with_send_rent_agreement(
        self, mock_send_agreement, mock_extract, mock_gpt
    ):
        mock_gpt.return_value = "Sending agreement"
        mock_extract.return_value = "send_rent_agreement"
        request = self._make_request(
            data={"query": "send rent agreement to Test Renter"}, user=self.user
        )
        response = smart_bot_reply(request)
        self.assertEqual(response.status_code, 200)
        mock_send_agreement.assert_called_once_with("Test Renter")

    @patch("smartbot.views.gpt_smart_reply")
    @patch("smartbot.views.extract_intent")
    @patch("smartbot.views.send_agreement_for_signature")
    def test_smart_bot_reply_with_send_agreement_for_signature(
        self, mock_send_sig, mock_extract, mock_gpt
    ):
        mock_gpt.return_value = "Sending for signature"
        mock_extract.return_value = "send_agreement_for_signature"
        request = self._make_request(
            data={"query": "send agreement for signature to Test Renter"},
            user=self.user,
        )
        response = smart_bot_reply(request)
        self.assertEqual(response.status_code, 200)
        mock_send_sig.assert_called_once_with("Test Renter")
