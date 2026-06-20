# RentSecureBE – Dependency Risk Matrix (Phase 4)

**Status:** ANALYSIS ONLY – No changes applied
**Date:** 2026-05-06

---

## Risk Scoring Methodology

Each package is scored on 5 dimensions (1–5 scale; higher = more risk):

| Dimension | 1 (low risk) | 5 (high risk) |
|---|---|---|
| **S** – Security | Well-maintained, no known CVE | Abandoned, has CVE, or unmaintained |
| **O** – Operational (outage) | Backed by major org, used at scale | Single-maintainer, unmaintained |
| **L** – License | MIT/BSD/Apache | GPL/AGPL/unknown |
| **M** – Maintenance Burden (install size + transitive weight) | <1MB, no native deps | >50MB, many native deps |
| **C** – Compatibility (Python + Django + future) | Compatible with all targets | Major version risk |

**Composite Risk** = max(S, O, L, M, C)

---

## Risk Matrix (49 Packages × 5 Dimensions)

### Production Top-Level (24 packages)

| # | Package | S | O | L | M | C | Composite | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | Django 4.2.30 | 2 | 1 | 1 | 4 | 4 | **4** | LTS ends Apr 2026; plan 5.0/5.2 upgrade |
| 2 | djangorestframework 3.16.0 | 1 | 1 | 1 | 2 | 1 | 2 | Current |
| 3 | djangorestframework_simplejwt 5.5.0 | 1 | 2 | 1 | 1 | 1 | 2 | Current |
| 4 | django-simple-history 3.8.0 | 2 | 3 | 1 | 1 | 1 | 3 | Smaller maintainer team |
| 5 | asgiref 3.8.1 | 1 | 1 | 1 | 1 | 1 | 1 | Django team |
| 6 | python-decouple 3.5 | 1 | 2 | 1 | 1 | 2 | 2 | v3.8 is latest |
| 7 | python-dateutil 2.9.0.post0 | 1 | 1 | 1 | 1 | 1 | 1 | Current |
| 8 | requests 2.32.3 | 1 | 1 | 1 | 1 | 1 | 1 | Current |
| 9 | weasyprint 66.0 | 2 | 2 | 1 | 5 | 1 | **5** | Native deps (cairo, pango, gdk-pixbuf); can fail in Docker build |
| 10 | **PyPDF2 3.0.1** | 3 | 4 | 1 | 1 | 3 | **4** | Project is in low maintenance; `pypdf` is the modern successor; plan migration in 12 months |
| 11 | **Pillow 11.2.1** | 2 | 1 | 1 | 3 | 1 | 3 | Frequent CVEs; pin explicitly |
| 12 | openpyxl 3.1.5 | 1 | 1 | 1 | 2 | 1 | 2 | Current |
| 13 | xlsxwriter 3.2.9 | 1 | 1 | 1 | 1 | 1 | 1 | Current |
| 14 | twilio 9.6.1 | 1 | 1 | 1 | 2 | 1 | 2 | Current |
| 15 | gTTS 2.5.4 | 2 | 3 | 1 | 1 | 1 | 3 | Hits Google Translate (no official API) |
| 16 | razorpay 1.4.2 | 3 | 3 | 1 | 1 | 3 | **3** | 4-year-old SDK; upgrade |
| 17 | **boto3 1.18.53** | 4 | 1 | 1 | 3 | 3 | **4** | **3+ years stale; URGENT upgrade to 1.35+** |
| 18 | fcm-django 2.2.1 | 2 | 3 | 1 | 1 | 1 | 3 | Smaller community |
| 19 | firebase-admin 6.8.0 | 1 | 1 | 1 | 4 | 1 | **4** | ~50MB; large dep tree |
| 20 | deep-translator 1.11.4 | 3 | 3 | 1 | 2 | 2 | 3 | Wraps many free APIs |
| 21 | **psycopg2-binary 2.9.10** | 1 | 1 | 1 | 2 | 1 | 2 | Current |
| 22 | **openai 1.0+** | 1 | 1 | 1 | 2 | 1 | 2 | Current (MISSING from requirements.txt) |
| 23 | **drf-writable-nested 0.7.0** | 3 | 4 | 1 | 1 | 2 | **4** | Single-maintainer; consider replacement with custom `create()` if abandoned |
| 24 | **Pillow 11.2.1 (explicit)** | – | – | – | – | – | 3 | (covered above) |

### Roadmap-Only (6 packages)

| # | Package | S | O | L | M | C | Composite | Notes |
|---|---|---|---|---|---|---|---|---|
| 25 | celery 5.6.3 | 1 | 1 | 1 | 4 | 1 | **4** | Heavy dep tree; but battle-tested |
| 26 | django-celery-beat 2.9.0 | 2 | 3 | 1 | 1 | 1 | 3 | Active maintainers |
| 27 | django-cors-headers 3.9.0 | 1 | 1 | 1 | 1 | 2 | 2 | **Upgrade 3.9 → 4.4 latest** |
| 28 | whitenoise 5.3.0 | 1 | 1 | 1 | 1 | 2 | 2 | **Upgrade 5.3 → 6.x latest** |
| 29 | django-storages 1.11.1 | 1 | 1 | 1 | 1 | 2 | 2 | **Upgrade 1.11 → 1.14.x** |
| 30 | dj-database-url 2.3.0 | 1 | 2 | 1 | 1 | 1 | 1 | Current |

