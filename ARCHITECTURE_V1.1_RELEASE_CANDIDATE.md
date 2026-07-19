# RentSecureBE — Architecture v1.1 Release Candidate

**Status:** RELEASE CANDIDATE — PENDING SIGN-OFF
**Date:** 2026-07-19
**Scope:** Final architecture review of v1.0 with critical corrections before freeze
**Authority:** Chief Software Architect
**Applies to:** All engineering teams

---

## Executive Summary

Architecture v1.0 is **fundamentally sound in direction** but contains **10 Critical and 14 High-severity findings** that must be resolved before freezing. The primary risks are:

1. **`AUTH_USER_MODEL` migration is architecturally impossible as specified** — Django does not support dual user models or proxy-based AUTH_USER_MODEL transitions.
2. **`apps/` parent directory migration is a hidden mega-migration** — every import path, URL include, migration reference, template tag, and static file path changes. It is not incremental.
3. **`payments/` app is NOT registered in `INSTALLED_APPS`** — all payment adapter code is currently unreachable.
4. **Sensitive financial data is stored in plaintext** — bank account numbers and IFSC codes have no encryption at rest.
5. **The dependency matrix references a `rent/` context that does not exist** and is deferred, creating phantom dependencies.
6. **The import-linter configuration creates a God-layer anti-pattern** by allowing every app to import from `rentsecure_be/`.
7. **Dead code (`ai_assistant/`, `dashboard/`) is treated as active bounded contexts** in the architecture document.
8. **Payment, notification, and PDF logic is scattered across 4+ apps** violating single-responsibility.

**Verdict: GO WITH CHANGES** — v1.0 must be corrected to v1.1 before implementation begins.

---

## Part 1: Architecture v1.0 Review Findings

### 1. Architectural Decision Validation

#### Finding AD-01: `AUTH_USER_MODEL` Migration Strategy is Invalid

- **Severity:** Critical
- **Why it is a problem:** The v1.0 document proposes creating `identity.User`, then keeping `core.User` as a proxy for one release cycle, then removing `core`. Django does **not** allow two concrete `User` models to coexist. A proxy model shares the same database table as its parent, so `core.User` cannot be a proxy of `identity.User` if both have separate migration histories. Furthermore, `AUTH_USER_MODEL` is a project-wide singleton — it cannot point to two models during a transition.
- **Long-term impact:** Attempting this migration will cause `RuntimeError`, migration conflicts, and data integrity failures. All ForeignKeys referencing `core.User` will break when `AUTH_USER_MODEL` flips.
- **Recommended change:** Keep `core.User` as `AUTH_USER_MODEL` permanently. Extract identity *services* (OTP, password, profile) into `apps/identity/services/`, but keep the `User` model in `core/` (or rename `core/` to `identity/` as a model container). Do **not** attempt to move the Django user model between apps.

#### Finding AD-02: `apps/` Parent Directory is a Hidden Mega-Migration

- **Severity:** Critical
- **Why it is a problem:** The v1.0 document proposes moving all apps from root-level (`core/`, `properties/`, `notification/`, etc.) into a new `apps/` parent directory. This changes every import path, every `INSTALLED_APPS` entry, every URL `include()`, every migration reference, every template tag, and every static/media path. The migration document frames this as "Phase 0: Foundation — no breaking changes," but it is inherently a breaking change for any code that imports from these apps.
- **Long-term impact:** A single failed `apps/` migration blocks all other phases. Rollback requires reverting every import path across 300+ files.
- **Recommended change:** **Reject** the `apps/` parent directory. Keep apps at the project root. The boundary between apps is already enforced by `import-linter.ini`; a parent directory adds no architectural value and enormous migration risk.

#### Finding AD-03: `rent/` Context is Phantom

- **Severity:** High
- **Why it is a problem:** The dependency matrix and context definitions reference `apps/rent/` with dependencies on `property/`, `payment/`, `document/`, `notification/`, and dependents `finance/` and `dashboard/`. However, the migration strategy explicitly **defers** `rent/` extraction to Stage 2. This creates phantom dependencies: `payment/` in the matrix does not depend on `property/`, yet the text says `payment/` needs `RentRecord` data. `ai/` depends on `rent/` but `rent/` does not exist.
- **Long-term impact:** Future developers will be unable to implement `rent/` because the architecture document has already assigned its responsibilities to other contexts (e.g., `RentRecord` stays in `property/`, `LateFeePolicy` is deferred).
- **Recommended change:** Remove all references to `rent/` from v1.1. Keep `RentRecord`, `RentCycle`, and rent logic in `properties/` permanently. If rent logic grows, extract it as a `properties` sub-module (`properties/rent/`), not a top-level bounded context.

#### Finding AD-04: `payment/` App is Not Registered in `INSTALLED_APPS`

- **Severity:** Critical
- **Why it is a problem:** The `payments/` directory exists with adapters, ports, and services, but `payments` is **absent from `INSTALLED_APPS`** in `rentsecure_be/settings.py:118-139`. Django will not load the app, will not apply its migrations (there are none), and will not recognize its models. Any view importing `payments.adapters.cashfree` works only because Python imports bypass Django's app registry, but the app is architecturally non-functional.
- **Long-term impact:** Payment adapters cannot be used consistently. The `payments/` app is a zombie — present in the filesystem but dead to Django.
- **Recommended change:** Add `payments` to `INSTALLED_APPS` immediately. Add a migration that creates any required tables (even if empty initially).

#### Finding AD-05: `ai_assistant/` and `dashboard/` are Dead Code Treated as Active Contexts

- **Severity:** High
- **Why it is a problem:** The v1.0 document lists `ai/` and `dashboard/` as bounded contexts with full ownership, maturity ratings, and public APIs. In reality, `ai_assistant` and `dashboard` are **not in `INSTALLED_APPS`** and have been dead code since at least the architecture baseline. Treating them as active contexts in the architecture document misleads future developers.
- **Long-term impact:** Resources will be wasted trying to implement interfaces and tests for contexts that do not exist in production.
- **Recommended change:** Mark `ai/` as **Experimental / Not Deployed** and `dashboard/` as **Experimental / Not Deployed** in v1.1. Remove their dependency matrix entries until they are activated.

#### Finding AD-06: Dependency Matrix Has Inconsistencies

- **Severity:** High
- **Why it is a problem:** The allowed import matrix (Section 5.1) contains errors:
  - Row `rent/` lists `notification/` and `finance/` as "cannot import", but `rent/` is deferred.
  - Row `payment/` lists `property/` as "cannot import", yet the text and actual code show payment adapters need `RentRecord` data from `property/`.
  - Row `ai/` lists `rent/` as a dependency, but `rent/` is deferred.
  - The matrix omits `ai_assistant/` and `dashboard/` entirely.
