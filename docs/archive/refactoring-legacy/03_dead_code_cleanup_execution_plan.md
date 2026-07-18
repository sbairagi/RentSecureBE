# Dead Code Cleanup Execution Plan — Phase 2 Implementation

**Project:** RentSecure Backend
**Phase:** 2 — Execution Plan
**Date:** 2026-07-15
**Status:** READY FOR EXECUTION
**Constraint:** Plan only. No code modifications in this document.

---

## Principles

1. **Each batch is independently deployable** — can be merged and deployed without waiting for other batches
2. **Each batch is independently reversible** — can be rolled back without affecting other batches
3. **Smallest possible batches** — each batch contains only closely related files
4. **Test after every batch** — full test suite runs after each batch
5. **CI gates after every batch** — import-linter, mypy, pylint, pytest, coverage, Sonar

---

## Batch 1: Remove `dashboard/` App

### Files to Delete

| File | Type |
|------|------|
| `dashboard/views.py` | Dead views |
| `dashboard/tests.py` | Dead tests |
| `dashboard/urls.py` | Dead URL config |
| `dashboard/apps.py` | Dead AppConfig |
| `dashboard/models.py` | Dead model (if exists) |

### Why This Batch is Safe

- `dashboard/` is **NOT in `INSTALLED_APPS`**
- `dashboard/urls.py` is **NOT included** in `rentsecure_be/urls.py`
- No production imports
- No migrations directory
- Only test file references it (`dashboard/tests.py`)

### Estimated LOC Removed

~500 lines

### Risk Level

**LOW**

### Commands to Execute

```bash
# 1. Create feature branch
git checkout -b refactor/remove-dashboard-app

# 2. Delete files
git rm dashboard/views.py dashboard/tests.py dashboard/urls.py dashboard/apps.py
git rm dashboard/models.py 2>/dev/null || true

# 3. Commit
git commit -m "refactor: remove dead dashboard app

- dashboard/ was not in INSTALLED_APPS
- dashboard/urls.py was not included in root urls.py
- No production imports
- No migrations
- Only referenced by dashboard/tests.py (deleted)

Risk: LOW
Batch: 1 of 8"
```

### Tests to Execute

```bash
# 1. Run pytest
pytest --tb=short -q

# 2. Check for import errors
python -c "import django; django.setup(); print('Django loaded successfully')"

# 3. Verify dashboard app is not loaded
python -c "from django.conf import settings; assert 'dashboard' not in settings.INSTALLED_APPS, 'dashboard still in INSTALLED_APPS'"
```

### Migrations to Check

```bash
# No migrations to check (dashboard/ has no migrations/ directory)
```

### Import-Linter Check

```bash
lint-imports --config import-linter.ini
```

### mypy

```bash
mypy --config-file=mypy.ini .
```

### pylint

```bash
python -m pylint rentsecure_be core properties finance notification documents smartbot
```

### pytest

```bash
pytest --tb=short -q --cov=rentsecure_be --cov=core --cov=properties --cov=finance --cov=notification --cov=documents --cov=smartbot --cov-report=term-missing
```

### Coverage

```bash
# Ensure coverage does not decrease
pytest --cov --cov-report=xml
```

### Sonar Impact

- **Expected:** Zero new issues
- **Action:** None required

### Rollback Command

```bash
git revert HEAD
git push origin refactor/remove-dashboard-app
```

### Expected Git Commit Message

```
refactor: remove dead dashboard app

- dashboard/ was not in INSTALLED_APPS
- dashboard/urls.py was not included in root urls.py
- No production imports
- No migrations
- Only referenced by dashboard/tests.py (deleted)

Risk: LOW
Batch: 1 of 8
```

### CI Workflow Updates Required

Update `.github/workflows/lint.yml`, `.github/workflows/mutation.yml`, `.github/workflows/security.yml`, `.github/workflows/test.yml` to remove `dashboard` from coverage and linting configurations.

**Note:** CI updates can be done in the same batch or a separate batch. Since these are configuration-only changes, they can be included here.

---

