# PR-004 Implementation Specification

## Move Webhooks to payments

---

## 1. Purpose

Move Cashfree and Razorpay webhook handlers from `core/views.py` to `payments/views/webhooks.py`, add webhook URLs to `payments/urls.py`, and keep old URLs in `core/urls.py` as deprecated 301/302 redirects. Introduce the `WebhookEvent` model with a unique `event_id` constraint to enforce webhook idempotency. Remove payment SDK imports (`razorpay`, `cashfree`) from `core/views.py` to comply with architecture rules.

This PR is **blocked until PR-001 is merged** because:
1. `payments` must be in `INSTALLED_APPS`
2. `payments/views/` and `payments/urls.py` must be functional
3. `payment_ownerbankdetails` table must exist (for payout notifications)

---

## 2. Scope

### 2.1 In Scope

- Create `payments/views/__init__.py` — package marker
- Create `payments/views/webhooks.py` — `cashfree_payout_webhook` and `razorpay_webhook` views with HMAC verification and idempotency
- Create `payments/urls.py` — webhook URL patterns
- Create `payments/tests/test_webhooks.py` — unit and integration tests for webhook handlers
- Create `payments/tests/test_webhook_idempotency.py` — idempotency tests (duplicate webhooks)
- Create `payments/tests/test_webhook_security.py` — security tests (invalid signatures rejected)
- Update `core/views.py` — remove `cashfree_payout_webhook`, `razorpay_webhook`, `_get_rent_from_event`, and `_process_rent_payment` function definitions
- Update `core/urls.py` — replace webhook handlers with 301/302 redirects to new `payments/` URLs
- Update `rentsecure_be/urls.py` — add `path("api/webhook/", include("payments.urls"))` BEFORE `core/` URLs
- Create `payments/tests/test_webhook_redirects.py` — tests for old URL redirects

### 2.2 Out of Scope

- Creating `payments/views/bank_details_views.py` (Phase 3, PR-030)
- Creating `payments/services/bank_details_service.py` (Phase 3, PR-031)
- Creating `payments/urls.py` for bank details endpoints (Phase 3)
- Moving `OwnerBankDetails` model (PR-002)
- Moving `NotificationPreference` model (PR-003)
- Splitting `core/views.py` (PR-005)
- Moving management commands (PR-006)
- Any changes to `core/views/reporting_views.py`, `core/views/bank_views.py`, or other view modules
- Any changes to `notification/`, `properties/`, or other apps outside webhook migration
- Dropping the `core_notificationpreference` or `core_ownerbankdetails` tables (deferred to Phase 5)
- Any changes to `rentsecure_be/services/` utilities (Phase 3)
- Any changes to `core/views.py` bank details or reporting views (only webhook handlers are removed)

---

## 3. Files

### 3.1 Files to Create

| File | Purpose | Owner |
|------|---------|-------|
| `payments/views/__init__.py` | Package marker | Platform Team |
| `payments/views/webhooks.py` | `cashfree_payout_webhook` and `razorpay_webhook` views with HMAC verification and idempotency | Platform Team |
| `payments/urls.py` | Webhook URL patterns (complete rewrite of placeholder) | Platform Team |
| `payments/tests/test_webhooks.py` | Unit and integration tests for webhook handlers | Platform Team |
| `payments/tests/test_webhook_idempotency.py` | Idempotency tests (duplicate webhooks) | Platform Team |
| `payments/tests/test_webhook_security.py` | Security tests (invalid signatures rejected) | Platform Team |
| `payments/tests/test_webhook_redirects.py` | Tests for old URL redirects | Platform Team |

### 3.2 Files to Modify

| File | Change | Owner |
|------|--------|-------|
| `core/views.py` | Remove `cashfree_payout_webhook`, `razorpay_webhook`, `_get_rent_from_event`, and `_process_rent_payment` function definitions; remove `razorpay` import | Platform Team |
| `core/urls.py` | Replace webhook handlers with 301/302 redirects to new `payments/` URLs | Platform Team |
| `rentsecure_be/urls.py` | Add `path("api/webhook/", include("payments.urls"))` BEFORE `core/` URLs | Platform Team |

### 3.3 Files to Delete

None.

---

## 4. Responsibilities

| Role | Responsibility |
|------|----------------|
| **Platform Team Lead** | Owns `payments/views/webhooks.py`, `payments/urls.py`, `core/urls.py` redirects, and `payments/tests/`. Approves PR. |
| **Security Lead** | Reviews webhook HMAC verification, idempotency implementation, and redirect security. |
| **Developer** | Implements webhook views, URLs, redirects, tests, and updates `core/views.py`. Runs full validation. |
| **AI Assistant** | Generates webhook views, tests, URL patterns, and doc updates per this spec. Stops and asks if dependency matrix is violated or if webhook idempotency logic is unclear. |

---

## 5. Acceptance Criteria

### 5.1 Functional

- [ ] `payments/views/webhooks.py` exists with `cashfree_payout_webhook` and `razorpay_webhook` function-based views.
- [ ] `payments/urls.py` contains webhook URL patterns.
- [ ] `rentsecure_be/urls.py` includes `payments/urls.py` with `path("api/webhook/", include("payments.urls"))` BEFORE `path("api/", include("core.urls"))`.
- [ ] `core/urls.py` webhook URLs (`webhook/cashfree/payout/` and `api/rent/payment-callback/`) return 301/302 redirects to new `payments/` URLs.
- [ ] `core/views.py` no longer contains `cashfree_payout_webhook`, `razorpay_webhook`, `_get_rent_from_event`, or `_process_rent_payment`.
- [ ] `core/views.py` no longer imports `razorpay`.
- [ ] Webhook handlers in `payments/views/webhooks.py` verify HMAC signatures for both Cashfree and Razorpay.
- [ ] Webhook handlers in `payments/views/webhooks.py` implement idempotency via `WebhookEvent` model.
- [ ] Duplicate webhooks return 200 with original response (idempotent replay).
- [ ] Invalid signatures return 401.
- [ ] `python manage.py check` passes.
- [ ] All URLs resolve correctly.

