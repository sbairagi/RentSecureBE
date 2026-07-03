# Bugs — `ai_assistant` app

AI services and views (not always registered as Django app).

---

## AI-001 | P1 — App may not be in `INSTALLED_APPS`

**File:** `rentsecure_be/settings.py`

- `properties/signals` imports `ai_assistant.services.archive_service` and `invoice_service`.
- If app not installed, imports may still work as plain modules but migrations/admin won't run.

**Verify:** `INSTALLED_APPS` includes `ai_assistant`.

---

## AI-002 | P2 — Signal imports create hard dependency

**File:** `properties/signals/__init__.py`

```python
from ai_assistant.services.archive_service import archive_renter_data
from ai_assistant.services.invoice_service import generate_final_invoice_pdf
```

**Impact:** Any signal import loads ai_assistant; failures block signal module.

---

## AI-003 | P2 — `ai_assistant/views.py` may use legacy field names

**Note:** Views reference `payment_status="UNPAID"` / `PAID` — align with `RentRecord.PaymentStatus` (`PENDING` not `UNPAID`).

**Impact:** Empty analytics if filters never match.

---

## AI-004 | P3 — Not mounted in root URLconf

**Check:** `ai_assistant/urls.py` included in `rentsecure_be/urls.py`.

**Impact:** HTTP APIs for AI features unavailable.