- **Long-term impact:** The import-linter configuration derived from this matrix will either allow illegal imports or block legal ones.
- **Recommended change:** Correct the matrix to reflect actual target state. Remove `rent/` references. Add `ai_assistant/` and `dashboard/` as deferred. Fix `payment/` to allow imports from `property/`.

#### Finding AD-07: Selective Repository Pattern is Undefined

- **Severity:** Medium
- **Why it is a problem:** The v1.0 document says "use repositories selectively" but provides no enforcement mechanism. The repository pattern is currently unused (dead modules in `properties/repositories/`). Without clear criteria, future developers will either never use repositories or overuse them.
- **Long-term impact:** Inconsistent query patterns across the codebase. Some services will use ORM directly, others will use repositories, creating confusion.
- **Recommended change:** Add a concrete decision tree to the coding standards:
  ```
  Use repository if: query spans 3+ tables AND is used by 3+ services
  Use ORM if: query touches 1-2 tables OR is used by 1-2 services
  ```

---

### 2. Hidden Production Risks

#### Finding PR-01: Plaintext Bank Details Storage

- **Severity:** Critical
- **Why it is a problem:** `core/models.py:108-120` stores `bank_account_number` and `ifsc_code` as plaintext `CharField`. The v1.0 document says "encrypt at rest (Phase 3)", but this is a financial regulatory requirement, not a Phase 3 optimization. Indian RBI guidelines and global PCI-adjacent standards require encryption of bank account data.
- **Long-term impact:** Data breach exposes bank account numbers of all owners. Regulatory penalties. Loss of user trust.
- **Recommended change:** Implement `django-cryptography` or `django-cryptographic-fields` for `bank_account_number` and `ifsc_code` **before** production deployment. Add `BankDetailsEncrypted` field type to `shared/`.

#### Finding PR-02: Webhook URLs are Hardcoded in `core/views.py`

- **Severity:** High
- **Why it is a problem:** `core/views.py` contains `cashfree_payout_webhook` and `razorpay_webhook` as function-based views at the project URL level. The v1.0 document says to move these to `payment/` in Phase 3, but until then, webhook endpoint changes require modifying `rentsecure_be/urls.py` and `core/urls.py` in two places.
- **Long-term impact:** A provider changes their webhook URL format → production outage until both URL configs are updated.
- **Recommended change:** Move webhook URLs to `payments/urls.py` immediately (Phase 0, not Phase 3). Keep `core/urls.py` as deprecated redirects.

#### Finding PR-03: `core/views.py` is a 566-Line God View

- **Severity:** High
- **Why it is a problem:** `core/views.py` contains OTP, password, subscription CRUD, bank details, owner reporting, two webhooks, and rent payment creation. Any change to any of these requires editing the same file, increasing merge conflicts and regression risk.
- **Long-term impact:** Developer productivity degrades as the file grows. Test coverage becomes harder to maintain.
- **Recommended change:** Split `core/views.py` into `auth_views.py`, `subscription_views.py`, `bank_views.py`, `reporting_views.py` in Phase 0 (pre-migration).

#### Finding PR-04: `type_compat.py` is an Infrastructure Hub

- **Severity:** High
- **Why it is a problem:** `rentsecure_be/type_compat.py` is imported by 20+ files across 6 apps. The v1.0 document says to move it to `shared/` in Phase 0, but until then, every app has a hard dependency on `rentsecure_be/` for a Python 3.12 compatibility shim.
- **Long-term impact:** Prevents true modularity. Any change to `type_compat.py` requires testing across all apps.
- **Recommended change:** Move `type_compat.py` to `shared/` in Phase 0. Keep a deprecated re-export in `rentsecure_be/` for one release cycle.

#### Finding PR-05: `payments/adapters/cashfree.py` Imports from `core.models` and `rentsecure_be.utils`

- **Severity:** High
- **Why it is a problem:** The Cashfree adapter imports `OwnerBankDetails` from `core.models` and `get_auth_token`/`add_beneficiary`/`make_payout` from `rentsecure_be.utils.cashfree_payout`. This creates hard dependencies on the identity app and project config layer.
- **Long-term impact:** Cannot extract `payments/` as a microservice without these dependencies.
- **Recommended change:** In Phase 0, move `cashfree_payout.py` functions into `payments/adapters/cashfree_client.py`. In Phase 1, move `OwnerBankDetails` to `payments/models.py`.

---

### 3. Migration Risks

#### Finding MR-01: No Rollback Plan for `apps/` Directory Creation

- **Severity:** Critical
- **Why it is a problem:** The v1.0 migration plan says "Phase 0: Foundation — no breaking changes" for moving `type_compat.py` and creating app skeletons. But creating `apps/` and moving apps into it changes every import path. If the migration fails halfway, the codebase is left with a mix of old and new import paths.
- **Long-term impact:** Migration failure leaves the codebase in an unrecoverable state without git revert, which loses all Phase 0-5 work.
- **Recommended change:** Since `apps/` parent directory is rejected (Finding AD-02), this risk is eliminated.

#### Finding MR-02: `AUTH_USER_MODEL` Change Has No Safe Rollback

- **Severity:** Critical
- **Why it is a problem:** The v1.0 document says to change `AUTH_USER_MODEL` in Phase 5 with "full rollback plan tested in staging." However, changing `AUTH_USER_MODEL` requires a data migration that copies all user data to a new table. If this fails in production, user authentication is completely broken.
- **Long-term impact:** Production outage during user migration. Potential data loss if rollback requires restoring from backup.
- **Recommended change:** Reject the `AUTH_USER_MODEL` change (Finding AD-01). Keep `core.User` as the permanent user model.

#### Finding MR-03: Circular Dependencies Will Worsen During Migration

- **Severity:** High
- **Why it is a problem:** The current codebase has 4 circular dependency cycles. The v1.0 migration plan says "zero circular dependencies" is a target, but does not specify *how* to break existing cycles before creating new ones. Moving apps into `apps/` without first breaking cycles will make them worse.
- **Long-term impact:** Import errors at application startup. Fragile refactoring.
- **Recommended change:** Add a **Phase -1 (Pre-Migration)** to the plan:
  1. Break `core ↔ properties` cycle by extracting shared interfaces
  2. Break `properties ↔ notification` cycle by using events
  3. Break `core ↔ rentsecure_be` cycle by moving `type_compat.py` to `shared/`
  4. Break `properties ↔ rentsecure_be` cycle by moving utilities

#### Finding MR-04: No Data Migration Plan for `OwnerBankDetails` and `NotificationPreference`