### 5.2 Non-Functional

- [ ] All tests pass (existing + new).
- [ ] No architecture test violations.
- [ ] No import-linter violations.
- [ ] No circular dependencies introduced.
- [ ] No `razorpay` or `cashfree` SDK imports remain in `core/`.
- [ ] No security vulnerabilities (Bandit 0 high/medium).
- [ ] `core/views.py` size is reduced by at least 80 lines.

---

## 6. Architecture Rules

### 6.1 Bounded Context Compliance

- `payments/` owns all webhook handlers from this point forward.
- `core/` no longer contains webhook handlers. Old URLs remain as 301/302 redirects for backward compatibility.
- `payments/views/webhooks.py` is the canonical location for all payment webhook logic.
- Webhook URLs are served from `payments/urls.py` under the `/api/webhook/` prefix.

### 6.2 Import Rules

| Source | payment | identity (core) |
|--------|---------|-----------------|
| **payment** | ✗ | ✓ |
| **identity** | ✗ | ✗ |

`identity/` (i.e., `core/`) **cannot** import from `payment/` per the v1.1 dependency matrix.

**Implications for this PR:**
1. `core/views.py` **must not** import from `payments/views/webhooks.py`. The old URL patterns must use Django's `redirect()` or `RedirectView` to point to the new `payments/` URLs.
2. `payments/views/webhooks.py` **may** import from `properties/` (to access `RentRecord`) because `payment/` is allowed to import from `property/` per the dependency matrix.
3. `payments/views/webhooks.py` **may** import from `notification/` (to send payout notifications) only if the dependency matrix allows `payment → notification`. **Per ADR-006, `payment/` may NOT import from `notification/` directly.** Webhook handlers must delegate notification sending to a service in `properties/` or use a domain event pattern. If the current implementation requires `payment/` to import from `notification/`, AI must STOP and ask for approval.

**Permitted pattern for Phase 0:** `payments/views/webhooks.py` imports from `properties/models/rent_record_models.py` and `properties/services/` (if notification triggers live there). If `notification/` import is unavoidable, an ADR exception is required.

### 6.3 Model Rules

- `WebhookEvent` model must be created in `payments/models.py` (or a new `payments/models/webhook_models.py` if file size requires splitting).
- `WebhookEvent` must have a unique constraint on `event_id` to enforce idempotency.
- `WebhookEvent` must have fields: `event_id` (unique), `provider` (choices: `CASHFREE`, `RAZORPAY`), `status` (choices: `PROCESSED`, `FAILED`, `PENDING`), `payload` (JSON), `created_at`, `processed_at`.
- Model file must not exceed 400 lines.
- Model must not contain business logic.
- `WebhookEvent` may use `HistoricalRecords` for audit logging (PR-008 expands this).

### 6.4 View Rules

- Webhook views are function-based views (not class-based) — this is acceptable for webhooks.
- Webhook views MUST use `@csrf_exempt` (required for external provider callbacks). This must be reviewed by Security Lead.
- Webhook views MUST verify HMAC signatures before processing.
- Webhook views MUST check `WebhookEvent` for duplicate `event_id` before processing (idempotency).
- Webhook views MUST NOT contain business logic — delegate to `PaymentService` + adapter.
- Webhook views MUST NOT log sensitive data (full payloads, signatures).
- View file (`payments/views/webhooks.py`) must not exceed 300 lines.

### 6.5 URL Rules

- `payments/urls.py` must define webhook URL patterns.
- `rentsecure_be/urls.py` must include `payments/urls.py` BEFORE `core/` URLs to ensure new URLs take precedence.
- `core/urls.py` webhook URLs must return 301/302 redirects to the new `payments/` URLs.
- Redirects must use Django's `redirect()` helper or `RedirectView` — not custom view logic.
- Old URLs must remain functional during the transition period (1 release cycle).

### 6.6 Security Rules

- All webhook handlers MUST verify HMAC signatures (Cashfree: `X-Cashfree-Signature`, Razorpay: `X-Razorpay-Signature`).
- All webhook handlers MUST implement idempotency via `WebhookEvent` model.
- Webhook endpoints MUST return 200 for duplicates (idempotent replay).
- Webhook endpoints MUST return 401 for invalid signatures.
- Webhook endpoints MUST return 400 for malformed payloads.
- Secrets (`CASHFREE_WEBHOOK_SECRET`, `RAZORPAY_WEBHOOK_SECRET`) must come from environment variables.
- Webhook handlers MUST NOT log full request bodies or sensitive fields.
- `@csrf_exempt` is required for webhook endpoints (external providers cannot supply CSRF tokens). This must be explicitly approved by Security Lead.

### 6.7 Naming Rules