### Development / Test (13 packages)

| # | Package | S | O | L | M | C | Composite | Notes |
|---|---|---|---|---|---|---|---|---|
| 31 | pytest 8.3.5 | 1 | 1 | 1 | 1 | 1 | 1 | Current |
| 32 | pytest-django 4.11.1 | 1 | 1 | 1 | 1 | 1 | 1 | Current |
| 33 | coverage | 1 | 1 | 1 | 1 | 1 | 1 | Current |
| 34 | mypy | 1 | 1 | 1 | 2 | 1 | 2 | Current |
| 35 | django-stubs | 2 | 2 | 1 | 1 | 1 | 2 | Active |
| 36 | djangorestframework-stubs | 2 | 2 | 1 | 1 | 1 | 2 | Active |
| 37 | black | 1 | 1 | 1 | 1 | 2 | 2 | Ruff replaces it; can remove |
| 38 | ruff | 1 | 1 | 1 | 1 | 1 | 1 | Current |
| 39 | pylint | 1 | 1 | 1 | 1 | 2 | 2 | Slow; can drop if Ruff+mypy is enough |
| 40 | pylint-django | 2 | 3 | 1 | 1 | 2 | 3 | Smaller community |
| 41 | bandit | 1 | 1 | 1 | 1 | 1 | 1 | Current |
| 42 | semgrep | 1 | 1 | 1 | 2 | 1 | 2 | Current |
| 43 | pip-audit | 1 | 1 | 1 | 1 | 1 | 1 | Current |

### REMOVE (19 packages) – Risk of Keeping

| # | Package | Risk if Kept | Action |
|---|---|---|---|
| 1 | **Flask** | LOW (3MB, no CVE) but signals sloppy lockfile | REMOVE |
| 2 | **fpdf** | LOW but unused; bloats lockfile | REMOVE |
| 3 | **fpdf2** | LOW but unused; bloats lockfile | REMOVE |
| 4 | **selenium** | MEDIUM (heavy, 50MB+ with browsers); security footprint | REMOVE |
| 5 | **SQLAlchemy** | LOW but unused; ~5MB | REMOVE |
| 6 | **pandas** | **MEDIUM** (~50MB; common CVE source) | REMOVE |
| 7 | **PyMySQL** | LOW but unused | REMOVE |
| 8 | **instagram-private-api** | **HIGH (security)** – unofficial reverse-engineered client | REMOVE **IMMEDIATELY** |
| 9 | **instaloader** | LOW but unused; ~5MB | REMOVE |
| 10 | **django-crum** | LOW but unused | REMOVE |
| 11 | **django-multiselectfield** | LOW but unused | REMOVE |
| 12 | **django-otp** | LOW but unused | REMOVE |
| 13 | **django-rest-auth** | **MEDIUM (security)** – deprecated 2019 | REMOVE |
| 14 | **django-s3-storage** | LOW but unused; duplicate of django-storages | REMOVE |
| 15 | **django-select2** | LOW but unused | REMOVE |
| 16 | **django-widget-tweaks** | LOW but unused | REMOVE |
| 17 | **google-api-python-client** | LOW but unused; ~20MB dep tree | REMOVE |
| 18 | **google-cloud-core** | LOW but unused | REMOVE |
| 19 | **arrow** | LOW but unused; dateutil is used | REMOVE |

---

## Composite Risk Distribution

| Composite Risk | Count | % |
|---|---|---|
| 1 (very low) | 6 | 14% |
| 2 (low) | 13 | 30% |
| 3 (medium) | 12 | 28% |
| 4 (medium-high) | 7 | 16% |
| 5 (high) | 1 (weasyprint) | 2% |
| **REMOVE** | 19 (separate category) | (n/a) |

---

## Top 5 Risk Items (Post-Cleanup)

1. **`weasyprint` (Score 5)** – Native deps (cairo, pango, gdk-pixbuf); Docker build can fail. Mitigation: use `taiga/weasyprint` Docker image or install system deps explicitly.
2. **`boto3 1.18.53` (Score 4)** – 3+ years stale. **URGENT upgrade to 1.35.x** in Phase 2C.
3. **`PyPDF2` (Score 4)** – Project in low maintenance; `pypdf` is the modern successor. Plan migration in 12 months.
4. **`firebase-admin` (Score 4)** – ~50MB dep tree (grpc, etc.). Cannot reduce; required by fcm-django.
5. **`celery` (Score 4)** – Heavy dep tree (kombu, billiard, amqp, etc.) but battle-tested and roadmap-required.
