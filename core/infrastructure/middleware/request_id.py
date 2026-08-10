import logging
import time
import uuid

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestIdFilter(logging.Filter):
    """
    Logging filter that injects the current request ID into the log record.
    Works thread-locally so it does not leak between requests.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        from asgiref.local import Local

        local = Local()
        request_id = getattr(local, "request_id", None)
        if request_id is None:
            try:
                from django.http import HttpRequest

                request = HttpRequest()
                request_id = getattr(request, "request_id", None)
            except Exception:
                logger.debug("Unable to create fallback HttpRequest for request_id")
        record.request_id = request_id or "-"
        return True


class RequestIdMiddleware(MiddlewareMixin):
    """
    Generates or reads X-Request-ID and makes it available on the request.
    Also injects the ID into log records so every log line is traceable.
    """

    REQUEST_ID_HEADER = "HTTP_X_REQUEST_ID"
    RESPONSE_HEADER = "X-Request-ID"

    def process_request(self, request):
        request_id = request.META.get(self.REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.request_id = request_id
        request.META["X-Request-ID"] = request_id
        try:
            from asgiref.local import Local

            local = Local()
            local.request_id = request_id
        except Exception:
            logger.debug("Unable to set request_id in thread local")
        return None

    def process_response(self, request, response):
        request_id = getattr(request, "request_id", None)
        if request_id:
            response[self.RESPONSE_HEADER] = request_id
        return response


class CorrelationIdMiddleware(MiddlewareMixin):
    """
    Reads X-Correlation-ID from the inbound request and echoes it back.
    Works alongside RequestIdMiddleware so both IDs are available.
    """

    HEADER = "HTTP_X_CORRELATION_ID"
    RESPONSE_HEADER = "X-Correlation-ID"

    def process_request(self, request):
        correlation_id = request.META.get(self.HEADER) or str(uuid.uuid4())
        request.correlation_id = correlation_id
        request.META["X-Correlation-ID"] = correlation_id
        return None

    def process_response(self, request, response):
        correlation_id = getattr(request, "correlation_id", None)
        if correlation_id:
            response[self.RESPONSE_HEADER] = correlation_id
        return response


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Logs every request with timing, method, path, status, and request ID.
    """

    def process_request(self, request):
        request._observability_start_time = time.perf_counter()
        return None

    def process_response(self, request, response):
        start = getattr(request, "_observability_start_time", None)
        if start is not None:
            duration_ms = (time.perf_counter() - start) * 1000
        else:
            duration_ms = -1

        request_id = getattr(request, "request_id", "unknown")
        logger.info(
            "%s %s %s %d %.1fms",
            request.method,
            request.path,
            request_id,
            response.status_code,
            duration_ms,
        )
        return response

    def process_exception(self, request, exception):
        request_id = getattr(request, "request_id", "unknown")
        logger.error(
            "Unhandled exception: %s %s %s %s: %s",
            request.method,
            request.path,
            request_id,
            exception.__class__.__name__,
            str(exception),
            exc_info=True,
        )
        return None
