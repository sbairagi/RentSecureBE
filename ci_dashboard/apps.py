"""
CI Dashboard - Production-Grade Local GitHub Actions Clone for Django.

Features:
- Parse GitHub Actions workflows from .github/workflows/
- Execute jobs locally with subprocess
- Real-time log streaming via SSE
- Dependency graph visualization
- Dashboard metrics
- Search, filter, rerun, download logs, PDF export
- Dark theme UI matching GitHub Actions
"""

from django.apps import AppConfig


class CiDashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ci_dashboard"
    verbose_name = "CI Dashboard"
