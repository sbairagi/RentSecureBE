"""Tests for smartbot/views.py — smart chatbot reply endpoint."""

from unittest.mock import patch

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
