from django.apps import AppConfig


class WealthConciergePlatformConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wealth_concierge_platform'

    def ready(self):
        import wealth_concierge_platform.signals 