- Migration file: `0002_webhook_event.py` (in `payments/migrations/`).
- View file: `payments/views/webhooks.py`.
- URL file: `payments/urls.py`.
- Test files: `test_webhooks.py`, `test_webhook_idempotency.py`, `test_webhook_security.py`, `test_webhook_redirects.py`.
- Test classes: `TestCashfreeWebhook`, `TestRazorpayWebhook`, `TestWebhookIdempotency`, `TestWebhookSecurity`, `TestWebhookRedirects`.
- Test methods: `test_valid_signature_returns_200`, `test_invalid_signature_returns_401`, `test_duplicate_event_returns_200`, `test_malformed_payload_returns_400`.

---

## 7. CI Requirements

### 7.1 Required CI Gates

All gates are **blocking**. PR cannot be merged if any gate fails.

| Gate | Tool | Threshold | Command |
|------|------|-----------|---------|
| Lint | Ruff | 0 errors | `ruff check .` |
| Format | Ruff | 0 issues | `ruff format --check .` |
| Type Check | MyPy | 0 errors | `mypy .` |
| Import Rules | import-linter | 0 violations | `import-linter check` |
| Tests | Pytest | All pass, ≥90% coverage | `pytest tests/ -v --cov` |
| Architecture | pytest | 0 failures | `pytest tests/architecture/ -v` |
| Django Check | manage.py | 0 errors | `python manage.py check` |
| Migrations | manage.py | Forward + reverse pass | `python manage.py test migrations` |
| Security | Bandit | 0 high/medium | `bandit -r payments/ core/` |
| Dependency | Safety | 0 critical | `safety check` |

### 7.2 Pipeline Order

```
Lint → Type Check → Import Rules → Tests → Architecture → Django Check → Migrations → Security → Dependency
```

### 7.3 Phase-Specific Architecture Tests

| Test | Purpose | Expected Result |
|------|---------|-----------------|
| `test_import_rules.py` | No `razorpay`/`cashfree` imports in non-adapter files | Pass |
| `test_sdk_placement.py` | Payment SDKs only in `payments/adapters/` | Pass |
| `test_rentsecure_be_boundary.py` | No app imports from `rentsecure_be/` | Pass |
| `test_god_views.py` | `core/views.py` reduced in size; `payments/views/webhooks.py` ≤300 lines | Pass |
| `test_circular_deps.py` | No new circular dependencies | Pass |
| `test_layer_compliance.py` | No view imports from other apps' models (webhook views use services or direct `RentRecord` import via `property/`) | Pass |

**Note on `test_import_rules.py`:** This test must verify that `razorpay` and `cashfree` SDK imports are confined to `payments/adapters/` and `payments/views/webhooks.py` only. No other files may import these SDKs.

---

## 8. Testing Strategy

### 8.1 Test Tiers Required

| Tier | Scope | Requirement |
|------|-------|-------------|
| **Unit** | Webhook signature verification, idempotency check | ≥90% coverage |
| **Integration** | End-to-end webhook processing with test payloads | ≥80% coverage |
| **Security** | Invalid signatures, malformed payloads, missing headers | 100% pass |
| **Redirect** | Old URL redirects to new URLs | 100% pass |
| **Architecture** | Import boundaries, SDK placement, view size | 0 violations |

### 8.2 Webhook Handler Tests: `payments/tests/test_webhooks.py`

Required test cases:
- `test_cashfree_valid_signature_returns_200` — valid HMAC signature returns 200 and processes webhook
- `test_cashfree_invalid_signature_returns_401` — invalid HMAC signature returns 401
- `test_cashfree_missing_signature_returns_400` — missing signature returns 400
- `test_cashfree_missing_secret_raises_improperly_configured` — missing `CASHFREE_WEBHOOK_SECRET` raises `ImproperlyConfigured`
- `test_razorpay_valid_signature_returns_200` — valid HMAC signature returns 200 and processes webhook
- `test_razorpay_invalid_signature_returns_401` — invalid HMAC signature returns 401
- `test_razorpay_missing_signature_returns_400` — missing signature returns 400
- `test_razorpay_missing_secret_raises_improperly_configured` — missing `RAZORPAY_WEBHOOK_SECRET` raises `ImproperlyConfigured`
- `test_cashfree_transfer_success_updates_payout_status` — `TRANSFER_SUCCESS` event updates `RentRecord.payout_status` to `SUCCESS`
- `test_cashfree_transfer_failed_updates_payout_status` — `TRANSFER_FAILED` event updates `RentRecord.payout_status` to `FAILED`
- `test_razorpay_payment_captured_marks_paid` — `payment.captured` event marks rent as paid
- `test_razorpay_payment_link_paid_marks_paid` — `payment_link.paid` event marks rent as paid
- `test_non_post_method_returns_405` — GET/PUT/DELETE to webhook returns 405

### 8.3 Idempotency Tests: `payments/tests/test_webhook_idempotency.py`

Required test cases:
- `test_duplicate_cashfree_webhook_returns_200` — same `transferId` sent twice returns 200 both times, processes only once
- `test_duplicate_razorpay_webhook_returns_200` — same Razorpay event sent twice returns 200 both times, processes only once
- `test_webhook_event_created_on_first_processing` — `WebhookEvent` record created with `status=PROCESSED`
- `test_webhook_event_prevents_duplicate_processing` — second request finds existing `WebhookEvent` and returns 200 without reprocessing
- `test_webhook_event_with_different_event_id_processed` — different `event_id` for same rent is processed normally

### 8.4 Security Tests: `payments/tests/test_webhook_security.py`

