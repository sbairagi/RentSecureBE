# Business Gaps & Bugs Audit

Comparison of `docs/business-rules/`, models, views, signals, webhooks, and `properties/test_loopholes_critical.py`.

**Legend:** BUG | GAP | SECURITY | DOC

---

## Executive summary

| Category | Approx. count |
|----------|----------------|
| Critical (money, security, crashes) | 6 |
| High (enforcement / automation) | 9 |
| Medium (validation holes) | 15 |
| Rules documented but not enforced | 7 areas |

The [business-rules](../business-rules/README.md) docs describe **intended** behavior well. Many paths are **aspirational** until signals, webhooks, and subscription seeding are fixed.

---

## Critical

### GAP-001 | SECURITY — Razorpay webhook insecure and unreliable

| | |
|--|--|
| **Refs** | [16-payments](../business-rules/16-payments-and-webhooks.md), `core/views.py` |
| **Issue** | `razorpay_webhook` is defined **three times**; only the last handler runs — **no HMAC verification**, handles `payment_link.paid`. |
| **Impact** | Fake POST can mark rent PAID; legitimate payments may 404 if `reference_id` ≠ rent id (not set in `create_payment_link`). Double webhook → duplicate payout attempts. |
| **Fix** | Single handler, verify signature, set `reference_id` on payment link, idempotent PAID transition. |

---

### GAP-002 | BUG — Cashfree / payout notification paths can crash

| | |
|--|--|
| **Refs** | [11-payout](../business-rules/11-payout-retry.md), `rentsecure_be/services/cashfree_service.py`, `core/views.py` |
| **Issue** | Uses `rent.renter.property.owner`, `owner.profile.whatsapp_number`; `rent = rent.save()` misuse. |
| **Impact** | Payout may succeed but webhook/notify fails. |
| **Fix** | Use `rent.owner`, `UserProfile` via `notification_preference` or documented WhatsApp field; fix save calls. |

---

### GAP-003 | GAP — Multiple active renters on one unit

| | |
|--|--|
| **Refs** | [07-renters](../business-rules/07-renters.md), `TEST_DOCUMENTATION.md` |
| **Issue** | No DB constraint or API check for two `status=active` renters on same `Unit`. |
| **Impact** | Unclear rent obligation; wrong occupancy. |
| **Fix** | Validate on create: at most one `active`/`notice_period` per unit; or DB constraint. |

---

### GAP-004 | BUG — `get_free_plan_limit` missing on `FeatureEnforcer`

| | |
|--|--|
| **Refs** | [04-buildings](../business-rules/04-buildings.md), [02-subscription](../business-rules/02-subscription-and-usage-limits.md), `properties/views/building_views.py` |
| **Issue** | `enforcer.get_free_plan_limit(...)` called but class only has `_get_free_plan_limit`. |
| **Impact** | Owners past subscription grace → **AttributeError** when listing buildings (not “slice to free limit”). |
| **Fix** | Add public method delegating to `_get_free_plan_limit`; audit `unit_views.py` for same pattern. |

---

### GAP-005 | SECURITY — Self-service subscription and add-on abuse

| | |
|--|--|
| **Refs** | [02-subscription](../business-rules/02-subscription-and-usage-limits.md), `core/views.py`, `core/serializers.py` |
| **Issue** | `UserSubscriptionViewSet` allows user to assign any `plan` without payment. `AddOnPurchase.amount` is **summed into limits**. |
| **Impact** | Free users can grant themselves Elite limits. |
| **Fix** | Admin-only or payment-webhook-gated plan changes; separate “purchased units” from price `amount`. |

---

### GAP-006 | GAP — Missing `PlanFeatureLimit` → unlimited (paid plans)

| | |
|--|--|
| **Refs** | `properties/feature_enforcer.py` |
| **Issue** | `_get_plan_limit`: `PlanFeatureLimit.DoesNotExist` → returns `'unlimited'`. |
| **Impact** | Misconfigured plan rows = no cap for that feature. |
| **Fix** | Default to `0` or free-tier limit; log misconfiguration. |

---

## High

### GAP-007 | GAP — Django signals not registered

