from django.apps import AppConfig

from shared.type_compat import override


class PropertiesConfig(AppConfig):
    """Application configuration for the properties app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "properties"

    @override
    def ready(self) -> None:
        import properties.signals  # noqa
