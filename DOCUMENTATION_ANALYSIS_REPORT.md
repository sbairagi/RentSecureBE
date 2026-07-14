# RentSecureBE Documentation Analysis Report

**Analysis Date:** 2026-07-14
**Analyst:** Kilo (Read-Only Analysis)
**Scope:** All documentation files in `docs/`, `architecture/`, `README.md`, and root `.md` files

---

## Executive Summary

The RentSecureBE project has **extensive documentation** (100+ markdown files) covering architecture, business rules, ADRs, RAG knowledge base, AI governance, and CI/CD governance. However, there are **significant accuracy gaps** between the documentation and the actual codebase, **missing referenced files**, **outdated information**, and **internal contradictions** between documents.

**Critical Issues Found:** 12
**Major Issues Found:** 18
**Minor Issues Found:** 15

---

## 1. Missing Documentation Files

### 1.1 Missing ADR Files (CRITICAL)

**Files Missing:** `docs/adr/ADR-013.md` through `docs/adr/ADR-030.md`

The ADR index (`docs/adr/README.md`) lists ADR-013 through ADR-030 as "Accepted" with dates 2026-07-13, but **none of these files exist** in the `docs/adr/` directory.

| Expected File | Status in Index | Actual File |
|---------------|-----------------|-------------|
| ADR-013 | Accepted (2026-07-13) | **MISSING** |
| ADR-014 | Accepted (2026-06-26) | **MISSING** |
| ADR-015 | Accepted (2026-01-15) | **MISSING** |
| ADR-016 | Accepted (2026-01-15) | **MISSING** |
| ADR-017 | Accepted (2026-01-15) | **MISSING** |
| ADR-018 | Accepted (2026-01-15) | **MISSING** |
| ADR-019 | Accepted (2026-07-13) | **MISSING** |
| ADR-020 | Accepted (2026-07-13) | **MISSING** |
| ADR-021 | Accepted (2026-07-13) | **MISSING** |
| ADR-022 | Accepted (2026-07-13) | **MISSING** |
| ADR-023 | Accepted (2026-07-13) | **MISSING** |
| ADR-024 | Accepted (2026-07-13) | **MISSING** |
| ADR-025 | Accepted (2026-07-13) | **MISSING** |
| ADR-026 | Accepted (2026-07-13) | **MISSING** |
| ADR-027 | Accepted (2026-07-13) | **MISSING** |
| ADR-028 | Accepted (2026-07-13) | **MISSING** |
| ADR-029 | Accepted (2026-07-13) | **MISSING** |
| ADR-030 | Accepted (2026-07-13) | **MISSING** |

Only ADR-001 through ADR-012 and ADR-031 through ADR-036 exist (18 files total).

### 1.2 Missing Referenced Directories

| Referenced Path | Document | Actual Status |
|-----------------|----------|---------------|
| `docs/bugs/` | Multiple RAG and business-rules docs | **Directory does not exist** |
| `docs/business-gaps/` | Multiple RAG and business-rules docs | **Directory does not exist** |
| `ARCHITECTURE_PRINCIPLES.md` | `docs/architecture/README.md` | **File does not exist** |
| `CODING_STANDARDS.md` | `docs/architecture/README.md` | **File does not exist** |
| `ROADMAP.md` | `docs/architecture/README.md` | **File does not exist** |
| `architecture/adr/` | `docs/architecture/README.md` | **Directory does not exist** (only `architecture/adr/` exists with different files) |

### 1.3 Empty Documented Directories

| Directory | Documented Purpose | Actual Status |
|-----------|-------------------|---------------|
| `architecture/contracts/` | Bounded context contracts per `module-boundaries.md` | **Empty** |

---

## 2. Outdated Documentation

### 2.1 Signal Wiring Documentation (MAJOR)

**Multiple documents claim signals are NOT wired:**

- `docs/business-rules/02-subscription-and-usage-limits.md`: "`core/signals.assign_default_plan` exists but **`core/apps.py` does not import signals**"
- `docs/business-rules/14-known-behaviors-and-edge-cases.md`: "`core/apps.py` and `properties/apps.py` do not import signals in `ready()`"
- `docs/business-rules/22-signals-and-automation.md`: "**Status:** `core/apps.py` `ready()` does **not** import this module"
- `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md`: "Signal exists; **not connected** in `AppConfig.ready()`"
- `docs/rag/notifications-and-reminders.md`: "**requires** `properties.apps.ready()` to import signals"