| | |
|--|--|
| **Refs** | [22-signals](../business-rules/22-signals-and-automation.md), [17-notifications](../business-rules/17-notifications.md), `core/apps.py`, `properties/apps.py` |
| **Issue** | `ready()` does not `import core.signals` / `properties.signals`. |
| **Impact** | No auto Free plan, no usage sync, no receipt/voice on PAID, no vacancy/archive/defaulter automation. |
| **Fix** | Import signals in `AppConfig.ready()`. |

---

### GAP-008 | GAP — Usage counter drift and double tracking

| | |
|--|--|
| **Refs** | [02-subscription](../business-rules/02-subscription-and-usage-limits.md), `properties/signals/__init__.py` |
| **Issue** | ViewSets `increment`/`decrement` vs unwired `update_usage_count`; typo `max_buldings` in building signal. |
| **Impact** | False 403 at limit or over-quota usage. |
| **Fix** | Single source of truth (recount from DB or only manual counter); fix typo. |

---

### GAP-009 | GAP — Feature key name mismatch (images/documents)

| | |
|--|--|
| **Refs** | [09-unit-images](../business-rules/09-unit-images-and-documents.md), `properties/views/unit_views.py` |
| **Issue** | ViewSets use `unit_images` / `unit_documents`; plan rows often use `max_unit_images` / `max_document_uploads`. |
| **Impact** | Missing limit row → unlimited (see GAP-006). |
| **Fix** | Align keys everywhere; migration for `PlanFeatureLimit` rows. |

---

### GAP-010 | GAP — Renter status fields not validated

| | |
|--|--|
| **Refs** | [07-renters](../business-rules/07-renters.md), `test_loopholes_critical.py` |
| **Issue** | `is_active=True` + `status=deactivated`; revoked + active; flagged + active allowed. Lists filter `status` only. |
| **Impact** | Ambiguous tenant state; wrong eligibility for rent/reminders. |
| **Fix** | Model `clean()` or serializer rules tying `is_active` to `status`. |

---

### GAP-011 | BUG — Defaulter signal logic wrong (when enabled)

| | |
|--|--|
| **Refs** | `properties/signals/__init__.py` |
| **Issue** | Uses `rent.status == "UNPAID"` (field is `payment_status`); sets `renter.active_agreement` (field missing). |
| **Impact** | Defaulter rules never run. |
| **Fix** | Use `PENDING` + past `rent_due_date`; remove invalid fields. |

---

### GAP-012 | BUG — Vacancy signal uses `unit.unit_number`

| | |
|--|--|
| **Refs** | `properties/signals/__init__.py` |
| **Issue** | `Unit` field is `unit`, not `unit_number`. |
| **Impact** | AttributeError if signal wired. |
| **Fix** | Use `unit.unit` or building display name. |

---

### GAP-013 | BUG — Renter / owner rent APIs use `renter.property.name`

| | |
|--|--|
| **Refs** | [13-renter-facing](../business-rules/13-renter-facing-apis.md), `properties/views/rent_record_views.py` |
| **Issue** | `renter.property` → `Unit`; no `.name` on Unit. |
| **Impact** | 500 on `get_latest_due_rent`, `owner_rent_overview`. |
| **Fix** | Use `unit.unit`, `building.name`, or serializer fields. |

---

### GAP-014 | BUG — Subscription expiry compares date to datetime

| | |
|--|--|
| **Refs** | `properties/feature_enforcer.py` |
| **Issue** | `sub.end_date < timezone.now()`; grace uses `timezone.now() - sub.end_date`. |
| **Impact** | Off-by-one / inconsistent grace behavior. |
| **Fix** | Compare `date` to `timezone.localdate()` consistently. |

---

### GAP-015 | GAP — New owners blocked without DB seed (signals unwired)

| | |
|--|--|
| **Refs** | [02-subscription](../business-rules/02-subscription-and-usage-limits.md), [14-known](../business-rules/14-known-behaviors-and-edge-cases.md) |
| **Issue** | Docs: Free limits without subscription. Code: no auto `UserSubscription`; `_get_plan_limit` can return 0. |
| **Impact** | 403 on all creates (integration tests fail without manual setup). |
| **Fix** | Wire `core/signals` + seed `PlanFeatureLimit` for `free`. |

