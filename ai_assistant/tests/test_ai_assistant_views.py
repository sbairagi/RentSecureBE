"""Tests for ai_assistant views."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from rest_framework.test import APIRequestFactory, force_authenticate

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from ai_assistant.models import Conversation, Message
from core.models import (
    AddOnPurchase,
    PlanFeatureLimit,
    SubscriptionPlan,
    UserSubscription,
)

User = get_user_model()


def _ensure_ai_feature_limits():
    free_plan, _ = SubscriptionPlan.objects.get_or_create(
        name="free",
        defaults={"monthly_price": Decimal("0"), "yearly_price": Decimal("0")},
    )
    PlanFeatureLimit.objects.get_or_create(
        plan=free_plan,
        feature_key="ai_chat_messages",
        defaults={"value": "10"},
    )


class ConversationModelTest(TestCase):
    def test_create_conversation(self):
        _ensure_ai_feature_limits()
        user = User.objects.create_user(
            username="convuser", password="testpass123", full_name="Conv User"
        )
        conv = Conversation.objects.create(user=user, title="Test chat")
        self.assertEqual(conv.user, user)
        self.assertEqual(conv.title, "Test chat")

    def test_conversation_str(self):
        _ensure_ai_feature_limits()
        user = User.objects.create_user(
            username="convuser2", password="testpass123", full_name="Conv User 2"
        )
        conv = Conversation.objects.create(user=user)
        self.assertIn("Conv User 2", str(conv))


class MessageModelTest(TestCase):
    def test_create_message(self):
        _ensure_ai_feature_limits()
        user = User.objects.create_user(username="msguser", password="testpass123")
        conv = Conversation.objects.create(user=user)
        msg = Message.objects.create(
            conversation=conv,
            role=Message.Role.USER,
            content="Hello",
        )
        self.assertEqual(msg.content, "Hello")
        self.assertFalse(msg.is_error)

    def test_message_str(self):
        _ensure_ai_feature_limits()
        user = User.objects.create_user(username="msguser2", password="testpass123")
        conv = Conversation.objects.create(user=user)
        msg = Message.objects.create(
            conversation=conv,
            role=Message.Role.USER,
            content="Hello world test message",
        )
        self.assertIn("Hello world test", str(msg))


class SuggestedQuestionsTest(TestCase):
    def test_suggested_questions_returns_list(self):
        user = User.objects.create_user(username="quser", password="testpass123")
        factory = APIRequestFactory()
        request = factory.get("/api/ai-assistant/suggested-questions/")
        force_authenticate(request, user=user)

        from ai_assistant.views import suggested_questions

        response = suggested_questions(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("questions", response.data)
        self.assertIsInstance(response.data["questions"], list)
        self.assertTrue(len(response.data["questions"]) > 0)

    def test_suggested_questions_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/ai-assistant/suggested-questions/")

        from ai_assistant.views import suggested_questions

        response = suggested_questions(request)
        self.assertEqual(response.status_code, 401)


class ChatWithAssistantTest(TestCase):
    def setUp(self):
        _ensure_ai_feature_limits()
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="chatuser", password="testpass123"
        )
        free_plan = SubscriptionPlan.objects.get(name="free")
        PlanFeatureLimit.objects.filter(
            plan=free_plan, feature_key="ai_chat_messages"
        ).update(value="100")
        UserSubscription.objects.get_or_create(
            user=self.user,
            defaults={
                "plan": free_plan,
                "start_date": timezone.now().date(),
                "end_date": timezone.now().date() + timedelta(days=30),
                "is_active": True,
            },
        )

    def _post(self, data):
        request = self.factory.post("/api/ai-assistant/chat/", data=data, format="json")
        force_authenticate(request, user=self.user)
        from ai_assistant.views import chat_with_assistant

        return chat_with_assistant(request)

    def test_chat_requires_message(self):
        response = self._post({})
        self.assertEqual(response.status_code, 400)

    def test_chat_creates_conversation(self):
        with patch("ai_assistant.views.generate_ai_response") as mock_ai:
            mock_ai.return_value = {
                "response": "Test response",
                "tools_used": [],
                "data": {},
                "sources": [],
            }
            response = self._post({"message": "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("conversation_id", response.data)
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(Message.objects.count(), 2)

    def test_chat_returns_tools_used(self):
        with patch("ai_assistant.views.generate_ai_response") as mock_ai:
            mock_ai.return_value = {
                "response": "Test response",
                "tools_used": ["get_pending_rents"],
                "data": {"total_pending": "1000"},
                "sources": ["backend"],
            }
            response = self._post({"message": "How much rent is pending?"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["response"]["tools_used"], ["get_pending_rents"])


class ConversationCRUDTest(TestCase):
    def setUp(self):
        _ensure_ai_feature_limits()
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="convcrud", password="testpass123", full_name="Conv CRUD"
        )
        free_plan = SubscriptionPlan.objects.get(name="free")
        PlanFeatureLimit.objects.filter(
            plan=free_plan, feature_key="ai_chat_messages"
        ).update(value="100")
        UserSubscription.objects.get_or_create(
            user=self.user,
            defaults={
                "plan": free_plan,
                "start_date": timezone.now().date(),
                "end_date": timezone.now().date() + timedelta(days=30),
                "is_active": True,
            },
        )
        self.conv = Conversation.objects.create(user=self.user, title="Test")

    def test_list_conversations(self):
        request = self.factory.get("/api/ai-assistant/conversations/")
        force_authenticate(request, user=self.user)
        from ai_assistant.views import conversations

        response = conversations(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["conversations"]), 1)

    def test_create_conversation(self):
        request = self.factory.post(
            "/api/ai-assistant/conversations/",
            {"title": "New chat"},
            format="json",
        )
        force_authenticate(request, user=self.user)
        from ai_assistant.views import conversations

        response = conversations(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Conversation.objects.count(), 2)

    def test_delete_conversation(self):
        request = self.factory.delete(
            f"/api/ai-assistant/conversations/{self.conv.id}/"
        )
        force_authenticate(request, user=self.user)
        from ai_assistant.views import conversation_detail

        response = conversation_detail(request, str(self.conv.id))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Conversation.objects.count(), 0)

    def test_delete_other_user_conversation_forbidden(self):
        other = User.objects.create_user(
            username="otheruser", password="testpass123", full_name="Other User"
        )
        request = self.factory.delete(
            f"/api/ai-assistant/conversations/{self.conv.id}/"
        )
        force_authenticate(request, user=other)
        from ai_assistant.views import conversation_detail

        response = conversation_detail(request, str(self.conv.id))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Conversation.objects.count(), 1)


class SubscriptionGatingTest(TestCase):
    def setUp(self):
        _ensure_ai_feature_limits()
        self.factory = APIRequestFactory()
        self.free_plan = SubscriptionPlan.objects.create(
            name="free", monthly_price=Decimal("0"), yearly_price=Decimal("0")
        )
        PlanFeatureLimit.objects.create(
            plan=self.free_plan, feature_key="ai_chat_messages", value="0"
        )
        self.user = User.objects.create_user(username="subuser", password="testpass123")
        UserSubscription.objects.create(
            user=self.user,
            plan=self.free_plan,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
        )

    def test_chat_blocked_without_ai_limit(self):
        request = self.factory.post(
            "/api/ai-assistant/chat/",
            {"message": "Hello"},
            format="json",
        )
        force_authenticate(request, user=self.user)
        from ai_assistant.views import chat_with_assistant

        response = chat_with_assistant(request)
        self.assertEqual(response.status_code, 429)

    def test_chat_allowed_with_ai_limit(self):
        PlanFeatureLimit.objects.filter(
            plan=self.free_plan, feature_key="ai_chat_messages"
        ).update(value="10")
        request = self.factory.post(
            "/api/ai-assistant/chat/",
            {"message": "Hello"},
            format="json",
        )
        force_authenticate(request, user=self.user)
        from ai_assistant.views import chat_with_assistant

        with patch("ai_assistant.views.generate_ai_response") as mock_ai:
            mock_ai.return_value = {
                "response": "OK",
                "tools_used": [],
                "data": {},
                "sources": [],
            }
            response = chat_with_assistant(request)
        self.assertEqual(response.status_code, 200)

    def test_chat_allowed_with_addon(self):
        PlanFeatureLimit.objects.filter(
            plan=self.free_plan, feature_key="ai_chat_messages"
        ).update(value="0")
        AddOnPurchase.objects.create(user=self.user, name="ai_chat_messages", amount=10)
        request = self.factory.post(
            "/api/ai-assistant/chat/",
            {"message": "Hello"},
            format="json",
        )
        force_authenticate(request, user=self.user)
        from ai_assistant.views import chat_with_assistant

        with patch("ai_assistant.views.generate_ai_response") as mock_ai:
            mock_ai.return_value = {
                "response": "OK",
                "tools_used": [],
                "data": {},
                "sources": [],
            }
            response = chat_with_assistant(request)
        self.assertEqual(response.status_code, 200)