- **Severity:** High
- **Why it is a problem:** The v1.0 document says to move `OwnerBankDetails` to `payment/models.py` (Phase 3) and `NotificationPreference` to `notification/models.py` (Phase 4), but provides no data migration strategy. Django data migrations for models with ForeignKeys to `AUTH_USER_MODEL` are non-trivial.
- **Long-term impact:** Data loss during model migration. Orphaned records.
- **Recommended change:** Add explicit data migration steps to Phase 3 and Phase 4:
  ```python
  # Phase 3: Copy core_ownerbankdetails → payment_ownerbankdetails
  # Phase 4: Copy core_notificationpreference → notification_notificationpreference
  ```

#### Finding MR-05: `import-linter.ini` is Not Updated in the Migration Plan

- **Severity:** Medium
- **Why it is a problem:** The v1.0 document says to update `import-linter.ini` in Phase 0, but the current file references old app names and does not include `payments`, `ai_assistant`, or `dashboard`. The migration plan does not specify the new configuration.
- **Long-term impact:** Import-linter will either pass incorrectly or block valid imports after migration.
- **Recommended change:** Provide the complete `import-linter.ini` v1.1 configuration in the architecture document.

---

### 4. Dependency Violations

#### Finding DV-01: `payments/` App is a Zombie

- **Severity:** Critical
- **Why it is a problem:** `payments/` has adapters, ports, and services, but is not in `INSTALLED_APPS`. Any code importing from `payments/` works only because Python's import system doesn't check Django's app registry. The app has no migrations, so its models (when added) will not have database tables.
- **Long-term impact:** Payment adapters are unreliable. Adding models to `payments/` without migrations will cause `OperationalError` at runtime.
- **Recommended change:** Add `payments` to `INSTALLED_APPS` in Phase 0. Create initial migration.

#### Finding DV-02: `rentsecure_be/` is a Service Container

- **Severity:** High
- **Why it is a problem:** `rentsecure_be/services/` contains `cashfree_service.py`, `razorpay_service.py`, `leegality_service.py`, and `i18n_service.py`. These are imported by 9+ files across `core/`, `properties/`, `smartbot/`, `management/`, and `notification/`. The v1.0 document says to remove these in Phase 3-6, but until then, `rentsecure_be/` is a hidden service locator.
- **Long-term impact:** Apps cannot be tested in isolation. `rentsecure_be/` becomes a god-module in the infrastructure layer.
- **Recommended change:** Move services to their owning apps immediately:
  - `cashfree_service.py` → `payments/`
  - `razorpay_service.py` → `payments/`
  - `leegality_service.py` → `smartbot/`
  - `i18n_service.py` → `shared/` or `notification/`
  - `export_utils.py` → `properties/` or `dashboard/`

#### Finding DV-03: `notification/` Contains Domain Business Logic

- **Severity:** High
- **Why it is a problem:** `notification/services/rent_notify_service.py`, `late_fees_notify_service.py`, `schedule_reminders.py`, and `extra_charge_reminders.py` all contain domain-specific logic (rent due messages, late fee calculations, tax reminders). The notification module should only dispatch messages, not decide *when* and *what* to send.
- **Long-term impact:** Changes to rent due logic require modifying the notification module. Notification module cannot be reused for other domains.
- **Recommended change:** Move all domain-specific notification triggers to `properties/services/`. `notification/` should only provide `send_email()`, `send_push()`, `send_whatsapp()`, `send_sms()`, `send_voice()`.

#### Finding DV-04: `core.models` is Imported by 63 Modules

- **Severity:** High
- **Why it is a problem:** `core.models` is the highest fan-in module (63 importers). Every model that has a ForeignKey to `User` imports `core.models.User` directly instead of using `settings.AUTH_USER_MODEL` string references. This makes the `User` model un-movable.
- **Long-term impact:** The `AUTH_USER_MODEL` migration (Finding AD-01) is blocked because 63 modules import `core.models.User` directly.
- **Recommended change:** Enforce `settings.AUTH_USER_MODEL` string references in all ForeignKeys. Use `TYPE_CHECKING` blocks for type hints.

#### Finding DV-05: `properties.models` is Imported by 74 Modules

- **Severity:** High
- **Why it is a problem:** `properties.models` is the highest fan-in module overall (74 importers). It is imported by `core/`, `notification/`, `smartbot/`, `finance/`, `documents/`, `dashboard/`, `management/`, and `tests/`. This makes `properties/` a hidden hub.
- **Long-term impact:** Any change to `properties/models` has blast radius across the entire codebase.
- **Recommended change:** Introduce `properties/services/` interfaces for cross-app communication. Enforce that no app imports `properties.models` directly except `properties/` itself.

---

### 5. Governance Gaps

#### Finding GG-01: No Architecture Change Approval Workflow

- **Severity:** High
- **Why it is a problem:** The v1.0 document says "Architecture Review Board reviews all ADRs" but does not define the board membership, meeting cadence, or approval threshold. There is no mechanism to prevent a developer from adding a new import to `core/views.py` without review.
- **Long-term impact:** Architectural decay accelerates as the team grows.
- **Recommended change:** Define the Architecture Review Board in `ARCHITECTURE_GOVERNANCE.md`:
  - Members: Staff Engineer, Platform Team Lead, Security Lead
  - Cadence: Weekly async review, monthly sync
  - Approval: 2-of-3 for shared/platform changes, 1-of-3 for app-internal changes

#### Finding GG-02: No Enforcement of "No Business Logic in Views"

- **Severity:** High
- **Why it is a problem:** The v1.0 document says "never put business logic in views" but there is no automated enforcement. `core/views.py` contains payment webhook handling, bank details validation, and owner reporting — all business logic.
- **Long-term impact:** Views accumulate business logic over time, becoming god views.
- **Recommended change:** Add an architecture test that scans all `views.py` files for model imports (excluding serializers and permissions). Fail the build if a view imports a model from another app.

#### Finding GG-03: No Ownership Registry for Models and Services

- **Severity:** Medium
- **Why it is a problem:** The v1.0 document lists "Ownership: Platform Team" or "Ownership: Product Team" for each bounded context, but there is no mechanism to enforce this. Any developer can modify `properties/models/unit_models.py` without notifying the Product Team.
- **Long-term impact:** Unreviewed changes to domain models cause data corruption and business logic drift.
- **Recommended change:** Add `OWNERS` file to each app directory:
  ```
  # properties/OWNERS
  model: Product Team
  service: Product Team
  view: Product Team
  ```

#### Finding GG-04: No ADR Lifecycle Management

