"""Tests for smartbot views."""

from unittest.mock import patch

from rest_framework.test import APIRequestFactory, force_authenticate

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from smartbot.views import smart_bot_reply

User = get_user_model()


def _jwt_request(user, method="GET", data=None, path="/test"):
    from rest_framework_simplejwt.tokens import RefreshToken

    from django.test import RequestFactory

    factory = RequestFactory()
    token = RefreshToken.for_user(user).access_token
    kwargs = {}
    if data:
        kwargs["data"] = data
    req = getattr(factory, method.lower())(
        path, HTTP_AUTHORIZATION=f"Bearer {token}", **kwargs
    )
    return req


def _anon_request(method="GET", data=None, path="/test"):
    from django.test import RequestFactory

    factory = RequestFactory()
    kwargs = {}
    if data:
        kwargs["data"] = data
    req = getattr(factory, method.lower())(path, **kwargs)
    req.user = AnonymousUser()
    return req


class SmartBotViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="smartbot_user",
            email="smartbot@test.com",
            password="p",
            full_name="SmartBot User",
            phone="+919999999999",
        )

    def test_smart_bot_reply_returns_answer(self):
        with patch("smartbot.views.gpt_smart_reply", return_value="Hello!"):
            with patch("smartbot.views.extract_intent", return_value=None):
                response = smart_bot_reply(
                    _jwt_request(self.user, method="POST", data={"query": "hello"})
                )
        self.assertEqual(response.status_code, 200)
        self.assertIn("answer", response.data)

    def test_smart_bot_reply_anonymous_returns_401(self):
        response = smart_bot_reply(
            _anon_request(method="POST", data={"query": "hello"})
        )
        self.assertEqual(response.status_code, 401)

    def test_smart_bot_reply_triggers_rent_reminder(self):
        with patch("smartbot.views.gpt_smart_reply", return_value="Reminder sent"):
            with patch(
                "smartbot.views.extract_intent", return_value="send_rent_reminder"
            ):
                with patch("smartbot.views.send_rent_reminder") as mock_send:
                    response = smart_bot_reply(
                        _jwt_request(
                            self.user,
                            method="POST",
                            data={"query": "send reminder to John"},
                        )
                    )
        self.assertEqual(response.status_code, 200)
        mock_send.assert_called_once_with("John")

    def test_smart_bot_reply_saves_chat(self):
        with patch("smartbot.views.gpt_smart_reply", return_value="Test reply"):
            with patch("smartbot.views.extract_intent", return_value=None):
                response = smart_bot_reply(
                    _jwt_request(self.user, method="POST", data={"query": "test query"})
                )
        self.assertEqual(response.status_code, 200)
        from smartbot.models import SmartBotChat

        self.assertTrue(
            SmartBotChat.objects.filter(user=self.user, message="test query").exists()
        )

    def test_smart_bot_reply_empty_query(self):
        with patch("smartbot.views.gpt_smart_reply", return_value=""):
            with patch("smartbot.views.extract_intent", return_value=None):
                response = smart_bot_reply(
                    _jwt_request(self.user, method="POST", data={"query": ""})
                )
        self.assertEqual(response.status_code, 200)
        self.assertIn("answer", response.data)

    def test_smart_bot_reply_triggers_retry_payout(self):
        with patch("smartbot.views.gpt_smart_reply", return_value="retrying"):
            with patch("smartbot.views.extract_intent", return_value="retry_payout"):
                with patch("smartbot.views.retry_payout") as mock_retry:
                    response = smart_bot_reply(
                        _jwt_request(
                            self.user,
                            method="POST",
                            data={"query": "retry payout for John"},
                        )
                    )
        self.assertEqual(response.status_code, 200)
        mock_retry.assert_called_once_with("John")

    def test_smart_bot_reply_triggers_send_rent_agreement(self):
        with patch("smartbot.views.gpt_smart_reply", return_value="sending agreement"):
            with patch(
                "smartbot.views.extract_intent",
                return_value="send_rent_agreement",
            ):
                with patch("smartbot.views.send_rent_agreement") as mock_send:
                    response = smart_bot_reply(
                        _jwt_request(
                            self.user,
                            method="POST",
                            data={"query": "send agreement to John"},
                        )
                    )
        self.assertEqual(response.status_code, 200)
        mock_send.assert_called_once_with("John")

    def test_smart_bot_reply_triggers_send_agreement_for_signature(self):
        with patch("smartbot.views.gpt_smart_reply", return_value="signing"):
            with patch(
                "smartbot.views.extract_intent",
                return_value="send_agreement_for_signature",
            ):
                with patch("smartbot.views.send_agreement_for_signature") as mock_send:
                    response = smart_bot_reply(
                        _jwt_request(
                            self.user,
                            method="POST",
                            data={"query": "send agreement for signature to John"},
                        )
                    )
        self.assertEqual(response.status_code, 200)
        mock_send.assert_called_once_with("John")


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