Required test cases:
- `test_invalid_signature_rejected` — signature mismatch returns 401
- `test_tampered_payload_rejected` — payload modified after signing returns 401
- `test_missing_x_cashfree_signature` — missing header returns 400
- `test_missing_x_razorpay_signature` — missing header returns 400
- `test_malformed_json_returns_400` — invalid JSON body returns 400
- `test_missing_transfer_id_returns_404` — Cashfree payload without `transferId` returns 404
- `test_missing_event_returns_200` — Cashfree payload without `event` field is handled gracefully
- `test_rent_not_found_returns_404` — Razorpay payload with unknown `order_id` returns 404

### 8.5 Redirect Tests: `payments/tests/test_webhook_redirects.py`

Required test cases:
- `test_cashfree_old_url_redirects_to_new` — `/api/webhook/cashfree/payout/` returns 301/302 to `/api/webhook/cashfree/payout/`
- `test_razorpay_old_url_redirects_to_new` — `/api/rent/payment-callback/` returns 301/302 to `/api/webhook/razorpay/`
- `test_redirect_preserves_method` — redirect works for POST requests
- `test_new_url_accessible_directly` — `/api/webhook/cashfree/payout/` and `/api/webhook/razorpay/` return 200 (or 401/400 without proper signature)

### 8.6 Contract Tests

No new contract tests are required in this PR. The `payment ↔ property` contract is already covered by existing tests. Contract tests for webhook payloads are added in Phase 3 when `payments/services/webhook_service.py` is created.

### 8.7 Architecture Tests

AI must verify the following architecture tests pass after changes:
- `test_import_rules.py` — no forbidden SDK imports in new/modified files
- `test_sdk_placement.py` — `razorpay` and `cashfree` imports only in `payments/adapters/` and `payments/views/webhooks.py`
- `test_rentsecure_be_boundary.py` — no `rentsecure_be/` imports in new/modified files
- `test_god_views.py` — `payments/views/webhooks.py` ≤300 lines; `core/views.py` reduced
- `test_circular_deps.py` — no new circular dependencies
- `test_layer_compliance.py` — `payments/views/webhooks.py` may import from `properties/` (allowed by matrix)

### 8.8 Security Tests

- Run `bandit -r payments/ core/` and verify 0 high/medium findings.
- Verify no sensitive data (bank details, OTPs, secrets) appears in webhook test output.
- Verify no secrets or API keys in webhook view files.
- Verify `@csrf_exempt` is only used on webhook views with explicit justification.

### 8.9 Forbidden Test Patterns

- No `time.sleep()` in tests.
- No test dependencies on execution order.
- No hardcoded test data (use factories).
- No mocking Django ORM in integration tests (use test database).
- No direct database access in unit tests (use model methods or ORM).

---

## 9. Migration Strategy

### 9.1 Forward Migration

**Step 1: Apply PR-001 migrations**
```bash
python manage.py migrate
```
Verifies `payment_ownerbankdetails` table exists.

**Step 2: Apply PR-004 migration**
```bash
python manage.py migrate payments
```
Runs `0002_webhook_event.py`. Creates `payment_webhookevent` table.

**Step 3: Verify URLs**
```bash
python manage.py shell -c "
from django.urls import reverse
from django.test import Client
client = Client()
response = client.get('/api/webhook/cashfree/payout/')
assert response.status_code in (301, 302), f'Expected redirect, got {response.status_code}'
"
```

### 9.2 URL Migration Details

**Before PR-004:**
- Cashfree webhook: `/api/webhook/cashfree/payout/` (in `core/urls.py`)
- Razorpay webhook: `/api/rent/payment-callback/` (in `core/urls.py`)

**After PR-004:**
- Cashfree webhook: `/api/webhook/cashfree/payout/` (in `payments/urls.py`, served directly)
- Razorpay webhook: `/api/webhook/razorpay/` (in `payments/urls.py`, served directly)
- Old URLs redirect to new URLs via 301/302 in `core/urls.py`

**URL mapping:**

| Old URL | New URL | Redirect Type |
|---------|---------|---------------|
| `/api/webhook/cashfree/payout/` | `/api/webhook/cashfree/payout/` | 301 (permanent) |
| `/api/rent/payment-callback/` | `/api/webhook/razorpay/` | 301 (permanent) |

### 9.3 Rollback URL Migration

If rollback is required, old URLs in `core/views.py` are restored via `git revert`. The `payments/urls.py` include in `rentsecure_be/urls.py` is removed. Redirects in `core/urls.py` are reverted to direct view references.

### 9.4 Data Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Webhook URL breakage | Medium | High | Test redirects on staging before merge |
| Duplicate webhook processing | Medium | High | Idempotency enforced via `WebhookEvent` model |
| Invalid signature accepted | Low | High | HMAC verification tested with known-good and known-bad signatures |
| `core/views.py` regression | Low | Medium | All existing view tests must pass after webhook removal |
| Circular dependency introduced | Low | Medium | Architecture tests verify no new cycles |

---

## 10. Rollback Plan

### 10.1 Rollback Triggers

Rollback is triggered if any of the following occur:
- Webhook handlers fail on staging or production (provider callbacks return 500).
- HMAC verification breaks legitimate provider callbacks.
- Idempotency logic causes missed webhook processing.
- Old URLs do not redirect correctly.
- `core/views.py` removal causes `ImportError` or `AttributeError` in existing code.
- Any CI gate fails after merge and cannot be fixed within 30 minutes.
- Production incident: payment status not updated after webhook.
- Security finding: webhook endpoint accepts invalid signatures.

### 10.2 Rollback Steps

