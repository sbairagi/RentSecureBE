# Bugs — `properties` app

Buildings, units, renters, rent records, feature limits, signals.

---

## PROP-001 | P1 — `get_free_plan_limit` does not exist on `FeatureEnforcer`

**Files:** `properties/views/building_views.py:27`, `properties/views/unit_views.py:38`

```python
free_limit = enforcer.get_free_plan_limit('max_buildings')
```

**Class only has:** `_get_free_plan_limit` (private).

**Impact:** `AttributeError` when listing buildings/units after subscription grace period.

---

## PROP-002 | P1 — Django signals defined but not registered

**File:** `properties/apps.py` — does not import `properties.signals`.

**Impact:** All receivers in `properties/signals/__init__.py` never run (receipts, voice notes, usage sync, vacancy alerts, archive).

**Fix:** `import properties.signals` in `AppConfig.ready()`.

---

## PROP-003 | P1 — Defaulter helper uses wrong fields

**File:** `properties/signals/__init__.py` — `update_renter_defaulter_status`

- `rent.status == "UNPAID"` — model uses `payment_status` (`PENDING`/`PAID`/`FAILED`).
- `renter.active_agreement = None` — field does not exist on `Renter`.

**Impact:** Defaulter logic never works when signals are enabled.

---

## PROP-004 | P1 — Vacancy WhatsApp uses `unit.unit_number`

**File:** `properties/signals/__init__.py:106`

- `Unit` field is `unit`, not `unit_number`.

**Impact:** `AttributeError` when renter deactivated and signal runs.

---

## PROP-005 | P1 — Vacancy signal uses `owner.profile`

**File:** `properties/signals/__init__.py:105`

- Should be `owner.userprofile` (or `NotificationPreference` / `whatsapp_number` on `User`).

---

## PROP-006 | P1 — Building usage signal typo `max_buldings`

**File:** `properties/signals/__init__.py:28`

**Impact:** Wrong `UsageLimit` key if signals are wired.

---

## PROP-007 | P2 — Feature key mismatch in ViewSets vs plan DB

**Files:** `properties/views/unit_views.py`

| ViewSet uses | Plan docs often use |
|--------------|---------------------|
| `unit_images` | `max_unit_images` |
| `unit_documents` | `max_document_uploads` |

Combined with enforcer returning `unlimited` when limit row missing → uploads uncapped.

---

## PROP-008 | P1 — `FeatureEnforcer._get_plan_limit` missing row → `unlimited`

**File:** `properties/feature_enforcer.py:47-48`

**Impact:** Misconfigured plans grant unlimited features.

---

## PROP-009 | P2 — `is_expired()` compares `date` to `datetime`

**File:** `properties/feature_enforcer.py:22`

```python
return sub.end_date and sub.end_date < timezone.now()
```

**Impact:** Grace/expiry edge cases wrong.

---

## PROP-010 | P1 — Renter APIs: `renter.property.name`

**File:** `properties/views/rent_record_views.py` — `get_latest_due_rent`, `owner_rent_overview`

- `Renter.property` → `Unit`; no `.name` attribute.

**Impact:** HTTP 500 on common endpoints.

---

## PROP-011 | P2 — No validation: multiple active renters per unit

**Model/API:** `Renter` — only `unique_together (unit, phone)`.

**Impact:** Two active tenants on one unit; unclear rent responsibility.

---

## PROP-012 | P2 — Renter `is_active` vs `status` not enforced

**Tests:** `test_loopholes_critical.py::RenterStatusLoopholes`

**Impact:** Deactivated renters can remain `is_active=True`; list filters `status` only.

---

## PROP-013 | P2 — Archived units allow active renters / new caretakers

**Tests:** `UnitArchivingLoopholes`

**Impact:** Data inconsistent with “archived” semantics.

---

## PROP-014 | P2 — `RentRecordViewSet` swallows Razorpay errors

**File:** `properties/views/rent_record_views.py` — bare `except Exception: pass` on payment link creation.

**Impact:** Rent record created with no payment link; owner not informed.

---

## PROP-015 | P2 — `rent_records` limit key not in `FEATURE_CHOICES`

**File:** `core/models.py` vs `rent_record_views.py`

**Impact:** Admin/plan config easy to misconfigure.

---

## PROP-016 | P3 — Cached queryset stores model instances

**Files:** various ViewSets

**Impact:** Stale in-memory objects across requests in some cache backends (usually queryset re-evaluated on filter; still risky pattern).

---

## PROP-017 | P2 — `generate_final_invoice_on_exit` saves renter in signal

**File:** `properties/signals/__init__.py:117`

**Impact:** Possible infinite `post_save` recursion if not careful (update_fields mitigates partially).
