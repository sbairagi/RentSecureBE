# Bugs — `management/commands`

Scheduled / batch jobs at repo root `management/commands/`.

---

## CMD-001 | P1 — `generate_monthly_rent_records` broken imports and fields

**File:** `management/commands/generate_monthly_rent_records.py`

```python
from rent.models import Renter, RentRecord
...
RentRecord.objects.filter(renter=renter, month=month, year=year)
RentRecord.objects.create(..., amount=..., month=..., year=..., payment_status="UNPAID")
```

**Issues:**

- Module `rent.models` does not exist (should be `properties.models`).
- `RentRecord` uses `rent_month`, `amount_paid`, `payment_status=PENDING` — not `month`/`year`/`UNPAID`.

**Impact:** Command crashes if run.

---

## CMD-002 | P1 — `daily_rent_reminder` broken imports

**File:** `management/commands/daily_rent_reminder.py`

```python
from rent.models import Renter
from services.rent_reminder_service import send_rent_reminder
```

**Impact:** `ModuleNotFoundError`.

---

## CMD-003 | P2 — `seed_subscription_plans` fully commented

**File:** `management/commands/seed_subscription_plans.py`

**Impact:** Fresh DB has no plans/limits → all creates 403.

---

## CMD-004 | P2 — `downgrade_expired_users` fully commented

**File:** `management/commands/downgrade_expired_users.py`

**Impact:** Expired users keep excess data forever.

---

## CMD-005 | P2 — `archive_expired_users_data` (verify)

**File:** `management/commands/archive_expired_users_data.py`

- Likely commented or stale imports — verify before production cron.

---

## CMD-006 | P3 — Duplicate command filenames

**Examples:** `notification/management/__init__ 2.py` (space in name) in git status.

**Impact:** Confusion; may not be discoverable by Django.

---

## CMD-007 | P2 — Properties app commands

**Path:** `properties/management/commands/generate_monthly_extra_charges.py`

- Verify imports and model fields separately before scheduling.