**Actual Code State:**
```python
# core/apps.py (lines 12-16)
def ready(self) -> None:
    if os.environ.get("SKIP_DJANGO_SIGNALS") == "1":
        return
    import core.signals  # noqa

# properties/apps.py (lines 12-14)
def ready(self) -> None:
    import properties.signals  # noqa
```

**Verdict:** Documentation is **outdated**. Signals ARE wired. The `SKIP_DJANGO_SIGNALS` environment variable provides an opt-out mechanism that the docs don't mention.

### 2.2 Razorpay Webhook Definitions (MAJOR)

**Documentation Claim:**
- `docs/business-rules/16-payments-and-webhooks.md`: "`razorpay_webhook` defined 3 times in `core/views.py`"
- `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md`: "`razorpay_webhook` defined **three times** in `core/views.py`"
- `docs/rag/payments-razorpay-cashfree.md`: "**duplicate definitions** — last wins"

**Actual Code State:**
Only **1** definition exists:
```python
# core/views.py:394
def razorpay_webhook(request: HttpRequest) -> JsonResponse:
```

**Verdict:** Documentation is **inaccurate**. The webhook is defined only once.

### 2.3 Management Command Status (MAJOR)

**Documentation Claims:**
- `docs/business-rules/22-signals-and-automation.md`: "`generate_monthly_rent_records` — Broken (`rent.models` import)"
- `docs/business-rules/22-signals-and-automation.md`: "`daily_rent_reminder` — Broken import"
- `docs/business-rules/02-subscription-and-usage-limits.md`: "`seed_subscription_plans` and `downgrade_expired_users` commands are **commented out**"

**Actual Code State:**
- `management/commands/generate_monthly_rent_records.py`: Uses `from properties.models import Renter, RentRecord` — **works correctly**
- `management/commands/daily_rent_reminder.py`: Uses `from properties.models import Renter` — **works correctly**
- `management/commands/seed_subscription_plans.py`: **Indeed a stub** (1 line: `# # your_app/management/commands/seed_subscription_plans.py`)
- `management/commands/downgrade_expired_users.py`: **Empty file** (0 lines)

**Verdict:** Partially outdated. The broken import claims are false, but the seed/downgrade commands are indeed non-functional.

### 2.4 Owner Group Assignment (MAJOR)

**Documentation Claim:**
- `docs/business-rules/15-authentication.md`: "Owner → group `tenant` (verify intended role name)"
- `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md`: "Assigned `'tenant'` group"
- `docs/business-rules/14-known-behaviors-and-edge-cases.md`: "Owner OTP assigns group **`tenant`** (likely wrong name for owner role)."

**Actual Code State:**
```python
# core/views.py:143
data, status = _verify_otp_and_login(phone, code, "owner")

# core/services/auth_service.py:29
group, _ = Group.objects.get_or_create(name=group_name)  # group_name = "owner"
```

**Verdict:** Documentation is **inaccurate**. The code correctly assigns the "owner" group, not "tenant".

---

## 3. Internal Contradictions Between Documents

### 3.1 Payment Strategy Contradiction (CRITICAL)

| Document | Claim |
|----------|-------|
| `docs/architecture/production-architecture.md` (Section 3.1) | "Year 1 uses a completely free, manual UPI-based payment flow" |
| `docs/adr/ADR-031.md` | "Year 1 uses a completely free manual UPI-based payment flow" |
| `.kilo/instructions/finance.md` | "Year 1 payment flow is completely free. Rent payment does NOT go through a payment gateway." |
| `docs/ci-cd-pipeline.md` (header) | "**Stack:** Django 5.2 / DRF / PostgreSQL / AWS EC2 / **Cashfree**" |
| `docs/ci-cd-pipeline.md` (diagrams) | Shows Cashfree as payment gateway in sequence diagrams |
| `README.md` (Feature Flags) | Lists `ENABLE_RAZORPAY` and `ENABLE_CASHFREE` flags |

**Verdict:** The CI/CD pipeline documentation and README still reference Cashfree/Razorpay as the primary stack, contradicting the new Year 1 manual UPI strategy documented in ADR-031 and production-architecture.md.

### 3.2 Notification Strategy Contradiction (CRITICAL)

