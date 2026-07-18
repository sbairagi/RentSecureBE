# RentSecure Backend — Migration Plan

**Project:** RentSecure Backend
**Phase:** Migration Planning
**Date:** 2026-07-15
**Status:** PLANNING ONLY — No code modifications
**Constraint:** Documentation only. No production code was modified.

---

## 1. Executive Summary

### 1.1 Overall Migration Objective

The RentSecure backend has reached approximately 50% completion and exhibits **rapid development artifacts** rather than intentional bounded-context design. This migration plan establishes a safe, incremental path to a clean Domain-Driven Design (DDD) architecture without disrupting production or ongoing feature development.

**Primary objectives:**
1. Eliminate duplicate implementations (WhatsApp, Leegality, i18n, PDF generation)
2. Relocate misplaced services to their correct bounded contexts
3. Merge overlapping apps (`smartbot` + `ai_assistant` → `assistant`)
4. Establish clear dependency boundaries between bounded contexts
5. Prepare the codebase for Stage 2 payment gateway activation
6. Maintain zero downtime and full backward compatibility throughout

### 1.2 Guiding Principles

| Principle | Description |
|-----------|-------------|
| **Never break production** | No migration phase may introduce a breaking change to running systems |
| **One bounded context at a time** | Migrate one context completely before beginning the next |
| **One logical change per PR** | Each PR moves a single file or consolidates a single concern |
| **CI must pass after every phase** | No phase is complete until the full CI pipeline is green |
| **Compatibility wrappers until migration completes** | Deprecated modules re-export new locations until all callers are updated |
| **Rollback must always be possible** | Every phase must have a tested, documented rollback procedure |
| **No Big Bang migration** | All changes are incremental and reversible |

### 1.3 Zero-Downtime Philosophy

Migration will be performed using the **strangler fig pattern**:

1. **Phase 0**: Establish compatibility wrappers at old import locations
2. **Phase 1**: Implement new code at target locations
3. **Phase 2**: Migrate call sites one-by-one to new imports
4. **Phase 3**: Remove old code only after zero callers remain

At no point during the migration will:
- A production import break
- A Django app fail to load
- A URL route become unreachable
- A management command become unrunnable
- A signal handler become unregistered

### 1.4 Backward Compatibility Strategy

All migrations maintain backward compatibility through:

1. **Alias imports**: Old modules re-export new implementations
2. **Deprecation warnings**: Logged but not enforced
3. **Parallel implementations**: Old and new coexist during migration
4. **Feature flags**: Disabled services remain importable until Stage 2
5. **Gradual cutover**: Call sites migrate one-at-a-time with CI validation

---

## 2. Migration Principles

### 2.1 Hard Rules

1. **Never modify `INSTALLED_APPS` during migration** — Add new apps only after all code is migrated
2. **Never delete a module until all imports are updated** — Use `grep` to verify zero remaining imports
3. **Never change public API signatures** — Method signatures, return types, and behavior must remain identical
4. **Never break existing tests** — All existing tests must pass before and after each phase
5. **Never introduce circular dependencies** — Validate import graph after each phase
6. **Never bypass feature flags** — Disabled services remain importable and functional
7. **Never modify Django models during migration** — Model moves require separate migration planning
8. **One PR per phase** — Each phase is a single, reviewable PR
9. **No mixing of concerns** — Do not consolidate unrelated changes in the same PR
10. **Document every change** — Update architecture docs after each phase

### 2.2 Soft Rules

1. Prefer moving files over copying files
2. Maintain original file structure within moved modules
3. Preserve git history with `git mv` where possible
4. Keep test files with their source files
5. Update documentation in the same PR as the code change
6. Run the full test suite locally before pushing

### 2.3 What This Migration Will NOT Do

1. **Will NOT create new Django apps** during the migration — Apps are restructured, not created
2. **Will NOT modify database schemas** — No model changes
3. **Will NOT change URL structures** — URL routing is preserved
4. **Will NOT enable disabled features** — Feature flags remain unchanged
5. **Will NOT delete any code** — Only moves and consolidations
6. **Will NOT modify settings** — `settings.py` remains untouched
7. **Will NOT change CI/CD pipelines** — Workflows remain unchanged

---

## 3. Dependency Validation

### 3.1 Validation Checklist

Before any file is moved, ALL of the following must be verified:

| Validation | Command/Tool | Pass Criteria |
|------------|--------------|---------------|
| **Forward imports** | `grep -r "from <module>" --include="*.py" .` | Document all importers |
| **Reverse imports** | `grep -r "import <module>" --include="*.py" .` | Document all importers |
| **Circular dependencies** | `import-linter` or manual analysis | Zero cycles introduced |
| **Runtime imports** | `grep -r "__import__\|importlib" --include="*.py" .` | None affected |
| **Django admin registrations** | `grep -r "admin.site.register" --include="*.py" .` | None affected |
| **Signal registrations** | `grep -r "@receiver\|post_save\|post_delete" --include="*.py" .` | None affected |
| **URL registrations** | `grep -r "path(\|include(" --include="*.py" .` | None affected |
| **Celery tasks** | `grep -r "shared_task\|@app.task\|\.delay\|\.apply_async" --include="*.py" .` | None affected |
| **Management commands** | `grep -r "call_command" --include="*.py" .` | None affected |
| **Migrations** | `find . -name "*.py" -path "*/migrations/*"` | None affected |
| **Feature flags** | `grep -r "ENABLE_" --include="*.py" .` | None affected |
| **Type annotations** | `mypy --strict` | Zero new errors |

### 3.2 Validation Template

For each file to be moved, complete this template:

```yaml
file: path/to/source.py
destination: path/to/destination.py
forward_imports:
  - file: path/to/importer.py
    line: 42
    import: from path.to.source import SomeClass
reverse_imports: []  # files that source imports
django_registrations: []
signal_registrations: []
url_registrations: []
celery_tasks: []
management_commands: []
migrations: []
feature_flags: []
validation_status: PENDING
```

### 3.3 Dependency Map