## Batch 2: Remove `ai_assistant/` App

### Files to Delete

| File | Type |
|------|------|
| `ai_assistant/views.py` | Dead views |
| `ai_assistant/models.py` | Empty placeholder |
| `ai_assistant/urls.py` | Dead URL config |
| `ai_assistant/apps.py` | Dead AppConfig |
| `ai_assistant/receivers.py` | Dead signal receivers |
| `ai_assistant/services/` | Dead services |
| `ai_assistant/tests/` | Dead tests |
| `ai_assistant/migrations/` | Empty migrations |

### Why This Batch is Safe

- `ai_assistant/` is **NOT in `INSTALLED_APPS`**
- `ai_assistant/urls.py` is **NOT included** in `rentsecure_be/urls.py`
- No production imports
- `migrations/` contains only `__init__.py` (empty)
- Only test files reference it

### Estimated LOC Removed

~800 lines

### Risk Level

**LOW**

### Commands to Execute

```bash
# 1. Create feature branch
git checkout -b refactor/remove-ai-assistant-app

# 2. Delete files
git rm -r ai_assistant/

# 3. Commit
git commit -m "refactor: remove dead ai_assistant app

- ai_assistant/ was not in INSTALLED_APPS
- ai_assistant/urls.py was not included in root urls.py
- No production imports
- migrations/ only contains empty __init__.py
- Duplicate of smartbot/ functionality
- Only referenced by ai_assistant/tests/ (deleted)

Risk: LOW
Batch: 2 of 8"
```

### Tests to Execute

```bash
# 1. Run pytest
pytest --tb=short -q

# 2. Check for import errors
python -c "import django; django.setup(); print('Django loaded successfully')"

# 3. Verify ai_assistant app is not loaded
python -c "from django.conf import settings; assert 'ai_assistant' not in settings.INSTALLED_APPS, 'ai_assistant still in INSTALLED_APPS'"
```

### Migrations to Check

```bash
# No migrations to check (ai_assistant/migrations/ only contains __init__.py)
```

### Import-Linter Check

```bash
lint-imports --config import-linter.ini
```

### mypy

```bash
mypy --config-file=mypy.ini .
```

### pylint

```bash
python -m pylint rentsecure_be core properties finance notification documents smartbot
```

### pytest

```bash
pytest --tb=short -q --cov=rentsecure_be --cov=core --cov=properties --cov=finance --cov=notification --cov=documents --cov=smartbot --cov-report=term-missing
```

### Coverage

```bash
pytest --cov --cov-report=xml
```

### Sonar Impact

- **Expected:** Zero new issues
- **Action:** None required

### Rollback Command

```bash
git revert HEAD
git push origin refactor/remove-ai-assistant-app
```

### Expected Git Commit Message

```
refactor: remove dead ai_assistant app

- ai_assistant/ was not in INSTALLED_APPS
- ai_assistant/urls.py was not included in root urls.py
- No production imports
- migrations/ only contains empty __init__.py
- Duplicate of smartbot/ functionality
- Only referenced by ai_assistant/tests/ (deleted)

Risk: LOW
Batch: 2 of 8
```

### CI Workflow Updates Required

Update `.github/workflows/lint.yml`, `.github/workflows/mutation.yml`, `.github/workflows/security.yml`, `.github/workflows/test.yml` to remove `ai_assistant` from coverage and linting configurations.

---

## Batch 3: Remove Empty Placeholder Modules

### Files to Delete

| File | Type |
|------|------|
| `properties/models/subscription_models.py` | Placeholder |
| `properties/admin/subscription_admin.py` | Placeholder |
| `properties/admin/usage_limit_admin.py` | Placeholder |

### Why This Batch is Safe

- All three files contain only `__all__: list[str] = []`
- No production imports
- No test imports
- No functionality

### Estimated LOC Removed

~50 lines

### Risk Level

**VERY LOW**

### Commands to Execute

