# RentSecure Engineering Standards

**Status:** MANDATORY
**Effective Date:** 2026-07-19
**Applies To:** All engineers, reviewers, and contributors to RentSecureBE
**Authority:** Chief Software Architect / Architecture Review Board
**Source of Truth:** ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md, ADR-001 through ADR-010

---

## Table of Contents

1. [Folder Structure](#1-folder-structure)
2. [Naming Conventions](#2-naming-conventions)
3. [DDD Rules](#3-ddd-rules)
4. [Service Rules](#4-service-rules)
5. [Serializer Rules](#5-serializer-rules)
6. [View Rules](#6-view-rules)
7. [Model Rules](#7-model-rules)
8. [Repository Rules](#8-repository-rules)
9. [Signals](#9-signals)
10. [Transactions](#10-transactions)
11. [Caching](#11-caching)
12. [Logging](#12-logging)
13. [Security](#13-security)
14. [Permissions](#14-permissions)
15. [Testing](#15-testing)
16. [Imports](#16-imports)
17. [Dependency Rules](#17-dependency-rules)
18. [Migrations](#18-migrations)
19. [API Versioning](#19-api-versioning)
20. [Documentation](#20-documentation)
21. [Code Review Checklist](#21-code-review-checklist)
22. [Definition of Done](#22-definition-of-done)
23. [Definition of Ready](#23-definition-of-ready)
24. [Anti-patterns](#24-anti-patterns)
25. [Forbidden Practices](#25-forbidden-practices)
26. [Architecture Violations](#26-architecture-violations)
27. [CI Requirements](#27-ci-requirements)

---

## 1. Folder Structure

### 1.1 Root Layout

```
rentsecure_be/
├── manage.py
├── pyproject.toml
├── pytest.ini
├── mypy.ini
├── ruff.toml
├── import-linter.ini
├── .env.example
├── .pre-commit-config.yaml
├── .gitignore
│
├── core/                        # Identity model container (User, UserProfile, OTP)
│   ├── __init__.py
│   ├── models.py                # ONLY identity models after Phase 5
│   ├── views/                   # Deprecated; removed in Phase 5
│   ├── services/                # Deprecated; removed in Phase 5
│   ├── serializers.py           # Deprecated; removed in Phase 5
│   ├── urls.py                  # Deprecated; removed in Phase 5
│   ├── management/
│   │   └── commands/
│   └── migrations/
│
├── identity/                    # Identity bounded context (services, views)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── otp_service.py
│   │   └── password_service.py
│   ├── views/
│   │   ├── __init__.py
│   │   ├── auth_views.py
│   │   ├── otp_views.py
│   │   └── password_views.py
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   └── migrations/
│
├── properties/                  # Property bounded context
│   ├── models/
│   │   ├── __init__.py
│   │   ├── unit_models.py
│   │   ├── rent_record_models.py
│   │   └── ...
│   ├── services/
│   ├── views/
│   ├── repositories/            # Phase 6+
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── contract/
│   ├── management/
│   │   └── commands/
│   └── migrations/
│
├── subscription/                # Subscription bounded context
│   ├── models.py
│   ├── services/
│   ├── views/
│   ├── tests/
│   ├── management/
│   │   └── commands/
│   └── migrations/
│
├── payments/                    # Payment bounded context
│   ├── models.py
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── manual.py
│   │   ├── cashfree.py
│   │   ├── razorpay.py
│   │   └── cashfree_client.py
│   ├── ports/
│   │   └── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── webhook_service.py
│   │   └── bank_details_service.py
│   ├── views/
│   │   ├── __init__.py
│   │   ├── webhooks.py
│   │   └── bank_details_views.py
│   ├── urls.py
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── contract/
│   └── migrations/
│
├── notification/                # Notification bounded context
│   ├── models.py
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── email.py
│   │   ├── fcm.py
│   │   ├── inapp.py
│   │   ├── whatsapp.py
│   │   └── sms.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── notification_dispatcher.py
│   ├── views/
│   ├── tests/
│   ├── management/
│   │   └── commands/
│   └── migrations/
│
├── documents/                   # Document bounded context
├── finance/                     # Finance bounded context
├── referral/                    # Referral bounded context
├── dashboard/                   # Dashboard bounded context (experimental)
│   ├── services/
│   ├── views/
│   ├── repositories/
│   ├── tests/
│   └── migrations/
│
├── smartbot/                    # AI assistant (active)
├── ai_assistant/                # AI assistant (dead code; remove in Phase 6)
│
├── shared/                      # Shared kernel (no business logic)
│   ├── __init__.py
│   ├── fields.py                # EncryptedCharField, EncryptedTextField
│   ├── type_compat.py
│   ├── exceptions.py
│   ├── domain_events.py
│   └── tests/
│
├── platform/                    # Infrastructure adapters
│   ├── cache/
│   ├── storage/
│   ├── search/
│   └── events/
│
├── tests/                       # Cross-cutting tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── factories.py
│   ├── architecture/
│   │   ├── test_import_rules.py
│   │   ├── test_layer_compliance.py
│   │   ├── test_sdk_placement.py
│   │   ├── test_god_views.py
│   │   ├── test_god_models.py
│   │   ├── test_circular_deps.py
│   │   ├── test_rentsecure_be_boundary.py
│   │   └── test_shared_purity.py
│   ├── contract/
│   ├── performance/
│   └── test_migrations.py
│
├── docs/                        # Documentation
│   ├── architecture/
│   │   ├── adr/
│   │   ├── contexts/
│   │   └── principles.md
│   ├── api/
│   ├── deployment/
│   └── migration/
│
├── rentsecure_be/               # Django project config
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
└── management/                  # REMOVED in Phase 0 — commands move to app directories
```

### 1.2 Forbidden Root Directories

- **`apps/`** — Rejected. Apps live at project root. See ADR-001.
- **`config/`** — Rejected. Django configuration stays in `rentsecure_be/settings/`. See ADR-001.
- **Root `management/commands/`** — Rejected. Commands live in app `management/commands/`. See ADR-007.

### 1.3 Mandatory App Subdirectories

Every active Django app MUST contain:

| Subdirectory | Required | Purpose |
|--------------|----------|---------|
| `models/` or `models.py` | Yes | Model definitions |
| `services/` | Yes | Business logic |
| `views/` | Yes | HTTP endpoints |
| `tests/` | Yes | Tests (unit, integration, contract) |
| `management/commands/` | Yes | Management commands |
| `migrations/` | Yes | Django migrations |
| `serializers.py` | Optional | DRF serializers (if API) |
| `urls.py` | Optional | App URL patterns |
| `repositories/` | Phase 6+ | Repository pattern (selective) |

---

## 2. Naming Conventions

### 2.1 Files and Directories

| Artifact | Convention | Example |
|----------|-----------|---------|
| Python files | `snake_case` | `auth_service.py`, `bank_details_views.py` |
| Python packages | `snake_case` | `identity/services/` |
| Django apps | `snake_case` | `properties`, `payments`, `notification` |
| Test files | `test_<module>.py` | `test_auth_service.py` |
| Test directories | `tests/` at app root | `properties/tests/unit/` |
| Migration files | Auto-generated by Django | `0001_initial.py` |
| Management commands | `snake_case` | `send_rent_reminders.py` |
| Architecture tests | `test_<rule>.py` | `test_god_views.py` |

### 2.2 Classes

| Artifact | Convention | Example |
|----------|-----------|---------|
| Models | `PascalCase` | `User`, `OwnerBankDetails`, `RentRecord` |
| Services | `PascalCase` + `Service` suffix | `AuthService`, `BankDetailsService` |
| Views | `PascalCase` + `View` suffix (class) or `snake_case` (function) | `SendOTPView`, `send_otp` |
| Serializers | `PascalCase` + `Serializer` suffix | `UserSerializer`, `RentRecordSerializer` |
| Adapters | `PascalCase` + `Adapter` suffix | `EmailAdapter`, `CashfreeAdapter` |
| Repositories | `PascalCase` + `Repository` suffix | `OwnerReportingRepository` |
| Forms | `PascalCase` + `Form` suffix | `BankDetailsForm` |
| Permissions | `PascalCase` + `Permission` suffix | `IsOwnerPermission` |

### 2.3 Functions and Methods

| Artifact | Convention | Example |
|----------|-----------|---------|
| Functions | `snake_case` | `send_otp`, `verify_webhook` |
| Methods | `snake_case` | `get_queryset`, `perform_create` |
| Private methods | `_snake_case` | `_validate_bank_details` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_UPLOAD_SIZE`, `DEFAULT_CACHE_TTL` |

### 2.4 Variables

| Artifact | Convention | Example |
|----------|-----------|---------|
| Local variables | `snake_case` | `user`, `rent_amount` |
| Instance variables | `snake_case` | `self.user`, `self.payment_status` |
| Class variables | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |

### 2.5 Databases and Migrations

| Artifact | Convention | Example |
|----------|-----------|---------|
| Database tables | `appname_modelname` | `core_user`, `payment_ownerbankdetails` |
| Migration names | Auto-generated or `descriptive_name` | `0002_migrate_ownerbankdetails` |

### 2.6 URLs

| Artifact | Convention | Example |
|----------|-----------|---------|
| URL patterns | `snake_case` with hyphens in paths | `api/owner/bank-details/` |
| URL names | `snake_case` | `owner_bank_details_update` |
| Namespaces | `snake_case` | `payments:webhook:cashfree` |

---

## 3. DDD Rules

### 3.1 Bounded Contexts

- Each bounded context is a Django app with a single owner team.
- Apps must not contain logic from other domains.
- Domain events replace direct cross-context calls over time (Phase 6+).

### 3.2 Entities

- Entities have a unique identity (`id`).
- Entities contain business methods that operate on their own data.
- Entities must not import from other apps.

### 3.3 Value Objects

- Value objects are immutable and defined in the owning app.
- Value objects may live in `models/` or `types.py` within the app.
- Shared value objects (e.g., `Money`) live in `shared/`.

### 3.4 Aggregates

- Aggregates are clusters of entities treated as a unit.
- Aggregate roots are the only entry point for external access.
- Example: `RentRecord` is the aggregate root for rent cycle, late fees, and payment requests.

### 3.5 Domain Events

- Domain events are facts that have occurred in the domain.
- Events are immutable and named in past tense: `PaymentApproved`, `RentRecordCreated`.
- Events are defined in `shared/domain_events.py` or app-specific `events.py`.
- Events are published via the event bus (Phase 6+). Until then, events are emitted via explicit service calls.

### 3.6 Domain Services

- Domain services contain logic that does not naturally belong to an entity.
- Domain services live in `services/` within the owning app.
- Domain services must not import from other apps' `models/` or `views/`.

### 3.7 Repositories

- Repositories are used for complex queries (3+ tables, 3+ services). See [Repository Rules](#8-repository-rules).
- Repositories live in the owning app's `repositories/` directory.
- Repositories are introduced in Phase 6. Until then, services use Django ORM directly.

### 3.8 Anti-Corruption Layer

- Adapters translate external systems (payment gateways, notification providers) to internal interfaces.
- Adapters live in `adapters/` within the owning app (e.g., `payments/adapters/`).
- Adapters implement ports defined in `ports/` or `shared/`.

---

## 4. Service Rules

### 4.1 General

- All business logic MUST live in services, never in views or serializers.
- Services are the only entry point for business workflows.
- Services must be stateless. State is passed as method parameters.
- Services must not import from other apps' `views/` or `models/`.

### 4.2 Service Location

| Service Type | Location |
|-------------|----------|
| Identity services | `identity/services/` |
| Subscription services | `subscription/services/` |
| Payment services | `payments/services/` |
| Domain notification triggers | `properties/services/` (NOT `notification/services/`) |
| Reporting services | `dashboard/services/` |
| Platform services | `platform/` (infrastructure only) |

### 4.3 Service Naming

- Service classes end with `Service`: `AuthService`, `BankDetailsService`.
- Service methods use `snake_case`: `send_otp()`, `approve_payment()`.
- Service methods return domain objects or result wrappers, never HTTP responses.

### 4.4 Service Dependencies

- Services depend on other services via constructor injection or method parameters.
- Services must not instantiate their own dependencies (no `Adapter()` inside service methods).
- Services must not depend on Django `settings` directly (use dependency injection).

### 4.5 Error Handling

- Services raise domain-specific exceptions defined in `shared/exceptions.py`.
- Services must not catch and suppress exceptions silently.
- Services must not return `None` for error cases; use result wrappers or raise exceptions.

---

## 5. Serializer Rules

### 5.1 General

- Serializers are for **validation and representation only**.
- Serializers must not contain business logic.
- Serializers must not call external APIs or services directly.
- Serializers must not perform database writes outside `create()` / `update()`.

### 5.2 Structure

- Serializers live in `serializers.py` within the app.
- Use separate serializers for input validation and output representation.
- Example: `RentRecordCreateSerializer` (input) vs `RentRecordSerializer` (output).

### 5.3 Validation

- All input validation MUST happen in serializers.
- Use DRF field validators (`validate_<field>()`) and object validators (`validate()`).
- Do not perform validation in views or services for incoming API payloads.

---

## 6. View Rules

### 6.1 General

- Views are **thin** — they delegate to services and return responses.
- Views must not contain business logic, validation logic, or external API calls.
- Views must not import models from other apps (use services instead).
- Views must not import payment SDKs (`razorpay`, `cashfree`) directly.
- Views must not import from `rentsecure_be/`.

### 6.2 View Types

| View Type | Use Case | Location |
|-----------|----------|----------|
| `APIView` | Custom API endpoints | `views/<domain>_views.py` |
| `GenericAPIView` + mixins | CRUD endpoints | `views/<domain>_views.py` |
| `ViewSet` | RESTful resource collections | `views/<domain>_views.py` |
| Function-based views | Simple endpoints, webhooks | `views/webhooks.py` |

### 6.3 View Size Limit

- No view file may exceed **300 lines**.
- If a view file exceeds 300 lines, split by domain responsibility.

### 6.4 What Views Must Not Do

- Must not call `PaymentGateway` directly (use `PaymentService`).
- Must not call `NotificationChannel` directly (use `NotificationService`).
- Must not query multiple apps' models (use services).
- Must not perform data migrations.
- Must not log sensitive data (OTPs, bank details, tokens).

---

## 7. Model Rules

### 7.1 General

- Models represent the domain and MUST NOT contain business logic.
- Models must not import from other apps' `views/` or `services/`.
- Models must not import from `rentsecure_be/`.
- Models must not call external APIs.

### 7.2 Model Size Limit

- No `models.py` or `models/*.py` file may exceed **400 lines**.
- If a model file exceeds 400 lines, split into:
  - `unit.py` (model definitions)
  - `unit_validators.py` (validators)
  - `unit_choices.py` (TextChoices)

### 7.3 Field Naming

- Use `snake_case` for field names: `bank_account_number`, `ifsc_code`.
- Use `null=True, blank=True` for optional fields.
- Use `default=` for fields with sensible defaults.
- Never use `null=True` on `CharField` or `TextField` (use `blank=True` + `default=''`).

### 7.4 Foreign Keys

- All ForeignKeys MUST use `settings.AUTH_USER_MODEL` string references.
- All cross-app ForeignKeys MUST use string references: `"properties.Unit"`.
- Direct imports of `User` model (`from core.models import User`) are FORBIDDEN in models, views, and services.
- Use `TYPE_CHECKING` blocks for type hints with ForeignKeys.

```python
from typing import TYPE_CHECKING
from django.conf import settings
from django.db import models

if TYPE_CHECKING:
    from core.models import User

class RentRecord(models.Model):
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rent_records",
    )
```

### 7.5 Sensitive Fields

- `bank_account_number` and `ifsc_code` MUST use encrypted field types (`EncryptedCharField`).
- All PII fields (email, phone, address) must be evaluated for encryption requirements.
- Sensitive fields must not be logged, printed, or exposed in error messages.

### 7.6 Model Managers

- Use custom managers for common querysets: `RentRecord.objects.active()`.
- Managers must not contain business logic (only queryset filtering).
- Business logic belongs in services or repositories.

---

## 8. Repository Rules

### 8.1 When to Use Repositories

Use a repository if and only if:
- Query spans **3+ tables** AND
- Query is used by **3+ services**

Use Django ORM directly if:
- Query touches **1-2 tables** OR
- Query is used by **1-2 services**

### 8.2 Repository Structure

- Repositories live in the owning app's `repositories/` directory.
- Repository names end with `Repository`: `OwnerReportingRepository`.
- Repository methods return domain objects, querysets, or result wrappers.
- Repositories must not contain business logic (only query logic).

### 8.3 Repository Dependencies

- Repositories depend on Django ORM only.
- Repositories must not import from other apps.
- Repositories are used by services, never by views.

### 8.4 Phase Introduction

- Repositories are introduced in **Phase 6**.
- Until Phase 6, all data access uses Django ORM directly in services.

---

## 9. Signals

### 9.1 General

- Django signals are FORBIDDEN for business logic.
- Signals are ONLY allowed for infrastructure events:
  - `post_save` for audit logging (via `django-simple-history`)
  - `post_migrate` for data seeding
- All business events must go through explicit service calls or the event bus (Phase 6+).

### 9.2 Signal Rules

- Signal handlers must be registered in `apps.py` (`ready()` method), never in `models.py` or `views.py`.
- Signal handlers must be thin: delegate to services.
- Signal handlers must not import from other apps' `views/` or `models/`.

### 9.3 Prohibited Signal Patterns

- `@receiver` decorators in `models.py` or `views.py` — FORBIDDEN.
- Signal handlers that query other apps' models — FORBIDDEN.
- Signal handlers that send notifications directly — FORBIDDEN (use `NotificationService`).

---

## 10. Transactions

### 10.1 General

- All financial operations MUST be wrapped in `@transaction.atomic()`.
- All multi-model writes MUST be wrapped in `@transaction.atomic()`.
- Use `select_for_update()` for pessimistic locking when race conditions are possible.

### 10.2 Financial Operations

- Payment approval/rejection MUST be atomic.
- Bank details updates MUST be atomic.
- Subscription creation/renewal MUST be atomic.
- Rent record generation MUST be atomic.

### 10.3 Distributed Locking

- Use distributed locking for critical financial operations (see Security rules).
- Year 1: Use Django cache lock (`cache.add` with expiry) for single-process safety.
- Stage 2: Use Redis lock for multi-process safety.

### 10.4 Error Handling

- Catch `IntegrityError` and translate to domain exceptions.
- Never swallow `TransactionManagementError`.
- Always provide rollback instructions in error messages.

---

## 11. Caching

### 11.1 Year 1 Cache Backend

- **Django Local Memory Cache (`LocMemCache`)** is the default for Year 1.
- Redis cache backend is introduced in Phase 6 via `platform/cache/redis.py`.
- `CACHE_BACKEND` setting controls which backend is active (defaults to `locmem`).

### 11.2 What to Cache

| Data | Cache TTL | Rationale |
|------|-----------|-----------|
| Dashboard metrics | 5 minutes | Expensive aggregation queries |
| Owner reports | 5 minutes | Expensive aggregation queries |
| Feature flags | 1 minute | Changes are rare but must propagate |
| Session data | Default | Django session framework |
| Static assets | Forever | CDN / `ManifestStaticFilesStorage` |

### 11.3 What NOT to Cache

- Financial data (payment status, bank details) — NEVER cache without explicit encryption.
- Real-time notification counts — stale data causes UX issues.
- Permission checks — security risk if stale.

### 11.4 Cache Keys

- Use namespaced cache keys: `rentsecure:owner_report:{owner_id}:{month}`.
- Never use user input directly in cache keys without sanitization.
- Document cache key format in code comments.

---

## 12. Logging

### 12.1 Log Levels

| Level | Use Case |
|-------|----------|
| `DEBUG` | Development only. Detailed diagnostic info. |
| `INFO` | Normal operation: request received, payment approved, email sent. |
| `WARNING` | Recoverable issues: retry attempted, fallback used, deprecated API called. |
| `ERROR` | Failures: webhook processing failed, external API timeout, database error. |
| `CRITICAL` | System failure: database unavailable, payment gateway down. |

### 12.2 What to Log

- All incoming webhooks (provider, event type, status).
- All payment state changes (submitted, approved, rejected).
- All authentication events (login, logout, OTP requested, OTP verified).
- All permission denials (who, what endpoint, when).
- All external API calls (provider, endpoint, status, latency).

### 12.3 What NOT to Log

- OTPs — NEVER log, even in DEBUG mode.
- Bank account numbers — log only `last_4` for debugging.
- IFSC codes — never log.
- API keys, tokens, secrets — never log.
- Full request/response bodies for payment webhooks — log only event_id and status.

### 12.4 Log Format

```python
import structlog

logger = structlog.get_logger(__name__)

logger.info(
    "payment_approved",
    payment_id=str(payment.id),
    owner_id=str(owner.id),
    amount=payment.amount,
    payout_status=payment.payout_status,
)
```

### 12.5 Audit Logging

- `django-simple-history` is enabled for:
  - `OwnerBankDetails`
  - `WebhookEvent`
  - `RentRecord.payout_status`
- Audit logs include: user, timestamp, old value, new value.
- Audit logs are immutable (no delete or update).

---

## 13. Security

### 13.1 Sensitive Data

- Bank account numbers and IFSC codes MUST use encrypted fields (`EncryptedCharField`).
- All PII fields (email, phone, address) must be evaluated for encryption.
- Sensitive data must never appear in logs, error messages, or API responses.

### 13.2 Webhook Security

- All incoming webhooks MUST verify HMAC signature.
- All webhooks MUST implement idempotency via `WebhookEvent` model with `event_id` unique constraint.
- Webhook endpoints MUST return 200 for duplicates (idempotent replay).
- Webhook endpoints MUST return 401 for invalid signatures.

### 13.3 Secrets Management

- All secrets (API keys, database credentials, JWT secrets) MUST come from environment variables.
- `.env` files MUST be in `.gitignore`.
- `python-decouple` or `django-environ` is used for configuration.
- Secrets MUST NOT be committed to the repository.
- Secrets MUST NOT appear in logs or error messages.

### 13.4 OTP Security

- OTPs MUST NOT be logged or printed, even in DEBUG mode.
- OTPs MUST expire after 10 minutes.
- OTPs MUST have a maximum of 3 verification attempts.
- Use a dedicated test phone number with known OTP in test environments.

### 13.5 Password Security

- Passwords MUST be hashed with Django's `PBKDF2PasswordHasher` (default).
- Passwords MUST NOT be logged or returned in API responses.
- Password reset tokens MUST expire after 1 hour.
- Password reset tokens MUST be single-use.

### 13.6 Idempotency

- All payment flows MUST be idempotent.
- All webhook handlers MUST support retries.
- All async tasks MUST support retry policies.
- Use distributed locking for critical financial operations.

### 13.7 Security Scanning

- Bandit scan runs on every PR (0 high/medium vulnerabilities allowed).
- Safety dependency audit runs on every PR (0 critical vulnerabilities allowed).
- Security review required before production deploy.

---

## 14. Permissions

### 14.1 General

- All API endpoints MUST have explicit permission checks.
- Default permission: `IsAuthenticated`.
- Use DRF permission classes for access control.
- Never rely on "security through obscurity" (hidden URLs, unlisted endpoints).

### 14.2 Permission Rules

| Resource | Permission |
|----------|-----------|
| Owner can view own properties | `IsOwner` |
| Tenant can view own rent records | `IsTenant` |
| Admin can view all | `IsAdmin` |
| Payment webhooks (incoming) | `WebhookSignaturePermission` |
| Password reset | `AllowAny` (token validated in service) |

### 14.3 Permission Implementation

- Custom permissions inherit from `BasePermission`.
- Permission checks MUST happen in `has_permission()` or `has_object_permission()`.
- Permission checks MUST NOT happen in views or serializers.
- Permission checks MUST NOT happen in services (services assume permissions are validated).

### 14.4 Object-Level Permissions

- Use `django-guardian` or custom `has_object_permission()` for row-level access.
- Object-level permission checks MUST happen in the view or permission class, never in the service.
- Services receive the user as a parameter and assume the caller has already validated permissions.

---

## 15. Testing

### 15.1 Test Tiers

| Tier | Scope | Owner | Frequency | Blocking |
|------|-------|-------|-----------|----------|
| **Unit** | Services, models, utilities | App team | Every commit | Yes |
| **Integration** | View → Service → Model | App team | Every commit | Yes |
| **Contract** | App boundaries (public APIs) | Architecture team | Every PR | Yes |
| **Architecture** | Import rules, layer compliance, god views/models | Architecture team | Every commit | Yes |
| **Migration** | Forward + reverse + data integrity | App team | Every PR | Yes |
| **Security** | OWASP Top 10, secrets, webhooks | Security team | Every release | Yes |
| **Performance** | Query counts, response times | App team | Nightly | No |

### 15.2 Coverage Requirements

| Metric | Requirement | Enforcement |
|--------|-------------|-------------|
| Unit test coverage | ≥90% | Blocking in CI |
| Integration test coverage | ≥80% | Blocking in CI |
| Architecture test pass rate | 100% | Blocking in CI |
| Mutation testing score | ≥80% | Blocking in CI (from Phase 0) |
| Performance p95 | <200ms | Non-blocking (nightly alert) |

### 15.3 Test Location

- Unit tests: `app/tests/unit/`
- Integration tests: `app/tests/integration/`
- Contract tests: `app/tests/contract/` or `tests/contract/`
- Architecture tests: `tests/architecture/`
- Migration tests: `tests/test_migrations.py`

### 15.4 Test Naming

- Test files: `test_<module>.py`
- Test classes: `Test<Class>` (e.g., `TestAuthService`)
- Test methods: `test_<behavior>` (e.g., `test_send_otp_creates_record`)

### 15.5 Test Factories

- Use `factory_boy` for test data creation.
- Factories live in `tests/factories.py`.
- Each app may have app-specific factories in `app/tests/factories.py`.

### 15.6 Mocking

- Mock external services (payment gateways, notification providers) in unit tests.
- Mock Django `settings` when testing configuration-dependent code.
- Do NOT mock Django ORM in integration tests (use test database).
- Do NOT mock the service layer in view tests (use real services with test database).

### 15.7 Dead Code Tests

- `ai_assistant/` and `dashboard/` tests are EXCLUDED from coverage reports until activated.
- Exclude via `.coveragerc`:
  ```ini
  [run]
  omit =
      */ai_assistant/*
      */dashboard/*
  ```

---

## 16. Imports

### 16.1 Import Order

Use `ruff` with `isort` configuration. Standard order:

1. Standard library
2. Third-party packages
3. Django imports
4. App imports (alphabetical within each group)

```python
# Standard library
import os
from typing import TYPE_CHECKING

# Third-party
import structlog
from django.conf import settings
from rest_framework import status

# App imports
from core.models import User
from payments.services import PaymentService
from properties.models import Unit
```

### 16.2 Forbidden Imports

| Import | Forbidden In | Allowed In |
|--------|-------------|------------|
| `from rentsecure_be.X import Y` | All apps | `rentsecure_be/` only |
| `from razorpay` | All files except `payments/adapters/razorpay.py` | `payments/adapters/` |
| `from cashfree` | All files except `payments/adapters/cashfree.py` | `payments/adapters/` |
| `from twilio` | All files except `notification/adapters/sms.py` | `notification/adapters/` |
| `from boto3` | All files except `notification/adapters/` and `documents/` | Adapter modules |
| `from core.models import User` | Models, views, services (use string refs) | `TYPE_CHECKING` blocks only |
| `from core.views import ...` | Direct `core.views` import | `core.views.auth_views`, etc. |
| `from properties.models import ...` | Apps other than `properties/` and tests | `properties/` services via interfaces |

### 16.3 Import Style

- Use absolute imports, not relative imports.
- Use `from module import Class` style, not `import module.Class`.
- Import one class per line when practical, or group related classes:

```python
# Preferred
from core.models import User
from core.models import UserProfile

# Acceptable
from core.models import User, UserProfile

# Avoid
from core import models
```

---

## 17. Dependency Rules

### 17.1 Allowed Import Matrix

| Source | shared | platform | identity | subscription | property | payment | notification | document | finance | referral | dashboard |
|--------|--------|----------|----------|--------------|----------|---------|--------------|----------|---------|----------|-----------|
| **shared** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **platform** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **identity** | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **subscription** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **property** | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **payment** | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **notification** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **document** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **finance** | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ |
| **referral** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **dashboard** | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ |
| **ai_assistant** | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ |

### 17.2 Key Rules

1. **No app may import from `rentsecure_be/`** (except `rentsecure_be/` itself).
2. **`payment/` may import from `property/`** (needs `RentRecord` data).
3. **`notification/` may NOT import from `property/` directly.** Domain notification triggers live in `properties/services/` and call `notification/` adapters.
4. **`ai_assistant/` is deferred** — partial dependencies shown, no active enforcement until activated.
5. **`rent/` is removed** from the matrix. Rent logic stays in `properties/`.

### 17.3 Enforcement

- `import-linter.ini` encodes the allowed import matrix.
- `tests/architecture/test_import_rules.py` and `test_layer_compliance.py` enforce boundaries.
- All violations block CI.

---

## 18. Migrations

### 18.1 General

- Migrations MUST be reversible unless explicitly marked irreversible.
- Data migrations MUST preserve all data.
- Migrations MUST be tested forward and backward in CI.
- Migrations MUST NOT delete data without explicit approval and rollback plan.

### 18.2 Naming

- Auto-generated migrations: `XXXX_<auto_name>.py`.
- Data migrations: `XXXX_<descriptive_name>.py` (e.g., `0002_migrate_ownerbankdetails.py`).

### 18.3 Data Migrations

- Data migrations MUST be additive (copy data, don't delete).
- Old tables MUST be retained for 1 release cycle before deletion.
- Data migrations MUST be tested on production-like data before merge.
- Data migrations MUST include row count and checksum verification.

### 18.4 Migration Testing

- Every migration is tested with `manage.py migrate` (forward) and `manage.py migrate --reverse` (backward).
- Data migrations include integrity tests (row counts, checksums).
- Migration tests run in CI on every PR touching migrations.

### 18.5 Migration Policy

| Phase | Migration Risk | Rollback Requirement |
|-------|---------------|----------------------|
| Phase -1 | Low (empty initial) | Revert + `migrate --reverse` |
| Phase 0 | Medium (data copy) | Revert + `migrate --reverse` (old table remains) |
| Phase 1-4 | None (services only) | Revert PR |
| Phase 5 | High (table drops) | Restore from backup |
| Phase 6 | Low (new tables) | Revert + `migrate --reverse` |

---

## 19. API Versioning

### 19.1 Versioning Strategy

- Year 1: No API versioning. All endpoints are `/api/v1/` implicitly.
- API versioning is introduced when external consumers require stable contracts.
- Breaking changes ONLY happen in Phase 5 (v2.0.0).

### 19.2 Backward Compatibility

| Phase | Compatibility | Mechanism |
|-------|---------------|-----------|
| Phase -1 | 100% | Additive changes only |
| Phase 0 | 100% | Additive changes only |
| Phase 1-4 | 100% | Deprecated shims + redirects |
| Phase 5 | Breaking | v2.0.0 release with migration guide |
| Phase 6 | 100% | Additive changes only |

### 19.3 Deprecation Policy

- Old URLs return `301/302` redirects during transition (Phases 1-4).
- Deprecated endpoints include `Deprecation` header.
- Deprecated endpoints are monitored for usage before removal.
- Migration guide published before v2.0.0 release.

---

## 20. Documentation

### 20.1 Required Documentation

| Document | Owner | Update Trigger |
|----------|-------|----------------|
| `ARCHITECTURE_V1.1.md` | Staff Engineer | After each phase |
| `docs/architecture/contexts/<name>.md` | App owner | After each phase |
| `docs/api/` | App owner | After each phase |
| `docs/deployment/` | DevOps | After each phase |
| `README.md` | Staff Engineer | After each phase |
| `CHANGELOG.md` | DevOps | Every release |
| `docs/migration/v1-to-v2.md` | Staff Engineer | Before v2.0.0 |

### 20.2 Context Documentation

Each bounded context MUST have a context document (`docs/architecture/contexts/<name>.md`) containing:
- Ownership (team)
- Responsibilities
- Public APIs (endpoints and services)
- Dependencies (allowed imports)
- Data model (key entities)
- Sequence diagrams for key workflows

### 20.3 API Documentation

- All endpoints MUST be documented in `docs/api/`.
- Documentation includes: URL, method, permissions, request body, response body, error codes.
- OpenAPI/Swagger is generated from DRF schema (preferred) or maintained manually.

---

## 21. Code Review Checklist

Every PR MUST pass this checklist before merge.

### Architecture

- [ ] No business logic in views or serializers (delegates to services)
- [ ] No `rentsecure_be/` imports in app code
- [ ] No payment SDK imports (`razorpay`, `cashfree`) outside `payments/adapters/`
- [ ] No `twilio`/`boto3` imports outside allowed adapter modules
- [ ] No `core.models.User` direct imports (use `settings.AUTH_USER_MODEL` string refs)
- [ ] No `core.views` direct imports (use submodules)
- [ ] No circular dependencies introduced
- [ ] No new `apps/` or `config/` directories
- [ ] No `ai_assistant/` activation without ADR

### Security

- [ ] No secrets, API keys, or tokens in code or logs
- [ ] No OTPs logged or printed
- [ ] No bank account numbers or IFSC codes in plaintext
- [ ] All webhooks verify HMAC signatures
- [ ] All webhooks implement idempotency
- [ ] All financial operations use `@transaction.atomic()`
- [ ] All permissions are explicit (no implicit access)
- [ ] No SQL injection vectors (use ORM, parameterized queries)
- [ ] No XSS vectors (escape output in templates)
- [ ] Bandit scan passes (0 high/medium)
- [ ] Safety scan passes (0 critical)

### Testing

- [ ] All new code has unit tests (≥90% coverage for new code)
- [ ] All integration tests pass
- [ ] Architecture tests pass
- [ ] Migration tests pass (if migration included)
- [ ] No `ai_assistant/` or `dashboard/` tests inflate coverage
- [ ] Tests use factories, not hardcoded data
- [ ] No test depends on execution order
- [ ] No test uses `time.sleep()` (use freezegun or mocking)

### Code Quality

- [ ] Ruff passes (0 errors)
- [ ] MyPy passes (0 errors)
- [ ] No `print()` statements (use `logger`)
- [ ] No commented-out code
- [ ] No `# TODO` without issue reference
- [ ] No `# FIXME` without owner and date
- [ ] No `pass` statements without comment
- [ ] No empty `except:` clauses
- [ ] No bare `except Exception:` without re-raise or logging

### Migrations

- [ ] Migration is reversible (or marked irreversible with justification)
- [ ] Data migration includes forward and reverse tests
- [ ] Data migration includes integrity checks (row counts, checksums)
- [ ] No destructive operations without explicit approval
- [ ] Migration naming is descriptive

### Documentation

- [ ] Context documentation updated (if bounded context changed)
- [ ] API documentation updated (if endpoint changed)
- [ ] ADR created (if architectural decision made)
- [ ] CHANGELOG.md updated (for releases)

---

## 22. Definition of Done

A task is **Done** when ALL of the following are true:

### Code

- [ ] Code is written, reviewed, and merged to the phase branch.
- [ ] All CI gates pass: lint, type check, import rules, tests, architecture, security, mutation.
- [ ] No architecture test violations.
- [ ] No import-linter violations.
- [ ] No circular dependencies.
- [ ] No security vulnerabilities (Bandit 0 high/medium, Safety 0 critical).

### Tests

- [ ] Unit tests written for all new services, models, and utilities (≥90% coverage).
- [ ] Integration tests written for all new endpoints and workflows (≥80% coverage).
- [ ] Architecture tests pass (new code does not violate boundaries).
- [ ] Migration tests pass (if migration included).
- [ ] Contract tests pass (if cross-context API changed).
- [ ] All existing tests still pass (no regressions).

### Security

- [ ] No secrets in code or logs.
- [ ] No sensitive data exposed in API responses.
- [ ] All webhooks verify HMAC (if webhook changed).
- [ ] All webhooks implement idempotency (if webhook changed).
- [ ] All financial operations use transactions (if payment flow changed).
- [ ] All permissions are explicit (if endpoint changed).

### Documentation

- [ ] Context documentation updated (if bounded context changed).
- [ ] API documentation updated (if endpoint changed).
- [ ] ADR created and approved (if architectural decision made).
- [ ] CHANGELOG.md updated (for releases).

### Deployment

- [ ] Code deployed to staging.
- [ ] Staging validation passed (24 hours for Phase 0-4, 48 hours for webhooks, 3 days for Phase 5).
- [ ] Rollback procedure documented and tested.
- [ ] No production incidents during staging validation.

### Rollback

- [ ] Rollback procedure documented in the PR.
- [ ] Rollback tested on staging (for Phases 0-5).
- [ ] Rollback time measured and within acceptable limits.

---

## 23. Definition of Ready

A task is **Ready** when ALL of the following are true:

### Clarity

- [ ] Task has a clear, single-sentence description.
- [ ] Acceptance criteria are defined (Gherkin-style preferred).
- [ ] Task is scoped to a single PR (≤400 lines, ≤15 files).
- [ ] Dependencies are identified and completed (or explicitly allowed to proceed).
- [ ] No blocking dependencies on other teams.

### Design

- [ ] Architecture decision is documented (ADR if architectural).
- [ ] Affected apps and services are identified.
- [ ] Data migration plan is defined (if model change).
- [ ] Rollback strategy is defined.
- [ ] API contract changes are documented (if API change).

### Testing

- [ ] Test strategy is defined (unit, integration, contract, architecture).
- [ ] Test data requirements are identified.
- [ ] Test environment is ready (fixtures, factories, mocks).

### Documentation

- [ ] Context documentation update is planned (if bounded context changed).
- [ ] API documentation update is planned (if endpoint changed).
- [ ] Migration guide update is planned (if breaking change).

### Security

- [ ] Security review is scheduled (for financial, auth, or webhook changes).
- [ ] Sensitive data handling is documented (if PII or financial data).
- [ ] Permission changes are reviewed (if access control changed).

---

## 24. Anti-patterns

### 24.1 God Objects

- **God View:** `core/views.py` with 566 lines containing OTP, password, subscription, bank details, and webhooks. FORBIDDEN.
- **God Model:** `properties/models/unit_models.py` with 482 lines. FORBIDDEN.
- **God Service:** `rentsecure_be/services/` containing Cashfree, Razorpay, Leegality, and i18n services. FORBIDDEN.
- **God App:** `core/` containing identity, payment, subscription, reporting, and bank details. FORBIDDEN.

### 24.2 Anemic Models

- Models that are pure data containers with no behavior are acceptable for simple entities.
- Models that have complex business logic spread across services are acceptable.
- Models that have behavior in views (God View anti-pattern) are FORBIDDEN.

### 24.3 Leaky Abstractions

- Services that expose ORM querysets to views (views filter/sort directly).
- Repositories that expose Django ORM internals to services.
- Adapters that expose provider-specific exceptions to services.

### 24.4 Shotgun Surgery

- Changing a single business rule requires editing 10+ files across 5 apps.
- Mitigation: Use domain events and service layer to centralize business logic.

### 24.5 Golden Hammer

- Using the repository pattern for every query (over-engineering).
- Using signals for every cross-context communication (hard to trace).
- Using microservices for every bounded context (premature).

### 24.6 Spaghetti Dependencies

- Circular dependencies between apps.
- Apps importing from `rentsecure_be/` as a service locator.
- `notification/` importing `properties.models.RentRecord` directly.

### 24.7 Magic Numbers and Strings

- Hardcoded URLs, provider keys, and configuration values in code.
- Mitigation: Use settings, environment variables, and constants.

### 24.8 Copy-Paste Duplication

- Duplicate management commands at root level.
- Duplicate `send_monthly_rent_summary` in root and `properties/`.
- Mitigation: Single source of truth in owning app.

---

## 25. Forbidden Practices

These practices are FORBIDDEN and will block CI.

### 25.1 Code

- `print()` statements for logging (use `structlog`).
- `raise Exception` without custom exception class.
- Bare `except:` or `except Exception:` without logging.
- `pass` statements without explanatory comment.
- `time.sleep()` in production code (use async tasks).
- `os.system()` or `subprocess` with user input (command injection risk).
- `pickle.loads()` on untrusted data (deserialization vulnerability).
- `md5` or `sha1` for security purposes (use `sha256` or Django's password hashers).

### 25.2 Models

- `null=True` on `CharField` or `TextField` (use `blank=True, default=''`).
- `on_delete=models.CASCADE` on `ForeignKey` to `User` without explicit consideration.
- Storing `bank_account_number` or `ifsc_code` as plaintext `CharField`.
- Storing passwords in any field other than `PasswordField` (Django's built-in).
- Storing OTPs in plaintext without expiry validation.

### 25.3 Views

- Business logic in views (validation, external API calls, database writes outside serializer `create/update`).
- Direct instantiation of payment adapters (`CashfreeAdapter()`) in views.
- Returning sensitive data (bank details, OTPs) in API responses.
- Using `@csrf_exempt` without explicit ADR and security review.
- Using `@transaction.atomic` on GET requests (transaction per view call).

### 25.4 Services

- Services importing from other apps' `models/` or `views/`.
- Services instantiating their own dependencies (no DI).
- Services catching and suppressing all exceptions.
- Services returning `None` for error cases.

### 25.5 Imports

- `from rentsecure_be.X import Y` in any app code.
- `from core.models import User` in models, views, or services (use string refs).
- `from properties.models import RentRecord` in `notification/` (use `properties/services/`).
- `from razorpay` or `from cashfree` outside `payments/adapters/`.
- Relative imports (`from .models import User`).

### 25.6 Configuration

- Hardcoded API keys, tokens, or secrets in code.
- Secrets in `.env` files that are committed to the repository.
- `DEBUG = True` in production settings.
- `ALLOWED_HOSTS = ['*']` in production settings.

---

## 26. Architecture Violations

These violations block CI and MUST be fixed before merge.

### 26.1 Import Violations

| Violation | Detection | Blocking |
|-----------|-----------|----------|
| App imports from `rentsecure_be/` | `test_rentsecure_be_boundary.py` | Yes |
| App imports from `apps/` or `config/` | `import-linter.ini` | Yes |
| `razorpay`/`cashfree` import in non-adapter | `test_sdk_placement.py` | Yes |
| `twilio` import outside `notification/adapters/` | `test_import_rules.py` | Yes |
| `boto3` import outside `notification/` and `documents/` | `test_import_rules.py` | Yes |
| View imports model from another app | `test_layer_compliance.py` | Yes |
| View imports service from another app | `test_layer_compliance.py` | Yes |
| `shared/` imports from `django` or any app | `test_shared_purity.py` | Yes |

### 26.2 Structural Violations

| Violation | Detection | Blocking |
|-----------|-----------|----------|
| Circular dependencies | `test_circular_deps.py` | Yes |
| View file exceeds 300 lines | `test_god_views.py` | Yes |
| Model file exceeds 400 lines | `test_god_models.py` | Yes |
| `core/views.py` exists (single file) | `test_god_views.py` | Yes |
| `payments/` not in `INSTALLED_APPS` | `manage.py check` | Yes |
| Management commands at root level | `test_god_views.py` | Yes |
| `apps/` or `config/` directories exist | `test_import_rules.py` | Yes |

### 26.3 Security Violations

| Violation | Detection | Blocking |
|-----------|-----------|----------|
| Bank details in plaintext | Architecture test | Yes |
| OTP logged or printed | Architecture test | Yes |
| Webhook without idempotency | Architecture test | Yes |
| Webhook without HMAC verification | Architecture test | Yes |
| Secret in code or logs | Bandit scan | Yes |

---

## 27. CI Requirements

### 27.1 Pipeline Gates

Every PR MUST pass all gates before merge.

| Gate | Tool | Threshold | Blocking |
|------|------|-----------|----------|
| Lint | Ruff | 0 errors | Yes |
| Type Check | MyPy | 0 errors | Yes |
| Import Rules | import-linter | 0 violations | Yes |
| Tests | Pytest | All pass, ≥90% coverage | Yes |
| Django Check | `manage.py check` | 0 errors | Yes |
| Architecture | pytest `tests/architecture/` | 0 failures | Yes |
| Security | Bandit | 0 high/medium | Yes |
| Dependency Audit | Safety | 0 critical | Yes |
| Mutation | Sonar | ≥80% mutation score | Yes |
| Migration | pytest-django | Forward + reverse pass | Yes |

### 27.2 Pipeline Order

```
Lint → Test → Shard Val → Contract → Django Check → Architecture → Security → Mutation → Hypothesis → Migration → Quality Gate → Deploy Ready
```

### 27.3 Branch Protection

| Branch Type | Require PR | Require Approvals | Require Status Checks | Dismiss Stale Reviews |
|-------------|-----------|-------------------|----------------------|----------------------|
| `main` | Yes | 2 | All | Yes |
| `phase-{N}` | Yes | 1 | All | Yes |
| Task branches | Yes | 0 | Lint + Tests | No |

### 27.4 PR Size Limits

| Metric | Limit |
|--------|-------|
| Lines changed per PR | Max 400 |
| Files changed per PR | Max 15 |
| PR lifetime | Max 7 days |

If a task exceeds these limits, split it into smaller PRs.

### 27.5 Deployment Gates

| Environment | Trigger | Approval Required |
|-------------|---------|-------------------|
| Development | Every push to task branch | None |
| Staging | PR merged to `phase-{N}` | 1 approval |
| Production | PR merged from `phase-{N}` to `main` | 2 approvals + Security Lead sign-off |

### 27.6 Rollback Requirements

- Every phase has a documented rollback procedure.
- Rollback is tested on staging before production deploy.
- Rollback time is measured and within acceptable limits:
  - Phase -1 to 4: ≤30 minutes
  - Phase 5: ≤4 hours
  - Phase 6: ≤15 minutes per PR

---

## Appendix A: Quick Reference

### Must / Must Not / Should / Should Not

| Keyword | Meaning | Enforcement |
|---------|---------|-------------|
| **MUST** | Mandatory. Blocked in CI if violated. | CI, architecture tests, code review |
| **MUST NOT** | Forbidden. Blocked in CI if detected. | CI, architecture tests, code review |
| **SHOULD** | Recommended. Requires ADR exception if violated. | Code review |
| **SHOULD NOT** | Discouraged. Requires ADR exception if violated. | Code review |

### Key Contacts

| Role | Responsibility |
|------|----------------|
| Staff Engineer | ADR approvals, `shared/` changes, architecture gates |
| Platform Team Lead | `platform/`, `shared/`, `payments/`, `notification/`, `identity/` |
| Product Team Lead | `properties/`, `finance/`, `documents/`, `dashboard/` |
| Security Lead | Security reviews, encryption, audit logging, webhook verification |
| DevOps Engineer | CI/CD, deployments, infrastructure, monitoring |
| QA Lead | Test strategy, coverage enforcement, regression testing |

---

## Appendix B: Related Documents

- [Architecture v1.1 Release Candidate](../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Architecture v1.1 Implementation Master Plan](../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Phase 0 Execution Plan](../PHASE_0_EXECUTION_PLAN.md)
- [Engineering Backlog](../ENGINEERING_BACKLOG.md)
- [Architecture Decision Records](../docs/architecture/adr/README.md)
- [Backend Engineering Rules](../.kilo/instructions/backend.md)
- [Security Rules](../.kilo/instructions/security.md)
- [Testing Rules](../.kilo/instructions/testing.md)
- [Finance Module Rules](../.kilo/instructions/finance.md)
- [Notification Module Rules](../.kilo/instructions/notifications.md)

---

## Appendix C: Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-19 | Chief Software Architect | Initial release for v1.1 freeze |

**Next Review:** After Phase 0 completion
**Approval Required:** Staff Engineer, Platform Team Lead, Product Team Lead, Security Lead, DevOps Engineer, QA Lead

---

*End of RentSecure Engineering Standards*
