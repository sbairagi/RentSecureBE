# Bugs — `rentsecure_be` (project services)

Razorpay, Cashfree, payout utilities — not a Django app but payment integration layer.

---

## RSBE-001 | P0 — Payment link missing `reference_id`

**File:** `rentsecure_be/services/razorpay_service.py`

- No `reference_id` in `payment_link.create` payload.
- Webhook in `core/views.py` expects it for `payment_link.paid`.

**Impact:** Payment success does not link to `RentRecord`.

---

## RSBE-002 | P0 — Hardcoded callback URL

**File:** `rentsecure_be/services/razorpay_service.py:25`

```python
"callback_url": "https://yourdomain.com/api/rent/payment-callback/",
"callback_method": "get"
```

**Impact:** Wrong environment; Razorpay may use GET callback while webhook is POST.

---

## RSBE-003 | P1 — `pay_owner_after_rent` wrong attributes

**File:** `rentsecure_be/services/cashfree_service.py`

| Line | Bug |
|------|-----|
| 37 | `rent.owner.beneficiary_id` — beneficiary on `OwnerBankDetails`, not `User` |
| 44 | `rent.property.id` — use `rent.unit_id` |
| 69 | `rent = rent.save()` — `save()` returns `None` |
| 72-73 | `rent.renter.property.owner`, `owner.profile` — invalid paths |

---

## RSBE-004 | P1 — `process_rent_payout` wrong owner lookup

**File:** `rentsecure_be/services/cashfree_service.py:105`

```python
OwnerBankDetails.objects.get(owner=rent.renter.property.owner)
```

**Fix:** `owner=rent.owner` (or `rent.unit.owner`).

---

## RSBE-005 | P1 — `register_owner_with_cashfree` uses `phone_number`

**File:** `rentsecure_be/services/cashfree_service.py:21`

- `User` model field is `phone`, not `phone_number`.

---

## RSBE-006 | P2 — `register_cashfree_beneficiary` uses `profile.phone_number`

**File:** `rentsecure_be/services/cashfree_service.py:87`

- `UserProfile` has `whatsapp_number`; related name is `userprofile`.

---

## RSBE-007 | P3 — Imports at bottom of `cashfree_service.py`

**File:** `rentsecure_be/services/cashfree_service.py:137-140`

- `import requests` after function definitions; circular import risk with `delete_beneficiary`.

---

## RSBE-008 | P2 — `delete_beneficiary` circular import

**File:** `rentsecure_be/services/cashfree_service.py:145`

```python
from .cashfree_service import get_auth_token
```

**Impact:** ImportError if that function is called.