1. **Deploy decision:** Confirm rollback decision with Platform Team Lead.
2. **Git revert:**
   ```bash
   git revert <PR-004-merge-commit-sha>
   git push origin main
   ```
3. **Restore `core/views.py`:** Restore webhook handler functions from git.
4. **Restore `core/urls.py`:** Revert redirects to direct view references.
5. **Remove `payments/urls.py` include from `rentsecure_be/urls.py`.**
6. **Reverse migration:**
   ```bash
   python manage.py migrate --reverse payments 0002_webhook_event
   ```
   This removes the `payment_webhookevent` table.
7. **Deploy reverted code:** Deploy the reverted commit to staging, then production.
8. **Smoke tests:**
   ```bash
   python manage.py check
   python manage.py migrate
   python manage.py shell -c "from core.views import cashfree_payout_webhook; print(cashfree_payout_webhook)"
   ```
9. **Verify provider callbacks:** Send test webhooks from Cashfree test mode and Razorpay test mode. Verify old URLs respond correctly.
10. **Notify team:** Post rollback completion notice with root cause and fix plan.

### 10.3 Estimated Rollback Time

**30 minutes** (git revert + migrate --reverse + deploy + smoke tests + provider verification).

### 10.4 Data Risk

**Low.** The `WebhookEvent` table can be removed via `migrate --reverse`. Old webhook handlers are restored from git. No data is lost during rollback.

### 10.5 Rollback Validation

- Rollback must be tested on staging **before** production deploy.
- Test sequence:
  1. Apply PR-004 to staging.
  2. Verify new webhook URLs respond correctly.
  3. Verify old URLs redirect correctly.
  4. Execute rollback steps 2-9 above.
  5. Verify old webhook URLs respond directly.
  6. Re-apply PR-004 after successful rollback test.

---

## 11. Expected Git Diff

### 11.1 Summary

| Metric | Value |
|--------|-------|
| Files changed | 9 (7 new, 3 modified) |
| Files added | 7 |
| Files modified | 3 |
| Files deleted | 0 |
| Lines added | ~420 |
| Lines removed | ~120 |
| Net change | ~300 lines |

### 11.2 Files Added (~280 lines)

| File | Approx Lines | Description |
|------|---------------|-------------|
| `payments/views/__init__.py` | 0 | Package marker |
| `payments/views/webhooks.py` | ~150 | Cashfree and Razorpay webhook handlers with HMAC + idempotency |
| `payments/urls.py` | ~30 | Webhook URL patterns (rewrites placeholder) |
| `payments/tests/test_webhooks.py` | ~120 | Unit and integration tests for webhook handlers |
| `payments/tests/test_webhook_idempotency.py` | ~60 | Idempotency tests |
| `payments/tests/test_webhook_security.py` | ~60 | Security tests |
| `payments/tests/test_webhook_redirects.py` | ~40 | Redirect tests |

### 11.3 Files Modified (~180 lines)

| File | Approx Lines Changed | Description |
|------|----------------------|-------------|
| `core/views.py` | -120, +0 | Remove `cashfree_payout_webhook`, `razorpay_webhook`, `_get_rent_from_event`, `_process_rent_payment`, and `razorpay` import |
| `core/urls.py` | +15, -15 | Replace webhook handlers with 301/302 redirects |
| `rentsecure_be/urls.py` | +3, -0 | Add `path("api/webhook/", include("payments.urls"))` BEFORE `core/` URLs |

### 11.4 Diff Constraints

- No file in the diff may exceed 400 lines total after modification.
- No more than 15 files changed (actual count: 9 — within limit).
- No deletions of existing functionality (old URLs remain as redirects).

---

## 12. Definition of Done

PR-004 is **Done** when ALL of the following are true.

### Code
- [ ] `payments/views/webhooks.py` created with Cashfree and Razorpay handlers.
- [ ] `payments/views/__init__.py` created.
- [ ] `payments/urls.py` created with webhook URL patterns.
- [ ] `rentsecure_be/urls.py` includes `payments/urls.py` BEFORE `core/` URLs.
- [ ] `core/urls.py` webhook URLs return 301/302 redirects.
- [ ] `core/views.py` webhook handlers removed; `razorpay` import removed.
- [ ] `WebhookEvent` model created with `event_id` unique constraint.
- [ ] Webhook idempotency implemented and tested.

### Tests
- [ ] `payments/tests/test_webhooks.py` created with all required test cases.
- [ ] `payments/tests/test_webhook_idempotency.py` created with all required test cases.
- [ ] `payments/tests/test_webhook_security.py` created with all required test cases.
- [ ] `payments/tests/test_webhook_redirects.py` created with all required test cases.
- [ ] All new tests pass.
- [ ] All existing tests pass (no regressions).
- [ ] Test coverage ≥90% for new code.
- [ ] Redirect tests pass on staging.

### CI
- [ ] `ruff check .` passes (0 errors).
- [ ] `ruff format --check .` passes.
- [ ] `mypy .` passes (0 errors).
- [ ] `import-linter check` passes (0 violations).
- [ ] `pytest tests/ -v --cov` passes.
- [ ] `pytest tests/architecture/ -v` passes.
- [ ] `python manage.py check` passes.
- [ ] `python manage.py makemigrations --check` passes.
- [ ] `bandit -r payments/ core/` passes (0 high/medium).
- [ ] `safety check` passes (0 critical).

