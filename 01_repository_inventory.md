# 01 Repository Inventory

**Analysis Date:** 2026-07-14
**Repository:** RentSecureBE
**Type:** Django + DRF Modular Monolith
**Analysis Scope:** Read-only structural and architectural audit

---

## 1. Project Overview

| Attribute | Value |
|-----------|-------|
| **Language** | Python 3.12 |
| **Framework** | Django 5.2.1 + DRF 3.16.0 |
| **Database** | PostgreSQL (production), SQLite (dev/CI) |
| **License** | Not specified in repo |
| **Primary Purpose** | Property management platform with rent payments, AI assistant, document generation, and notifications |
| **Architecture Style** | Modular monolith with documented bounded contexts and import-linter rules |
| **Total Python Files** | ~250+ |
| **Total Django Apps** | 8 active + 2 dead (not in INSTALLED_APPS) |
| **Total Migrations** | ~60+ |

---

## 2. Django Apps

| App | In INSTALLED_APPS | Bounded Context | Status |
|-----|:-----------------:|-----------------|:------:|
| `core` | Yes | Identity & Access + Subscription | Active |
| `properties` | Yes | Property & Rent Management | Active |
| `notification` | Yes | Communication / Notifications | Active |
| `finance` | Yes | Finance & Compliance | Active |
| `documents` | Yes | Document Management | Active |
| `smartbot` | Yes | AI Assistant / Chatbot | Active |
| `referral_and_earn` | Yes | Growth & Referrals | Active |
| `django_extensions` | Yes | Dev Tooling | Active |
| `ai_assistant` | **No** | AI Assistant (duplicate) | **Dead** |
| `dashboard` | **No** | Analytics & Dashboard | **Dead** |

---

## 3. Key Configuration Files

| File | Purpose |
|------|---------|
| `rentsecure_be/settings.py` | Django settings (302 lines, monolithic) |
| `rentsecure_be/urls.py` | Root URL configuration |
| `rentsecure_be/wsgi.py` | WSGI application entry point |
| `rentsecure_be/asgi.py` | ASGI application entry point |
| `import-linter.ini` | Architecture import boundary rules |
| `pyproject.toml` | Tool configs (ruff, mypy, pytest, coverage, bandit, vulture, isort) |
| `requirements.txt` | Unified runtime + dev dependencies (56 packages) |
| `conftest.py` | Pytest configuration and fixtures |
| `.gitignore` | Git ignore rules |
| `kilo.json` | Kilo engineering platform config |

---

## 4. Top-Level Directory Structure

| Directory | Purpose | Layer |
|-----------|---------|-------|
| `core/` | Authentication, OTP, subscriptions, bank details, webhooks | Domain |
| `properties/` | Buildings, units, renters, rent records, caretakers, extra charges | Domain |
| `notification/` | In-app notifications, FCM push, WhatsApp, SMS, voice | Application |
| `finance/` | CA profiles, tax submissions, tax document generation | Application |
| `documents/` | PDF generation for agreements, dossiers, receipts | Application |
| `smartbot/` | AI chatbot, smart actions, GPT, Leegality e-signature | Application |
| `referral_and_earn/` | Referral codes, bonus tracking | Domain |
| `ai_assistant/` | AI insights, analytics, chat (dead — not in INSTALLED_APPS) | Dead |
| `dashboard/` | Agreement status HTML, simple view (dead — not in INSTALLED_APPS) | Dead |
| `rentsecure_be/` | Django project config + domain services (misplaced) | Infrastructure |
| `shared/` | Generic interfaces, exceptions, validators, constants (underutilized) | Shared |
| `management/` | Global management commands (misplaced) | Infrastructure |
| `tests/` | Cross-cutting tests (architecture, hypothesis, performance) | Testing |
| `scripts/` | CI validation, diagram generation, seed data | Infrastructure |
| `tools/` | CI guards, migration guards, deployment scripts | Infrastructure |
| `docs/` | ADRs, business rules, RAG knowledge base, architecture docs | Documentation |
| `architecture/` | ADRs, module boundaries, dependency rules, generated artifacts | Documentation |
| `fonts/` | WeasyPrint font assets (DejaVu) | Infrastructure |
| `.github/` | GitHub Actions workflows (25+ files) | CI/CD |
| `.benchmarks/` | Benchmark result storage (empty) | CI/CD |
| `.githooks/` | Git pre-push hook | CI/CD |
| `.grimp_cache/` | Grimp import analysis cache | Infrastructure |

