# Bugs — Project config & dependencies

Settings, URLs, requirements — cross-cutting.

---

## CFG-001 | P1 — `python-decouple==3.9` in requirements

**File:** `requirements.txt`

- PyPI max version is **3.8**.

**Impact:** `pip install -r requirements.txt` fails on clean machines.

---

## CFG-002 | P2 — `dashboard` URLs mounted but app not in `INSTALLED_APPS`

**Files:** `rentsecure_be/urls.py`, `rentsecure_be/settings.py`

**Impact:** Views may work without app registry; no models/migrations for dashboard.

---

## CFG-003 | P1 — `ai_assistant` not in `INSTALLED_APPS`

- `properties/signals` imports `ai_assistant.services.*` but app is **not** registered.
- `dashboard` has URLs but is **not** in `INSTALLED_APPS`.

**Action:** Add apps or remove imports/routes.

---

## CFG-004 | P2 — Settings header says Django 5.2; requirements pin 4.2.30

**Files:** `rentsecure_be/settings.py` comment vs `requirements.txt`

**Impact:** Doc/onboarding confusion only if versions actually match installed package.

---

## CFG-005 | P3 — pytest coverage gate 90% with ~32% actual

**File:** `pytest.ini` — `--cov` with fail-under

**Impact:** CI/local `pytest` exits failure even when tests pass.

---

## CFG-006 | P2 — `referral_and_earn` in `INSTALLED_APPS` but minimal URL exposure

**Note:** Only used inside `core` OTP — OK if intentional.

---

## CFG-007 | P0 — Payment webhooks `@csrf_exempt` without alternate auth (active Razorpay handler)

**File:** `core/views.py`

- Exempt is required for webhooks but must pair with signature verification (see CORE-001).
