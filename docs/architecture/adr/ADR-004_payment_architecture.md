# ADR-004: Payment Architecture

**Status:** Accepted
**Date:** 2026-07-19
**Deciders:** Chief Software Architect, Staff Engineer, Platform Team Lead, Security Lead
**Supersedes:** ADR-010 (v1.0 — Payment Integration)

---

## Context

Payment logic in RentSecureBE is currently scattered across four locations:
- `core/models.py`: `OwnerBankDetails` (plaintext `bank_account_number` and `ifsc_code`)
- `core/views.py`: `cashfree_payout_webhook` and `razorpay_webhook` function-based views
- `core/services/`: `BankDetailsService`
- `rentsecure_be/services/`: `CashfreeService`, `RazorpayService`, `LeegalityService`
- `rentsecure_be/utils/`: `cashfree_payout.py`

Critical security and architectural findings:
1. **`payments/` app is not in `INSTALLED_APPS`** — all payment adapter code is unreachable by Django
2. **Bank details stored in plaintext** — violates RBI guidelines and PCI-adjacent standards
3. **Webhook URLs are hardcoded in `core/views.py`** — provider URL changes require edits in two places
4. **`core/views.py` is a 566-line god view** containing payment webhook handling
5. **Payment, notification, and PDF logic is scattered across 4+ apps** violating single-responsibility

Year 1 payment flow is completely free: rent payment does NOT go through a payment gateway. Owners receive payment via manual UPI. The `payments/` app exists with adapters but is architecturally non-functional.

---

## Decision

RentSecureBE uses a **layered payment architecture** with `payments/` as a first-class Django app, encrypted financial fields, and adapter-based gateway integration.

### Key Rules

1. **`payments/` is in `INSTALLED_APPS` from Phase -1.** The app is functional from day one.
2. **`OwnerBankDetails` lives in `payments/models.py` with encrypted fields.** `bank_account_number` and `ifsc_code` use `django-cryptography` `encrypt()` fields.
3. **Webhook handlers live in `payments/views/webhooks.py`.** HMAC verification and idempotency are implemented here.
4. **Payment adapters implement the `PaymentGateway` interface.** Year 1 adapter: `ManualPaymentAdapter`. Disabled adapters: `CashfreeAdapter`, `RazorpayAdapter` (behind feature flags).
5. **Webhook idempotency is enforced via `WebhookEvent` model** with `event_id` unique constraint.
6. **Audit logging uses `django-simple-history`** on `OwnerBankDetails`, `WebhookEvent`, and `RentRecord.payout_status`.
7. **No payment SDK imports in `core/` or any non-adapter file.** Enforced by architecture tests.
8. **All payment operations go through `PaymentService` + `PaymentGateway`.** Views never instantiate adapters directly.

### Year 1 Payment Flow (Manual UPI)

1. Owner registers UPI ID and uploads QR code
2. Owner provides bank account details (encrypted at rest)
3. Tenant sees owner's payment details (UPI ID, QR, bank account)
4. Tenant pays via any UPI app
5. Tenant uploads UTR (required) and screenshot (optional)
6. Status becomes `Payment Submitted`
7. Owner verifies manually and clicks Approve/Reject
8. On approval: Rent Receipt PDF is generated, receipt is emailed, status becomes `Paid`

### Adapter Strategy

| Adapter | Status | Feature Flag | Use Case |
|---------|--------|-------------|----------|
| `ManualPaymentAdapter` | Enabled | `UPI_PAYMENT_ENABLED = True` | Year 1 manual UPI flow |
| `CashfreeAdapter` | Disabled | `CASHFREE_PAYMENTS_ENABLED = False` | Stage 2 auto-payout |
| `RazorpayAdapter` | Disabled | `RAZORPAY_PAYMENTS_ENABLED = False` | Stage 2 auto-payment |

---

## Alternatives Considered

### 1. Keep Payment Logic in `core/`

**Description:** Leave `OwnerBankDetails`, webhooks, and bank services in `core/`.

**Pros:**
- No migration effort
- Simple for current team

**Cons:**
- `core/` remains a God app with payment responsibilities
- Bank details in plaintext (critical security risk)
- Webhook handlers mixed with OTP and subscription views
- No adapter abstraction for future gateway integration
- `payments/` remains a zombie app

**Decision:** Rejected. Violates security requirements and single-responsibility principle.

### 2. Third-Party Payment Gateway from Day 1

**Description:** Integrate Cashfree or Razorpay as the primary payment method from launch.

**Pros:**
- Automated payment processing
- Reduced manual verification overhead

**Cons:**
- Adds cost (transaction fees)
- Adds dependency on external provider uptime
- Violates Year 1 "free payment flow" principle
- Requires idempotency, webhooks, and reconciliation from Day 1
- Regulatory compliance for auto-debit is complex in India

**Decision:** Rejected. Year 1 strategy is manual UPI. Stage 2 enables gateways via feature flags.