### Architecture
- [ ] No `rentsecure_be/` imports in new/modified files.
- [ ] No `razorpay` or `cashfree` imports in `core/`.
- [ ] No circular dependencies introduced.
- [ ] `payments/views/webhooks.py` ≤300 lines.
- [ ] `core/views.py` reduced in size.
- [ ] Old URLs return 301/302 redirects.
- [ ] New URLs serve webhook handlers directly.

### Documentation
- [ ] `docs/architecture/contexts/payment.md` updated with webhook migration info.
- [ ] ADR-004 updated to reflect PR-004 completion.
- [ ] CHANGELOG.md updated.

### Deployment
- [ ] PR approved by Platform Team Lead and Security Lead.
- [ ] Merged to `phase-0-foundation` branch.
- [ ] Deployed to staging.
- [ ] Staging validation passed (48 hours — webhooks require extended validation).
- [ ] Provider test webhooks verified (Cashfree test mode, Razorpay test mode).
- [ ] Rollback tested on staging before production deploy.
- [ ] No production incidents during staging validation.

---

## 13. Developer Checklist

### Pre-Implementation
- [ ] Verify PR-001 is merged to `phase-0-foundation` branch.
- [ ] Verify `payments` is in `INSTALLED_APPS`.
- [ ] Verify `payments/views/` and `payments/urls.py` exist.
- [ ] Verify current webhook handlers in `core/views.py` (`cashfree_payout_webhook`, `razorpay_webhook`).
- [ ] Verify current webhook URLs in `core/urls.py`.
- [ ] Verify current `rentsecure_be/urls.py` URL include order.
- [ ] Read `ENGINEERING_STANDARDS.md` sections: View Rules, Import Rules, Migrations, Security.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Dependency Rules, Migration Rules, Files AI Must Never Modify Automatically.
- [ ] Check `core/views.py` for `razorpay` and `cashfree` imports.
- [ ] Check `core/views.py` for webhook handler function signatures.
- [ ] Confirm dependency matrix constraint: `core/` cannot import from `payment/` (see §6.2).
- [ ] Confirm `payment/` may import from `property/` (for `RentRecord` access).
- [ ] Confirm `payment/` may NOT import from `notification/` directly (see §6.2).

### Implementation
- [ ] Create `payments/views/__init__.py`.
- [ ] Create `payments/views/webhooks.py` with `cashfree_payout_webhook` and `razorpay_webhook`.
- [ ] Implement HMAC verification for both providers.
- [ ] Implement `WebhookEvent` idempotency check in both handlers.
- [ ] Create `payments/urls.py` with webhook URL patterns.
- [ ] Update `rentsecure_be/urls.py` to include `payments/urls.py` BEFORE `core/` URLs.
- [ ] Update `core/urls.py` to replace webhook handlers with 301/302 redirects.
- [ ] Remove webhook handlers from `core/views.py`.
- [ ] Remove `razorpay` import from `core/views.py`.
- [ ] Create `payments/tests/test_webhooks.py`.
- [ ] Create `payments/tests/test_webhook_idempotency.py`.
- [ ] Create `payments/tests/test_webhook_security.py`.
- [ ] Create `payments/tests/test_webhook_redirects.py`.
- [ ] Run `python manage.py makemigrations --check` (should not generate new migrations for existing models).
- [ ] Run `python manage.py migrate` and verify success.

### Testing
- [ ] Run `pytest payments/tests/test_webhooks.py -v`.
- [ ] Run `pytest payments/tests/test_webhook_idempotency.py -v`.
- [ ] Run `pytest payments/tests/test_webhook_security.py -v`.
- [ ] Run `pytest payments/tests/test_webhook_redirects.py -v`.
- [ ] Run `pytest tests/ -v --cov` and verify ≥90% coverage for new code.
- [ ] Run `pytest tests/architecture/ -v` and verify 0 failures.
- [ ] Verify old URLs redirect: `/api/webhook/cashfree/payout/` → `/api/webhook/cashfree/payout/` (301/302).
- [ ] Verify old URLs redirect: `/api/rent/payment-callback/` → `/api/webhook/razorpay/` (301/302).
- [ ] Verify new URLs serve webhook handlers directly.
- [ ] Verify `razorpay` import is removed from `core/views.py`.

### Validation
- [ ] Run `ruff check .` and verify 0 errors.
- [ ] Run `ruff format --check .` and verify 0 issues.
- [ ] Run `mypy .` and verify 0 errors.
- [ ] Run `import-linter check` and verify 0 violations.
- [ ] Run `python manage.py check` and verify 0 errors.
- [ ] Run `python manage.py makemigrations --check` and verify 0 errors.
- [ ] Run `bandit -r payments/ core/` and verify 0 high/medium.
- [ ] Run `safety check` and verify 0 critical.
- [ ] Verify no `print()` statements in new code.
- [ ] Verify no `# TODO` or `# FIXME` comments.
- [ ] Verify no commented-out code.
- [ ] Verify no hardcoded secrets.
- [ ] Verify no `from rentsecure_be.X import Y` in new code.
- [ ] Verify no `from razorpay` or `from cashfree` imports in `core/`.

### Rollback
- [ ] Document rollback plan in PR description.
- [ ] Test rollback on staging: apply PR-004, verify webhooks, execute rollback, verify old URLs work.

### PR
- [ ] Commit message follows conventional commits format.
- [ ] Branch name follows `<type>/<ticket-id>-<description>` format.
- [ ] PR description includes: summary, motivation, changes, testing, rollback plan.
- [ ] PR size is within limits (≤400 lines, ≤15 files — actual: ~300 lines, 9 files).
- [ ] PR is linked to Phase 0 task 0.4.
- [ ] Security review completed by Security Lead.