```
Current Import Graph (simplified):

notification/utils.py
  ├── fcm_django.models.FCMDevice
  └── twilio.rest.Client

notification/services/whatsapp_service.py
  ├── twilio.rest.Client
  ├── notification.utils.send_whatsapp_message (CROSS)
  └── boto3 (optional)

notification/services/rent_notify_service.py
  ├── notification.services.voice_service
  ├── notification.services.whatsapp_service
  ├── rentsecure_be.services.i18n_service
  └── properties.models.RentRecord

notification/services/extra_charge_reminders.py
  ├── notification.services.voice_service
  ├── notification.services.whatsapp_service
  └── rentsecure_be.services.i18n_service

smartbot/services/leegality_service.py
  ├── requests
  └── django.conf.settings

rentsecure_be/services/leegality_service.py
  ├── requests
  └── django.conf.settings

smartbot/services/agreement_service.py
  ├── django.template.loader
  └── weasyprint.HTML

core/services/owner_reporting_service.py
  ├── properties.models.rent_record_models.RentRecord
  └── django.db.models.Sum

properties/services/summary_service.py
  ├── core.models.NotificationPreference
  ├── notification.services.whatsapp_service
  └── django.core.mail.send_mail

smartbot/actions.py
  ├── notification.utils.send_whatsapp_message
  ├── properties.models.Renter, RentRecord
  ├── rentsecure_be.services.cashfree_service
  ├── smartbot.services.agreement_service
  ├── smartbot.services.leegality_service
  └── smartbot.whatsapp_service

ai_assistant/services/i18n_service.py
  └── (duplicate of rentsecure_be.services.i18n_service)

ai_assistant/services/archive_service.py
  ├── properties.models.Renter
  └── django.core.files.storage

ai_assistant/services/invoice_service.py
  ├── django.template.loader
  └── weasyprint.HTML

ai_assistant/services/unit_service.py
  ├── properties.models.Unit
  └── properties.repositories.unit_repository
```

---

## 4. Migration Order

### PHASE 0: Pre-Migration Preparation

**Objective:** Establish validation infrastructure and compatibility wrappers.

**Duration:** 1-2 days
**Complexity:** Low
**Risk:** Very Low

**Tasks:**
1. Create `docs/refactoring/migration_checklist.md` with per-phase validation steps
2. Create a `migration/` directory for tracking migration state
3. Add import-linter configuration to detect circular dependencies
4. Add mypy strict checking to CI
5. Document all current imports for files targeted in Phase 1-4

**Validation Checklist:**
- [ ] All current imports documented in `migration/imports_phase1.json`
- [ ] import-linter passes with current codebase
- [ ] mypy --strict passes with current codebase
- [ ] Full test suite passes

**Rollback Plan:** N/A — no code changes

---

### PHASE 1: WhatsApp Consolidation

**Objective:** Merge duplicate `send_whatsapp_message` implementations into a single source of truth.

**Duration:** 1-2 days
**Complexity:** Low
**Risk:** Low

**Files Involved:**

| File | Action |
|------|--------|
| `notification/utils.py` | MODIFY — remove WhatsApp functions, keep push only |
| `notification/services/whatsapp_service.py` | KEEP — becomes canonical implementation |

**Preconditions:**
- All call sites documented
- Both implementations have identical behavior for common cases
- No Celery tasks depend on the return value of `send_whatsapp_message`

**Dependency Validation:**
```bash
# Find all call sites
grep -r "send_whatsapp_message" --include="*.py" .
# Expected: notification/utils.py, notification/services/whatsapp_service.py,
#           notification/services/communication.py,
#           notification/services/rent_notify_service.py,
#           notification/services/extra_charge_reminders.py,
#           notification/services/voice_note_service.py,
#           notification/services/late_fees_notify_service.py,
#           properties/services/summary_service.py,
#           properties/views/property_views.py,
#           smartbot/actions.py,
#           smartbot/whatsapp_service.py,
#           properties/services/renter_onboarding_service.py
```

**Migration Steps:**

1. **Create compatibility wrapper in `notification/utils.py`**:
   ```python
   # notification/utils.py
   import warnings
   from notification.services.whatsapp_service import send_whatsapp_message as _send_whatsapp_message

   def send_whatsapp_message(to: str, message: str) -> Any:
       warnings.warn(
           "notification.utils.send_whatsapp_message is deprecated. "
           "Use notification.services.whatsapp_service.send_whatsapp_message instead.",
           DeprecationWarning,
           stacklevel=2,
       )
       return _send_whatsapp_message(to, message)

   def send_push_notification(user: Any, title: str, body: str) -> None:
       # Keep existing implementation
       ...
   ```

2. **Update `notification/services/whatsapp_service.py`** to be the canonical implementation (already is).

3. **Migrate call sites one-by-one** (in separate commits):
   - `notification/services/communication.py`
   - `notification/services/rent_notify_service.py`
   - `notification/services/extra_charge_reminders.py`
   - `notification/services/voice_note_service.py`
   - `notification/services/late_fees_notify_service.py`
   - `properties/services/summary_service.py`
   - `properties/views/property_views.py`
   - `smartbot/actions.py`
   - `smartbot/whatsapp_service.py`
   - `properties/services/renter_onboarding_service.py`

4. **Remove compatibility wrapper** after all call sites are migrated.

**Validation Checklist:**
- [ ] All call sites use `notification.services.whatsapp_service`
- [ ] No imports of `notification.utils.send_whatsapp_message` remain
- [ ] All tests pass
- [ ] No DeprecationWarnings in test output
- [ ] `notification/utils.py` only contains `send_push_notification`

**CI Requirements:**
- ruff check passes
- mypy --strict passes
- pytest passes with current Python version
- No new warnings

**Rollback Plan:**
- Revert the PR that removes the compatibility wrapper
- All call sites remain functional via wrapper

**Estimated Complexity:** Low
**Estimated Effort:** 2-3 hours

---

### PHASE 2: Leegality Consolidation

**Objective:** Merge duplicate Leegality e-signature implementations into `documents/services/leegality.py`.

**Duration:** 2-3 days
**Complexity:** Medium
**Risk:** Medium

**Files Involved:**

| File | Action |
|------|--------|
| `rentsecure_be/services/leegality_service.py` | MOVE → `documents/services/leegality.py` |
| `smartbot/services/leegality_service.py` | MERGE into `documents/services/leegality.py` |
| `properties/views/unit_views.py` | UPDATE import |
| `smartbot/actions.py` | UPDATE import |