- **Severity:** Medium
- **Why it is a problem:** The v1.0 document lists 8 ADRs but does not specify how ADRs are proposed, reviewed, deprecated, or superseded. There is no versioning for ADRs.
- **Long-term impact:** Old ADRs conflict with new ones. Developers do not know which ADR is current.
- **Recommended change:** Define ADR lifecycle in governance:
  - Proposed → Accepted → Deprecated → Superseded
  - Each ADR has a `supersedes` field
  - ADR index is maintained in `docs/architecture/INDEX.md`

---

### 6. Security Concerns

#### Finding SEC-01: Plaintext Bank Account and IFSC Storage

- **Severity:** Critical
- **Why it is a problem:** `core/models.py:108-120` stores `bank_account_number` and `ifsc_code` as plaintext. This is a critical PII/financial data exposure.
- **Long-term impact:** Regulatory non-compliance (RBI guidelines). Data breach liability.
- **Recommended change:** Implement encrypted fields before production:
  ```python
  from django_cryptography.fields import encrypt
  bank_account_number = encrypt(models.CharField(max_length=30))
  ifsc_code = encrypt(models.CharField(max_length=20))
  ```

#### Finding SEC-02: Webhook Verification Logic is Scattered

- **Severity:** High
- **Why it is a problem:** `core/views.py` contains inline HMAC verification for Cashfree and Razorpay webhooks. The v1.0 document says to move this to adapters, but the current implementation mixes verification with view logic.
- **Long-term impact:** A webhook bypasses verification if a developer copies the view logic without the HMAC check.
- **Recommended change:** Move webhook verification to `payments/adapters/` in Phase 0. Views should only call `WebhookService.verify()` and `WebhookService.handle()`.

#### Finding SEC-03: No Idempotency Keys for Webhooks

- **Severity:** High
- **Why it is a problem:** The v1.0 document says "add idempotency keys to all webhooks (Phase 3)" but Cashfree and Razorpay webhooks can be retried by the provider. Without idempotency keys, a retried webhook can double-process a payment.
- **Long-term impact:** Duplicate payment approvals. Financial discrepancies.
- **Recommended change:** Add idempotency key check to webhook handlers in Phase 0:
  ```python
  WebhookEvent.objects.get_or_create(event_id=payload["event_id"])
  ```

#### Finding SEC-04: OTP is Logged in DEBUG Mode

- **Severity:** Medium
- **Why it is a problem:** `core/views.py:73-76` prints the OTP to stdout in DEBUG mode. In production, this could end up in logs, monitoring dashboards, or error tracking systems.
- **Long-term impact:** OTP exposure enables account takeover.
- **Recommended change:** Never log OTPs, even in DEBUG. Use a dedicated test phone number with a known OTP in test environments.

#### Finding SEC-05: No Audit Logging for Payment Operations

- **Severity:** High
- **Why it is a problem:** The v1.0 document says "add audit logging to payment operations (Phase 3)" but there is no audit trail for who approved/rejected payments, who updated bank details, or who triggered a payout retry.
- **Long-term impact:** Cannot investigate payment disputes. Cannot detect fraudulent approvals.
- **Recommended change:** Enable `django-simple-history` for `OwnerBankDetails`, `PaymentTransaction`, and `RentRecord.payout_status`. Add audit log in Phase 0.

#### Finding SEC-06: Feature Flags are Boolean Globals, Not Per-User

- **Severity:** Medium
- **Why it is a problem:** `ENABLE_RAZORPAY`, `ENABLE_CASHFREE`, `ENABLE_WHATSAPP` are global boolean flags. The v1.0 document says "enable for 10% of users (canary)" but the current implementation cannot do per-user feature flags.
- **Long-term impact:** Cannot roll out payment gateways gradually. Must flip a global switch.
- **Recommended change:** Replace boolean flags with a `FeatureFlag` model that supports per-user, per-tenant, and percentage rollouts.

---

### 7. Scalability Bottlenecks

#### Finding SB-01: `LocMemCache` is Not Safe for Multi-Process

- **Severity:** High
- **Why it is a problem:** The v1.0 document says "Year 1: Django Local Memory Cache" but the production architecture document acknowledges that `LocMemCache` breaks when scaling beyond a single Gunicorn worker. The current settings use `LocMemCache` with no plan for transition.
- **Long-term impact:** Scaling to 2+ workers causes cache inconsistencies. Dashboard metrics will be wrong. Feature flags will flicker.
- **Recommended change:** Add `RedisCache` backend to `platform/cache/` in Phase 6. Add a `CACHE_BACKEND` setting that defaults to `locmem` but can be switched to `redis`.

#### Finding SB-02: `notification.services.whatsapp_service` is Imported by 21 Modules

- **Severity:** High
- **Why it is a problem:** `notification/services/whatsapp_service.py` is imported by 21 modules across 6 apps. This makes WhatsApp notification a hidden dependency hub. Any change to the WhatsApp API requires updating the notification module and testing all 21 importers.
- **Long-term impact:** Notification module cannot be scaled independently. Changes have blast radius across the codebase.
- **Recommended change:** Replace direct imports with domain events. Apps should publish `RentDueEvent`, `PaymentApprovedEvent`, etc. The `notification/` app should subscribe to these events.

#### Finding SB-03: `properties/models/unit_models.py` is 482 Lines

- **Severity:** Medium
- **Why it is a problem:** `Unit` model contains 482 lines with `__init__` logic, field definitions, and business methods. The v1.0 document says "defer full DDD structure" but does not address model file size.
- **Long-term impact:** Model files become unmaintainable. Merge conflicts on model changes are frequent.
- **Recommended change:** Split `unit_models.py` into `unit.py` (model), `unit_validators.py` (validators), `unit_choices.py` (TextChoices).

#### Finding SB-04: No Connection Pooling for PostgreSQL

- **Severity:** Medium
- **Why it is a problem:** The production architecture document shows RDS PostgreSQL but does not mention PgBouncer or connection pooling. With 3 Gunicorn workers and Django's default connection handling, the database can run out of connections under load.
- **Long-term impact:** Production outage when database connection limit is reached.
- **Recommended change:** Add PgBouncer to the infrastructure plan for Stage 2. Use `django-db-connection-pool` for Year 1 if connection count exceeds 10.

---

### 8. Operational Issues

#### Finding OI-01: 15 Root-Level Management Commands

- **Severity:** High
- **Why it is a problem:** There are 15 management commands at the project root (`management/commands/`) and additional commands inside app `management/` directories. The v1.0 document does not address this. Commands at the root level are invisible to developers looking for app-specific commands.
- **Long-term impact:** Commands are duplicated (e.g., `send_monthly_rent_summary` exists in both root and `properties/`). Unclear ownership.
- **Recommended change:** Move all commands to their owning app's `management/commands/` directory in Phase 0. Delete duplicates.

#### Finding OI-02: No Migration Rollback Testing