---

## Medium

| ID | Type | Summary | Refs |
|----|------|---------|------|
| GAP-016 | GAP | Zero `rent_amount` allowed on `Renter` | [07-renters](../business-rules/07-renters.md) |
| GAP-017 | GAP | No cap on overpayment `amount_paid` | [08-rent-records](../business-rules/08-rent-records.md) |
| GAP-018 | GAP | Rent `date_paid` before `renter.start_date` allowed | [08-rent-records](../business-rules/08-rent-records.md) |
| GAP-019 | GAP | Archived units: active renters / new caretakers allowed | [05-units](../business-rules/05-units.md) |
| GAP-020 | GAP | `Unit.status` vs `is_vacant` can contradict | [05-units](../business-rules/05-units.md) |
| GAP-021 | GAP | `building_name` can differ from `building.name` | [05-units](../business-rules/05-units.md) |
| GAP-022 | GAP | Overlapping caretaker date ranges on same unit | [06-caretakers](../business-rules/06-caretakers.md) |
| GAP-023 | GAP | Same phone on multiple units (by design?) | [07-renters](../business-rules/07-renters.md) |
| GAP-024 | GAP | `ExtraCharge` has no plan limit | — |
| GAP-025 | DOC | `rent_records` limit used but not in `FEATURE_CHOICES` | [08-rent-records](../business-rules/08-rent-records.md) |
| GAP-026 | BUG | Owner OTP adds Django group `tenant` | [15-authentication](../business-rules/15-authentication.md) |
| GAP-027 | SECURITY | `CAProfileViewSet` lists all CAs | [18-finance](../business-rules/18-finance-and-tax.md) |
| GAP-028 | BUG | `TaxSubmissionToCA` filters `tax_summary__user` — field missing | [18-finance](../business-rules/18-finance-and-tax.md) |
| GAP-029 | GAP | Race on duplicate rent month → IntegrityError not 400 | [08-rent-records](../business-rules/08-rent-records.md) |
| GAP-030 | BUG | `generate_monthly_rent_records`, `daily_rent_reminder` import `rent.models` | [22-signals](../business-rules/22-signals-and-automation.md) |

---

## Documentation vs code (aspirational rules)

| Documented rule | Actual today |
|-----------------|--------------|
| Plan limits before every create | Only if subscription + limits seeded |
| Receipt / voice note on PAID | False (signals unwired) |
| New user gets Free subscription | False (signal unwired) |
| Downgrade trims resources after grace | False (command commented) |
| Defaulter after 3 missed rents | False (broken + unwired) |
| Secure Razorpay webhook | False (unsigned handler active) |
| Expired owner sees N buildings only | Crashes (GAP-004) |

---

## Fix priority (recommended)

1. **GAP-001** — Razorpay webhook (security + idempotency)
2. **GAP-007** — Wire signals OR remove claims from notification docs
3. **GAP-004** — `get_free_plan_limit` crash
4. **GAP-003** — One active renter per unit
5. **GAP-005** — Lock subscription / add-on APIs
6. **GAP-013** — Renter due-rent / owner overview 500s
7. **GAP-015** — Seed Free plan + default subscription on signup
8. **GAP-002** — Payout path attribute errors

---

## Verified as working (sanity check)

| Rule | Status |
|------|--------|
| OTP 5 min / 60s resend | OK |
| One rent per renter per `rent_month` | OK (`unique_together` + ViewSet) |
| Negative `amount_paid` on `full_clean()` | OK |
| Owner cannot mutate another owner's building (API tests) | OK when subscription allows create |
| JWT required on property ViewSets | OK |

---

## Traceability

| Source | Path |
|--------|------|
| Business rules | `docs/business-rules/` |
| Loophole tests | `properties/test_loopholes_critical.py` |
| Issue registry | `properties/TEST_DOCUMENTATION.md` |
| Enforcer | `properties/feature_enforcer.py` |

*Do not treat this file as legal/compliance sign-off—it is an engineering audit snapshot.*
