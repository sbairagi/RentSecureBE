import logging
import time

from django.db import connection
from django.http import JsonResponse
from django.views import View

logger = logging.getLogger(__name__)


class HealthCheckView(View):
    """
    Liveness check - returns 200 if the app is running.
    """

    def get(self, request):
        return JsonResponse(
            {
                "status": "ok",
                "service": "rentsecure-be",
                "timestamp": int(time.time()),
            }
        )


class ReadinessCheckView(View):
    """
    Readiness check - verifies database connectivity.
    """

    def get(self, request):
        try:
            connection.ensure_connection()
            db_status = "ok"
        except Exception as exc:
            logger.error("Database readiness check failed: %s", exc)
            db_status = "error"

        response_data = {
            "status": "ready" if db_status == "ok" else "not_ready",
            "service": "rentsecure-be",
            "checks": {
                "database": db_status,
            },
            "timestamp": int(time.time()),
        }
        status_code = 200 if db_status == "ok" else 503
        return JsonResponse(response_data, status=status_code)


class LivenessCheckView(View):
    """
    Liveness check - lightweight check that the app process is alive.
    """

    def get(self, request):
        return JsonResponse(
            {
                "status": "alive",
                "service": "rentsecure-be",
                "timestamp": int(time.time()),
            }
        )
