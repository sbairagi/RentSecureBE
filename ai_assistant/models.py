from __future__ import annotations

from django.conf import settings
from django.db import models


class Conversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_conversations",
    )
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.user} - {self.title or 'Conversation'}"


class Message(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    tools_used = models.JSONField(default=list, blank=True)
    data = models.JSONField(default=dict, blank=True)
    sources = models.JSONField(default=list, blank=True)
    is_error = models.BooleanField(default=False)
    error_code = models.CharField(max_length=50, blank=True)
    retry_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self) -> str:
        return f"{self.conversation} - {self.role}: {self.content[:50]}"