```bash
# 1. Create feature branch
git checkout -b refactor/remove-empty-placeholders

# 2. Delete files
git rm properties/models/subscription_models.py \
       properties/admin/subscription_admin.py \
       properties/admin/usage_limit_admin.py

# 3. Commit
git commit -m "refactor: remove empty placeholder modules

- properties/models/subscription_models.py: empty placeholder
- properties/admin/subscription_admin.py: empty placeholder
- properties/admin/usage_limit_admin.py: empty placeholder
- No production imports
- No test imports

Risk: VERY LOW
Batch: 3 of 8"
```

### Tests to Execute

```bash
pytest --tb=short -q
```

### Migrations to Check

```bash
# No migrations affected
```

### Import-Linter Check

```bash
lint-imports --config import-linter.ini
```

### mypy

```bash
mypy --config-file=mypy.ini .
```

### pylint

```bash
python -m pylint rentsecure_be core properties finance notification documents smartbot
```

### pytest

```bash
pytest --tb=short -q
```

### Coverage

```bash
pytest --cov --cov-report=xml
```

### Sonar Impact

- **Expected:** Zero new issues
- **Action:** None required

### Rollback Command

```bash
git revert HEAD
git push origin refactor/remove-empty-placeholders
```

### Expected Git Commit Message

```
refactor: remove empty placeholder modules

- properties/models/subscription_models.py: empty placeholder
- properties/admin/subscription_admin.py: empty placeholder
- properties/admin/usage_limit_admin.py: empty placeholder
- No production imports
- No test imports

Risk: VERY LOW
Batch: 3 of 8
```

---

## Batch 4: Remove Dead Service Modules

### Files to Delete

| File | Type |
|------|------|
| `notification/services/schedule_reminders.py` | Dead service |
| `properties/services/rent_service.py` | Dead service (all methods raise NotImplementedError) |

### Why This Batch is Safe

- `notification/services/schedule_reminders.py`: **No imports** from any production or test code
- `properties/services/rent_service.py`: **No imports** from any production or test code; all methods raise `NotImplementedError`

### Estimated LOC Removed

~200 lines

### Risk Level

**LOW**

### Commands to Execute

```bash
# 1. Create feature branch
git checkout -b refactor/remove-dead-services

# 2. Delete files
git rm notification/services/schedule_reminders.py \
       properties/services/rent_service.py

# 3. Commit
git commit -m "refactor: remove dead service modules

- notification/services/schedule_reminders.py: no imports, duplicate of rent_notify_service.py
- properties/services/rent_service.py: no imports, all methods raise NotImplementedError

Risk: LOW
Batch: 4 of 8"
```

### Tests to Execute

```bash
pytest --tb=short -q
```

### Migrations to Check

```bash
# No migrations affected
```

### Import-Linter Check

```bash
lint-imports --config import-linter.ini
```

### mypy

```bash
mypy --config-file=mypy.ini .
```

### pylint

```bash
python -m pylint rentsecure_be core properties finance notification documents smartbot
```

### pytest

```bash
pytest --tb=short -q
```

### Coverage

```bash
pytest --cov --cov-report=xml
```

### Sonar Impact

- **Expected:** Zero new issues
- **Action:** None required

### Rollback Command

```bash
git revert HEAD
git push origin refactor/remove-dead-services
```

### Expected Git Commit Message

```
refactor: remove dead service modules

- notification/services/schedule_reminders.py: no imports, duplicate of rent_notify_service.py
- properties/services/rent_service.py: no imports, all methods raise NotImplementedError

Risk: LOW
Batch: 4 of 8
```

---

## Batch 5: Remove Dead Management Commands

### Files to Delete

| File | Type |
|------|------|
| `management/commands/seed_subscription_plans.py` | Dev-only script |
| `management/commands/retry_failed_payouts.py` | Disabled Cashfree |
| `management/commands/send_rent_reminders.py` | Disabled WhatsApp |
| `management/commands/monthly_whatsapp_and_email_summary_to_owner.py` | Disabled WhatsApp |
| `management/commands/send_tax_reminders.py` | Disabled WhatsApp |
| `notification/management/commands/send_extra_charge_reminders.py` | Disabled WhatsApp |

