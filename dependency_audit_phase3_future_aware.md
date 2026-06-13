# RentSecureBE – Phase 3 Dependency Audit (Future-Aware Analysis)

**Status:** ANALYSIS ONLY – No changes applied
**Date:** 2026-05-06
**Auditor:** Principal Staff Engineer / Dependency Governance Reviewer
**Input:** Future RentSecure roadmap (multi-tenant SaaS, mobile app, WhatsApp, push, voice, PDFs, S3, PostgreSQL, payments, subscriptions, AI assistant, Celery workers, audit logs, NRI/HNI support, etc.)

---

## 1. Methodology – Roadmap-Aware Evaluation

For every package called out in the validation pass (and the broader "Possibly Unused" set), we evaluated **BOTH**:

1. **Current usage** – verified imports, INSTALLED_APPS, MIDDLEWARE, settings, templates (from Phase 1/2/Validation)
2. **Future roadmap alignment** – explicit value to the planned 12-month feature set

Classification buckets:

- **A. KEEP NOW** – actively used by production code today
- **B. KEEP FOR ROADMAP** – not currently used but high-likelihood required within 12 months based on the explicit roadmap
- **C. REMOVE** – no current use AND no realistic roadmap value

For every package: name, current usage evidence, future roadmap justification, risk if removed, recommendation.

---

## 2. Roadmap Mapping (How each roadmap item maps to packages)

| Roadmap Item | Packages It Requires |
|---|---|
| Multi-tenant Property Management SaaS | Django, DRF, simplejwt, `django-cors-headers`, `whitenoise` |
| React Native Mobile App | `django-cors-headers` (CORS for mobile clients hitting API) |
| Angular/Web Admin Panel | `django-cors-headers` (CORS), `whitenoise` (static admin) |
| WhatsApp Notifications | twilio, requests, `boto3` (optional media S3) |
| Push Notifications (FCM) | `fcm-django`, `firebase-admin` |
| Voice Notes (gTTS / ElevenLabs) | gTTS, twilio |
| Digital Rent Agreements | weasyprint, PyPDF2, twilio, Leegality (out-of-scope) |
| PDF Generation & PDF Merging | weasyprint, PyPDF2 |
| Property History Reports | weasyprint, PyPDF2, `django-simple-history` |
| AWS Deployment | boto3, `whitenoise`, gunicorn (out-of-scope) |
| S3 Media Storage | boto3, `django-storages` |
| PostgreSQL Production Database | `psycopg2-binary` |
| Payment Gateway Integration | razorpay, requests |
| Subscription Plans | Django ORM (no extra pkg), `celery` (for renewals) |
| Add-On Purchases | Django ORM, `celery` |
| Analytics Dashboard | `django-cors-headers`, Django ORM |
| AI Assistant | openai, `deep-translator`, requests |
| Future Microservice Migration | All current packages (no extra pkg; possibly `grpcio` for gRPC) |
| Background Jobs / Scheduled Tasks | `celery`, `django-celery-beat` |
| Scheduled Notifications / Rent / Tax Reminders | `celery`, `django-celery-beat`, twilio, `fcm-django` |
| Queue Processing | `celery` (kombu) or Redis client |
| Celery Workers / Beat | `celery`, `django-celery-beat`, kombu (transitive) |
| Async Processing | `celery` (or `asgiref` for async views) |
| Audit Logs | `django-simple-history` |
| Owner / Caretaker / Renter Management | Django ORM, DRF |
| Image Uploads | `Pillow` (mandatory for `ImageField`) |
| Document Uploads | Django `FileField`, `Pillow` (for thumbnails), `django-storages` (for S3) |
| Future NRI/HNI Support | No new package; may add `python-dateutil`, `babel` later |

---

## 3. A. KEEP NOW (Currently Required)

These 21 packages are confirmed production-critical today. No removal.

