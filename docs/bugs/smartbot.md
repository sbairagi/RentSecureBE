# Bugs — `smartbot` app

GPT assistant and intent actions.

---

## BOT-001 | P2 — Large blocks of commented dead code

**File:** `smartbot/views.py` (top ~55 lines)

**Impact:** Confusing maintenance; old `rent.models` references in comments.

---

## BOT-002 | P2 — Intent actions inherit same payout/property bugs

**Files:** `smartbot/actions.py` (retry payout, send agreement)

- Actions call property/rent services that contain RSBE-003/004 bugs.

**Impact:** SmartBot-triggered payout retry may fail same as REST API.

---

## BOT-003 | P3 — Keyword-only intents

**File:** `smartbot/intents.py`

- Fragile matching (`"reminder" in query and "rent" in query`).

**Impact:** False positives/negatives; not a crash bug.

---

## BOT-004 | P1 — `smartbot` not included in root URLconf

**Files:** `rentsecure_be/urls.py`, `smartbot/urls.py`

- App is in `INSTALLED_APPS` but **no** `path(..., include("smartbot.urls"))` in root urls.

**Impact:** `smart_bot_reply` HTTP API unreachable.

---

## BOT-005 | P2 — Context queries use month/year on `RentRecord`

**File:** `smartbot/views.py`

- Uses `payment_status` and date filters; ensure field names match model (`rent_month` vs `month` property).

**Impact:** Wrong answers if queryset filters use nonexistent DB fields.
