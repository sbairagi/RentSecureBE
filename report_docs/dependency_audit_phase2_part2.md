# RentSecureBE – Dependency Hygiene Audit (Phase 2) – Part 2

**Status:** ANALYSIS ONLY – No changes applied

This document extends `dependency_audit_phase2.md` with the remaining content:
sections 3.1 (summary), 4 (Possibly Unused evidence), 5 (Security), 6 (Migration Plan), 7 (Proposed splits).

---

## 3.1 Classification Summary

| Category | Count | % of 217 |
|---|---|---|
| Production (P) | 16 | 7.4% |
| Development (D) | 2 | 0.9% |
| Transitive (T) | 158 | 72.8% |
| Possibly Unused (U) | 33 | 15.2% |
| Unknown (?) | 2 | 0.9% |
| Risky (subset of U) | 1 | 0.5% |

**Production top-level packages (the only ones that should appear in `requirements.txt`):**

1. `Django==4.2.30`
2. `djangorestframework==3.16.0`
3. `djangorestframework_simplejwt==5.5.0`
4. `django-simple-history==3.8.0`
5. `django-celery-beat==2.9.0`
6. `asgiref==3.8.1`
7. `python-decouple==3.5`
8. `python-dateutil==2.9.0.post0`
9. `requests==2.32.3`
10. `weasyprint==66.0`
11. `twilio==9.6.1`
12. `razorpay==1.4.2` (needs upgrade)
13. `boto3==1.18.53` (needs upgrade)
14. `fcm-django==2.2.1`
15. `firebase-admin==6.8.0` (transitive of fcm-django, but pin explicitly)
16. `openpyxl==3.1.5`
17. `xlsxwriter==3.2.9`
18. `gTTS==2.5.4`
19. `deep-translator==1.11.4`
20. `celery==5.6.3` (only if celery app is properly defined; otherwise remove)
21. `PyPDF2` (re-add – used in `documents/utils.py: from PyPDF2 import PdfMerger`)
22. `Pillow` (re-add – weasyprint heavy user; verify if explicit dependency needed)

> **Note:** `PyPDF2` is imported in `documents/utils.py` but is not in the current top-217 list. This indicates it was likely pulled transitively and pinned as a "top-level" by mistake; it should be added back as an explicit top-level dependency. `Pillow` is similarly not in the top-217 list but is a known runtime dep of weasyprint.

---

## 4. Possibly Unused Packages – Detailed Evidence

### 4.1 High-Confidence Unused (Confidence ≥ 90%)

| Package | Confidence | Files Searched | Found? | Reason | Recommendation |
|---|---|---|---|---|---|
| **Flask==3.1.1** | 99% | All *.py | NO | Zero imports; framework overlap with Django | **Remove** |
| **fpdf==1.7.2** | 95% | All *.py | NO | Project uses weasyprint | **Remove** |
| **fpdf2==2.8.3** | 95% | All *.py | NO | Project uses weasyprint | **Remove** |
| **selenium==4.29.0** | 99% | All *.py | NO | No browser automation in code | **Remove** |
| **SQLAlchemy==2.0.41** | 99% | All *.py | NO | Django ORM only | **Remove** (duplicate functionality) |
| **instagram-private-api==1.6.0.0** | 99% | All *.py | NO | **UNOFFICIAL reverse-engineered client** | **Remove immediately** (security + license risk) |
| **instaloader==4.14.1** | 99% | All *.py | NO | Zero imports | **Remove** |
| **pandas==2.2.2** | 90% | All *.py | NO | openpyxl/xlsxwriter don't require pandas | **Remove** |
| **PyMySQL==1.0.2** | 95% | All *.py | NO | DB is PostgreSQL (prod) / SQLite (dev) | **Remove** |
| **django-rest-auth==0.9.5** | 99% | All *.py | NO | Deprecated 2019; replaced by simplejwt | **Remove** |
| **django-cors-headers==3.9.0** | 95% | All *.py + settings | NO | Not in INSTALLED_APPS, not in MIDDLEWARE | **Remove** or wire it up |
| **django-crum==0.7.9** | 99% | All *.py | NO | No CRUM middleware used | **Remove** |
| **django-multiselectfield==0.1.12** | 99% | All *.py | NO | No MultiSelectField in models | **Remove** |
| **django-otp==1.6.0** | 99% | All *.py | NO | Custom OTP model in `core.models` | **Remove** |
| **django-s3-storage==0.13.4** | 99% | All *.py + settings | NO | Uses django-storages instead | **Remove** (duplicate) |
| **django-select2==8.2.3** | 99% | All *.py + settings | NO | Only for admin UI, not wired | **Remove** |
| **django-widget-tweaks==1.4.8** | 99% | All *.py | NO | Template-only and not referenced | **Remove** |
| **drf-writable-nested==0.7.0** | 99% | All *.py | NO | Zero usages | **Remove** |
| **dj-database-url==2.3.0** | 90% | All *.py + settings | NO | Settings uses `decouple.config` directly | **Remove** (or migrate) |
| **google-api-python-client==2.170.0** | 99% | All *.py | NO | firebase-admin provides what is needed | **Remove** |
| **google-cloud-core==2.4.3** | 99% | All *.py | NO | Not used | **Remove** |
| **google-cloud-firestore==2.20.2** | 99% | All *.py | NO | Not used | **Remove** |
| **google-cloud-storage==3.1.0** | 99% | All *.py | NO | Not used | **Remove** |

### 4.2 Medium-Confidence Unused (Confidence 50–80%)

| Package | Confidence | Reason | Recommendation |
|---|---|---|---|
| **whitenoise==5.3.0** | 70% | Not in MIDDLEWARE; static files served via Django runserver only. May be needed in production | **Wire it up in settings.py** or remove. Decision required. |
| **django-storages==1.11.1** | 50% | Not in INSTALLED_APPS. Possibly a leftover from S3 experimentation. | **Confirm with team** – remove if S3 not planned |
| **celery==5.6.3** | 60% | No `from celery` imports; no `celery.py`. `django_celery_beat` is in INSTALLED_APPS. | **Architectural decision required** – either define celery app or remove all celery packages |
| **arrow==1.3.0** | 60% | 0 direct imports; could be celery-scheduler transitive | Confirm with `pip show arrow` if it survives removal of celery |

### 4.3 Low-Confidence / Likely Transitive (Confidence < 50%)

These are mostly Jup
