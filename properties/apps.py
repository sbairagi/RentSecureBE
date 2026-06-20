import os

from django.apps import AppConfig


class PropertiesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "properties"

    def ready(self) -> None:
        # Skip signal imports during mypy type checking
        if os.environ.get("MYPY_RUNNING") != "1":
            import properties.signals  # noqa
