from django.apps import AppConfig


class ReferralConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "referral_and_earn"

    def ready(self) -> None:
        import referral_and_earn.signals  # noqa