### 3. Adapter-Based Payment Architecture (Selected)

**Description:** `payments/` app with `PaymentGateway` interface, encrypted fields, webhook idempotency, and adapter-based gateway integration.

**Pros:**
- `payments/` is a first-class Django app (in `INSTALLED_APPS`)
- Financial data encrypted at rest (RBI compliance)
- Webhook idempotency prevents double-processing
- Adapter pattern allows gateway swap without changing business logic
- Year 1 manual flow is simple; Stage 2 gateways are ready to enable
- Audit logging for payment operations

**Cons:**
- Requires Phase 0 data migration for `OwnerBankDetails`
- Requires Phase 0 webhook move (risk of breaking provider callbacks)
- Adapter abstraction adds complexity for Year 1 manual flow

**Decision:** Accepted. Meets security requirements and provides clear upgrade path to Stage 2.

---

## Consequences

### Positive
- `payments/` is architecturally functional (in `INSTALLED_APPS`)
- Bank details encrypted at rest (RBI compliance)
- Webhook idempotency prevents double-processing
- Adapter pattern enables Stage 2 gateway integration without business logic changes
- Audit logging for payment disputes and fraud detection
- `core/views.py` shrinks by ~100 lines (webhooks moved)
- Clear ownership: Platform Team owns complete payment flow

### Negative
- Phase 0 data migration for `OwnerBankDetails` is medium-risk
- Phase 0 webhook move requires coordination with Cashfree/Razorpay test environments
- Adapter abstraction adds code volume for Year 1 (manual flow only)
- Feature flags are global booleans in Year 1 (per-user flags in Phase 6)

### Neutral
- `NotificationPreference` moves to `notification/models.py` in Phase 0 (related but separate concern)
- `core/services/bank_details_service.py` moves to `payments/services/` in Phase 3
- Rent Receipt PDF generation uses WeasyPrint (unchanged)

---

## Migration Notes

### Phase -1: Foundation
- Add `payments` to `INSTALLED_APPS`
- Create `payments/migrations/__init__.py`
- Move `cashfree_payout.py` from `rentsecure_be/utils/` to `payments/adapters/cashfree_client.py`
- Update `payments/adapters/cashfree.py` imports

### Phase 0: Critical Fixes
- Create `shared/fields.py` with `EncryptedCharField` and `EncryptedTextField`
- Create `payments/models.py` with `OwnerBankDetails` using encrypted fields
- Create `payments/views/webhooks.py` with `cashfree_payout_webhook` and `razorpay_webhook`
- Create `payments/urls.py` with webhook URL patterns
- Create `WebhookEvent` model with `event_id` unique constraint
- Move webhook URLs from `core/urls.py` to `payments/urls.py`; keep old URLs as 301/302 redirects
- Add webhook idempotency checks
- Add `HistoricalRecords` to `OwnerBankDetails` and `WebhookEvent`
- Create data migration: `core_ownerbankdetails` → `payment_ownerbankdetails`
- Deprecate `OwnerBankDetails` in `core/models.py`

### Phase 3: Service Consolidation
- Create `payments/services/webhook_service.py` and `payments/services/bank_details_service.py`
- Move `update_owner_bank_details` view to `payments/views/bank_details_views.py`
- Remove duplicate `cashfree_service.py`, `razorpay_service.py`, `leegality_service.py` from `rentsecure_be/services/`
- Update all cross-app imports
- Remove `core/services/bank_details_service.py`

### Rollback
- Phase -1: Revert PR. Remove `payments` from `INSTALLED_APPS`. No data changes.
- Phase 0: `git revert` + `migrate --reverse`. Old `core_ownerbankdetails` table remains.
- Phase 3: `git revert` + restore `core/views/` webhook handlers. 30-minute rollback.

---

## Future Evolution

### Stage 2 (Trigger: >500 payments/month or >10 hours/week manual verification)
- Enable `CashfreeAdapter` for auto-payout (10% canary, then 100%)
- Enable `RazorpayAdapter` for tenant auto-payment
- Webhook handlers process instant payment confirmations
- Idempotency keys prevent double-processing during provider retries

### Stage 3
- `payments/` may become a microservice if transaction volume justifies it
- Distributed locking for payment approvals (prevent race conditions)
- Reconciliation service for bank statement matching

### Long-term
- `payments/` remains the canonical payment bounded context
- Adapter pattern supports additional gateways (Paytm, PhonePe) via new adapters
- Encrypted fields extend to other PII (email, phone) as regulatory requirements evolve

---

## References

- [Architecture v1.1 Release Candidate — Findings PR-01 through PR-06](../../../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Implementation Master Plan — Phase 0, Phase 3](../../../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Finance Module Rules](../../../.kilo/instructions/finance.md)
- [Notification Module Rules](../../../.kilo/instructions/notifications.md)
- [RBI Guidelines on Payment Data Security](https://rbi.org.in)
