from __future__ import annotations

import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response

from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from ai_assistant.models import Conversation, Message
from ai_assistant.serializers import (
    ConversationDetailSerializer,
    ConversationSerializer,
)
from ai_assistant.services.chat_service import generate_ai_response
from properties.feature_enforcer import FeatureEnforcer

logger = logging.getLogger(__name__)


def _check_ai_access(user) -> tuple[Response | None, FeatureEnforcer | None]:
    if isinstance(user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=401), None

    enforcer = FeatureEnforcer(user)

    if not enforcer.can_create("ai_chat_messages"):
        return (
            Response(
                {
                    "error": "rate_limit_exceeded",
                    "message": (
                        "You have reached your monthly AI limit. "
                        "Please upgrade your plan."
                    ),
                },
                status=429,
            ),
            None,
        )

    return None, enforcer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def suggested_questions(request: DRFRequest) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=401)

    questions = [
        "How much rent is pending this month?",
        "Which renters have overdue rent?",
        "Which units are vacant?",
        "How much rent was collected this month?",
        "Which agreements are expiring soon?",
        "Which maintenance requests are still open?",
        "How many active renters do I have?",
        "What is my payout status?",
        "Show me my subscription details.",
        "What is my next rent due?",
    ]

    try:
        _ = request.user.renter_profile
        questions.extend(
            [
                "What is my next rent due?",
                "Show my payment history.",
                "Show my agreement status.",
            ]
        )
    except Exception:
        logger.debug("User has no renter profile", exc_info=True)

    return Response({"questions": questions})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat_with_assistant(request: DRFRequest) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=401)

    error_response, enforcer = _check_ai_access(request.user)
    if error_response is not None:
        return error_response

    message_text = (request.data.get("message") or "").strip()
    if not message_text:
        return Response({"error": "Message is required."}, status=400)

    conversation_id = request.data.get("conversation_id")
    conversation = None
    if conversation_id:
        try:
            conversation = Conversation.objects.get(
                id=conversation_id, user=request.user
            )
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found."}, status=404)

    if conversation is None:
        conversation = Conversation.objects.create(
            user=request.user,
            title=message_text[:50],
        )

    Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        content=message_text,
    )

    history = list(
        conversation.messages.order_by("timestamp").values("role", "content")[:20]
    )

    try:
        result = generate_ai_response(request.user, message_text, history)
    except Exception:
        logger.exception("AI response generation failed")
        assistant_message = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content="I couldn't process your request. Please try again.",
            is_error=True,
            error_code="provider_failure",
        )
        enforcer.increment("ai_chat_messages")
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=["updated_at"])
        return Response(
            {
                "conversation_id": str(conversation.id),
                "response": {
                    "response": assistant_message.content,
                    "tools_used": [],
                    "data": {},
                    "sources": [],
                    "timestamp": assistant_message.timestamp.isoformat(),
                    "is_error": True,
                    "error_code": "provider_failure",
                },
            },
            status=200,
        )

    assistant_message = Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content=result["response"],
        tools_used=result.get("tools_used", []),
        data=result.get("data", {}),
        sources=result.get("sources", []),
    )

    enforcer.increment("ai_chat_messages")
    conversation.updated_at = timezone.now()
    conversation.save(update_fields=["updated_at"])

    return Response(
        {
            "conversation_id": str(conversation.id),
            "response": {
                "response": result["response"],
                "tools_used": result.get("tools_used", []),
                "data": result.get("data", {}),
                "sources": result.get("sources", []),
                "timestamp": assistant_message.timestamp.isoformat(),
                "is_error": False,
                "error_code": None,
            },
        }
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def conversations(request: DRFRequest) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=401)

    if request.method == "POST":
        title = (request.data.get("title") or "").strip()
        conversation = Conversation.objects.create(user=request.user, title=title[:255])
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=201)

    conversations_qs = Conversation.objects.filter(user=request.user).order_by(
        "-updated_at"
    )
    serializer = ConversationSerializer(conversations_qs, many=True)
    return Response({"conversations": serializer.data})


@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def conversation_detail(request: DRFRequest, pk: str) -> Response:
    if isinstance(request.user, AnonymousUser):
        return Response({"error": "Unauthorized"}, status=401)

    try:
        conversation = Conversation.objects.get(id=pk, user=request.user)
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation not found."}, status=404)

    if request.method == "DELETE":
        conversation.delete()
        return Response(status=204)

    serializer = ConversationDetailSerializer(conversation)
    return Response(serializer.data)