- **Severity:** High
- **Why it is a problem:** The v1.0 document says "full rollback plan tested in staging" for Phase 1 and Phase 5, but there is no CI step that validates migration rollback. A migration that works forward may fail backward.
- **Long-term impact:** Production migration failure requires manual rollback, causing extended downtime.
- **Recommended change:** Add a CI step that runs `python manage.py migrate --reverse` on a test database after each migration.

#### Finding OI-03: `db.sqlite3` is in the Repository Root

- **Severity:** Medium
- **Why it is a problem:** `db.sqlite3` exists at the repository root. This is a local development database that should be gitignored. It is not currently in `.gitignore`.
- **Long-term impact:** Developers accidentally commit local database with production-like data. Repository size grows.
- **Recommended change:** Add `db.sqlite3` to `.gitignore`. Add a pre-commit hook that rejects database files.

#### Finding OI-04: No Database Backup Verification

- **Severity:** Medium
- **Why it is a problem:** The production architecture document mentions "Automated backups (7 days)" for RDS but does not include backup verification in the CI/CD pipeline or operational runbook.
- **Long-term impact:** Backup corruption is discovered only when a restore is needed — during an incident.
- **Recommended change:** Add weekly backup restoration test to the operational runbook.

---

### 9. Testing Gaps

#### Finding TG-01: No Contract Tests Between Bounded Contexts

- **Severity:** High
- **Why it is a problem:** The v1.0 document says "every app boundary must have contract tests" but no contract tests currently exist. The current `tests/contract/` directory is empty.
- **Long-term impact:** Changes to one context's API break other contexts without detection until integration testing.
- **Recommended change:** Add contract tests in Phase 0:
  - `tests/contract/test_property_contract.py`
  - `tests/contract/test_payment_contract.py`
  - `tests/contract/test_notification_contract.py`

#### Finding TG-02: No Architecture Regression Tests

- **Severity:** High
- **Why it is a problem:** The v1.0 document says "architecture contract tests run on every commit" but the current architecture tests only validate the CI pipeline structure, not the application architecture. There are no tests that verify `core/views.py` does not import `razorpay`, or that `notification/` does not import `properties.models`.
- **Long-term impact:** Architectural violations accumulate undetected.
- **Recommended change:** Implement AST-based architecture tests using `import-linter` + custom pytest tests:
  ```python
  def test_views_do_not_import_payment_adapters():
      for view_file in glob("core/views/*.py"):
          assert "razorpay" not in read(view_file)
          assert "cashfree" not in read(view_file)
  ```

#### Finding TG-03: No Migration Tests

- **Severity:** Medium
- **Why it is a problem:** The v1.0 document says "every migration must have migration tests" but no migration tests currently exist.
- **Long-term impact:** Migration failures are discovered only during deployment.
- **Recommended change:** Add `tests/test_migrations.py` using `django-test-migrations` or similar.

#### Finding TG-04: `ai_assistant/` and `dashboard/` Have No Tests

- **Severity:** Low
- **Why it is a problem:** These apps are dead code (not in `INSTALLED_APPS`) but have test directories. Tests for dead code give false confidence about coverage.
- **Long-term impact:** Coverage metrics are inflated. Real coverage of active code is lower than reported.
- **Recommended change:** Exclude `ai_assistant/` and `dashboard/` from coverage reports until they are activated.

---

### 10. CI/CD Gaps

#### Finding CD-01: `import-linter` is Not Enforced in CI

- **Severity:** Critical
- **Why it is a problem:** The architecture compliance report shows **100/100 (COMPLIANT)** but this refers to the CI pipeline structure, not the application architecture. The `import-linter.ini` is configured to allow each app to import from `rentsecure_be/`, which means cross-app imports through `rentsecure_be/` are "allowed." The actual codebase has 145+ cross-app import violations that `import-linter` does not catch because of this misconfiguration.
- **Long-term impact:** Import violations accumulate undetected. The "zero tolerance" policy is unenforceable.
- **Recommended change:** Rewrite `import-linter.ini` to enforce direct app-to-app boundaries:
  ```
  [importlinter:properties]
  type = layers
  layers = properties, shared, platform
  ```
  Do NOT include `rentsecure_be` as an allowed layer for any app.

#### Finding CD-02: No Pre-Commit Hook for Architecture Violations

- **Severity:** Medium
- **Why it is a problem:** Developers can commit code that imports `razorpay` in `core/views.py` and only discover the violation after pushing to GitHub.
- **Long-term impact:** CI pipeline is blocked by easily-preventable violations.
- **Recommended change:** Add `pre-commit` hook that runs `import-linter check` and `ruff check` locally.

#### Finding CD-03: Mutation Testing Threshold is Not Blocking

- **Severity:** Medium
- **Why it is a problem:** The CI configuration says "mutation score 80%" but marks it as "No" (not blocking). This means SonarCloud mutation test failures do not block PRs.
- **Long-term impact:** Mutant code (code that passes tests but is semantically wrong) is merged.
- **Recommended change:** Set mutation testing as a blocking gate in the quality gate configuration.

---

### 11. Ownership Ambiguities

#### Finding OA-01: `payment/` Ownership is Unclear

- **Severity:** High
- **Why it is a problem:** The v1.0 document says `payment/` is owned by "Platform Team", but `OwnerBankDetails` is in `core/` (Identity), `RentRecord` payment fields are in `properties/`, and payment webhooks are in `core/views.py`. No single team owns the end-to-end payment flow.
- **Long-term impact:** Payment bugs have no clear owner. Fixes require coordination across multiple teams.
- **Recommended change:** Assign `payment/` ownership to the Platform Team. Move `OwnerBankDetails` to `payment/`. Move payment webhooks to `payment/`. The Platform Team owns the complete payment flow.

#### Finding OA-02: `notification/` Business Logic Ownership is Unclear

- **Severity:** High
- **Why it is a problem:** `notification/services/schedule_reminders.py` queries `RentRecord` and `PropertyTaxRecord` — these are property domain concerns. But the file lives in `notification/`. Is the Platform Team or Product Team responsible for when reminders are sent?
- **Long-term impact:** Reminder logic changes require cross-team coordination.
- **Recommended change:** Move all domain-specific notification triggers to the owning domain's `services/`. The `notification/` app should only provide channel adapters.

#### Finding OA-03: `rent/` Has No Owner

- **Severity:** Medium
- **Why it is a problem:** The v1.0 document lists `rent/` as owned by "Product Team" but also defers it to Stage 2. The Product Team currently owns `properties/`, which contains rent logic.
- **Long-term impact:** When `rent/` is eventually extracted, there is no clear owner.
- **Recommended change:** Since `rent/` is rejected (Finding AD-03), assign rent logic ownership to the Product Team within `properties/`.

---

