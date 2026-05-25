# Bugs — `referral_and_earn` app

Referral codes and bonuses.

---

## REF-001 | P2 — Bonus applied without payment fraud checks

**File:** `core/views.py` (with `referral_and_earn.models.Referral`)

```python
referrer_referral.bonus_earned += 500
```

**Impact:** No cap, no verification referrer is distinct owner, self-referral possible if codes leak.

---

## REF-002 | P2 — Invalid referral code after user persisted

**File:** `core/views.py`

- User saved before referral validation completes in error path.

**Impact:** Orphan users on bad referral code (400 after partial create).

---

## REF-003 | P3 — Referral code collision handling

**File:** `referral_and_earn/models.py` — `uuid` fragment uppercased.

**Impact:** Rare collision on `save()`; no retry loop.

---

## REF-004 | P3 — No API surface in root urls for referral-only endpoints

**Note:** Referral logic only in OTP flow, not standalone CRUD — by design unless frontend needs listing.
