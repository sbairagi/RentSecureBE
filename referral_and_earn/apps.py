from django.apps import AppConfig

from shared.type_compat import override


class ReferralConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "referral_and_earn"

    @override
    def ready(self) -> None:
        import referral_and_earn.signals  # noqa