**Preconditions:**
- Phase 1 complete and merged
- Both implementations analyzed for behavioral differences
- Documented API contract for Leegality service

**Dependency Validation:**
```bash
# Find all call sites
grep -r "leegality_service\|send_agreement_for_signature\|initiate_signature\|check_signature_status" --include="*.py" .
# Expected:
#   rentsecure_be/services/leegality_service.py (source)
#   smartbot/services/leegality_service.py (source)
#   properties/views/unit_views.py (imports send_agreement_for_signature)
#   smartbot/actions.py (imports initiate_signature)
#   smartbot/tests/test_leegality_service.py (tests)
```

**Migration Steps:**

1. **Create `documents/services/leegality.py`** with unified API:
   ```python
   # documents/services/leegality.py
   from __future__ import annotations

   import json
   from typing import Any

   import requests

   from django.conf import settings

   LEEGALITY_API_URL = "https://api.leegality.com/v3/document/upload"
   LEEGALITY_DOCUMENT_URL = "https://api.leegality.com/v3/document"


   def initiate_signature(renter: Any, file_path: str) -> dict[str, Any]:
       # Merge both implementations
       ...

   def check_signature_status(signature_request_id: str) -> str | None:
       # From smartbot/services/leegality_service.py
       ...

   def send_agreement_for_signature(
       agreement: Any,
       owner_email: str,
       renter_email: str,
   ) -> dict[str, Any]:
       # From rentsecure_be/services/leegality_service.py
       ...
   ```

2. **Create compatibility wrappers**:
   ```python
   # rentsecure_be/services/leegality_service.py
       warnings.warn(
           "rentsecure_be.services.leegality_service is deprecated. "
           "Use documents.services.leegality instead.",
           DeprecationWarning,
           stacklevel=2,
       )
       from documents.services.leegality import send_agreement_for_signature as _send_agreement_for_signature
       return _send_agreement_for_signature(agreement, owner_email, renter_email)

   # smartbot/services/leegality_service.py
       warnings.warn(
           "smartbot.services.leegality_service is deprecated. "
           "Use documents.services.leegality instead.",
           DeprecationWarning,
           stacklevel=2,
       )
       from documents.services.leegality import initiate_signature as _initiate_signature
       return _initiate_signature(renter, file_path)
   ```

3. **Migrate call sites**:
   - `properties/views/unit_views.py` → import from `documents.services.leegality`
   - `smartbot/actions.py` → import from `documents.services.leegality`
   - `smartbot/tests/test_leegality_service.py` → import from `documents.services.leegality`

4. **Remove compatibility wrappers** after all call sites are migrated.

**Validation Checklist:**
- [ ] `documents/services/leegality.py` passes all tests
- [ ] No imports of `rentsecure_be.services.leegality_service` remain
- [ ] No imports of `smartbot.services.leegality_service` remain
- [ ] Leegality webhook in `properties/views/unit_views.py` still functions
- [ ] All tests pass
- [ ] No DeprecationWarnings in test output

**CI Requirements:**
- ruff check passes
- mypy --strict passes
- pytest passes
- No new warnings

**Rollback Plan:**
- Revert the PR that removes compatibility wrappers
- Old implementations remain functional via wrappers

**Estimated Complexity:** Medium
**Estimated Effort:** 4-6 hours

---

### PHASE 3: i18n Service Extraction

**Objective:** Move `rentsecure_be/services/i18n_service.py` to `shared/services/i18n.py` and update all call sites.

**Duration:** 1-2 days
**Complexity:** Low
**Risk:** Low

**Files Involved:**

| File | Action |
|------|--------|
| `rentsecure_be/services/i18n_service.py` | MOVE → `shared/services/i18n.py` |
| `notification/services/rent_notify_service.py` | UPDATE import |
| `notification/services/extra_charge_reminders.py` | UPDATE import |
| `notification/services/communication.py` | UPDATE import |

**Preconditions:**
- Phase 2 complete and merged
- `shared/` app is available for new modules

**Dependency Validation:**
```bash
grep -r "i18n_service\|translate_msg" --include="*.py" .
# Expected call sites:
#   rentsecure_be/services/i18n_service.py (source)
#   notification/services/rent_notify_service.py
#   notification/services/extra_charge_reminders.py
#   notification/services/communication.py
```

**Migration Steps:**

1. **Create `shared/services/i18n.py`** with the implementation from `rentsecure_be/services/i18n_service.py`.

2. **Create compatibility wrapper**:
   ```python
   # rentsecure_be/services/i18n_service.py
   import warnings
   from shared.services.i18n import translate_msg as _translate_msg

   def translate_msg(message: str, lang: str) -> str:
       warnings.warn(
           "rentsecure_be.services.i18n_service is deprecated. "
           "Use shared.services.i18n.translate_msg instead.",
           DeprecationWarning,
           stacklevel=2,
       )
       return _translate_msg(message, lang)
   ```

3. **Migrate call sites** in `notification/` to use `shared.services.i18n`.

4. **Remove compatibility wrapper** after all call sites are migrated.

**Validation Checklist:**
- [ ] `shared/services/i18n.py` exists and passes tests
- [ ] No imports of `rentsecure_be.services.i18n_service` remain
- [ ] All notification tests pass
- [ ] No DeprecationWarnings in test output

**CI Requirements:**
- ruff check passes
- mypy --strict passes
- pytest passes

**Rollback Plan:**
- Revert the PR that removes the compatibility wrapper
- Old import path remains functional

**Estimated Complexity:** Low
**Estimated Effort:** 2-3 hours

---

### PHASE 4: PDF Generation Consolidation

**Objective:** Consolidate all PDF generation into `documents/utils/pdf_generator.py`.

**Duration:** 3-5 days
**Complexity:** Medium
**Risk:** Medium

**Files Involved:**

| File | Action |
|------|--------|
| `smartbot/services/agreement_service.py` | MOVE → `documents/services/agreement.py` |
| `properties/utils/utils.py` (PDF functions) | MOVE → `documents/utils/pdf_generator.py` |
| `documents/utils.py` | MERGE into `documents/utils/pdf_generator.py` |
| `documents/views.py` | UPDATE to use consolidated functions |
| `finance/views.py` | UPDATE to use consolidated functions |
| `properties/services/receipt_service.py` | UPDATE to use consolidated functions |

