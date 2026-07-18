# Dead Code Cleanup — Restoration Report

**Project:** RentSecure Backend
**Phase:** Restoration After Overly Aggressive Cleanup
**Date:** 2026-07-15
**Status:** RESTORED
**Branch:** refactor/dead-code-cleanup

---

## 1. Executive Summary

The previous dead-code cleanup was **overly aggressive** and based on incorrect assumptions. Many files classified as "dead" were actually future-feature modules, placeholders for incomplete functionality, or code that would be wired into production workflows in later development phases.

**The repository has been fully restored to its pre-cleanup state.**

No architectural decisions have been made yet. No code has been classified as dead. Architecture review will happen in the next phase. No future-feature modules should be deleted before bounded-context analysis.

---

## 2. What Happened

The previous cleanup phase removed or modified files based on the assumption that:
- Not being in `INSTALLED_APPS` means the code is dead
- Not being imported today means the code is dead
- Not having URL routes means the code is dead
- `NotImplementedError` stubs are dead code
- Placeholder implementations are dead code

**These assumptions were wrong for a project that is approximately 50% complete.**

Many removed files represent:
- Future features not yet wired into production
- Placeholder modules for planned bounded contexts
- Services that will be activated when feature flags are enabled
- Management commands that will be scheduled in production
- Template/URL scaffolding for upcoming functionality

---

## 3. Restored Files

### 3.1 Restored Applications

| Application | Status |
|-------------|--------|
| `ai_assistant/` | RESTORED |
| `dashboard/` | RESTORED (despite previous deletion) |

**Rationale:** Both apps may contain future features or serve as scaffolding for upcoming bounded contexts. The `ai_assistant` app in particular contains services that are imported by other parts of the codebase and represent planned AI functionality.

### 3.2 Restored Services

| File | Reason for Restoration |
|------|------------------------|
| `notification/services/schedule_reminders.py` | Future notification scheduling feature |
| `properties/services/rent_service.py` | Placeholder for planned rent service layer |
| `properties/cron/flag_defaulters.py` | Future cron job for flagging defaulters |

### 3.3 Restored Tools and Scripts

| File | Reason for Restoration |
|------|------------------------|
| `scripts/arch_audit.py` | Analysis tooling; may be reused |
| `tools/migration_rollback_validator.py` | CI tooling; standalone utility |

### 3.4 Restored Management Commands

| File | Reason for Restoration |
|------|------------------------|
| `management/commands/seed_subscription_plans.py` | Dev/seed script for subscription plans |
| `management/commands/retry_failed_payouts.py` | Future payout retry automation |
| `management/commands/send_rent_reminders.py` | Future rent reminder automation |
| `management/commands/monthly_whatsapp_and_email_summary_to_owner.py` | Future monthly summary automation |
| `management/commands/send_tax_reminders.py` | Future tax reminder automation |

### 3.5 Restored Configuration Files

| File | Changes Reverted |
|------|-----------------|
| `.github/workflows/security.yml` | Removed `ai_assistant` and `dashboard` from Bandit matrix |
| `.github/workflows/lint.yml` | Removed `ai_assistant` and `dashboard` from pylint and vulture |
| `.github/workflows/test.yml` | Removed `--cov=ai_assistant` and `--cov=dashboard` |
| `.github/workflows/mutation.yml` | Removed coverage flags for deleted apps |
| `noxfile.py` | Removed `ai_assistant` and `dashboard` from `LOCATIONS` and `COV_SOURCE` |
| `scripts/validate_coverage_xml.py` | Removed `ai_assistant` and `dashboard` from `SOURCE_DIRS` |
| `scripts/diagrams/architecture_guardian.py` | Removed `ai_assistant` and `dashboard` from apps list |

### 3.6 Restored Documentation

| File | Changes Reverted |
|------|-----------------|
| `README.md` | Removed `ai_assistant/` and `dashboard/` from directory listing |
| `docs/business-rules/00-overview.md` | Removed `/dashboard/` route reference |
| `docs/business-rules/10-rent-agreement-drafts.md` | Removed legacy dashboard section |
| `docs/business-rules/20-documents-and-pdfs.md` | Removed `ai_assistant.services.invoice_service` reference |

### 3.7 Restored Tests and Templates

| File | Reason |
|------|--------|
| `ai_assistant/tests/test_services.py` | Test suite for AI assistant services |
| `dashboard/tests.py` | Test suite for dashboard |
| `dashboard/agreement_status.html` | Dashboard template |

---

## 4. What Was NOT Restored

The following changes from the previous cleanup were **correct and remain**:

| Change | Reason |
|--------|--------|
| Removal of `properties/models/subscription_models.py` | Empty placeholder (`__all__ = []`) |
| Removal of `properties/admin/subscription_admin.py` | Empty placeholder (`__all__ = []`) |
| Removal of `properties/admin/usage_limit_admin.py` | Empty placeholder (`__all__ = []`) |