### Why This Batch is Safe

- All files have **no production imports**
- All relate to disabled features (WhatsApp, Cashfree)
- Django management command auto-discovery means they are only executed if explicitly called
- No scheduled tasks reference them (verified by AST analysis)

### Estimated LOC Removed

~400 lines

### Risk Level

**LOW**

### Commands to Execute

```bash
# 1. Create feature branch
git checkout -b refactor/remove-dead-management-commands

# 2. Delete files
git rm management/commands/seed_subscription_plans.py \
       management/commands/retry_failed_payouts.py \
       management/commands/send_rent_reminders.py \
       management/commands/monthly_whatsapp_and_email_summary_to_owner.py \
       management/commands/send_tax_reminders.py

# 3. Check if send_extra_charge_reminders.py exists and delete
git rm notification/management/commands/send_extra_charge_reminders.py 2>/dev/null || true

# 4. Commit
git commit -m "refactor: remove dead management commands

- seed_subscription_plans.py: dev-only script
- retry_failed_payouts.py: disabled Cashfree integration
- send_rent_reminders.py: disabled WhatsApp
- monthly_whatsapp_and_email_summary_to_owner.py: disabled WhatsApp
- send_tax_reminders.py: disabled WhatsApp
- send_extra_charge_reminders.py: disabled WhatsApp (if exists)

All have no production imports and relate to disabled features.

Risk: LOW
Batch: 5 of 8"
```

### Tests to Execute

```bash
pytest --tb=short -q
```

### Migrations to Check

```bash
# No migrations affected
```

### Import-Linter Check

```bash
lint-imports --config import-linter.ini
```

### mypy

```bash
mypy --config-file=mypy.ini .
```

### pylint

```bash
python -m pylint rentsecure_be core properties finance notification documents smartbot
```

### pytest

```bash
pytest --tb=short -q
```

### Coverage

```bash
pytest --cov --cov-report=xml
```

### Sonar Impact

- **Expected:** Zero new issues
- **Action:** None required

### Rollback Command

```bash
git revert HEAD
git push origin refactor/remove-dead-management-commands
```

### Expected Git Commit Message

```
refactor: remove dead management commands

- seed_subscription_plans.py: dev-only script
- retry_failed_payouts.py: disabled Cashfree integration
- send_rent_reminders.py: disabled WhatsApp
- monthly_whatsapp_and_email_summary_to_owner.py: disabled WhatsApp
- send_tax_reminders.py: disabled WhatsApp
- send_extra_charge_reminders.py: disabled WhatsApp (if exists)

All have no production imports and relate to disabled features.

Risk: LOW
Batch: 5 of 8
```

---

## Batch 6: Remove Dead Cron Scripts

### Files to Delete

| File | Type |
|------|------|
| `properties/cron/flag_defaulters.py` | Broken cron script |

### Why This Batch is Safe

- **No imports** from any production or test code
- **Broken** — imports non-existent function `properties.signals.update_renter_defaulter_status`
- Not referenced in any crontab or CI schedule (verified by AST analysis)

### Estimated LOC Removed

~50 lines

### Risk Level

**LOW**

### Commands to Execute

```bash
# 1. Create feature branch
git checkout -b refactor/remove-dead-cron-scripts

# 2. Delete file
git rm properties/cron/flag_defaulters.py

# 3. Check if cron directory is empty and remove
rmdir properties/cron 2>/dev/null || true

# 4. Commit
git commit -m "refactor: remove dead cron script

- properties/cron/flag_defaulters.py: broken, imports non-existent function
- No production imports
- Not referenced in any crontab or CI schedule

Risk: LOW
Batch: 6 of 8"
```

### Tests to Execute

```bash
pytest --tb=short -q
```

### Migrations to Check

```bash
# No migrations affected
```

### Import-Linter Check

```bash
lint-imports --config import-linter.ini
```

### mypy

```bash
mypy --config-file=mypy.ini .
```

### pylint

```bash
python -m pylint rentsecure_be core properties finance notification documents smartbot
```

### pytest