| # | Package | Current Evidence | Roadmap Alignment |
|---|---|---|---|
| 1 | `Django==4.2.30` | Framework | All roadmap items |
| 2 | `djangorestframework==3.16.0` | 20+ import sites | API for mobile + web |
| 3 | `djangorestframework_simplejwt==5.5.0` | `core/urls.py`, `core/views.py`, settings | Mobile + web auth |
| 4 | `django-simple-history==3.8.0` | Many imports, INSTALLED_APPS, MIDDLEWARE | Audit logs (roadmap) |
| 5 | `asgiref==3.8.1` | Django internal | Async roadmap |
| 6 | `python-decouple==3.5` | `settings.py` | All env config |
| 7 | `python-dateutil==2.9.0.post0` | 2 imports | Date math; NRI timezone support later |
| 8 | `requests==2.32.3` | 5 import sites | Cashfree, Leegality, Twilio (HTTP) |
| 9 | `weasyprint==66.0` | 9 import sites | PDF roadmap |
| 10 | `PyPDF2==3.0.0` | `documents/utils.py: from PyPDF2 import PdfMerger` | PDF Merging roadmap |
| 11 | `Pillow==11.2.1` | `ImageField` in 3 models (`caretaker_image`, `renter_image`, `unit_image`) | Image uploads roadmap |
| 12 | `openpyxl==3.1.5` | `finance/utils.py` | Tax reports, exports |
| 13 | `xlsxwriter==3.2.9` | `core/utils/export_utils.py` | Export dashboard, reports |
| 14 | `twilio==9.6.1` | 4 import sites | WhatsApp + SMS + Voice |
| 15 | `gTTS==2.5.4` | 1 import | Voice notes |
| 16 | `razorpay==1.4.2` | `core/views.py`, `rentsecure_be/services/razorpay_service.py` | Payment gateway |
| 17 | `boto3==1.18.53` | `notification/services/whatsapp_service.py: import boto3` (lazy) | **AWS deployment + S3 roadmap** |
| 18 | `fcm-django==2.2.1` | 2 import sites, INSTALLED_APPS | **Push notifications roadmap** |
| 19 | `firebase-admin==6.8.0` | Backend for fcm-django | **Push notifications roadmap** |
| 20 | `deep-translator==1.11.4` | `ai_assistant/services/i18n_service.py` | **AI assistant + i18n roadmap** |
| 21 | `psycopg2-binary` (NOT yet in requirements.txt) | CI installs separately; production will use PostgreSQL | **PostgreSQL production roadmap** |

---

## 4. B. KEEP FOR ROADMAP (Not used today, but high future value)

These 9 packages are NOT currently used, but the **explicit roadmap requires them within 12 months**. **Keep them.**