**Preconditions:**
- Phase 3 complete and merged
- All PDF generation functions documented
- Template paths validated

**Dependency Validation:**
```bash
# Find all PDF generation call sites
grep -r "weasyprint\|HTML(string=\|generate_rent_invoice_pdf\|generate_agreement_pdf\|generate_unit_history_pdf\|generate_tax_pdf\|generate_rent_receipt_pdf" --include="*.py" .
# Expected:
#   smartbot/services/agreement_service.py (source)
#   properties/utils/utils.py (source)
#   documents/utils.py (source)
#   documents/views.py (inline)
#   finance/views.py (inline)
#   properties/services/receipt_service.py (source)
```

**Migration Steps:**

1. **Create `documents/utils/pdf_generator.py`** with unified API:
   ```python
   # documents/utils/pdf_generator.py
   from __future__ import annotations

   import logging
   from typing import Any

   from django.template.loader import render_to_string

   logger = logging.getLogger(__name__)


   def generate_rent_agreement_pdf(rent_record: Any) -> bytes:
       """Generate rent agreement PDF."""
       ...

   def generate_rent_invoice_pdf(rent: Any) -> bytes:
       """Generate rent invoice PDF."""
       ...

   def generate_unit_history_pdf(unit_obj: Any) -> bytes:
       """Generate unit history PDF."""
       ...

   def generate_tax_pdf(user: Any, properties: Any, fy: str) -> str:
       """Generate tax summary PDF."""
       ...

   def generate_rent_receipt_pdf(rent_record: Any) -> bytes:
       """Generate rent receipt PDF."""
       ...
   ```

2. **Move implementations** from source files to `pdf_generator.py`.

3. **Create compatibility wrappers** at old locations:
   ```python
   # smartbot/services/agreement_service.py
   import warnings
   from documents.utils.pdf_generator import generate_rent_agreement_pdf as _generate_rent_agreement_pdf

   def generate_agreement_pdf(rent_record: Any) -> str:
       warnings.warn(
           "smartbot.services.agreement_service.generate_agreement_pdf is deprecated. "
           "Use documents.utils.pdf_generator.generate_rent_agreement_pdf instead.",
           DeprecationWarning,
           stacklevel=2,
       )
       return _generate_rent_agreement_pdf(rent_record)
   ```

4. **Migrate call sites** one-by-one.

5. **Remove compatibility wrappers** after all call sites are migrated.

**Validation Checklist:**
- [ ] All PDF generation functions exist in `documents/utils/pdf_generator.py`
- [ ] All call sites use new import paths
- [ ] Generated PDFs are identical to before migration
- [ ] All tests pass
- [ ] No DeprecationWarnings in test output

**CI Requirements:**
- ruff check passes
- mypy --strict passes
- pytest passes
- Manual PDF generation test for each PDF type

**Rollback Plan:**
- Revert the PR that removes compatibility wrappers
- All PDF generation remains functional via wrappers

**Estimated Complexity:** Medium
**Estimated Effort:** 8-12 hours

---

### PHASE 5: Owner Reporting Relocation

**Objective:** Move `core/services/owner_reporting_service.py` to `properties/services/owner_reporting_service.py`.

**Duration:** 1-2 days
**Complexity:** Low
**Risk:** Low

**Files Involved:**

| File | Action |
|------|--------|
| `core/services/owner_reporting_service.py` | MOVE → `properties/services/owner_reporting_service.py` |
| `core/views.py` | UPDATE import |

**Preconditions:**
- Phase 4 complete and merged

**Dependency Validation:**
```bash
grep -r "owner_reporting_service\|OwnerReportingService" --include="*.py" .
# Expected:
#   core/services/owner_reporting_service.py (source)
#   core/views.py (imports OwnerReportingService)
#   core/tests/test_views.py (tests)
```

**Migration Steps:**

1. **Move file** to `properties/services/owner_reporting_service.py`.

2. **Create compatibility wrapper**:
   ```python
   # core/services/owner_reporting_service.py
   import warnings
   from properties.services.owner_reporting_service import OwnerReportingService as _OwnerReportingService

   class OwnerReportingService(_OwnerReportingService):
       def __init__(self, *args: Any, **kwargs: Any) -> None:
           warnings.warn(
               "core.services.owner_reporting_service is deprecated. "
               "Use properties.services.owner_reporting_service instead.",
               DeprecationWarning,
               stacklevel=2,
           )
           super().__init__(*args, **kwargs)
   ```

3. **Update call site** in `core/views.py`.

4. **Remove compatibility wrapper** after call site is updated.

**Validation Checklist:**
- [ ] `properties/services/owner_reporting_service.py` exists
- [ ] `core/views.py` imports from new location
- [ ] All owner reporting endpoints function correctly
- [ ] All tests pass

**CI Requirements:**
- ruff check passes
- mypy --strict passes
- pytest passes

**Rollback Plan:**
- Revert the PR that removes the compatibility wrapper
- Old import path remains functional

**Estimated Complexity:** Low
**Estimated Effort:** 2-3 hours

---

### PHASE 6: Property Notification Relocation

**Objective:** Move property-specific notification services from `notification/services/` to `properties/services/`.

**Duration:** 3-5 days
**Complexity:** Medium
**Risk:** Medium

**Files Involved:**

| File | Action |
|------|--------|
| `notification/services/rent_notify_service.py` | MOVE → `properties/services/notification_service.py` |
| `notification/services/extra_charge_reminders.py` | MOVE → `properties/services/extra_charge_notifications.py` |
| `notification/services/late_fees_notify_service.py` | MOVE → `properties/services/late_fee_notifications.py` |
| `properties/signals/__init__.py` | UPDATE imports |
| `properties/utils/utils.py` | UPDATE imports |

**Preconditions:**
- Phase 5 complete and merged
- All property notification call sites documented