```bash
pytest --tb=short -q
```

### Coverage

```bash
pytest --cov --cov-report=xml
```

### Sonar Impact

- **Expected:** Zero new issues
- **Action:** None required

### Rollback Command

```bash
git revert HEAD
git push origin refactor/remove-dead-cron-scripts
```

### Expected Git Commit Message

```
refactor: remove dead cron script

- properties/cron/flag_defaulters.py: broken, imports non-existent function
- No production imports
- Not referenced in any crontab or CI schedule

Risk: LOW
Batch: 6 of 8
```

---

## Batch 7: Remove Obsolete Standalone Scripts

### Files to Delete

| File | Type |
|------|------|
| `scripts/arch_audit.py` | One-time analysis script |
| `tools/migration_rollback_validator.py` | Standalone CI/testing tool |

### Why This Batch is Safe

- **No imports** from any Django application code
- **Not referenced** in any CI workflow
- Standalone scripts for one-time use
- Can be archived instead of deleted if needed

### Estimated LOC Removed

~500 lines

### Risk Level

**VERY LOW**

### Commands to Execute

```bash
# 1. Create feature branch
git checkout -b refactor/remove-obsolete-scripts

# 2. Delete files
git rm scripts/arch_audit.py \
       tools/migration_rollback_validator.py

# 3. Commit
git commit -m "refactor: remove obsolete standalone scripts

- scripts/arch_audit.py: one-time architecture audit script
- tools/migration_rollback_validator.py: standalone CI/testing tool
- No imports from any Django application code
- Not referenced in any CI workflow

Risk: VERY LOW
Batch: 7 of 8"
```

### Tests to Execute

```bash
pytest --tb=short -q
```

### Migrations to Check

```bash
# No migrations affected
```

### Import-Linter Check

```bash
lint-imports --config import-linter.ini
```

### mypy

```bash
mypy --config-file=mypy.ini .
```

### pylint

```bash
python -m pylint rentsecure_be core properties finance notification documents smartbot
```

### pytest

```bash
pytest --tb=short -q
```

### Coverage

```bash
pytest --cov --cov-report=xml
```

### Sonar Impact

- **Expected:** Zero new issues
- **Action:** None required

### Rollback Command

```bash
git revert HEAD
git push origin refactor/remove-obsolete-scripts
```

### Expected Git Commit Message

```
refactor: remove obsolete standalone scripts

- scripts/arch_audit.py: one-time architecture audit script
- tools/migration_rollback_validator.py: standalone CI/testing tool
- No imports from any Django application code
- Not referenced in any CI workflow

Risk: VERY LOW
Batch: 7 of 8
```

---

## Batch 8: Update CI/CD Workflows

### Files to Update

| File | Change |
|------|--------|
| `.github/workflows/lint.yml` | Remove `dashboard` and `ai_assistant` from pylint and coverage configs |
| `.github/workflows/mutation.yml` | Remove `dashboard` and `ai_assistant` from coverage config |
| `.github/workflows/security.yml` | Remove `dashboard` and `ai_assistant` from bandit app list |
| `.github/workflows/test.yml` | Remove `--cov=dashboard` from pytest command |
| `.github/workflows/quality.yml` | Remove `dashboard` and `ai_assistant` if present |

### Why This Batch is Required

After Batches 1 and 2 delete the `dashboard/` and `ai_assistant/` apps, CI workflows that reference these apps will fail or produce errors.

### Estimated LOC Changed

~50 lines modified

### Risk Level

**LOW**

### Commands to Execute

```bash
# 1. Create feature branch
git checkout -b refactor/update-ci-workflows

# 2. Update workflow files (manual edits required)
# Use edit tool or sed to remove dashboard and ai_assistant references

# 3. Commit
git commit -m "chore: update CI workflows after removing dead apps

- Remove dashboard from lint.yml, mutation.yml, security.yml, test.yml
- Remove ai_assistant from lint.yml, mutation.yml, security.yml, test.yml
- Update coverage configurations to exclude removed apps

Risk: LOW
Batch: 8 of 8"
```