| # | Package | Current Usage | Future Roadmap Justification | Risk if Removed | Recommendation |
|---|---|---|---|---|---|
| 1 | **`celery==5.6.3`** | 0 imports, no `celery.py` (infrastructure inert) | **CRITICAL** – Roadmap explicitly lists: Background Jobs, Scheduled Notifications/Rent/Tax Reminders, Queue Processing, Celery Workers, Celery Beat, Async Processing. These cannot be built without celery. | High – blocks the entire "Background Jobs" roadmap; team would have to re-add it within months. | **KEEP** but FIX the architecture (create `rentsecure_be/celery.py`, add Celery worker + beat processes in deploy.yml, convert management commands to `@shared_task`). |
| 2 | **`django-celery-beat==2.9.0`** | Imported in `properties/scheduler.py` (read-only); in INSTALLED_APPS | **CRITICAL** – Required for "Scheduled Notifications" + "Celery Beat" roadmap. PeriodicTask model is the foundation for cron-like job definitions. | High – blocks scheduled jobs. | **KEEP** and convert to full Celery use. |
| 3 | **`django-cors-headers==3.9.0`** | Not wired (not in INSTALLED_APPS, not in MIDDLEWARE) | **CRITICAL** – Roadmap lists: React Native Mobile App + Angular Web Admin Panel. Both will be cross-origin clients; CORS middleware is mandatory for browser-based Angular and required for many mobile deployment scenarios. | High – production mobile/web clients will fail CORS preflight. | **KEEP** and wire up in `INSTALLED_APPS` + `MIDDLEWARE` immediately. |
| 4 | **`whitenoise==5.3.0`** | Not wired | **HIGH** – Roadmap: Angular Web Admin Panel, AWS Deployment, Multi-tenant SaaS. Whitenoise is the lightest-weight WSGI static-files solution for Django; avoids the need for S3/CloudFront for admin static files. Reduces operational complexity for EC2 deployment. | Medium – would need to set up nginx/ALB/CloudFront instead (higher DevOps cost). | **KEEP** and add to MIDDLEWARE. |
| 5 | **`django-storages==1.11.1`** | Not imported | **HIGH** – Roadmap: S3 Media Storage, AWS Deployment, Document Uploads. Project already uses boto3 directly; adding `django-storages` enables `DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"` which integrates with `ImageField`/`FileField` automatically. | Medium – team would re-add it within weeks of implementing S3. | **KEEP**. Configure `DEFAULT_FILE_STORAGE` when S3 is enabled. |
| 6 | **`dj-database-url==2.3.0`** | 0 imports | **MEDIUM** – Roadmap: PostgreSQL Production, Microservice Migration, Multi-tenant SaaS. `dj-database-url` enables `DATABASE_URL=postgres://…` style config (12-factor app), which is critical for AWS ECS / Kubernetes deployments where DB credentials come from secrets. | Low – team would add it when containerizing. | **KEEP**. Replace manual `decouple.config` calls in `settings.py` with `dj-database-url.parse(config("DATABASE_URL"))`. |
| 7 | **`drf-writable-nested==0.7.0`** | 0 imports | **MEDIUM** – Roadmap: Owner/Caretaker/Renter Management (nested serializers), Digital Rent Agreements (clause nesting). Useful for `WritableNestedSerializer` when creating parent + child in one POST (e.g. `Renter + RentAgreementDraft` together). | Low – alternative is custom `create()` method. | **KEEP** – small, useful. Document when to use. |
| 8 | **`google-cloud-firestore==2.20.2`** | 0 imports | **LOW-MEDIUM** – Roadmap mentions "Future Microservice Migration". If a future Node.js or Go microservice writes to Firestore, the Django side may need to read aggregated data. Not needed for current Postgres-only stack. | Low – can be added when actually used. | **REMOVE for now; re-add on demand.** (Not currently used, not committed roadmap.) |
| 9 | **`google-cloud-storage==3.1.0`** | 0 imports | **MEDIUM** – Roadmap: AWS Deployment explicitly chosen. GCS is a competitor to S3. If roadmap later mentions GCS, this is needed. | Low – S3 is the chosen cloud. | **REMOVE for now** unless GCS is added to roadmap. |

---

## 5. C. REMOVE (No current use AND no realistic roadmap value)

These 16 packages have **no current use** and **no clear roadmap value**. Safe to remove.

