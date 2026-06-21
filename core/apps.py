import os

from django.apps import AppConfig

from rentsecure_be.type_compat import override


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    @override
    def ready(self) -> None:
        if os.environ.get("SKIP_DJANGO_SIGNALS") == "1":
            return
        import core.signals  # noqa
