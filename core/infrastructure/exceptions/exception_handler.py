import logging
from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def _build_error_payload(
    exc: Exception,
    context: dict[str, Any],
    status_code: int,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    message = str(exc) if str(exc) else "An error occurred."
    code = exc.__class__.__name__ if hasattr(exc, "__class__") else "UNKNOWN_ERROR"
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "request_id": request_id,
        }
    }


def exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    request = context.get("request")
    request_id = getattr(request, "request_id", None) if request else None

    drf_response = drf_exception_handler(exc, context)
    if drf_response is not None:
        status_code = drf_response.status_code
        data = drf_response.data

        if status_code == status.HTTP_400_BAD_REQUEST:
            details = _extract_validation_details(data)
            payload = _build_error_payload(
                exc, context, status_code, request_id, details
            )
        elif status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            logger.error("Server error: %s", exc, exc_info=True)
            payload = _build_error_payload(exc, context, status_code, request_id)
        else:
            payload = _build_error_payload(exc, context, status_code, request_id)

        return Response(payload, status=drf_response.status_code)

    return None


def _extract_validation_details(data: Any) -> dict[str, Any]:
    if isinstance(data, dict):
        if "detail" in data:
            return {"non_field_errors": [str(data["detail"])]}
        result = {}
        for key, value in data.items():
            if isinstance(value, list):
                result[key] = [str(v) for v in value]
            else:
                result[key] = [str(value)]
        return result
    if isinstance(data, list):
        return {"non_field_errors": [str(item) for item in data]}
    return {"non_field_errors": [str(data)]}