---

## 5. Key Architectural Observations

### Active Bounded Contexts (Documented)
1. Identity & Access Management (`core`)
2. Subscription & Billing (`core`)
3. Property Management (`properties`)
4. Rent Management (`properties`)
5. Finance & Payments (`finance`)
6. Document Management (`documents`)
7. Notifications (`notification`)
8. AI Assistant (`smartbot`)
9. Referral & Loyalty (`referral_and_earn`)
10. Dashboard & Analytics (`dashboard`)

### Dead Code
- `ai_assistant/` — Not in INSTALLED_APPS, URLs not wired, duplicates `smartbot` + `dashboard`
- `dashboard/` — Not in INSTALLED_APPS, URLs not wired, 21-line view only

### Import-Linter Compliance
- Configured with layered architecture: each app may only import from `rentsecure_be` and itself
- **15+ documented cross-app import violations** exist in the codebase

### Technology Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| **Framework** | Django | 5.2.1 |
| **API** | Django REST Framework | 3.16.0 |
| **Auth** | SimpleJWT | 5.5.1 |
| **Database** | PostgreSQL (prod), SQLite (dev) | — |
| **Cache** | Django LocMemCache | Built-in |
| **Channels** | Django Channels + Redis | 4.2.0 + 4.1.0 |
| **PDF** | WeasyPrint | 69.0 |
| **AI/LLM** | OpenAI (legacy v0.x) | 0.28.1 |
| **Payments** | Razorpay, Cashfree (disabled in Year 1) | 1.4.2 |
| **Notifications** | Twilio, FCM Django, Firebase Admin | 9.6.1 / 2.2.1 / 6.8.0 |
| **Excel** | openpyxl, xlsxwriter | 3.1.5 / 3.2.9 |
| **Task Queue** | Celery + django-celery-beat (contradicts Year 1 policy) | 5.6.3 / 2.9.0 |
| **Testing** | pytest, hypothesis, factory-boy, schemathesis | 9.0.3 / 6.136.0 / 3.3.0 |
| **Linting** | ruff, pylint, mypy, black, isort, bandit | Latest |

---

## 6. Critical Issues Summary

| # | Issue | Severity | Affected Apps |
|---|-------|----------|---------------|
| 1 | `ai_assistant` duplicates `smartbot` + `dashboard` | CRITICAL | ai_assistant, smartbot, dashboard |
| 2 | Payment services in `rentsecure_be/services/` instead of `finance/` | CRITICAL | rentsecure_be, finance |
| 3 | `core/` mixes Identity + Subscription bounded contexts | HIGH | core |
| 4 | `properties/` is a god module (10+ model files) | HIGH | properties |
| 5 | 15+ cross-app import violations | HIGH | core, finance, documents, smartbot, dashboard, ai_assistant |
| 6 | `dashboard/` and `ai_assistant/` not in INSTALLED_APPS | HIGH | dashboard, ai_assistant |
| 7 | Business logic embedded in `notification/services/` | HIGH | notification |
| 8 | Duplicate management commands at root and app level | MEDIUM | management, properties, notification |
| 9 | `shared/interfaces.py` protocols defined but never used | MEDIUM | shared |
| 10 | `settings.py` contradicts Year 1 policy (Celery, Redis) | MEDIUM | rentsecure_be |

---

*End of Document*