### 12. Future Misuse Risks

#### Finding FM-01: `core/views.py` Will Be Copied, Not Refactored

- **Severity:** High
- **Why it is a problem:** The v1.0 migration plan says to "update `core/views.py` to delegate to `identity/` URLs" in Phase 1. But `core/views.py` is 566 lines with 8 responsibilities. A developer facing a deadline will copy the file to `identity/views.py` rather than extracting each responsibility into its own service.
- **Long-term impact:** `identity/views.py` becomes a 500-line god view.
- **Recommended change:** In Phase 0, split `core/views.py` into focused view modules BEFORE extracting to `identity/`. The migration should move *already-clean* code, not dump a god view into a new app.

#### Finding FM-02: `payment/` Adapters Will Bypass the Service Layer

- **Severity:** High
- **Why it is a problem:** The v1.0 document defines `PaymentService` and `PaymentGateway` interface, but `core/views.py` currently instantiates `CashfreeAdapter` directly. Future developers will continue this pattern because it is "simpler" than injecting the gateway.
- **Long-term impact:** Payment adapters are instantiated in views, making testing impossible and business logic untestable.
- **Recommended change:** Make adapter instantiation impossible in views by using dependency injection in the service layer. Add an architecture test that verifies no view imports from `payments.adapters`.

#### Finding FM-03: Django Signals Will Be Overused

- **Severity:** Medium
- **Why it is a problem:** The v1.0 document says "use Django signals for Phase 1-5" but signals are already overused. `properties/signals/__init__.py` imports notification services directly. Future developers will add more signal handlers, creating an invisible dependency web.
- **Long-term impact:** Signal handlers are hard to trace and test. Business logic disappears into `@receiver` decorators.
- **Recommended change:** Limit signals to infrastructure events (user created, user deleted). All business events should go through explicit service calls or the Phase 6 event bus.

#### Finding FM-04: `shared/` Will Become a Dumping Ground

- **Severity:** Medium
- **Why it is a problem:** The v1.0 document says "shared/ is sacred" but the current `shared/` already has naming conflicts (`ValidationError` in both `exceptions.py` and `types.py`) and unused code. Without strict governance, future developers will add "shared" utilities that are actually domain-specific.
- **Long-term impact:** `shared/` becomes a god module with domain logic, defeating its purpose.
- **Recommended change:** Enforce that every addition to `shared/` requires an ADR. Add an architecture test that fails if any `shared/` file imports from `django` or any app.

#### Finding FM-05: `rent/` Will Be Re-Introduced as a God Context

- **Severity:** Medium
- **Why it is a problem:** If `rent/` is ever extracted, it will inherit `RentRecord`, `RentCycle`, `LateFeePolicy`, `PaymentRequest`, `AgreementDraft`, and rent receipt logic. This is a large, cohesive set of responsibilities that will become a new god app.
- **Long-term impact:** The extraction solves one problem (property app is too big) but creates another (rent app is too big).
- **Recommended change:** Reject `rent/` as a bounded context (Finding AD-03). Keep rent logic in `properties/` with sub-modules.

---

## Part 2: Architecture v1.1 Release Candidate

### 2.1 Updated Architecture Decisions

| Decision | v1.0 | v1.1 | Rationale |
|---|---|---|---|
| App parent directory | `apps/<context>/` | **Rejected** — keep apps at root | `apps/` parent changes every import path. No architectural value. High risk. |
| `AUTH_USER_MODEL` migration | Move to `identity/` | **Rejected** — keep `core.User` | Django does not support dual user models or proxy AUTH_USER_MODEL transitions. |
| `rent/` bounded context | Deferred to Stage 2 | **Rejected** — keep in `properties/` | Phantom context. `RentRecord` stays in `properties/`. Rent logic is a `properties` sub-module. |
| `payment/` registration | Phase 3 | **Phase 0** — register immediately | Zombie app. Must be in `INSTALLED_APPS` to be functional. |
| `ai_assistant/` and `dashboard/` | Active contexts | **Deferred / Not Deployed** | Not in `INSTALLED_APPS`. Dead code. |
| `type_compat.py` location | `rentsecure_be/` → `shared/` in Phase 0 | **Phase 0** — move immediately | 20+ infrastructure boundary violations. |
| `OwnerBankDetails` location | `core/` → `payment/` in Phase 3 | **Phase 0** — move immediately | Financial entity in identity app. Critical security risk. |
| `NotificationPreference` location | `core/` → `notification/` in Phase 4 | **Phase 0** — move immediately | Notification concern in identity app. |
| `import-linter.ini` | Update in Phase 0 | **Phase 0** — rewrite immediately | Current config creates God-layer anti-pattern. |
| Root management commands | Not addressed | **Phase 0** — move to apps | 15 commands at root violate app boundaries. |
| Bank details encryption | Phase 3 | **Phase 0** — before production | Critical security requirement. |
| Webhook URLs | Phase 3 | **Phase 0** — move to `payments/` | Payment webhooks in `core/views.py` is a critical risk. |

### 2.2 Revised Migration Strategy (v1.1)

| Phase | Duration | Goal | Breaking Changes |
|---|---|---|---|
| **Phase -1** | Week 1 | Break circular dependencies | None |
| **Phase 0** | Week 2-3 | Foundation & Critical Fixes | None (additive only) |
| **Phase 1** | Week 4-6 | Extract Identity Services | None |
| **Phase 2** | Week 7-9 | Extract Subscription | None |
| **Phase 3** | Week 10-12 | Extract Payment | None |
| **Phase 4** | Week 13-14 | Extract Dashboard & Notification | None |
| **Phase 5** | Week 15-16 | Deprecate Core | **YES** — remove `core` views/models |
| **Phase 6** | Week 17-20 | Optimization | None |

#### Phase -1: Break Circular Dependencies (Week 1)

**Goal:** Eliminate all 4 circular dependency cycles before creating new structure.

**Tasks:**
1. Move `type_compat.py` from `rentsecure_be/` to `shared/` (breaks `core ↔ rentsecure_be` and `properties ↔ rentsecure_be`)
2. Extract `NotificationService.send_otp()` to a shared interface (breaks `core → notification`)
3. Move `rent_notify_service.py` domain methods to `properties/services/` (breaks `properties ↔ notification`)
4. Move `OwnerBankDetails` from `core/models.py` to `payments/models.py` (breaks `core → payment`)

#### Phase 0: Foundation & Critical Fixes (Week 2-3)

**Goal:** Fix all Critical findings without breaking production.