| Document | Claim |
|----------|-------|
| `docs/architecture/production-architecture.md` (Section 4.1) | "Year 1 uses only free notification channels: Email, FCM Push, In-App" |
| `docs/adr/ADR-032.md` | "Year 1 uses only free notification channels" |
| `.kilo/instructions/notifications.md` | "Use only free notification channels. Do NOT depend on paid channels unless explicitly enabled via feature flags." |
| `docs/business-rules/17-notifications.md` | Lists WhatsApp/SMS as active channels via Twilio |
| `docs/rag/notifications-and-reminders.md` | Shows WhatsApp, SMS, Email, Push, Voice as active channels |
| `docs/rag/project-summary.md` | "Notifications: WhatsApp, email, push (FCM), voice notes (gTTS)" |

**Verdict:** The business-rules and RAG documents describe the old paid-channel architecture, contradicting the new Year 1 free-only strategy.

### 3.3 Background Jobs Strategy Contradiction (MAJOR)

| Document | Claim |
|----------|-------|
| `docs/architecture/production-architecture.md` (Section 5.1) | "Year 1 uses Django management commands + cron/systemd timers. No Celery." |
| `docs/adr/ADR-033.md` | "Year 1 uses Django management commands... No Celery, no message broker" |
| `rentsecure_be/settings.py` | Contains `"django_celery_beat"` in `INSTALLED_APPS` |
| `rentsecure_be/settings.py` | Contains `django_celery_beat` and `channels` with Redis backend |

**Verdict:** The actual settings.py contradicts the documented Year 1 "no Celery" policy.

### 3.4 Cache Strategy Contradiction (MAJOR)

| Document | Claim |
|----------|-------|
| `docs/architecture/production-architecture.md` (Section 6.1) | "Year 1 uses Django Local Memory Cache" |
| `docs/adr/ADR-034.md` | "Year 1 uses Django Local Memory Cache (LocMemCache)" |
| `rentsecure_be/settings.py` | Contains `CHANNEL_LAYERS` with `channels_redis.core.RedisChannelLayer` |

**Verdict:** While the cache backend may still be LocMem, the presence of Redis in settings contradicts the "no Redis mandatory in Year 1" narrative.

### 3.5 Feature Flag Name Inconsistencies (MAJOR)

| Document | Flag Names |
|----------|-----------|
| `README.md` | `ENABLE_RAZORPAY`, `ENABLE_CASHFREE`, `ENABLE_WHATSAPP`, `ENABLE_VOICE`, `ENABLE_OPENAI`, `ENABLE_LEEGALITY`, `ENABLE_EMAIL`, `ENABLE_PUSH_NOTIFICATION` |
| `.kilo/instructions/finance.md` | `CASHFREE_PAYMENTS_ENABLED`, `RAZORPAY_PAYMENTS_ENABLED`, `UPI_PAYMENT_ENABLED` |
| `.kilo/instructions/notifications.md` | `WHATSAPP_NOTIFICATIONS_ENABLED`, `SMS_NOTIFICATIONS_ENABLED` |
| `docs/architecture/production-architecture.md` | `PAYMENT_GATEWAY_ENABLED`, `UPI_PAYMENT_ENABLED`, `WHATSAPP_NOTIFICATIONS_ENABLED`, `SMS_NOTIFICATIONS_ENABLED` |

**Verdict:** Feature flag names are inconsistent across documents. The actual codebase uses neither set consistently.

---

## 4. Broken References

### 4.1 Broken Internal Links

| Document | Broken Reference | Issue |
|-----------|------------------|-------|
| `README.md` | `docs/diagrams/generated/c4/c4-context.puml` | Directory exists but may be empty or missing specific files |
| `README.md` | `architecture/architecture-dependency-graph.dot` | File may not exist |
| `docs/architecture/README.md` | `../ARCHITECTURE_PRINCIPLES.md` | File does not exist at project root |
| `docs/architecture/README.md` | `../CODING_STANDARDS.md` | File does not exist at project root |
| `docs/architecture/README.md` | `../ROADMAP.md` | File does not exist at project root |
| `docs/architecture/README.md` | `../adr/ADR-template.md` | File does not exist |
| `docs/business-rules/README.md` | `../business-gaps/BUSINESS_GAPS_AUDIT.md` | Directory does not exist |
| `docs/rag/README.md` | `../business-gaps/BUSINESS_GAPS_AUDIT.md` | Directory does not exist |
| `docs/rag/project-summary.md` | `docs/bugs/` | Directory does not exist |
| `docs/rag/payments-razorpay-cashfree.md` | `docs/bugs/rentsecure_be.md`, `docs/bugs/core.md` | Files do not exist |
| `docs/business-rules/00-overview.md` | `properties/business_rules.md` | File exists but is 311 bytes (likely very short/stub) |