**Dependency Validation:**
```bash
grep -r "rent_notify_service\|extra_charge_reminders\|late_fees_notify_service\|send_payout_notification\|notify_renter\|notify_owner\|notify_owner_post_payout\|send_due_extra_charge_reminders\|notify_renter_about_late_fee\|notify_owner_about_late_fee" --include="*.py" .
# Expected call sites:
#   notification/services/rent_notify_service.py (source)
#   notification/services/extra_charge_reminders.py (source)
#   notification/services/late_fees_notify_service.py (source)
#   properties/signals/__init__.py (imports send_payout_notification, send_thank_you_voice_note, etc.)
#   properties/utils/utils.py (imports notify_renter_about_late_fee, notify_owner_about_late_fee)
#   core/views.py (imports send_payout_notification)
#   properties/services/renter_onboarding_service.py (imports send_whatsapp_message)
```

**Migration Steps:**

1. **Create `properties/services/notification_service.py`** with rent notification logic.

2. **Create `properties/services/extra_charge_notifications.py`** with extra charge reminder logic.

3. **Create `properties/services/late_fee_notifications.py`** with late fee notification logic.

4. **Create compatibility wrappers** at old locations.

5. **Migrate call sites**:
   - `properties/signals/__init__.py`
   - `properties/utils/utils.py`
   - `core/views.py`

6. **Remove compatibility wrappers** after all call sites are migrated.

**Validation Checklist:**
- [ ] All property notification services exist in `properties/services/`
- [ ] No imports from `notification/services/rent_notify_service` remain
- [ ] No imports from `notification/services/extra_charge_reminders` remain
- [ ] No imports from `notification/services/late_fees_notify_service` remain
- [ ] All signal handlers function correctly
- [ ] All tests pass
- [ ] No DeprecationWarnings in test output

**CI Requirements:**
- ruff check passes
- mypy --strict passes
- pytest passes
- Signal handler tests pass

**Rollback Plan:**
- Revert the PR that removes compatibility wrappers
- Old import paths remain functional

**Estimated Complexity:** Medium
**Estimated Effort:** 6-8 hours

---

### PHASE 7: Assistant Merge (`smartbot` + `ai_assistant`)

**Objective:** Merge `smartbot` and `ai_assistant` into a single `assistant` app, then extract non-AI responsibilities to their domain apps.

**Duration:** 5-7 days
**Complexity:** High
**Risk:** High

**Files Involved:**

| File | Action |
|------|--------|
| `smartbot/` | RESTRUCTURE → `assistant/` |
| `ai_assistant/` | MERGE into `assistant/`, then extract non-AI files |
| `smartbot/services/leegality_service.py` | MOVE → `documents/services/leegality.py` (already done in Phase 2) |
| `smartbot/services/agreement_service.py` | MOVE → `documents/services/agreement.py` |
| `smartbot/whatsapp_service.py` | MERGE into `notification/services/whatsapp_service.py` (already done in Phase 1) |
| `smartbot/actions.py` | SPLIT — operational actions move to domain apps |
| `smartbot/cron/reminders.py` | MOVE → `properties/cron/` or `documents/cron/` |

**Preconditions:**
- Phases 1-6 complete and merged
- All duplicate code consolidated
- All call sites documented

**Dependency Validation:**
```bash
# Comprehensive import analysis
grep -r "from smartbot\|import smartbot\|from ai_assistant\|import ai_assistant" --include="*.py" .
# Expected call sites:
#   core/views.py (none)
#   properties/views/unit_views.py (none)
#   notification/services/*.py (none)
#   smartbot/ (internal imports)
#   ai_assistant/ (internal imports)
#   tests/ (test imports)
```

**Migration Steps:**

1. **Create `assistant/` app** with standard Django app structure.

2. **Move core AI files** to `assistant/`:
   - `smartbot/models.py` → `assistant/models.py`
   - `smartbot/views.py` → `assistant/views.py`
   - `smartbot/intents.py` → `assistant/intents.py`
   - `smartbot/services/gpt_services.py` → `assistant/services/llm.py`
   - `smartbot/services/chatbot_service.py` → `assistant/services/chat.py`

3. **Move non-AI files to domain apps**:
   - `smartbot/services/leegality_service.py` → `documents/services/leegality.py`
   - `smartbot/services/agreement_service.py` → `documents/services/agreement.py`
   - `smartbot/whatsapp_service.py` → merge into `notification`
   - `smartbot/actions.py` operational functions → `properties/services/`
   - `smartbot/cron/reminders.py` → `properties/cron/` or `documents/cron/`

4. **Move `ai_assistant` files**:
   - `ai_assistant/services/archive_service.py` → `properties/services/`
   - `ai_assistant/services/invoice_service.py` → `documents/services/`
   - `ai_assistant/services/unit_service.py` → `properties/services/`
   - `ai_assistant/services/finance_ai.py` → evaluate with product team
   - `ai_assistant/services/i18n_service.py` → DELETE (duplicate of Phase 3)

5. **Create compatibility wrappers** at old import locations.

6. **Migrate call sites** one-by-one.

7. **Remove compatibility wrappers** after all call sites are migrated.

8. **Delete old apps** (`smartbot/`, `ai_assistant/`) only after zero imports remain.

**Validation Checklist:**
- [ ] `assistant/` app exists with core AI functionality
- [ ] All AI models in `assistant/models.py`
- [ ] All AI views in `assistant/views.py`
- [ ] All AI services in `assistant/services/`
- [ ] No imports of `smartbot` or `ai_assistant` remain
- [ ] All tests pass
- [ ] Chatbot API functions correctly
- [ ] No DeprecationWarnings in test output

**CI Requirements:**
- ruff check passes
- mypy --strict passes
- pytest passes
- Signal handler tests pass
- API contract tests pass

**Rollback Plan:**
- Keep `smartbot/` and `ai_assistant/` with compatibility wrappers until Phase 7 is fully validated
- Revert PR that deletes old apps if issues arise

**Estimated Complexity:** High
**Estimated Effort:** 16-24 hours

---

### PHASE 8: Analytics Extraction

**Objective:** Create `analytics/` app for owner dashboard and reporting functionality.

**Duration:** 3-5 days
**Complexity:** Medium
**Risk:** Medium

**Files Involved:**

| File | Action |
|------|--------|
| `properties/views/owner_dashboard.py` | MOVE → `analytics/views/owner_dashboard.py` |
| `properties/services/unit_service.py` (analytics functions) | MOVE → `analytics/services/analytics_service.py` |
| `properties/views/property_views.py` (unit_analytics) | UPDATE import |