### Tests to Execute

```bash
# No unit tests for CI workflows, but verify:
python -c "
import yaml
import os

workflows = [
    '.github/workflows/lint.yml',
    '.github/workflows/mutation.yml',
    '.github/workflows/security.yml',
    '.github/workflows/test.yml',
]

for wf in workflows:
    with open(wf) as f:
        content = f.read()
        # Check that removed apps are not referenced
        assert 'dashboard' not in content or 'dashboard' in content.split(), f'{wf} still references dashboard'
        assert 'ai_assistant' not in content or 'ai_assistant' in content.split(), f'{wf} still references ai_assistant'
print('CI workflow updates verified')
"
```

### Migrations to Check

```bash
# No migrations affected
```

### Import-Linter Check

```bash
lint-imports --config import-linter.ini
```

### mypy

```bash
mypy --config-file=mypy.ini .
```

### pylint

```bash
python -m pylint rentsecure_be core properties finance notification documents smartbot
```

### pytest

```bash
pytest --tb=short -q
```

### Coverage

```bash
pytest --cov --cov-report=xml
```

### Sonar Impact

- **Expected:** Zero new issues
- **Action:** None required

### Rollback Command

```bash
git revert HEAD
git push origin refactor/update-ci-workflows
```

### Expected Git Commit Message

```
chore: update CI workflows after removing dead apps

- Remove dashboard from lint.yml, mutation.yml, security.yml, test.yml
- Remove ai_assistant from lint.yml, mutation.yml, security.yml, test.yml
- Update coverage configurations to exclude removed apps

Risk: LOW
Batch: 8 of 8
```

---

## Execution Order

```
Batch 1: Remove dashboard/ app
    ↓
Batch 2: Remove ai_assistant/ app
    ↓
Batch 3: Remove empty placeholders
    ↓
Batch 4: Remove dead service modules
    ↓
Batch 5: Remove dead management commands
    ↓
Batch 6: Remove dead cron scripts
    ↓
Batch 7: Remove obsolete standalone scripts
    ↓
Batch 8: Update CI/CD workflows
```

**Note:** Batches 1 and 2 must be executed before Batch 8, because Batch 8 updates CI configs to remove references to the deleted apps. Batches 3–7 can be executed in any order, but the suggested order is from least risky to slightly more risky.

---

## Rollback Strategy

### Per-Batch Rollback

Each batch is designed to be independently reversible:

```bash
# If a batch causes issues:
git revert HEAD
git push origin <branch-name>

# This reverts only that batch's changes
# Other batches remain intact
```

### Global Rollback

If multiple batches cause issues:

```bash
# Revert all batches in reverse order
git revert <batch8-commit>
git revert <batch7-commit>
...
git revert <batch1-commit>
```

### Emergency Rollback

If the entire refactor branch needs to be abandoned:

```bash
# Switch to main
git checkout main

# Delete the refactor branch
git branch -D refactor/dead-code-cleanup

# Push to remote
git push origin --delete refactor/dead-code-cleanup
```

---

## CI/CD Pipeline After Each Batch

### Required Checks (Run After Every Batch)

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| pytest | `pytest --tb=short -q` | All tests pass |
| coverage | `pytest --cov --cov-report=xml` | Coverage does not decrease |
| mypy | `mypy --config-file=mypy.ini .` | No new type errors |
| pylint | `python -m pylint rentsecure_be core properties finance notification documents smartbot` | Score ≥ 8.0 |
| import-linter | `lint-imports --config import-linter.ini` | No new violations |
| Django checks | `python manage.py check --deploy` | No errors |
| migrations | `python manage.py makemigrations --check --dry-run` | No new migrations needed |

### GitHub Actions Workflow

