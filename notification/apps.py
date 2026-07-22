from django.apps import AppConfig

from shared.type_compat import override


class NotificationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notification"

    @override
    def ready(self) -> None:
        import notification.signals  # noqa