**Preconditions:**
- Phase 7 complete and merged
- Analytics requirements validated with product team

**Dependency Validation:**
```bash
grep -r "owner_dashboard_summary\|unit_analytics\|get_owner_analytics\|get_building_analytics" --include="*.py" .
# Expected call sites:
#   properties/views/owner_dashboard.py (source)
#   properties/views/property_views.py (imports unit_analytics)
#   properties/urls.py (URL routing)
```

**Migration Steps:**

1. **Create `analytics/` app** with standard structure.

2. **Move analytics code** to `analytics/`.

3. **Create compatibility wrappers** at old locations.

4. **Update URL routing** in `properties/urls.py` to point to new views.

5. **Migrate call sites**.

6. **Remove compatibility wrappers** after all call sites are migrated.

**Validation Checklist:**
- [ ] `analytics/` app exists
- [ ] All analytics endpoints function correctly
- [ ] Owner dashboard returns correct data
- [ ] Unit analytics returns correct data
- [ ] All tests pass
- [ ] No DeprecationWarnings in test output

**CI Requirements:**
- ruff check passes
- mypy --strict passes
- pytest passes
- API contract tests pass

**Rollback Plan:**
- Revert the PR that removes compatibility wrappers
- Old import paths remain functional

**Estimated Complexity:** Medium
**Estimated Effort:** 6-8 hours

---

### PHASE 9: Payments Extraction (Stage 2)

**Objective:** Extract payment processing into `payments/` app when Stage 2 payment gateways are activated.

**Duration:** 5-7 days
**Complexity:** High
**Risk:** High

**Files Involved:**

| File | Action |
|------|--------|
| `rentsecure_be/services/razorpay_service.py` | MOVE → `payments/adapters/razorpay.py` |
| `rentsecure_be/services/cashfree_service.py` | MOVE → `payments/adapters/cashfree.py` |
| `rentsecure_be/utils/cashfree_payout.py` | MOVE → `payments/adapters/cashfree_payout.py` |
| `core/views.py` | UPDATE imports |
| `properties/views/rent_record_views.py` | UPDATE imports |
| `smartbot/actions.py` | UPDATE imports |

**Preconditions:**
- Phases 1-8 complete and merged
- Stage 2 payment gateway activation approved
- Feature flags `ENABLE_RAZORPAY` and `ENABLE_CASHFREE` remain `False` during migration

**Dependency Validation:**
```bash
grep -r "razorpay_service\|cashfree_service\|cashfree_payout\|create_payment_link\|process_rent_payout\|add_beneficiary\|make_payout" --include="*.py" .
# Expected call sites:
#   rentsecure_be/services/razorpay_service.py (source)
#   rentsecure_be/services/cashfree_service.py (source)
#   rentsecure_be/utils/cashfree_payout.py (source)
#   core/views.py (imports)
#   properties/views/rent_record_views.py (imports)
#   smartbot/actions.py (imports)
#   core/services/bank_details_service.py (imports)
```

**Migration Steps:**

1. **Create `payments/` app** with adapter structure.

2. **Move payment services** to `payments/adapters/`.

3. **Create compatibility wrappers** at old locations.

4. **Migrate call sites** one-by-one.

5. **Remove compatibility wrappers** after all call sites are migrated.

6. **Delete old files** only after zero imports remain.

**Validation Checklist:**
- [ ] `payments/` app exists
- [ ] All payment adapters functional
- [ ] All payment endpoints function correctly
- [ ] Webhook handlers function correctly
- [ ] All tests pass
- [ ] No DeprecationWarnings in test output

**CI Requirements:**
- ruff check passes
- mypy --strict passes
- pytest passes
- Webhook tests pass

**Rollback Plan:**
- Keep old import paths with compatibility wrappers
- Revert PR that removes wrappers if issues arise

**Estimated Complexity:** High
**Estimated Effort:** 12-16 hours

---

## 5. Compatibility Strategy

### 5.1 Compatibility Wrappers

During migration, old import locations will re-export new implementations with deprecation warnings:

```python
# old_module.py
import warnings
from new_module import OriginalClass as _OriginalClass

class OriginalClass(_OriginalClass):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        warnings.warn(
            "old_module.OriginalClass is deprecated. "
            "Use new_module.OriginalClass instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)

# For module-level functions:
def original_function(*args: Any, **kwargs: Any) -> Any:
    warnings.warn(
        "old_module.original_function is deprecated. "
        "Use new_module.original_function instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from new_module import original_function as _original_function
    return _original_function(*args, **kwargs)
```

### 5.2 Deprecated Modules

Modules that are deprecated but still functional will:
1. Re-export the new implementation
2. Emit `DeprecationWarning` on import
3. Remain in the codebase until all call sites are migrated
4. Be removed only after zero imports remain (verified by `grep`)

### 5.3 Adapter Pattern

For services with multiple implementations (e.g., WhatsApp, Leegality):

```python
# notification/services/whatsapp_adapter.py
class WhatsAppAdapter:
    def send_message(self, to: str, message: str) -> bool:
        ...

    def send_audio(self, to: str, audio_path: str) -> bool:
        ...
```

This allows:
- Multiple implementations to coexist
- Runtime selection via feature flags
- Easy testing with mock adapters
- Clean separation of interface and implementation

### 5.4 Alias Imports

For moved modules, maintain alias imports:

```python
# smartbot/services/leegality_service.py (deprecated)
from documents.services.leegality import initiate_signature
from documents.services.leegality import check_signature_status

__all__ = ["initiate_signature", "check_signature_status"]
```

### 5.5 Staged Deprecation

1. **Stage 1**: Add compatibility wrapper, emit `DeprecationWarning`
2. **Stage 2**: Migrate all internal call sites
3. **Stage 3**: Update external documentation
4. **Stage 4**: Remove wrapper after one release cycle with no warnings

---

## 6. Testing Strategy

### 6.1 Unit Tests

For each migrated file:
- Run existing unit tests to verify behavior preservation
- Add tests for compatibility wrappers
- Add tests for deprecation warnings
- Verify no regressions in edge cases

**Command:**
```bash
pytest path/to/test_file.py -v
```

### 6.2 Integration Tests

For each phase:
- Test the full request/response cycle for affected endpoints
- Test signal handlers with migrated services
- Test management commands with migrated implementations
- Test webhook handlers with migrated services

