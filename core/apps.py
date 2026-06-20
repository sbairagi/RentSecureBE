from typing import override

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    @override
    def ready(self) -> None:
        import core.signals  # noqa
