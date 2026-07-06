from typing import override

from django.apps import AppConfig


class AiAssistantConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ai_assistant"

    @override
    def ready(self) -> None:
        import ai_assistant.receivers  # noqa: F401