**Command:**
```bash
pytest tests/test_api_contracts.py -v
pytest tests/test_properties_hypothesis.py -v
```

### 6.3 Regression Tests

For each phase:
- Run the full test suite before and after
- Compare coverage reports
- Verify no new failures

**Command:**
```bash
pytest --cov=rentsecure_be --cov=core --cov=properties --cov=notification \
       --cov=documents --cov=finance --cov=referral_and_earn \
       --cov-fail-under=90
```

### 6.4 API Tests

For each phase:
- Verify all API endpoints return expected responses
- Verify no 500 errors
- Verify no 404 errors for existing endpoints
- Verify authentication and permissions

**Command:**
```bash
pytest properties/tests/test_property_views.py -v
pytest notification/tests/test_notification_views.py -v
```

### 6.5 Smoke Tests

For each phase:
- Start Django development server
- Hit key endpoints manually
- Verify no import errors in logs
- Verify no signal registration errors

**Command:**
```bash
python manage.py check
python manage.py runserver
# Manual verification of key endpoints
```

### 6.6 Manual Verification

For each phase:
- Verify PDF generation produces valid PDFs
- Verify WhatsApp messages are sent correctly
- Verify Leegality signature flow works
- Verify notifications are delivered

### 6.7 CI Gates

Every PR must pass:
1. `ruff check` — zero errors
2. `mypy --strict` — zero new errors
3. `pytest` — all tests pass
4. `python manage.py check` — zero errors
5. `python manage.py makemigrations --check` — no new migrations
6. No new `DeprecationWarning` in test output

---

## 7. Rollback Strategy

### 7.1 Per-Phase Rollback

Each phase is implemented as a single PR. If issues arise:

1. **Identify the failing PR** — The phase that introduced the regression
2. **Revert the PR** — `git revert <commit-sha>`
3. **Verify restoration** — Run full test suite
4. **Diagnose** — Fix issues in a feature branch
5. **Re-apply** — Create new PR with fixes

### 7.2 Rollback Timeline

| Phase | Rollback Time | Impact |
|-------|--------------|--------|
| Phase 1 (WhatsApp) | < 5 minutes | No impact — old implementation still works |
| Phase 2 (Leegality) | < 5 minutes | No impact — old implementation still works |
| Phase 3 (i18n) | < 5 minutes | No impact — old implementation still works |
| Phase 4 (PDF) | < 10 minutes | No impact — old implementation still works |
| Phase 5 (Owner Reporting) | < 5 minutes | No impact — old import path works |
| Phase 6 (Property Notifications) | < 10 minutes | No impact — old import paths work |
| Phase 7 (Assistant Merge) | < 15 minutes | No impact — compatibility wrappers work |
| Phase 8 (Analytics) | < 10 minutes | No impact — old import paths work |
| Phase 9 (Payments) | < 15 minutes | No impact — old import paths work |

### 7.3 Rollback Prerequisites

Before starting any phase:
1. Ensure all changes are in a single, revertible commit
2. Tag the commit before starting the phase
3. Verify the tag can be checked out and tests pass
4. Document the exact rollback command

### 7.4 Emergency Rollback

If a phase causes production issues:
1. Immediately revert the phase PR
2. Deploy the reverted code
3. Investigate in a feature branch
4. Re-apply only after root cause is fixed

---

## 8. Definition of Done

A phase is considered **complete** only when ALL of the following are true:

1. **Code changes merged** — PR is merged to main
2. **All tests pass** — Full test suite passes on CI
3. **No deprecation warnings** — `DeprecationWarning` count is zero
4. **No new lint errors** — `ruff check` passes
5. **No new type errors** — `mypy --strict` passes
6. **Django check passes** — `python manage.py check` returns zero errors
7. **No broken imports** — All imports resolve correctly
8. **Documentation updated** — Architecture docs reflect the changes
9. **Compatibility wrappers removed** — Old import paths no longer exist
10. **Zero imports of old paths** — `grep` confirms no remaining imports

### 8.1 Phase Sign-Off

Each phase requires sign-off from:
1. **Backend Lead** — Code review and architecture approval
2. **QA Lead** — Test plan approval and regression testing
3. **DevOps Lead** — CI/CD pipeline approval

---

## 9. Risks

### 9.1 High Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Circular dependency introduced during move | Medium | High | Run import-linter after each phase; validate with mypy |
| Signal handler breaks after service move | Medium | High | Test signal handlers explicitly; maintain compatibility wrappers |
| Production outage due to import error | Low | High | Gradual roll-out with compatibility wrappers; rollback plan tested |
| Data loss during PDF consolidation | Low | High | No model changes; PDF generation is stateless |

### 9.2 Medium Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Deprecation warnings flood test output | Medium | Medium | Suppress warnings in tests during migration; remove suppression after |
| Call sites missed during migration | Medium | Medium | Use `grep` to find all call sites; automated import checking |
| mypy errors introduced by type changes | Medium | Medium | Run mypy after each file move; fix types immediately |
| Feature flag interactions break | Low | Medium | Test with both flag states; maintain unconditional imports until Phase 9 |
| Celery tasks reference moved modules | Low | Medium | Document all Celery tasks; validate task execution after each phase |

### 9.3 Low Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Test flakiness during migration | High | Low | Run tests multiple times; use `pytest --count=3` |
| Documentation out of sync | Medium | Low | Update docs in same PR as code changes |
| Git history loss | Low | Low | Use `git mv` for file moves |
| Merge conflicts | Medium | Low | Small, focused PRs; rebase frequently |

---

## 10. Success Metrics

### 10.1 Architecture Metrics

| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| Duplicate WhatsApp implementations | 2 | 0 | `grep -r "send_whatsapp_message" notification/` |
| Duplicate Leegality implementations | 2 | 0 | `grep -r "leegality_service" --include="*.py" .` |
| Duplicate i18n implementations | 2 | 0 | `grep -r "i18n_service" --include="*.py" .` |
| PDF generation locations | 5+ | 1 | Count files with `weasyprint.HTML` |
| Cross-context imports (core → properties) | Multiple | 0 | import-linter |
| Circular dependencies | 0 | 0 | import-linter |
| Property notifications in `notification/` | 4 files | 0 | Count in `notification/services/` |

