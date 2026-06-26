"""
CI Dashboard - Local GitHub Actions clone for Django.

This app parses GitHub Actions workflow files from .github/workflows/,
executes jobs locally, and provides a real-time dashboard with live log streaming.
"""

from django.apps import AppConfig


class CiDashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ci_dashboard"
    verbose_name = "CI Dashboard"

    def ready(self) -> None:
        """Import signals and setup when app is ready."""
        pass
