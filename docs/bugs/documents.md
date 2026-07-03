# Bugs — `documents` app

PDF generation for receipts, agreements, dossiers.

---

## DOC-001 | P3 — Nested URL path

**File:** `documents/urls.py` + `rentsecure_be/urls.py`

- Mounted at `/documents/` with inner `document/` prefix → e.g. `/documents/document/rent_receipt/`.

**Impact:** Clients must use full path; easy to misconfigure.

**Note:** `documents` **is** in `INSTALLED_APPS`.

---

## DOC-002 | P2 — Depends on correct property/renter data

**Files:** `documents/views.py` (ViewSets)

- PDF content likely reads `properties` models; inherits PROP-010/011 data issues.

---

## DOC-003 | P3 — No subscription gate verified in views

**Business rule:** `export_pdf_dossier` plan feature.

**Impact:** May generate dossiers without plan check if not in ViewSet.

**Action:** Confirm `FeatureEnforcer` in document ViewSets.

---

## DOC-004 | P3 — URL prefix nested `document/document/`

**File:** `documents/urls.py` — router under `path('document/', include(router.urls))`.

**Impact:** Double path segment; client must use correct URL (documentation issue).
