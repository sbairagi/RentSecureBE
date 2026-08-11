from django.urls import path

from .views import (
    chat_with_assistant,
    conversation_detail,
    conversations,
    suggested_questions,
)

app_name = "ai_assistant"

urlpatterns = [
    path("chat/", chat_with_assistant, name="chat"),
    path("suggested-questions/", suggested_questions, name="suggested-questions"),
    path("conversations/", conversations, name="conversations"),
    path(
        "conversations/<uuid:pk>/",
        conversation_detail,
        name="conversation-detail",
    ),
]
