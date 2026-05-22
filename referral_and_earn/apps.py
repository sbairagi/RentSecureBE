from django.apps import AppConfig


class ReferralConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'referral_and_earn'

    # apps.py
    def ready(self):
        pass