```yaml
# .github/workflows/dead-code-cleanup.yml
name: Dead Code Cleanup Validation

on:
  push:
    branches: [refactor/dead-code-cleanup]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run pytest
        run: pytest --tb=short -q
      - name: Run coverage
        run: pytest --cov --cov-report=xml
      - name: Run mypy
        run: mypy --config-file=mypy.ini .
      - name: Run pylint
        run: python -m pylint rentsecure_be core properties finance notification documents smartbot
      - name: Run import-linter
        run: lint-imports --config import-linter.ini
      - name: Django checks
        run: python manage.py check --deploy
        env:
          SECRET_KEY: test-secret-key
          DEBUG: False
          DATABASE_URL: sqlite:///test.db
```

---

## SonarCloud Impact Analysis

### Expected Changes

| Batch | Files Removed | Expected Sonar Issues Removed | Expected Sonar Coverage Impact |
|-------|---------------|------------------------------|-------------------------------|
| 1 | ~5 | ~0–2 (dead code warnings) | 0% |
| 2 | ~10 | ~0–5 (dead code warnings) | 0% |
| 3 | 3 | 0 | 0% |
| 4 | 2 | ~0–2 (duplicate code) | 0% |
| 5 | 6 | ~0–3 (dead code) | 0% |
| 6 | 1 | 0 | 0% |
| 7 | 2 | 0 | 0% |
| 8 | 0 | 0 | 0% |
| **Total** | **~29** | **~0–12** | **0%** |

### Sonar Quality Gate Impact

- **Bugs:** 0 new bugs expected
- **Vulnerabilities:** 0 new vulnerabilities expected
- **Code Smells:** ~0–12 dead code smells removed (positive impact)
- **Coverage:** No change (removed files have 0% coverage)
- **Quality Gate:** Should remain GREEN after all batches

### Sonar Recommendations

1. Run SonarCloud analysis after each batch
2. Monitor "New Code" period for 7 days after all batches
3. Verify that "Dead Code" category shows reduction
4. Ensure no new "Bug" or "Vulnerability" issues are introduced

---

## Estimated Timeline

| Batch | Estimated Time | Dependencies |
|-------|----------------|--------------|
| 1 | 30 minutes | None |
| 2 | 45 minutes | None |
| 3 | 15 minutes | None |
| 4 | 20 minutes | None |
| 5 | 25 minutes | None |
| 6 | 15 minutes | None |
| 7 | 20 minutes | None |
| 8 | 30 minutes | Batches 1 and 2 must be merged first |
| **Total** | **~3 hours** | |

---

## Final Checklist Before Execution

- [ ] All stakeholders have approved `docs/refactoring/02_verified_dead_code_report.md`
- [ ] Frontend team has verified that no API endpoints marked NEEDS_MANUAL_VERIFICATION are in use
- [ ] Ops team has verified that no cron jobs or scheduled tasks reference the files to be deleted
- [ ] CI/CD pipelines are passing on current `main` branch
- [ ] Feature branch `refactor/dead-code-cleanup` is created from latest `main`
- [ ] All developers are notified of the refactor branch and execution plan
- [ ] Rollback strategy is communicated to the team

---

## Appendix: Commands Reference

### Full Execution Script (All Batches)