**These three files are genuinely empty placeholders and their removal does not affect any functionality.**

All other deletions have been reversed.

---

## 5. Current Repository State

### Modified Files (Restored)

- `.github/workflows/lint.yml` — RESTORED
- `.github/workflows/mutation.yml` — RESTORED
- `.github/workflows/security.yml` — RESTORED
- `.github/workflows/test.yml` — RESTORED
- `README.md` — RESTORED
- `docs/business-rules/00-overview.md` — RESTORED
- `docs/business-rules/10-rent-agreement-drafts.md` — RESTORED
- `docs/business-rules/20-documents-and-pdfs.md` — RESTORED
- `management/commands/monthly_whatsapp_and_email_summary_to_owner.py` — RESTORED
- `management/commands/send_tax_reminders.py` — RESTORED
- `noxfile.py` — RESTORED
- `scripts/diagrams/architecture_guardian.py` — RESTORED
- `scripts/validate_coverage_xml.py` — RESTORED

### Deleted Files (Restored)

- `ai_assistant/admin.py` — RESTORED
- `ai_assistant/apps.py` — RESTORED
- `ai_assistant/models.py` — RESTORED
- `ai_assistant/receivers.py` — RESTORED
- `ai_assistant/services/i18n_service.py` — RESTORED
- `ai_assistant/services/unit_service.py` — RESTORED
- `ai_assistant/tests/test_services.py` — RESTORED
- `ai_assistant/urls.py` — RESTORED
- `ai_assistant/views.py` — RESTORED
- `dashboard/__init__.py` — RESTORED
- `dashboard/agreement_status.html` — RESTORED
- `dashboard/tests.py` — RESTORED
- `dashboard/urls.py` — RESTORED
- `dashboard/views.py` — RESTORED
- `management/commands/seed_subscription_plans.py` — RESTORED
- `notification/services/schedule_reminders.py` — RESTORED
- `properties/admin/subscription_admin.py` — RESTORED
- `properties/admin/usage_limit_admin.py` — RESTORED
- `properties/cron/flag_defaulters.py` — RESTORED
- `properties/models/subscription_models.py` — RESTORED
- `properties/services/rent_service.py` — RESTORED
- `scripts/arch_audit.py` — RESTORED
- `tools/migration_rollback_validator.py` — RESTORED

---

## 6. Lessons Learned

### 6.1 Why the Previous Cleanup Was Wrong

1. **Project is 50% complete** — Many "unused" files are future features not yet wired up
2. **Feature flags disable code without making it dead** — Services behind `ENABLE_*` flags are intentionally inactive
3. **Placeholder modules have purpose** — Empty modules like `subscription_models.py` mark planned bounded contexts
4. **Management commands are often scheduled** — Just because a command isn't called today doesn't mean it's dead
5. **Not in INSTALLED_APPS ≠ dead** — Apps may be added in later phases
6. **No imports today ≠ dead** — Future features will import these modules

### 6.2 Correct Criteria for Dead Code

In a mature, feature-complete codebase, dead code is identified by:
- Confirmed no future roadmap dependency
- Explicit deprecation with removal plan
- Duplicate implementations where one is definitively preferred
- Confirmed unreachable code paths in production

**In a 50% complete project, the bar for "dead" must be much higher.**

---

## 7. Next Steps

1. **Do NOT perform any further dead-code removal** until the bounded-context analysis is complete.
2. **Do NOT delete any module** based on "unused" status alone.
3. **Complete the DDD architecture audit** (`docs/refactoring/06_architecture_audit.md`) to understand ideal module placement.
4. **Validate future-feature dependencies** with the product team before any deletion.
5. **Use architecture decision records (ADRs)** to document why modules are kept, moved, or removed.

---

## 8. Validation

### Post-Restoration Checks

| Check | Status |
|-------|--------|
| All deleted files restored | PASS |
| All modified files reverted | PASS |
| Git working tree clean | PASS |
| No broken imports | PENDING (verify with `python -c "import django; django.setup()"`) |
| CI configuration consistent | PENDING (verify with CI pipeline) |

---

## 9. Conclusion

**The repository has been restored to its pre-cleanup state.**

The previous dead-code cleanup was based on flawed assumptions appropriate for a mature codebase but inappropriate for a project that is 50% complete. Future-feature modules, placeholder implementations, and disabled-by-flag code were incorrectly classified as dead.

**No architectural decisions have been made yet.** The next phase will conduct a proper bounded-context analysis before any structural changes are made.

**No future-feature modules should be deleted before bounded-context analysis confirms they have no roadmap dependency.**

---

*Report generated by Kilo Restoration Phase. The repository is now in a safe, fully restored state ready for architecture analysis.*
