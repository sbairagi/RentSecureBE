from __future__ import annotations

from rest_framework import serializers

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "role",
            "content",
            "timestamp",
            "tools_used",
            "data",
            "sources",
            "is_error",
            "error_code",
            "retry_count",
        ]
        read_only_fields = fields


class ConversationSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "title",
            "created_at",
            "updated_at",
            "message_count",
            "last_message",
        ]
        read_only_fields = fields

    def get_last_message(self, obj: Conversation) -> dict | None:
        last = obj.messages.order_by("-timestamp").first()
        if last is None:
            return None
        return MessageSerializer(last).data

    def get_message_count(self, obj: Conversation) -> int:
        return obj.messages.count()


class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "title",
            "created_at",
            "updated_at",
            "message_count",
            "messages",
        ]
        read_only_fields = fields

    def get_message_count(self, obj: Conversation) -> int:
        return obj.messages.count()