**Tasks:**
1. Add `payments` to `INSTALLED_APPS`
2. Add `OwnerBankDetails` to `payments/models.py` with encrypted fields
3. Move `cashfree_payout.py` to `payments/adapters/cashfree_client.py`
4. Move `NotificationPreference` from `core/models.py` to `notification/models.py`
5. Move webhook URLs from `core/urls.py` to `payments/urls.py`
6. Split `core/views.py` into `auth_views.py`, `subscription_views.py`, `bank_views.py`, `reporting_views.py`
7. Move root management commands to their owning apps
8. Rewrite `import-linter.ini` without `rentsecure_be` as an allowed layer
9. Add architecture contract tests
10. Add idempotency keys to webhook handlers
11. Add audit logging for payment operations
12. Add migration rollback tests to CI

#### Phase 1: Extract Identity Services (Week 4-6)

**Goal:** Move identity services out of `core/` without moving the User model.

**Tasks:**
1. Create `identity/services/` with `auth_service.py`, `otp_service.py`, `password_service.py`
2. Move services from `core/services/` to `identity/services/`
3. Update `core/views.py` to delegate to `identity/` services
4. Update all cross-app imports
5. **Do NOT create `identity.User` model. Do NOT change `AUTH_USER_MODEL`.**

#### Phase 2: Extract Subscription (Week 7-9)

**Goal:** Move subscription logic out of `core/`.

**Tasks:**
1. Create `subscription/services/` with `subscription_service.py`, `feature_enforcer.py`
2. Move `FeatureEnforcer` from `properties/feature_enforcer.py` to `subscription/`
3. Update `properties/` to import from `subscription/`
4. Remove `properties/feature_enforcer.py`

#### Phase 3: Extract Payment (Week 10-12)

**Goal:** Consolidate payment logic in `payments/`.

**Tasks:**
1. Add `Payment`, `PaymentTransaction`, `Refund` models to `payments/models.py`
2. Move webhook handlers to `payments/views/webhooks.py`
3. Remove payment code from `core/views.py`
4. Move `BankDetailsService` to `payments/services/`
5. Remove duplicate services from `rentsecure_be/`

#### Phase 4: Extract Dashboard & Notification (Week 13-14)

**Goal:** Move reporting out of `core/` and isolate notification concerns.

**Tasks:**
1. Create `dashboard/services/` with `owner_reporting_service.py`
2. Move reporting views from `core/views.py` to `dashboard/`
3. Move domain notification triggers from `notification/services/` to `properties/services/`
4. Simplify `notification/` to only channel adapters

#### Phase 5: Deprecate Core (Week 15-16)

**Goal:** Remove `core/` as a God app.

**Tasks:**
1. Remove all views from `core/views.py` (already moved)
2. Remove `OwnerBankDetails`, `NotificationPreference`, subscription models from `core/models.py`
3. Keep `User`, `UserProfile`, `OTP` in `core/models.py` (permanent)
4. Remove `core/` from being a service container
5. Rename `core/` to `identity/` (keep as model container)

#### Phase 6: Optimization (Week 17-20)

**Goal:** Add missing infrastructure.

**Tasks:**
1. Add event bus to `platform/events/`
2. Add repositories for complex queries
3. Add Redis cache backend
4. Consolidate `ai_assistant/` and `smartbot/` or remove dead code
5. Document bounded context APIs

### 2.3 Updated Dependency Rules

#### Corrected Allowed Import Matrix

| Source | shared | platform | identity | subscription | property | payment | notification | document | finance | referral | dashboard |
|---|---|---|---|---|---|---|---|---|---|---|---|
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

**Changes from v1.0:**
- Removed `rent/` row entirely
- Added `payment/` → `property/` dependency (payment needs `RentRecord`)
- Added `ai_assistant/` row (deferred, partial dependencies)
- Removed `rentsecure_be` as an allowed import target for all apps
- Removed `config/` as a separate app — configuration stays in `rentsecure_be/`

#### `rentsecure_be/` is NOT an allowed import target

The v1.0 matrix allowed every app to import from `rentsecure_be/`. This created a God-layer anti-pattern. In v1.1, **no app may import from `rentsecure_be/`** except `rentsecure_be/` itself. All utilities and services must move to their owning apps or to `shared/` or `platform/`.

### 2.4 Updated Governance Rules

#### Architecture Review Board

| Role | Responsibility |
|---|---|
| Staff Engineer | Approves all ADRs, reviews `shared/` and `platform/` changes |
| Platform Team Lead | Owns `platform/`, `shared/`, `payments/`, `notification/` |
| Product Team Lead | Owns `properties/`, `finance/`, `documents/` |
| Security Lead | Reviews all security-related changes |

#### Change Approval Thresholds

| Change Type | Approval Required |
|---|---|
| New file in `shared/` | Staff Engineer |
| New file in `platform/` | Staff Engineer + Platform Lead |
| New model in any app | App Owner + Staff Engineer |
| New cross-app import | App Owner + Architecture Review Board |
| Change to `import-linter.ini` | Staff Engineer |
| Deprecation of app or module | Staff Engineer |

#### ADR Lifecycle

1. **Proposed:** Created as PR with `docs/architecture/adr/ADR-XXX.md`
2. **Accepted:** Approved by 2-of-3 board members
3. **Deprecated:** Superseded by new ADR, marked with `supersedes` field
4. **Archived:** Moved to `docs/architecture/adr/archive/`

### 2.5 Updated Migration Rules

#### Mandatory Pre-Migration Steps

Before any app extraction:
1. All circular dependencies must be broken (Phase -1)
2. `import-linter.ini` must be updated and passing
3. All cross-app imports must be catalogued and approved
4. Rollback plan must be tested in staging

#### Data Migration Requirements

| Model Move | Data Migration | Rollback |
|---|---|---|
| `OwnerBankDetails`: core → payment | Copy `core_ownerbankdetails` → `payment_ownerbankdetails` | Keep `core_ownerbankdetails` for 1 release cycle |
| `NotificationPreference`: core → notification | Copy `core_notificationpreference` → `notification_notificationpreference` | Keep `core_notificationpreference` for 1 release cycle |
| Subscription models: core → subscription | Copy `core_subscription*` → `subscription_*` | Keep `core_*` for 1 release cycle |

#### Breaking Change Policy

- Breaking changes are ONLY allowed in Phase 5
- Phase 5 must be released as a major version (v2.0)
- `core/` must remain in `INSTALLED_APPS` as deprecated shims for 6 months post-Phase 5
- LTS branch must be maintained for 6 months

### 2.6 Updated Security Rules

#### Non-Negotiable Security Requirements (Before Production)

| Control | Requirement | Implementation |
|---|---|---|
| Bank details encryption | Encrypt at rest | `django-cryptography` fields |
| Webhook idempotency | All webhooks | `WebhookEvent` model with `event_id` unique constraint |
| Audit logging | All payment operations | `django-simple-history` on payment models |
| Webhook verification | All incoming webhooks | Move to `payments/adapters/` |
| OTP logging | Never | Remove `print()` from `send_otp` |
| Secrets management | Environment only | `.env` gitignored, `python-decouple` |