---

## 14. Reviewer Checklist

Use this checklist when reviewing PR-004.

### Architecture
- [ ] `payments/views/webhooks.py` contains both Cashfree and Razorpay handlers.
- [ ] `core/views.py` no longer contains webhook handlers.
- [ ] `core/views.py` no longer imports `razorpay`.
- [ ] `core/` does NOT import from `payments/` (dependency matrix compliance).
- [ ] `payments/views/webhooks.py` may import from `properties/` (allowed by matrix).
- [ ] No circular dependencies introduced.
- [ ] No new `apps/` or `config/` directories.
- [ ] `payments/views/webhooks.py` ≤300 lines.
- [ ] `core/views.py` reduced in size.
- [ ] Old URLs return 301/302 redirects.
- [ ] New URLs serve webhook handlers directly.

### Security
- [ ] HMAC verification implemented for both Cashfree and Razorpay.
- [ ] Invalid signatures return 401.
- [ ] Idempotency implemented via `WebhookEvent` model with unique `event_id`.
- [ ] Duplicate webhooks return 200 without reprocessing.
- [ ] No sensitive data logged (full payloads, signatures).
- [ ] Secrets come from environment variables.
- [ ] `@csrf_exempt` is used only on webhook views with justification.
- [ ] Bandit scan passes (0 high/medium).
- [ ] Safety scan passes (0 critical).

### Code Quality
- [ ] Ruff passes (0 errors, 0 formatting issues).
- [ ] MyPy passes (0 errors).
- [ ] No `print()` statements.
- [ ] No `# TODO` or `# FIXME` comments.
- [ ] No commented-out code.
- [ ] No empty `except:` clauses.
- [ ] Webhook code is readable and follows Django conventions.

### Testing
- [ ] `payments/tests/test_webhooks.py` covers all required test cases.
- [ ] `payments/tests/test_webhook_idempotency.py` covers all required test cases.
- [ ] `payments/tests/test_webhook_security.py` covers all required test cases.
- [ ] `payments/tests/test_webhook_redirects.py` covers all required test cases.
- [ ] All new tests pass.
- [ ] All existing tests pass (no regressions).
- [ ] No test uses `time.sleep()`.
- [ ] No test depends on execution order.
- [ ] Tests use factories, not hardcoded data.
- [ ] Redirect tests pass on staging data.

### Migrations
- [ ] `0002_webhook_event.py` migration (if created) is reversible.
- [ ] Migration runs cleanly on test database.
- [ ] `python manage.py migrate --reverse` works on test database.

### Documentation
- [ ] `docs/architecture/contexts/payment.md` updated with webhook migration details.
- [ ] ADR-004 updated to reflect PR-004 completion.
- [ ] CHANGELOG.md updated.
- [ ] PR description includes rollback plan and provider test verification steps.

### CI
- [ ] All CI gates pass.
- [ ] No import-linter violations.
- [ ] No architecture test failures.
- [ ] No circular dependency warnings.
- [ ] No `razorpay`/`cashfree` imports outside `payments/`.

---

## 15. AI Checklist

Use this checklist when generating PR-004 with AI assistance.

### Pre-Generation
- [ ] Read `ENGINEERING_STANDARDS.md` sections: View Rules, Import Rules, Migrations, Security.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Dependency Rules, Migration Rules, Files AI Must Never Modify Automatically.
- [ ] Verify PR-001 is merged to `phase-0-foundation` branch.
- [ ] Verify `payments` is in `INSTALLED_APPS`.
- [ ] Verify current webhook handlers in `core/views.py`.
- [ ] Verify current webhook URLs in `core/urls.py`.
- [ ] Verify current `rentsecure_be/urls.py` URL include order.
- [ ] Confirm dependency matrix constraint: `core/` cannot import from `payment/` (§6.2).
- [ ] Confirm `payment/` may import from `property/` (for `RentRecord`).
- [ ] Confirm `payment/` may NOT import from `notification/` directly (§6.2).
- [ ] Verify no `WebhookEvent` model exists yet in `payments/models.py`.

### Code Generation
- [ ] Generate `payments/views/__init__.py`.
- [ ] Generate `payments/views/webhooks.py` with `cashfree_payout_webhook` and `razorpay_webhook`.
- [ ] Implement HMAC verification for both providers.
- [ ] Implement `WebhookEvent` idempotency check in both handlers.
- [ ] Generate `payments/urls.py` with webhook URL patterns.
- [ ] Update `rentsecure_be/urls.py` to include `payments/urls.py` BEFORE `core/` URLs.
- [ ] Update `core/urls.py` to replace webhook handlers with 301/302 redirects.
- [ ] Remove webhook handlers from `core/views.py`.
- [ ] Remove `razorpay` import from `core/views.py`.
- [ ] **Do NOT** import from `payments/` in `core/`.
- [ ] **Do NOT** import from `notification/` in `payments/views/webhooks.py` (unless ADR exception granted).
- [ ] **Do NOT** drop old webhook URLs — keep as redirects.

### Test Generation
- [ ] Generate `payments/tests/test_webhooks.py` with all required test cases.
- [ ] Generate `payments/tests/test_webhook_idempotency.py` with all required test cases.
- [ ] Generate `payments/tests/test_webhook_security.py` with all required test cases.
- [ ] Generate `payments/tests/test_webhook_redirects.py` with all required test cases.
- [ ] **Do NOT** generate tests for `ai_assistant/` or `dashboard/`.
- [ ] **Do NOT** use `time.sleep()` in tests.
- [ ] **Do NOT** hardcode test data — use factories.