| # | Package | Why Remove (current + roadmap) | Risk |
|---|---|---|---|
| 1 | **`Flask==3.1.1`** | Django is the framework. No roadmap item mentions Flask. Has 0 imports. | LOW |
| 2 | **`fpdf==1.7.2`** | `fpdf2` is the maintained version. Weasyprint is the actual PDF engine. 0 imports. | LOW |
| 3 | **`fpdf2==2.8.3`** | Weasyprint is the production PDF engine. 0 imports. | LOW |
| 4 | **`selenium==4.29.0`** | No roadmap item mentions browser automation / E2E testing in Python (mobile/web testing uses their own tools). 0 imports. | LOW |
| 5 | **`SQLAlchemy==2.0.41`** | Django ORM only. No "switch ORM" roadmap item. 0 imports. | LOW |
| 6 | **`pandas==2.2.2`** | openpyxl/xlsxwriter handle Excel; no analytics/data-science item in roadmap (analytics dashboard uses Django ORM aggregations). 0 imports. | LOW |
| 7 | **`PyMySQL==1.0.2`** | Roadmap specifies PostgreSQL. 0 imports. | LOW |
| 8 | **`instagram-private-api==1.6.0.0`** | **Unofficial reverse-engineered client**; no roadmap item references Instagram integration. **HIGH SECURITY RISK** (license, malicious code, ToS violation). | LOW (removal); HIGH (if kept) |
| 9 | **`instaloader==4.14.1`** | No roadmap item. Likely aspirational. 0 imports. | LOW |
| 10 | **`django-crum==0.7.9`** | No roadmap item requires request-current-user middleware. Custom `core.utils` and `core.signals` already serve this purpose. 0 imports. | LOW |
| 11 | **`django-multiselectfield==0.1.12`** | No `MultiSelectField` in current models; roadmap doesn't add it (use `JSONField` if needed). 0 imports. | LOW |
| 12 | **`django-otp==1.6.0`** | Project has its own custom `OTP` model in `core.models`. No roadmap item requires TOTP/HOTP. 0 imports. | LOW |
| 13 | **`django-rest-auth==0.9.5`** | **DEPRECATED 2019**; replaced by `rest_framework_simplejwt` (already in use). 0 imports. | LOW |
| 14 | **`django-s3-storage==0.13.4`** | **Duplicate** of `django-storages`. Project uses boto3 directly. 0 imports. | LOW |
| 15 | **`django-select2==8.2.3`** | Mobile + web admin don't need server-side select2 widgets; they use frontend components. 0 imports; not in INSTALLED_APPS. | LOW |
| 16 | **`django-widget-tweaks==1.4.8`** | Templates use Angular/React for forms, not Django template form rendering. 0 imports; not in templates. | LOW |
| 17 | **`google-api-python-client==2.170.0`** | Firebase-admin provides what's used. No roadmap item requires Google Workspace APIs (Gmail, Calendar, Drive). 0 imports. | LOW |
| 18 | **`google-cloud-core==2.4.3`** | Transitive-only, not used. | LOW |
| 19 | **`arrow==1.3.0`** | 0 imports; `python-dateutil` is already used. | LOW |

**Total REMOVE: 19 packages**

---

## 6. Per-Package Cost-Benefit Analysis (Roadmap Packages Only)

| Package | Current Cost (security/maintenance) | Future Value (12 months) | Cost of Keeping | Cost of Removing | Verdict |
|---|---|---|---|---|---|
| `celery` + `django-celery-beat` | LOW (well-maintained, active) | **CRITICAL** (blocks Background Jobs, Scheduled Notifications, Rent Reminders, Tax Reminders, Queue Processing) | ~5MB Docker, 0 maintenance overhead | High – blocks entire async roadmap; team adds back within weeks | **KEEP (architecturally fix it now)** |
| `django-cors-headers` | LOW | **CRITICAL** (mobile + web admin are cross-origin) | Negligible | High – production CORS preflight fails | **KEEP (wire it up now)** |
| `whitenoise` | LOW | **HIGH** (lightest static-files solution for AWS EC2) | Negligible | Medium – ops complexity rises (need nginx/CDN for static) | **KEEP (wire it up now)** |
| `django-storages` | LOW | **HIGH** (S3 media roadmap) | Negligible | Medium – re-add when S3 is implemented | **KEEP** |
| `dj-database-url` | LOW | **MEDIUM** (12-factor config for ECS/K8s) | Negligible | Low – re-add when containerizing | **KEEP (refactor settings.py)** |
| `drf-writable-nested` | LOW | **MEDIUM** (nested serializers for Rent + Agreement, etc.) | Negligible | Low – use custom `create()` instead | **KEEP (small, useful)** |
| `google-cloud-firestore` | LOW | **LOW** (no commitment) | Negligible | Low | **REMOVE** |
| `google-cloud-storage` | LOW | **LOW** (AWS S3 is chosen, not GCS) | Negligible | Low | **REMOVE** |
| `boto3` | LOW + has CVE upgrade needed (1.18.53) | **HIGH** (S3 + AWS deployment) | ~30MB, needs upgrade | High – would need to add back immediately | **KEEP + upgrade to 1.35+ in Phase 2C** |
| `Pillow` | LOW | **HIGH** (ImageField, Image uploads) | ~10MB | High – Django raises `ImproperlyConfigured` | **KEEP (explicit top-level)** |
| `PyPDF2` | LOW | **HIGH** (PDF Merging roadmap)
