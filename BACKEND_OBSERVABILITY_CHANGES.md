# RentSecureBE Backend Observability Changes

## Summary of Changes

This document describes the backend changes required for the RentSecure observability architecture.

---

## 1. Health Check Endpoints

### New Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health/` | Liveness check |
| GET | `/api/health/readiness/` | Readiness check (DB connectivity) |
| GET | `/api/health/liveness/` | Lightweight liveness |

### Usage

```bash
# Liveness - returns 200 if app is running
curl http://localhost:8000/api/health/

# Readiness - returns 200 if DB is connected, 503 if not
curl http://localhost:8000/api/health/readiness/

# Liveness - lightweight check
curl http://localhost:8000/api/health/liveness/
```

---

## 2. Custom DRF Exception Handler

### Changes

- Added `EXCEPTION_HANDLER` to `REST_FRAMEWORK` settings
- New handler: `core.infrastructure.exceptions.exception_handler.exception_handler`
- All API errors now return consistent envelope:

```json
{
  "error": {
    "code": "ValidationError",
    "message": "Invalid input data.",
    "details": {
      "email": ["This field is required."]
    },
    "request_id": "uuid-here"
  }
}
```

### Status Code Mapping

| Status | Code |
|--------|------|
| 400 | `ValidationError` |
| 401 | `AuthenticationFailed` |
| 403 | `PermissionDenied` |
| 404 | `NotFound` |
| 405 | `MethodNotAllowed` |
| 406 | `NotAcceptable` |
| 415 | `UnsupportedMediaType` |
| 429 | `Throttled` |
| 500+ | `ServerError` |

---

## 3. Request ID / Correlation ID Middleware

### New Middleware

| Middleware | Purpose |
|------------|---------|
| `RequestIdMiddleware` | Generates/reads `X-Request-ID`, injects into log records |
| `CorrelationIdMiddleware` | Generates/reads `X-Correlation-ID` |
| `RequestLoggingMiddleware` | Logs every request with timing |

### Header Flow

```
Client → X-Request-ID: <client-id> → Server echoes back
Client → X-Correlation-ID: <client-id> → Server echoes back
```

### Log Output

```
[2025-01-01 12:00:00] [INFO] [req-uuid-123] core.views - POST /api/auth/login/ 200 123.4ms
```

---

## 4. Structured Logging

### Before

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
```

### After

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"request_id": {"()": "core.infrastructure.middleware.request_id.RequestIdFilter"}},
    "formatters": {
        "structured": {"format": "[%(asctime)s] [%(levelname)s] [%(request_id)s] %(name)s - %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "filters": ["request_id"], "formatter": "structured"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "core": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
```

---

## 5. Sentry Integration

### Installation

```bash
pip install sentry-sdk
```

### Configuration

Add to `.env`:

```env
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
APP_VERSION=1.0.0
```

### What Gets Captured

- Unhandled exceptions
- 500+ server errors
- Integration: Django, Logging

### What Does NOT Get Captured

- 400, 401, 403, 404 errors (handled by DRF)
- Sensitive headers are redacted before sending

---

## 6. Required Django Migrations

No new database models were added. No migrations required.

---

## 7. Verification Checklist

```bash
# 1. Run Django checks
python manage.py check

# 2. Test health endpoints
curl http://localhost:8000/api/health/        # Should return {"status": "ok"}
curl http://localhost:8000/api/health/readiness/  # Should return {"status": "ready"}
curl http://localhost:8000/api/health/liveness/   # Should return {"status": "alive"}

# 3. Test error envelope
curl -X POST http://localhost:8000/api/auth/login/ -H "Content-Type: application/json" -d '{}'
# Should return {"error": {"code": "ValidationError", "message": "...", "details": {...}, "request_id": "..."}}

# 4. Test 404
curl http://localhost:8000/api/nonexistent/
# Should return {"error": {"code": "NotFound", "message": "...", "request_id": "..."}}

# 5. Verify request ID in logs
# Make any request and check that logs contain [request-id]

# 6. Test Sentry (if configured)
# Trigger a 500 error and verify it appears in Sentry dashboard
```

---

## 8. Rollback Plan

If issues arise:

1. Revert `MIDDLEWARE` in `settings.py` to original
2. Revert `REST_FRAMEWORK` `EXCEPTION_HANDLER` to default
3. Revert `LOGGING` to original
4. Remove `core/infrastructure/` directory
5. Remove health check URLs from `core/urls.py`

No database migrations are involved, so rollback is safe.

---

## 9. Backend Compatibility Report

### Existing API Error Formats

The backend previously had inconsistent error formats:
- `{"error": "..."}` - most common
- `{"detail": "..."}` - DRF default for auth errors
- `{"error": "...", "details": "..."}` - documents app
- `{"status": "ok", "message": "..."}` - webhook success

### New Standard Format

All errors now use:
```json
{
  "error": {
    "code": "ErrorCode",
    "message": "Human-readable message.",
    "details": {},
    "request_id": "uuid"
  }
}
```

### Frontend Compatibility

The frontend `errorHandler.ts` already handles:
- `data.error.message` → user message
- `data.error.details` → validation details
- `data.error.request_id` → correlation ID

The new backend format is fully compatible.

### Breaking Changes

**None.** The new error envelope is backward compatible:
- Existing `data.message` still works (extracted from `data.error.message`)
- Existing `data.details` still works
- Existing `data.error.request_id` is new but ignored by old frontend code