#### Security Testing Requirements

| Test | Frequency | Tool |
|---|---|---|
| Bandit scan | Every PR | Bandit |
| Dependency audit | Every PR | Safety |
| Webhook replay test | Every PR | Custom pytest |
| Encryption verification | Every release | Custom management command |

### 2.7 Updated Coding Standards

#### Forbidden Patterns (Enforced by Architecture Tests)

1. **No `razorpay` import in `core/` or any non-adapter file**
2. **No `cashfree` import in `core/` or any non-adapter file**
3. **No `twilio` import outside `notification/adapters/`**
4. **No `boto3` import outside `notification/adapters/` and `documents/`**
5. **No `requests` to Cashfree/Razorpay outside `payments/adapters/`**
6. **No model imports across bounded contexts** (use services or string references)
7. **No `from rentsecure_be.X import Y`** (all utilities moved to owning apps)
8. **No business logic in views** (delegate to services)
9. **No `Notification.objects.create` outside `notification/`**
10. **No direct `User` model import** (use `settings.AUTH_USER_MODEL`)

#### Required Patterns

1. All ForeignKeys use `settings.AUTH_USER_MODEL` or `"app.Model"` string
2. All payment operations go through `PaymentService` + `PaymentGateway`
3. All notification triggers go through `NotificationService`
4. All webhook handlers live in `payments/views/webhooks.py`
5. All sensitive fields use encrypted field types

### 2.8 Updated Testing Standards

#### Mandatory Test Types

| Test Type | Scope | Owner | Frequency |
|---|---|---|---|
| Unit | Services, models, utilities | App team | Every commit |
| Integration | View → Service → Model | App team | Every commit |
| Contract | App boundaries | Architecture team | Every PR |
| Architecture | Import rules, layer compliance | Architecture team | Every commit |
| Migration | Forward + rollback | App team | Every PR |
| Security | OWASP Top 10 | Security team | Every release |
| Performance | Query counts, response times | App team | Nightly |

#### Architecture Test Requirements

```python
# tests/architecture/test_import_rules.py
def test_no_views_import_payment_adapters():
    for view_file in glob("core/views/*.py") + glob("properties/views/*.py"):
        assert "razorpay" not in read(view_file)
        assert "cashfree" not in read(view_file)
        assert "CashfreeAdapter" not in read(view_file)

def test_no_notification_imports_property_models():
    for file in glob("notification/services/*.py"):
        assert "RentRecord" not in read(file)
        assert "PropertyTaxRecord" not in read(file)

def test_no_rentsecure_be_imports():
    for app in ["core", "properties", "notification", "smartbot", "finance", "documents"]:
        for file in glob(f"{app}/**/*.py"):
            assert "rentsecure_be" not in read(file)
```

### 2.9 Updated CI Requirements

#### CI Pipeline Gates

| Gate | Tool | Threshold | Blocking |
|---|---|---|---|
| Lint | Ruff | 0 errors | Yes |
| Type Check | MyPy | 0 errors | Yes |
| Import Rules | import-linter | 0 violations | Yes |
| Unit Tests | Pytest | 90% coverage | Yes |
| Integration Tests | Pytest | 80% coverage | Yes |
| Architecture Tests | Pytest | 0 failures | Yes |
| Migration Tests | pytest-django | Forward + reverse pass | Yes |
| Security | Bandit | 0 high/medium | Yes |
| Dependency Audit | Safety | 0 critical | Yes |
| Mutation | Sonar | 80% mutation score | **Yes (changed from No)** |
| Performance | Locust | < 200ms p95 | No |

#### Required CI Steps

```yaml
# .github/workflows/ci.yml (required steps)
- name: Import Linter
  run: import-linter check
- name: Architecture Tests
  run: pytest tests/architecture/ -v
- name: Migration Tests
  run: pytest tests/test_migrations.py -v
- name: Security Scan
  run: bandit -r apps/ shared/ platform/
- name: Dependency Audit
  run: safety check
```

---

## Part 3: Final Sign-Off

### GO / GO WITH CHANGES / NO GO

**VERDICT: GO WITH CHANGES**

Architecture v1.0 provides an excellent strategic direction and demonstrates deep understanding of clean architecture, DDD, and long-term maintainability. However, it contains **10 Critical and 14 High-severity findings** that must be corrected before implementation begins.

The most important corrections are:

1. **Reject `apps/` parent directory** — keep apps at root level
2. **Reject `AUTH_USER_MODEL` migration** — keep `core.User` permanently
3. **Reject `rent/` bounded context** — keep rent logic in `properties/`
4. **Register `payments/` in `INSTALLED_APPS`** immediately
5. **Move `type_compat.py` to `shared/`** in Phase 0
6. **Move `OwnerBankDetails` to `payment/`** in Phase 0 with encryption
7. **Move `NotificationPreference` to `notification/`** in Phase 0
8. **Rewrite `import-linter.ini`** without `rentsecure_be` as allowed layer
9. **Move payment webhooks to `payments/`** in Phase 0
10. **Split `core/views.py`** before extracting to `identity/`

Once these corrections are incorporated into Architecture v1.1, the architecture is **production-ready** and suitable to freeze for 20+ years of maintainability.

### Conditions for GO (Unconditional)

| Condition | Owner | Deadline |
|---|---|---|
| Publish Architecture v1.1 with all v1.1 corrections | Staff Engineer | Before implementation starts |
| Register `payments` in `INSTALLED_APPS` | Platform Team | Week 0, Day 1 |
| Move `type_compat.py` to `shared/` | Platform Team | Phase 0 |
| Add bank account encryption | Platform Team | Phase 0 |
| Rewrite `import-linter.ini` | Architecture Team | Phase 0 |
| Break all circular dependencies | Architecture Team | Phase -1 |
| Set mutation testing as blocking CI gate | DevOps | Week 0 |

### Conditions for GO (Within Phase 0)

| Condition | Owner | Deadline |
|---|---|---|
| Split `core/views.py` into focused modules | Product Team | Phase 0 |
| Move root management commands to apps | Product Team | Phase 0 |
| Move webhook URLs to `payments/` | Platform Team | Phase 0 |
| Add webhook idempotency keys | Platform Team | Phase 0 |
| Add architecture regression tests | Architecture Team | Phase 0 |
| Add migration rollback tests | DevOps | Phase 0 |

---

*End of Architecture v1.1 Release Candidate*

**Prepared by:** Chief Software Architect
**Date:** 2026-07-19
**Next Review:** After Phase 0 completion