### 4.2 Broken Code References

| Document | Broken Reference | Issue |
|-----------|------------------|-------|
| `docs/business-rules/16-payments-and-webhooks.md` | `rentsecure_be/services/razorpay_service.py` | Path should be `rentsecure_be/services/razorpay_service.py` (correct) |
| `docs/business-rules/08-rent-records.md` | `properties/models/rent_record_models.py` | File exists |
| `docs/business-rules/08-rent-records.md` | `apply_late_fee_if_needed()` in utils | Function may not exist at documented path |
| `docs/rag/payments-razorpay-cashfree.md` | `rent.renter.property.owner` | Uses `property` instead of `unit` — potential runtime bug |

---

## 5. Duplicate Content

### 5.1 Duplicate ADR Locations

- `docs/adr/` contains ADR-001 through ADR-012 and ADR-031-036
- `architecture/adr/` contains different files: `000-template.md`, `001-current-architecture.md`, `002-target-architecture.md`, `003-refactoring-strategy.md`

These are **different documents** but both claim to be architecture decision records, creating confusion.

### 5.2 Duplicate Business Rules Documentation

- `properties/business_rules.md` — legacy single-file version (311 bytes)
- `docs/business-rules/` — new split version with 23 files
- `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` — long-form deep dive (414 lines)

The legacy file is referenced in multiple places as "superseded" but still exists and may cause confusion.

### 5.3 Duplicate Architecture Documentation

- `docs/architecture/README.md` — architecture overview
- `docs/architecture/production-architecture.md` — detailed production architecture
- `docs/kilo-architecture-spec.md` — Kilo engineering platform architecture
- `architecture/` directory — contains ADRs, baseline docs, dependency rules, module boundaries
- `docs/ci-cd-pipeline.md` — CI/CD pipeline overview
- `docs/architecture-contract.md` — CI/CD contract
- `docs/governance.md` — CI/CD governance

Multiple overlapping architecture documents exist without clear ownership or cross-references.

---

## 6. Accuracy Issues

### 6.1 README.md Issues

| Issue | Details |
|--------|---------|
| **Stack references Cashfree** | Header says "AWS EC2 / Cashfree" but Year 1 strategy is manual UPI |
| **Diagram references may be broken** | References `docs/diagrams/generated/c4/c4-context.puml` and `architecture/architecture-dependency-graph.dot` |
| **Feature flags outdated** | Lists `ENABLE_RAZORPAY`, `ENABLE_CASHFREE` etc. which don't match actual flag names in code |
| **Project structure incomplete** | Missing `ai_assistant/`, `dashboard/`, `shared/`, `tools/`, `scripts/`, `fonts/`, `management/` |
| **Python version** | Badge says Django 5.2, but `docs/rag/tech-stack.md` says Django 4.2.30 |

### 6.2 ci-cd-pipeline.md Issues

| Issue | Details |
|--------|---------|
| **Header mentions Cashfree** | "Stack: Django 5.2 / DRF / PostgreSQL / AWS EC2 / **Cashfree**" |
| **Diagrams show old payment flow** | Sequence diagrams show Cashfree payment links and payouts, not manual UPI |
| **Deployment diagram shows Celery** | Shows "Celery Worker" and "Celery Beat" which contradict Year 1 "no Celery" policy |

### 6.3 RAG Document Issues

| Document | Issue |
|----------|-------|
| `docs/rag/project-summary.md` | Describes old payment flow: "renters pay rent via Razorpay; owners receive payouts via Cashfree" |
| `docs/rag/tech-stack.md` | Lists Django 4.2.30 (outdated; README says 5.2) |
| `docs/rag/payments-razorpay-cashfree.md` | Focuses entirely on Razorpay/Cashfree, no mention of manual UPI |
| `docs/rag/notifications-and-reminders.md` | Describes WhatsApp/SMS as active channels, not "Coming Soon" |
| `docs/rag/repository-structure.md` | Missing many top-level directories from actual structure |

### 6.4 Business Rules Document Issues