### Validation
- [ ] Run `ruff check .` and fix all errors.
- [ ] Run `ruff format --check .` and fix all issues.
- [ ] Run `mypy .` and fix all errors.
- [ ] Run `import-linter check` and fix all violations.
- [ ] Run `pytest tests/ -v --cov` and verify all pass.
- [ ] Run `pytest tests/architecture/ -v` and verify 0 failures.
- [ ] Run `python manage.py check` and verify 0 errors.
- [ ] Run `python manage.py makemigrations --check` and verify 0 errors.
- [ ] Run `python manage.py migrate` and verify success.
- [ ] Run `bandit -r payments/ core/` and verify 0 high/medium.
- [ ] Run `safety check` and verify 0 critical.
- [ ] Verify `razorpay` import is removed from `core/views.py`.
- [ ] Verify old URLs redirect correctly.
- [ ] Verify new URLs serve webhook handlers directly.

### Stop and Ask Conditions
AI must **stop and ask human** before proceeding if:
- [ ] `payments/views/webhooks.py` **must** import from `notification/` and no delegation pattern satisfies the requirement.
- [ ] `core/views.py` removal of webhook handlers breaks other functionality.
- [ ] `core/urls.py` redirect pattern causes URL resolution conflicts.
- [ ] `rentsecure_be/urls.py` include order cannot be changed (other dependencies).
- [ ] `WebhookEvent` model design is unclear (field choices, constraint placement).
- [ ] HMAC verification logic differs from current implementation in unexpected ways.
- [ ] Any CI gate fails after 3 fix attempts.
- [ ] Dependency matrix exception is required to complete the task.
- [ ] `@csrf_exempt` is required but Security Lead has not approved it.

### Commit
- [ ] Commit message follows format: `feat(payments): move webhooks to payments with idempotency`
- [ ] Commit body explains: webhook migration approach, idempotency strategy, redirect strategy, reference to ADR-004.
- [ ] Branch name: `feature/phase-0-004-move-webhooks-to-payments`.

---

## 16. Stop-and-Ask Conditions

AI must **stop and ask human** before proceeding if:

1. `payments/views/webhooks.py` must import from `notification/` directly and no delegation pattern satisfies the requirement (dependency matrix violation).
2. `core/views.py` removal of webhook handlers causes import errors or broken functionality elsewhere.
3. `core/urls.py` redirect pattern causes URL resolution conflicts with other `core/` URLs.
4. `rentsecure_be/urls.py` include order cannot be changed due to other URL dependencies.
5. `WebhookEvent` model design requires fields or constraints not specified in this spec.
6. HMAC verification logic for either provider differs from current implementation in a way that would break existing webhook integrations.
7. Any CI gate fails after 3 fix attempts.
8. Dependency matrix exception is required to complete the task.
9. `@csrf_exempt` is required but Security Lead has not explicitly approved its use.
10. Provider test environments (Cashfree test mode, Razorpay test mode) are not available for staging validation.
11. The `create_rent_payment` view (also in `core/views.py`) needs to be moved but is not in scope for this PR.

---

## 17. Appendices

### Appendix A: Architecture Decision References

| Decision | Reference |
|----------|-----------|
| `payments/` bounded context | ADR-001, ADR-004 |
| Webhook handlers in `payments/views/webhooks.py` | ADR-004 §3 |
| `payment/` may import from `property/` | ADR-001 §2.3, ADR-006 |
| `payment/` may NOT import from `notification/` | ADR-006 dependency matrix |
| `core/` cannot import from `payment/` | ADR-001 §2.3, dependency matrix |
| No `razorpay`/`cashfree` imports in non-adapter files | ADR-004 §3.7, ADR-006 |
| Webhook idempotency via `WebhookEvent` | ADR-004 §3.5, Engineering Standards §13.2 |
| HMAC verification for all webhooks | Engineering Standards §13.2 |
| `@csrf_exempt` for webhook endpoints | Engineering Standards §14.2, ADR-004 |
| Phase 0 is additive only | ADR-007 §2.1 |
| Old URLs remain as redirects during transition | ADR-007 §2.5, Engineering Standards §19.3 |
| No `apps/` parent directory | ADR-001 |

### Appendix B: Related Documents

- [Architecture v1.1 Release Candidate](../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Architecture v1.1 Implementation Master Plan — Phase 0](../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Phase 0 Execution Plan — PR-004](../PHASE_0_EXECUTION_PLAN.md)
- [Engineering Backlog — Feature 0.4](../ENGINEERING_BACKLOG.md)
- [Engineering Standards](../ENGINEERING_STANDARDS.md)
- [AI Engineering Playbook](../AI_ENGINEERING_PLAYBOOK.md)
- [Payment Architecture ADR](../docs/architecture/adr/ADR-004_payment_architecture.md)
- [Migration Strategy ADR](../docs/architecture/adr/ADR-007_migration_strategy.md)
- [Import Rules ADR](../docs/architecture/adr/ADR-006_import_rules.md)
- [Bounded Context Strategy ADR](../docs/architecture/adr/ADR-001_bounded_context_strategy.md)

### Appendix C: Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-20 | Principal Software Architect | Initial PR-004 specification for v1.1 freeze |

**Next Review:** After PR-004 merge
**Approval Required:** Platform Team Lead, Security Lead

---

*End of PR-004 Implementation Specification*