```bash
#!/bin/bash
set -e

echo "Starting dead code cleanup..."

# Batch 1: dashboard/
echo "Batch 1: Removing dashboard/ app..."
git checkout -b refactor/remove-dashboard-app
git rm -r dashboard/
git commit -m "refactor: remove dead dashboard app"
pytest --tb=short -q
git push origin refactor/remove-dashboard-app
# Create PR and merge

# Batch 2: ai_assistant/
echo "Batch 2: Removing ai_assistant/ app..."
git checkout main
git pull origin main
git checkout -b refactor/remove-ai-assistant-app
git rm -r ai_assistant/
git commit -m "refactor: remove dead ai_assistant app"
pytest --tb=short -q
git push origin refactor/remove-ai-assistant-app
# Create PR and merge

# Batch 3: Empty placeholders
echo "Batch 3: Removing empty placeholders..."
git checkout main
git pull origin main
git checkout -b refactor/remove-empty-placeholders
git rm properties/models/subscription_models.py \
       properties/admin/subscription_admin.py \
       properties/admin/usage_limit_admin.py
git commit -m "refactor: remove empty placeholder modules"
pytest --tb=short -q
git push origin refactor/remove-empty-placeholders
# Create PR and merge

# Batch 4: Dead services
echo "Batch 4: Removing dead services..."
git checkout main
git pull origin main
git checkout -b refactor/remove-dead-services
git rm notification/services/schedule_reminders.py \
       properties/services/rent_service.py
git commit -m "refactor: remove dead service modules"
pytest --tb=short -q
git push origin refactor/remove-dead-services
# Create PR and merge

# Batch 5: Dead management commands
echo "Batch 5: Removing dead management commands..."
git checkout main
git pull origin main
git checkout -b refactor/remove-dead-management-commands
git rm management/commands/seed_subscription_plans.py \
       management/commands/retry_failed_payouts.py \
       management/commands/send_rent_reminders.py \
       management/commands/monthly_whatsapp_and_email_summary_to_owner.py \
       management/commands/send_tax_reminders.py
git commit -m "refactor: remove dead management commands"
pytest --tb=short -q
git push origin refactor/remove-dead-management-commands
# Create PR and merge

# Batch 6: Dead cron scripts
echo "Batch 6: Removing dead cron scripts..."
git checkout main
git pull origin main
git checkout -b refactor/remove-dead-cron-scripts
git rm properties/cron/flag_defaulters.py
rmdir properties/cron 2>/dev/null || true
git commit -m "refactor: remove dead cron script"
pytest --tb=short -q
git push origin refactor/remove-dead-cron-scripts
# Create PR and merge

# Batch 7: Obsolete scripts
echo "Batch 7: Removing obsolete scripts..."
git checkout main
git pull origin main
git checkout -b refactor/remove-obsolete-scripts
git rm scripts/arch_audit.py \
       tools/migration_rollback_validator.py
git commit -m "refactor: remove obsolete standalone scripts"
pytest --tb=short -q
git push origin refactor/remove-obsolete-scripts
# Create PR and merge

# Batch 8: Update CI workflows
echo "Batch 8: Updating CI workflows..."
git checkout main
git pull origin main
git checkout -b refactor/update-ci-workflows
# Manual edits to .github/workflows/*.yml to remove dashboard and ai_assistant
git commit -m "chore: update CI workflows after removing dead apps"
pytest --tb=short -q
git push origin refactor/update-ci-workflows
# Create PR and merge

echo "Dead code cleanup complete!"
```

---

## Post-Cleanup Verification

After all batches are merged:

```bash
# 1. Verify INSTALLED_APPS
python -c "
from django.conf import settings
print('INSTALLED_APPS:', settings.INSTALLED_APPS)
assert 'dashboard' not in settings.INSTALLED_APPS
assert 'ai_assistant' not in settings.INSTALLED_APPS
print('✓ INSTALLED_APPS verified')
"

# 2. Verify URL configuration
python -c "
from django.urls import get_resolver
resolver = get_resolver()
url_patterns = [str(p.pattern) for p in resolver.url_patterns]
print('URL patterns:', url_patterns)
print('✓ URL configuration verified')
"

# 3. Run full test suite
pytest --tb=short -q --cov=rentsecure_be --cov=core --cov=properties --cov=finance --cov=notification --cov=documents --cov=smartbot --cov-report=term-missing

# 4. Run import-linter
lint-imports --config import-linter.ini

# 5. Run mypy
mypy --config-file=mypy.ini .

# 6. Run pylint
python -m pylint rentsecure_be core properties finance notification documents smartbot

# 7. Check for any remaining references to deleted apps
grep -r "dashboard" . --include="*.py" | grep -v ".pyc" | grep -v "__pycache__" | grep -v ".nox" | grep -v ".venv" || echo "No dashboard references"
grep -r "ai_assistant" . --include="*.py" | grep -v ".pyc" | grep -v "__pycache__" | grep -v ".nox" | grep -v ".venv" || echo "No ai_assistant references"

echo "✓ Post-cleanup verification complete"
```

---

*Document generated by Kilo Phase 2 Execution Planning. No production code was modified.*