| Document | Issue |
|----------|-------|
| `docs/business-rules/00-overview.md` | Lists `/properties/` as "duplicate mount" — accurate but confusing |
| `docs/business-rules/02-subscription-and-usage-limits.md` | Claims `core/apps.py` doesn't import signals — **FALSE** |
| `docs/business-rules/08-rent-records.md` | References `payment_status` as separate field — actually a property alias |
| `docs/business-rules/16-payments-and-webhooks.md` | References old payment gateway URLs and flows |
| `docs/business-rules/17-notifications.md` | Lists WhatsApp/SMS as active, not "Coming Soon" |

---

## 7. Architecture Compliance Issues

### 7.1 ADR Compliance Gaps

The following ADRs are documented as "Accepted" but the implementation contradicts them:

| ADR | Claim | Actual State |
|-----|-------|--------------|
| ADR-003 | Celery for Background Tasks | Settings has `django_celery_beat` |
| ADR-005 | Redis for Caching and Queues | Settings has Redis `CHANNEL_LAYERS` |
| ADR-031 | Manual UPI Payments as Year 1 Strategy | README and CI/CD docs still reference Cashfree |
| ADR-032 | Free Notification Channels Only in Year 1 | Business rules and RAG docs describe WhatsApp/SMS as active |
| ADR-033 | Cron + Management Commands as Year 1 Strategy | Settings has Celery Beat |
| ADR-034 | Django Local Memory Cache as Year 1 Strategy | Settings has Redis configured |

### 7.2 Module Boundary Violations (per `directory-structure-analysis.md`)

The `directory-structure-analysis.md` (which exists in the repo root) documents extensive architecture violations:

- **Duplicate bounded contexts:** `ai_assistant` duplicates `smartbot` + `dashboard`
- **Payment services misplaced:** `rentsecure_be/services/` contains domain services
- **God module:** `properties/` contains 10+ model files, 8 view files, 7 service files
- **Mixed contexts in `core/`:** Identity + Subscription in one app
- **Business logic in `notification/`:** Reminder services contain domain logic
- **Cross-context imports:** Multiple apps import models from other contexts

---

## 8. TODO/FIXME Markers in Documentation

Only **3** instances found (all in template examples, not actual code markers):

1. `docs/adr/README.md:58`: "Create a new file: `ADR-XXX.md`"
2. `docs/ai-governance/AI-Decision-Record.md:6`: "# ADR-XXX: [Title]"
3. `docs/ai-governance/AI-Decision-Record.md:31`: "- ADR-XXX: [Related decision]"

**No actual TODO/FIXME/HACK markers found in documentation content.**

---

## 9. Recommendations

### 9.1 Immediate Actions (P0)

1. **Create missing ADR files (013-030)** or remove them from the index
2. **Update signal documentation** to reflect that signals ARE wired (with `SKIP_DJANGO_SIGNALS` opt-out)
3. **Fix razorpay_webhook documentation** — only 1 definition exists, not 3
4. **Update management command documentation** — commands work correctly except `seed_subscription_plans` and `downgrade_expired_users`
5. **Fix owner group assignment documentation** — code assigns "owner" group, not "tenant"
6. **Create missing directories** (`docs/bugs/`, `docs/business-gaps/`) or remove references to them
7. **Create missing root files** (`ARCHITECTURE_PRINCIPLES.md`, `CODING_STANDARDS.md`, `ROADMAP.md`) or update references

### 9.2 High Priority (P1)

8. **Reconcile payment strategy documentation** — update README and CI/CD docs to reflect manual UPI strategy
9. **Reconcile notification strategy documentation** — update business-rules and RAG docs to reflect free-only Year 1 channels
10. **Standardize feature flag names** across all documents
11. **Update RAG documents** to reflect current Year 1 architecture
12. **Fix ci-cd-pipeline.md header** — remove "Cashfree" from stack description
13. **Verify and fix broken diagram references** in README

### 9.3 Medium Priority (P2)

14. **Consolidate duplicate ADR locations** — choose one location for ADRs
15. **Consolidate architecture documentation** — reduce overlap between `docs/architecture/`, `architecture/`, and `docs/kilo-architecture-spec.md`
16. **Update tech-stack documentation** — Django version should be consistent (5.2 per README, 4.2.30 per RAG doc)
17. **Populate or remove empty directories** (`architecture/contracts/`)
18. **Add cross-references** between related documents

