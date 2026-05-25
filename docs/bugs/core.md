# Bugs — `core` app

Auth, users, subscriptions, payment webhooks, bank details.

---

## CORE-001 | P0 — `razorpay_webhook` defined twice; unsigned handler wins

**File:** `core/views.py` (~417–470)

- First function: HMAC verification + `payment.captured`.
- Second function **overwrites** the first: no signature check, handles `payment_link.paid`.

**Impact:** Forged webhooks can mark rent PAID and trigger payout.

**Fix:** Keep one handler with signature verification and idempotent updates.

---

## CORE-002 | P0 — Razorpay webhook lookup likely fails

**Files:** `core/views.py`, `rentsecure_be/services/razorpay_service.py`

- Webhook uses `reference_id` → `RentRecord.objects.get(id=ref_id)`.
- `create_payment_link()` does **not** set `reference_id` to rent id.

**Impact:** Real payments may not update records.

**Fix:** Pass `reference_id=str(rent_record.id)` when creating payment link.

---

## CORE-003 | P1 — Owner OTP assigns wrong Django group

**File:** `core/views.py` — `OwnerVerifyOTP`

```python
group = Group.objects.get(name='tenant')
user.groups.add(group)
```

**Impact:** Owners get `tenant` group; role-based permissions break if used.

**Fix:** Use `owner` (or create group) for owners; keep `renter` for renters.

---

## CORE-004 | P0 — Self-service subscription upgrade without payment

**Files:** `core/views.py` (`UserSubscriptionViewSet`), `core/serializers.py`

- User can POST/PUT `UserSubscription` with any `plan`.
- `AddOnPurchase.amount` is summed into feature limits.

**Impact:** Unlimited resources without paying.

**Fix:** Admin-only writes or payment-gateway webhook to change plan.

---

## CORE-005 | P1 — `cashfree_payout_webhook` wrong owner path

**File:** `core/views.py`

```python
owner = rent.renter.property.owner
phone = owner.profile.whatsapp_number
```

- `User` has `UserProfile` via `userprofile`, not `profile`.
- `property` on renter returns `Unit`; owner is `rent.owner` or `unit.owner`.

**Impact:** Webhook may crash after payout update.

---

## CORE-006 | P1 — Signals never loaded

**File:** `core/apps.py` — `ready()` is empty; `core/signals.py` not imported.

**Impact:** No auto `UserProfile`, `NotificationPreference`, or Free `UserSubscription` on signup.

**Fix:** `import core.signals` in `ready()`.

---

## CORE-007 | P2 — `User.get_or_create` without `full_name`

**File:** `core/views.py` — OTP verify

- `User` model requires `full_name` and `whatsapp_number` (non-blank on model).

**Impact:** May fail on create depending on DB constraints / defaults.

---

## CORE-008 | P2 — Referral invalid code returns 400 after user created

**File:** `core/views.py` — referral block runs after `user.save()`.

**Impact:** Partial signup state on invalid referral.

---

## CORE-009 | P3 — Duplicate / dead webhook code

**File:** `core/views.py` — commented blocks, duplicate imports, `create_rent_payment` alongside payment links.

**Impact:** Maintenance confusion.
