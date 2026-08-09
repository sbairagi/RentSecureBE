from django.apps import AppConfig


class VisitorsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "visitors"
    verbose_name = "Visitor Management"

    def ready(self) -> None:
        import visitors.signals  # noqa: F401