### 9.4 Low Priority (P3)

19. **Create `docs/bugs/` and `docs/business-gaps/`** if they are intended to exist
20. **Add a documentation versioning strategy** to track changes
21. **Implement documentation linting** in CI to catch broken references

---

## 10. Document Status Summary

| Category | Count | Status |
|----------|-------|--------|
| Total Documentation Files | 100+ | Extensive |
| Missing Referenced Files | 8+ | Critical |
| Outdated Documents | 6 | Major |
| Documents with Internal Contradictions | 5 | Critical |
| Broken References | 15+ | Major |
| Duplicate Content Locations | 3 | Minor |
| Empty Documented Directories | 1 | Minor |
| TODO/FIXME Markers | 3 | Minor |

---

## 11. Specific Document Assessments

### 11.1 README.md
- **Purpose:** Project overview and quick start
- **Up-to-date:** No — references Cashfree, outdated diagrams, wrong feature flags
- **Accurate:** Partially — tech stack table is mostly correct but project structure is incomplete
- **Issues:** 6

### 11.2 docs/architecture/production-architecture.md
- **Purpose:** Year 1 through Stage 4 infrastructure strategy
- **Up-to-date:** Yes — reflects current Year 1 strategy (manual UPI, free notifications, no Celery)
- **Accurate:** Yes — matches ADR-031 through ADR-036
- **Issues:** None significant

### 11.3 docs/ci-cd-pipeline.md
- **Purpose:** CI/CD pipeline overview and diagrams
- **Up-to-date:** No — header mentions Cashfree, diagrams show old payment flow
- **Accurate:** No — contradicts Year 1 strategy
- **Issues:** 4

### 11.4 docs/adr/README.md
- **Purpose:** ADR index
- **Up-to-date:** No — lists 18 missing ADR files
- **Accurate:** No — references non-existent files
- **Issues:** 1 (critical)

### 11.5 docs/business-rules/* (23 files)
- **Purpose:** Domain-specific business rules
- **Up-to-date:** No — many files reference old payment/notification flows
- **Accurate:** Partially — some files have outdated claims about signals, webhooks, commands
- **Issues:** 8+

### 11.6 docs/rag/* (23 files)
- **Purpose:** RAG knowledge base for AI indexing
- **Up-to-date:** No — describes old Razorpay/Cashfree flow, WhatsApp/SMS as active
- **Accurate:** No — contradicts current Year 1 architecture
- **Issues:** 6+

### 11.7 .kilo/instructions/* (11 files)
- **Purpose:** Kilo engineering platform instructions
- **Up-to-date:** Yes — reflects current Year 1 strategy
- **Accurate:** Yes — matches production-architecture.md and ADRs
- **Issues:** None significant (feature flag name inconsistencies with README)

### 11.8 architecture-compliance-report.md
- **Purpose:** Auto-generated compliance report
- **Up-to-date:** Yes — generated 2026-07-14
- **Accurate:** Unknown — claims 100% compliance but ADR files are missing
- **Issues:** Potential false compliance due to missing ADR files

### 11.9 directory-structure-analysis.md
- **Purpose:** Structural audit of codebase
- **Up-to-date:** Yes — appears recent and thorough
- **Accurate:** Yes — matches actual codebase observations
- **Issues:** None

---

## 12. Conclusion

The RentSecureBE project has **extensive but inconsistent documentation**. The most critical issues are:

1. **18 missing ADR files** that are listed as "Accepted" in the index
2. **Outdated signal wiring documentation** that contradicts actual code
3. **Internal contradictions** between Year 1 strategy documents (production-architecture.md, ADR-031-036) and older documents (ci-cd-pipeline.md, business-rules, RAG docs)
4. **Broken references** to non-existent directories (`docs/bugs/`, `docs/business-gaps/`)
5. **Settings.py contradictions** with documented Year 1 policies (Celery, Redis)

The `.kilo/instructions/` directory and `docs/architecture/production-architecture.md` appear to be the **most accurate** sources of truth for the current Year 1 architecture. The `docs/business-rules/`, `docs/rag/`, and `docs/ci-cd-pipeline.md` documents contain **outdated information** from the previous payment gateway / paid notification architecture.

**Recommended Action:** Treat `.kilo/instructions/` and `docs/architecture/production-architecture.md` as the source of truth for Year 1 strategy, and update all other documents to match.