### 10.2 Quality Metrics

| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| Test coverage | ≥90% | ≥90% | `pytest --cov` |
| mypy strict errors | Unknown | 0 | `mypy --strict` |
| ruff errors | Unknown | 0 | `ruff check` |
| DeprecationWarning count | 0 | 0 | `pytest -W error::DeprecationWarning` |
| Django system check errors | 0 | 0 | `python manage.py check` |
| CI pipeline duration | Current | < 20 min | GitHub Actions |
| Import resolution errors | 0 | 0 | `python -c "import django; django.setup()"` |

### 10.3 Process Metrics

| Metric | Target |
|--------|--------|
| PRs per phase | 1 |
| Tests added per phase | ≥ 2 |
| Rollback drills completed | 1 per phase |
| Documentation updates per phase | ≥ 1 |

---

## 11. Final Migration Timeline

### Recommended Execution Order

| Phase | Description | Duration | Dependencies | Complexity |
|-------|-------------|----------|--------------|------------|
| **Phase 0** | Pre-Migration Preparation | 1-2 days | None | Low |
| **Phase 1** | WhatsApp Consolidation | 1-2 days | Phase 0 | Low |
| **Phase 2** | Leegality Consolidation | 2-3 days | Phase 1 | Medium |
| **Phase 3** | i18n Extraction | 1-2 days | Phase 2 | Low |
| **Phase 4** | PDF Consolidation | 3-5 days | Phase 3 | Medium |
| **Phase 5** | Owner Reporting Relocation | 1-2 days | Phase 4 | Low |
| **Phase 6** | Property Notification Relocation | 3-5 days | Phase 5 | Medium |
| **Phase 7** | Assistant Merge | 5-7 days | Phase 6 | High |
| **Phase 8** | Analytics Extraction | 3-5 days | Phase 7 | Medium |
| **Phase 9** | Payments Extraction | 5-7 days | Phase 8 | High |

### Timeline Summary

| Week | Phases | Milestone |
|------|--------|-----------|
| Week 1 | Phase 0, Phase 1 | Preparation complete; WhatsApp consolidated |
| Week 2 | Phase 2, Phase 3 | Leegality consolidated; i18n extracted |
| Week 3-4 | Phase 4 | PDF generation consolidated |
| Week 5 | Phase 5 | Owner reporting relocated |
| Week 6-7 | Phase 6 | Property notifications relocated |
| Week 8-10 | Phase 7 | Assistant merge complete |
| Week 11-12 | Phase 8 | Analytics extracted |
| Week 13-14 | Phase 9 | Payments extracted (Stage 2) |

### Critical Path

```
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4
                                    ↓
Phase 5 → Phase 6 → Phase 7 → Phase 8 → Phase 9
```

### Buffer Time

- **Recommended buffer:** 2 weeks between phases
- **Total estimated duration:** 14-20 weeks (3.5-5 months)
- **Suggested cadence:** One phase per 1-2 week sprint

---

## 12. Appendices

### Appendix A: Migration Checklist Template

```markdown
## Phase N: [Name]

### Pre-Migration
- [ ] All imports documented
- [ ] All call sites identified
- [ ] Compatibility wrappers designed
- [ ] Rollback plan documented
- [ ] CI pipeline validated

### Migration
- [ ] New module created
- [ ] Implementation moved
- [ ] Compatibility wrapper added
- [ ] Call sites migrated
- [ ] Old code marked deprecated

### Validation
- [ ] All tests pass
- [ ] No new lint errors
- [ ] No new type errors
- [ ] No DeprecationWarnings
- [ ] Django check passes
- [ ] Manual verification complete

### Post-Migration
- [ ] Compatibility wrapper removed
- [ ] Old code deleted
- [ ] Documentation updated
- [ ] Architecture docs updated
- [ ] PR merged and deployed
```

### Appendix B: Import Tracking Commands

```bash
# Find all imports of a module
grep -r "from <module>" --include="*.py" .
grep -r "import <module>" --include="*.py" .

# Find all references to a function
grep -r "<function_name>" --include="*.py" .

# Find all Django registrations
grep -r "admin.site.register" --include="*.py" .
grep -r "@receiver" --include="*.py" .
grep -r "post_save\|post_delete" --include="*.py" .

# Find all URL patterns
grep -r "path(\|include(" --include="*.py" .

# Find all Celery tasks
grep -r "shared_task\|@app.task\|\.delay\|\.apply_async" --include="*.py" .

# Find all management command calls
grep -r "call_command" --include="*.py" .

# Find all feature flag checks
grep -r "ENABLE_" --include="*.py" .

# Run import-linter
lint-imports --config import-linter.ini

# Run mypy strict
mypy --strict --config-file=mypy.ini .
```

### Appendix C: Compatibility Wrapper Template

```python
"""
Compatibility wrapper for migrated module.

This module provides backward compatibility during migration.
All imports will be removed after all call sites are migrated.

DEPRECATED: Use <new_module> instead.
"""

import warnings
from typing import Any

# Re-export all public names from new module
from new_module import (
    ClassA,
    ClassB,
    function_a,
    function_b,
)

__all__ = [
    "ClassA",
    "ClassB",
    "function_a",
    "function_b",
]

# Emit deprecation warning on import
warnings.warn(
    "old_module is deprecated. Use new_module instead.",
    DeprecationWarning,
    stacklevel=2,
)
```

---

## 13. Conclusion

This migration plan provides a **safe, incremental path** from the current rapid-development architecture to a clean, bounded-context architecture.

**Key principles:**
1. **Zero breaking changes** — All migrations maintain backward compatibility
2. **One phase at a time** — Each phase is independently reviewable and reversible
3. **CI is non-negotiable** — No phase is complete until CI is green
4. **Documentation first** — Every change is documented before implementation
5. **Rollback always possible** — Every phase can be reverted in minutes

**Next steps:**
1. Review this migration plan with the team
2. Obtain approval for Phase 0
3. Execute Phase 0 to establish validation infrastructure
4. Begin Phase 1 after Phase 0 is complete

**This plan is living documentation** — It will be updated after each phase based on lessons learned and changing requirements.

---

*Report generated by Kilo Migration Planning Phase. This document is planning only. No production code was modified.*
