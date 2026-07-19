# PR-003 Implementation Specification

## Migrate NotificationPreference to notification

---

## 1. Purpose

Execute the data migration that copies all existing `NotificationPreference` records from the legacy `core_notificationpreference` table into the new `notification_notificationpreference` table created in PR-001. Deprecate the legacy `core.models.NotificationPreference` model and update all in-app references to use `notification.models.NotificationPreference`.

This PR is **blocked until PR-001 is merged** because:
1. `notification` must be in `INSTALLED_APPS`
2. `notification_notificationpreference` table must exist (created by PR-001 migration)
3. `notification/models.py` must contain the target `NotificationPreference` model

---

## 2. Scope

### 2.1 In Scope

- Create `notification/migrations/0003_migrate_notificationpreference.py` — data migration copying `core_notificationpreference` → `notification_notificationpreference`
- Create `core/migrations/XXXX_migrate_notificationpreference.py` — source-table migration (per P0EP; see §9.4 for placement note)
- Create `notification/tests/test_migrations.py` — forward and reverse migration tests with data integrity verification
- Create `notification/tests/test_models.py` — model tests for `NotificationPreference`
- Update `notification/models.py` — ensure `NotificationPreference` matches original `core/models.py` fields exactly
- Update `core/models.py` — deprecate `NotificationPreference` with `DeprecationWarning`; retain shim for 1 release cycle
- Update `core/signals.py` — delegate to `notification/` model (see §6.2 for dependency matrix constraint)
- Update `core/tests/test_signals.py` — update imports to reference `notification.models.NotificationPreference` or use shim appropriately
- Verify all cross-app imports of `core.models.NotificationPreference` are updated to `notification.models.NotificationPreference`

### 2.2 Out of Scope

- Creating `notification/views/notification_preference_views.py` (Phase 4, PR-040)
- Creating `notification/services/notification_preference_service.py` (Phase 4, PR-041)
- Creating `notification/urls.py` for notification preference endpoints (Phase 4)
- Moving webhook handlers (PR-004)
- Splitting `core/views.py` (PR-005)
- Moving management commands (PR-006)
- Any changes to `core/views/reporting_views.py` or other view modules
- Any changes to `payments/`, `properties/`, or other apps outside the NotificationPreference migration
- Dropping the `core_notificationpreference` table (deferred to Phase 5)
- Any changes to `rentsecure_be/services/` or other rentsecure_be utilities (Phase 3)

---

## 3. Files

### 3.1 Files to Create

| File | Purpose | Owner |
|------|---------|-------|
| `notification/migrations/0003_migrate_notificationpreference.py` | Data migration: copies `core_notificationpreference` → `notification_notificationpreference` | Platform Team |
| `core/migrations/XXXX_migrate_notificationpreference.py` | Source-table migration marker (see §9.4 for placement guidance) | Platform Team |
| `notification/tests/test_migrations.py` | Migration forward/reverse tests + data integrity tests | Platform Team |
| `notification/tests/test_models.py` | Model tests for `NotificationPreference` CRUD and constraints | Platform Team |

### 3.2 Files to Modify

| File | Change | Owner |
|------|--------|-------|
| `notification/models.py` | Ensure `NotificationPreference` fields exactly match original `core/models.py` definition; add `__str__`, Meta class | Platform Team |
| `core/models.py` | Add `DeprecationWarning` to `NotificationPreference`; retain shim for 1 release cycle | Platform Team |
| `core/signals.py` | Update imports to use `notification.models.NotificationPreference` (see §6.2 constraint) | Platform Team |
| `core/tests/test_signals.py` | Update imports to use `notification.models.NotificationPreference` (see §6.2 constraint) | Platform Team |

### 3.3 Files to Delete

None.

**Note on `core/migrations/XXXX_migrate_notificationpreference.py`:** Django data migrations that copy data between apps typically live in the target app's migration chain. This file is listed in P0EP as a "source table" marker. The implementer must verify whether Django's migration dependency graph requires a companion migration in `core/`. If `notification/migrations/0003` can declare a dependency on the existing `core` migration that created `core_notificationpreference`, then the `core/` migration is unnecessary and must not be created. See §9.4.

---

## 4. Responsibilities

| Role | Responsibility |
|------|----------------|
| **Platform Team Lead** | Owns `notification/migrations/0003_migrate_notificationpreference.py`, `notification/tests/`, `core/models.py` deprecation. Approves PR. |
| **Security Lead** | Reviews data migration for data integrity. Verifies no data exposure during migration. |
| **Developer** | Implements data migration, deprecation shim, test updates, and reference updates. Runs full validation. |
| **AI Assistant** | Generates migration, tests, and doc updates per this spec. Stops and asks if dependency matrix is violated. |

---

## 5. Acceptance Criteria

### 5.1 Functional

- [ ] `notification/migrations/0003_migrate_notificationpreference.py` exists and is generated/applied correctly.
- [ ] Migration copies **every row** from `core_notificationpreference` to `notification_notificationpreference` without loss.
- [ ] Boolean preference fields are preserved correctly during copy.
- [ ] `core/models.py` `NotificationPreference` emits `DeprecationWarning` when imported or instantiated.
- [ ] `core/models.py` `NotificationPreference` continues to map to `core_notificationpreference` table (shim).
- [ ] All cross-app imports of `core.models.NotificationPreference` are updated to `notification.models.NotificationPreference`.
- [ ] `core/signals.py` and `core/tests/test_signals.py` reference `notification.models.NotificationPreference` or delegate appropriately.
- [ ] `python manage.py migrate` applies all migrations cleanly on a fresh database.
- [ ] `python manage.py migrate` applies all migrations cleanly on a database with existing `core_notificationpreference` data.
- [ ] `python manage.py migrate --reverse` reverses the data migration cleanly on test database.

### 5.2 Non-Functional

- [ ] Data migration runs in <30 seconds on production-like data volume (tested on staging copy).
- [ ] Row count after forward migration equals row count before migration.
- [ ] All tests pass (existing + new).
- [ ] No architecture test violations.
- [ ] No import-linter violations.
- [ ] No circular dependencies introduced.
- [ ] No security vulnerabilities (Bandit 0 high/medium).

---

## 6. Architecture Rules

### 6.1 Bounded Context Compliance

- `notification/` owns `NotificationPreference` from this point forward.
- `core/` retains a deprecated shim of `NotificationPreference` for exactly 1 release cycle. The shim maps to `core_notificationpreference` table, which remains in the database until Phase 5.
- `properties/`, `payments/`, `finance/`, and other apps must import `NotificationPreference` from `notification/models.py`, not `core/models.py`.
- The `core_notificationpreference` table is read-only during the transition period. All new writes go to `notification_notificationpreference`.

### 6.2 Import Rules

**Critical dependency matrix constraint:**

| Source | shared | platform | identity (core) | subscription | property | payment | notification | document | finance | referral | dashboard |
|--------|--------|----------|-----------------|--------------|----------|---------|--------------|----------|---------|----------|-----------|
| **notification** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

`identity/` (i.e., `core/`) **can** import from `notification/` per the v1.1 dependency matrix. This is a key difference from the `payment/` constraint in PR-002.

**Implications for this PR:**

1. `core/signals.py` **may** import `notification.models.NotificationPreference` because the dependency matrix allows `identity → notification`.
2. `core/tests/test_signals.py` **may** import `notification.models.NotificationPreference`.
3. No ADR exception is required for `core/` to import from `notification/`.

**Permitted pattern for Phase 0:** `core/signals.py` and `core/tests/test_signals.py` may import directly from `notification.models.NotificationPreference`.

### 6.3 Model Rules

- `notification/models.py` `NotificationPreference` must match the original `core/models.py` definition field-for-field.
- `owner` ForeignKey must use `settings.AUTH_USER_MODEL` string reference (not `from core.models import User`).
- Boolean preference fields (`rent_alerts_whatsapp`, `rent_alerts_email`, `monthly_summary_email`, `monthly_summary_whatsapp`, `payout_alerts_whatsapp`, `payout_alerts_email`) must match original defaults exactly.
- Model file (`notification/models.py`) must not exceed 400 lines.
- Model must not contain business logic.
- `core/models.py` `NotificationPreference` shim must emit `DeprecationWarning` on import/instantiation.

### 6.4 Migration Rules

- Data migration must be **additive** (copy only, never delete).
- Old `core_notificationpreference` table must remain for 1 release cycle.
- Migration must be **reversible** — reverse operation must restore `core_notificationpreference` data or be marked irreversible with justification.
- Migration must include **data integrity checks**: row count, field value verification.
- Migration must be tested on a production-like data copy before merge.
- AI must **never** modify existing migration files that have already been applied to production.
- AI must **never** generate a migration that drops `core_notificationpreference` in this PR.

### 6.5 Security Rules

- No encrypted fields in `NotificationPreference` — all fields are booleans.
- Migration must not log preference data in a way that could identify users.
- Migration must not expose data in error messages or stack traces.

### 6.6 Naming Rules

- Migration file: `0003_migrate_notificationpreference.py` (in `notification/migrations/`).
- Test files: `test_migrations.py`, `test_models.py`.
- Test classes: `TestNotificationPreferenceMigration`, `TestNotificationPreferenceModel`.
- Test methods: `test_migrates_all_rows`, `test_reverse_migration_restores_data`, `test_preference_fields_preserved`.

---

## 7. CI Requirements

### 7.1 Required CI Gates

All gates are **blocking**. PR cannot be merged if any gate fails.

| Gate | Tool | Threshold | Command |
|------|------|-----------|---------|
| Lint | Ruff | 0 errors | `ruff check .` |
| Format | Ruff | 0 issues | `ruff format --check .` |
| Type Check | MyPy | 0 errors | `mypy .` |
| Import Rules | import-linter | 0 violations | `import-linter check` |
| Tests | Pytest | All pass, ≥90% coverage | `pytest tests/ -v --cov` |
| Architecture | pytest | 0 failures | `pytest tests/architecture/ -v` |
| Django Check | manage.py | 0 errors | `python manage.py check` |
| Migrations | manage.py | Forward + reverse pass | `python manage.py test migrations` |
| Security | Bandit | 0 high/medium | `bandit -r notification/ core/` |
| Dependency | Safety | 0 critical | `safety check` |

### 7.2 Pipeline Order

```
Lint → Type Check → Import Rules → Tests → Architecture → Django Check → Migrations → Security → Dependency
```

### 7.3 Phase-Specific Architecture Tests

| Test | Purpose | Expected Result |
|------|---------|-----------------|
| `test_import_rules.py` | No forbidden SDK imports in new code | Pass |
| `test_layer_compliance.py` | No view imports from `notification/` in `core/` (not applicable — allowed by matrix) | Pass |
| `test_rentsecure_be_boundary.py` | No app imports from `rentsecure_be/` | Pass |
| `test_god_models.py` | `notification/models.py` ≤400 lines | Pass |
| `test_circular_deps.py` | No new circular dependencies | Pass |

**Note on `test_layer_compliance.py`:** Unlike PR-002, `core/` **is allowed** to import from `notification/` per the dependency matrix. This test must verify that no other forbidden layer violations exist.

---

## 8. Testing Strategy

### 8.1 Test Tiers Required

| Tier | Scope | Requirement |
|------|-------|-------------|
| **Unit** | Deprecation warning in `core/models.py` | ≥90% coverage |
| **Migration** | Forward + reverse data migration | Forward + reverse pass |
| **Integration** | Notification preference API after migration | ≥80% coverage |
| **Architecture** | Import boundaries, layer compliance | 0 violations |
| **Security** | Bandit scan on changed files | 0 high/medium |

### 8.2 Unit Tests: `core/models.py` Deprecation Shim

Required test cases (`notification/tests/test_deprecation.py` or `core/tests/test_models.py`):
- `test_notification_preference_emits_deprecation_warning` — importing or instantiating `core.models.NotificationPreference` emits `DeprecationWarning`
- `test_notification_preference_shim_maps_to_core_table` — shim model maps to `core_notificationpreference` table
- `test_notification_preference_shim_has_all_fields` — shim has same fields as original model

### 8.3 Migration Tests: `notification/tests/test_migrations.py`

Required test cases:
- `test_migration_forward_copies_all_rows` — row count in `notification_notificationpreference` equals row count in `core_notificationpreference` before migration
- `test_migration_forward_preserves_preference_fields` — boolean field values are identical before/after copy
- `test_migration_forward_preserves_user_links` — `owner_id` values are preserved
- `test_migration_reverse_restores_data` — `migrate --reverse` restores original state (or marks irreversible with justification)
- `test_migration_on_empty_database` — migration runs cleanly when `core_notificationpreference` is empty
- `test_migration_on_production_like_data` — migration runs on a copy of production data without errors

### 8.4 Model Tests: `notification/tests/test_models.py`

Required test cases (in addition to those created in PR-001):
- `test_notification_preference_matches_original_schema` — field names, types, and constraints match `core/models.py` original
- `test_unique_together_owner` — duplicate `owner` raises `IntegrityError`
- `test_owner_foreign_key_uses_auth_user_model_string` — `owner` field uses `settings.AUTH_USER_MODEL`, not direct import

### 8.5 Signal Tests: `core/tests/test_signals.py`

Required test cases (update existing):
- `test_user_creation_creates_notification_preference` — update to verify preference is created via `notification/` model or shim works correctly
- `test_notification_preference_defaults` — update to verify defaults match `notification/models.py` definition

### 8.6 Contract Tests

No new contract tests are required in this PR. The `property → notification` contract is already covered by existing tests. Contract tests for notification preference API are added in Phase 4 when `notification/views/notification_preference_views.py` is created.

### 8.7 Architecture Tests

AI must verify the following architecture tests pass after changes:
- `test_import_rules.py` — no forbidden imports in new/modified files
- `test_layer_compliance.py` — `core/` imports from `notification/` are allowed per dependency matrix
- `test_rentsecure_be_boundary.py` — no `rentsecure_be/` imports in new/modified files
- `test_shared_purity.py` — `shared/fields.py` still passes (no regressions)
- `test_god_models.py` — `notification/models.py` ≤400 lines
- `test_circular_deps.py` — no new circular dependencies

### 8.8 Security Tests

- Run `bandit -r notification/ core/` and verify 0 high/medium findings.
- Verify no sensitive preference data appears in migration test output.
- Verify no secrets or API keys in migration files.

### 8.9 Forbidden Test Patterns

- No `time.sleep()` in tests.
- No test dependencies on execution order.
- No hardcoded test data (use factories).
- No mocking Django ORM in migration tests (use test database).
- No direct database access in unit tests (use model methods or ORM).

---

## 9. Migration Strategy

### 9.1 Forward Migration

**Step 1: Apply PR-001 migrations**
```bash
python manage.py migrate
```
Verifies `notification_notificationpreference` table exists.

**Step 2: Apply PR-003 data migration**
```bash
python manage.py migrate notification
```
Runs `0003_migrate_notificationpreference.py`. Copies all rows from `core_notificationpreference` to `notification_notificationpreference`.

**Step 3: Verify data integrity**
```bash
python manage.py shell -c "
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('SELECT COUNT(*) FROM core_notificationpreference')
    core_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM notification_notificationpreference')
    notification_count = cursor.fetchone()[0]
    assert core_count == notification_count, f'Row count mismatch: {core_count} vs {notification_count}'
"
```

### 9.2 Data Migration Details

**Source:** `core_notificationpreference`
**Target:** `notification_notificationpreference`
**Operation:** `INSERT INTO notification_notificationpreference SELECT * FROM core_notificationpreference`

**Field mapping (must be exact):**

| Source (`core_notificationpreference`) | Target (`notification_notificationpreference`) | Notes |
|----------------------------------------|------------------------------------------------|-------|
| `id` | `id` | Preserve original PK |
| `owner_id` | `owner_id` | ForeignKey to `core_user` |
| `rent_alerts_whatsapp` | `rent_alerts_whatsapp` | Boolean — copy as-is |
| `rent_alerts_email` | `rent_alerts_email` | Boolean — copy as-is |
| `monthly_summary_email` | `monthly_summary_email` | Boolean — copy as-is |
| `monthly_summary_whatsapp` | `monthly_summary_whatsapp` | Boolean — copy as-is |
| `payout_alerts_whatsapp` | `payout_alerts_whatsapp` | Boolean — copy as-is |
| `payout_alerts_email` | `payout_alerts_email` | Boolean — copy as-is |

### 9.3 Reverse Migration

**Operation:** `DELETE FROM notification_notificationpreference` (or mark migration as irreversible with justification).

**Preferred approach:** Reverse migration deletes rows from `notification_notificationpreference` that were added by the forward migration. Since the old `core_notificationpreference` table remains untouched, data is not lost.

```python
# In notification/migrations/0003_migrate_notificationpreference.py
def reverse(apps, schema_editor):
    # Delete rows that were copied from core
    # WARNING: This deletes data from notification_notificationpreference
    # Core data remains in core_notificationpreference
    pass
```

**If reverse migration is marked irreversible:** Provide justification in migration file docstring:
```python
"""
This migration is irreversible because it copies data
between tables and the reverse operation cannot reliably determine
which rows were copied vs. newly created.
The core_notificationpreference table is retained for reference.
"""
```

### 9.4 Migration Placement Note

The P0EP lists two migration files:
- `notification/migrations/0003_migrate_notificationpreference.py` — primary data migration
- `core/migrations/XXXX_migrate_notificationpreference.py` — source-table migration

**Standard Django pattern:** Cross-app data migrations live in the **target app's** migration chain. The target migration declares a dependency on the source app's migration that created the source table.

**Decision for this PR:** Create **only** `notification/migrations/0003_migrate_notificationpreference.py` with a dependency on the `core` migration that created `core_notificationpreference`. Do **not** create `core/migrations/XXXX_migrate_notificationpreference.py` unless Django's migration graph requires it (e.g., if `notification/0003` cannot declare a dependency on `core/` due to circular migration dependencies). If such a circular dependency exists, stop and ask the human to resolve the migration graph before proceeding.

### 9.5 Data Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Row count mismatch | Low | High | Verify row counts before/after in test and staging |
| Partial migration (crash mid-run) | Low | Medium | Migration runs in single transaction; Django wraps in atomic |
| Reverse migration data loss | Medium | Medium | Mark as irreversible OR delete only copied rows |
| Duplicate rows on re-run | Low | Low | Use `get_or_create` or check for existing rows |

---

## 10. Rollback Plan

### 10.1 Rollback Triggers

Rollback is triggered if any of the following occur:
- Data migration fails on staging or production (`OperationalError`, `ProgrammingError`).
- Row count after migration does not match row count before migration.
- `core/models.py` deprecation shim causes `ImportError` or `AttributeError` in existing code.
- Any CI gate fails after merge and cannot be fixed within 30 minutes.
- Production incident: notification preference API returns 500 errors after deployment.

### 10.2 Rollback Steps

1. **Deploy decision:** Confirm rollback decision with Platform Team Lead.
2. **Git revert:**
   ```bash
   git revert <PR-003-merge-commit-sha>
   git push origin main
   ```
3. **Reverse migration:**
   ```bash
   python manage.py migrate --reverse notification 0003_migrate_notificationpreference
   ```
   If reverse migration is marked irreversible, skip this step. The `notification_notificationpreference` table will remain but will be empty or contain stale data. Old `core_notificationpreference` table is unaffected.
4. **Restore `core/models.py`:** If `NotificationPreference` was removed (not just deprecated), restore it from the `main` branch pre-PR-003 state.
5. **Deploy reverted code:** Deploy the reverted commit to staging, then production.
6. **Smoke tests:**
   ```bash
   python manage.py check
   python manage.py migrate
   python manage.py shell -c "from core.models import NotificationPreference; print(NotificationPreference.objects.count())"
   ```
7. **Verify production health:** Check that notification preference endpoints return 200 (not 500). Verify that `core_notificationpreference` table is accessible.
8. **Notify team:** Post rollback completion notice with root cause and fix plan.

### 10.3 Estimated Rollback Time

**30 minutes** (git revert + migrate --reverse + deploy + smoke tests).

### 10.4 Data Risk

**Low.** The data migration is additive — it copies data from `core_notificationpreference` to `notification_notificationpreference` without deleting source data. Reverse migration removes copied rows from `notification_notificationpreference`. The original `core_notificationpreference` table is never modified by this PR.

### 10.5 Rollback Validation

- Rollback must be tested on staging **before** production deploy.
- Test sequence:
   1. Apply PR-003 to staging.
   2. Run data migration.
   3. Verify `notification_notificationpreference` has all rows.
   4. Execute rollback steps 2-7 above.
   5. Verify `core_notificationpreference` is still accessible and unchanged.
   6. Re-apply PR-003 after successful rollback test.

---

## 11. Expected Git Diff

### 11.1 Summary

| Metric | Value |
|--------|-------|
| Files changed | 7 (4 new, 3 modified) |
| Files added | 4 |
| Files modified | 3 |
| Files deleted | 0 |
| Lines added | ~310 |
| Lines removed | ~15 |
| Net change | ~295 lines |

### 11.2 Files Added (~210 lines)

| File | Approx Lines | Description |
|------|---------------|-------------|
| `notification/migrations/0003_migrate_notificationpreference.py` | ~45 | Data migration with forward and reverse functions |
| `core/migrations/XXXX_migrate_notificationpreference.py` | ~0–40 | Source-table migration marker (see §9.4; may not be needed) |
| `notification/tests/test_migrations.py` | ~90 | Forward/reverse tests + data integrity tests |
| `notification/tests/test_models.py` | ~75 | Model tests for `NotificationPreference` |

### 11.3 Files Modified (~100 lines)

| File | Approx Lines Changed | Description |
|------|----------------------|-------------|
| `notification/models.py` | +8, -0 | Ensure field definitions match original; add `__str__` and Meta if missing |
| `core/models.py` | +12, -5 | Add `DeprecationWarning` to `NotificationPreference`; retain shim |
| `core/signals.py` | +5, -5 | Update imports to reference `notification.models.NotificationPreference` (allowed by dependency matrix) |
| `core/tests/test_signals.py` | +5, -5 | Update imports to reference `notification.models.NotificationPreference` (allowed by dependency matrix) |

### 11.4 Diff Constraints

- No file in the diff may exceed 400 lines total after modification.
- No more than 15 files changed (actual count: 7 — well within limit).
- No deletions of existing functionality.

---

## 12. Definition of Done

PR-003 is **Done** when ALL of the following are true.

### Code
- [ ] `notification/migrations/0003_migrate_notificationpreference.py` created and tested.
- [ ] `core/models.py` `NotificationPreference` deprecated with `DeprecationWarning` (shim retained).
- [ ] `notification/models.py` `NotificationPreference` matches original schema exactly.
- [ ] All cross-app imports updated to `notification.models.NotificationPreference` where dependency matrix allows.
- [ ] `core/signals.py` and `core/tests/test_signals.py` updated per §6.2 constraints.
- [ ] `core/migrations/XXXX_migrate_notificationpreference.py` created only if migration graph requires it.

### Tests
- [ ] `notification/tests/test_migrations.py` created with all required test cases.
- [ ] `notification/tests/test_models.py` created with all required test cases.
- [ ] `core/tests/test_signals.py` updated to use `notification.models.NotificationPreference`.
- [ ] All new tests pass.
- [ ] All existing tests pass (no regressions).
- [ ] Migration forward test passes (row count matches).
- [ ] Migration reverse test passes (or marked irreversible with justification).
- [ ] Data integrity verified (field values, user links).
- [ ] Test coverage ≥90% for new code.

### CI
- [ ] `ruff check .` passes (0 errors).
- [ ] `ruff format --check .` passes.
- [ ] `mypy .` passes (0 errors).
- [ ] `import-linter check` passes (0 violations).
- [ ] `pytest tests/ -v --cov` passes.
- [ ] `pytest tests/architecture/ -v` passes.
- [ ] `python manage.py check` passes.
- [ ] `python manage.py makemigrations --check` passes.
- [ ] `bandit -r notification/ core/` passes (0 high/medium).
- [ ] `safety check` passes (0 critical).

### Architecture
- [ ] No `rentsecure_be/` imports in new/modified files.
- [ ] No circular dependencies introduced.
- [ ] `notification/models.py` ≤400 lines.
- [ ] `core/models.py` shim does not import from `notification/` (not required — allowed by matrix, but shim should remain standalone).
- [ ] Data migration is reversible (or marked irreversible with justification).

### Documentation
- [ ] `docs/architecture/contexts/notification.md` updated with `NotificationPreference` migration info.
- [ ] ADR-011 updated to reflect PR-003 completion.
- [ ] CHANGELOG.md updated.

### Deployment
- [ ] PR approved by Platform Team Lead and Security Lead.
- [ ] Merged to `phase-0-foundation` branch.
- [ ] Deployed to staging.
- [ ] Staging validation passed (24 hours).
- [ ] Rollback tested on staging before production deploy.
- [ ] No production incidents during staging validation.

---

## 13. Developer Checklist

### Pre-Implementation
- [ ] Verify PR-001 is merged to `phase-0-foundation` branch.
- [ ] Verify `notification` is in `INSTALLED_APPS`.
- [ ] Verify `notification/models.py` exists with `NotificationPreference`.
- [ ] Verify `notification_notificationpreference` table exists in database.
- [ ] Verify `core_notificationpreference` table exists and has data (check row count).
- [ ] Read `ENGINEERING_STANDARDS.md` sections: Model Rules, Import Rules, Migrations, Security.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Dependency Rules, Migration Rules, Files AI Must Never Modify Automatically.
- [ ] Check current `core/models.py` for existing `NotificationPreference` definition.
- [ ] Check current `core/signals.py` for `NotificationPreference` imports.
- [ ] Check current `core/tests/test_signals.py` for `NotificationPreference` imports.
- [ ] Confirm dependency matrix constraint: `core/` **can** import from `notification/` (see §6.2).

### Implementation
- [ ] Create `notification/migrations/0003_migrate_notificationpreference.py` with forward and reverse functions.
- [ ] Create `notification/tests/test_migrations.py` with all required test cases.
- [ ] Create `notification/tests/test_models.py` with all required test cases.
- [ ] Update `notification/models.py` to match original `NotificationPreference` schema exactly.
- [ ] Update `core/models.py` to add `DeprecationWarning` to `NotificationPreference` shim.
- [ ] Update `core/signals.py` imports per §6.2 (direct import from `notification/` is allowed).
- [ ] Update `core/tests/test_signals.py` imports per §6.2.
- [ ] Run `python manage.py makemigrations --check` (should not generate new migrations for existing models).
- [ ] Run `python manage.py migrate` and verify success.

### Testing
- [ ] Run `pytest notification/tests/test_migrations.py -v`.
- [ ] Run `pytest notification/tests/test_models.py -v`.
- [ ] Run `pytest core/tests/test_signals.py -v`.
- [ ] Run `pytest tests/ -v --cov` and verify ≥90% coverage for new code.
- [ ] Run `pytest tests/architecture/ -v` and verify 0 failures.
- [ ] Run `python manage.py migrate --reverse notification 0003_migrate_notificationpreference` and verify success.
- [ ] Run `python manage.py migrate` again and verify data is restored.
- [ ] Verify row counts: `core_notificationpreference` count == `notification_notificationpreference` count after forward migration.
- [ ] Verify `DeprecationWarning` is emitted when importing `core.models.NotificationPreference`.

### Validation
- [ ] Run `ruff check .` and verify 0 errors.
- [ ] Run `ruff format --check .` and verify 0 issues.
- [ ] Run `mypy .` and verify 0 errors.
- [ ] Run `import-linter check` and verify 0 violations.
- [ ] Run `python manage.py check` and verify 0 errors.
- [ ] Run `python manage.py makemigrations --check` and verify 0 errors.
- [ ] Run `bandit -r notification/ core/` and verify 0 high/medium.
- [ ] Run `safety check` and verify 0 critical.
- [ ] Verify no `print()` statements in new code.
- [ ] Verify no `# TODO` or `# FIXME` comments.
- [ ] Verify no commented-out code.
- [ ] Verify no hardcoded secrets.
- [ ] Verify no `from rentsecure_be.X import Y` in new code.

### Rollback
- [ ] Document rollback plan in PR description.
- [ ] Test rollback on staging: apply PR-003, verify data, execute rollback, verify `core_notificationpreference` intact.

### PR
- [ ] Commit message follows conventional commits format.
- [ ] Branch name follows `<type>/<ticket-id>-<description>` format.
- [ ] PR description includes: summary, motivation, changes, testing, rollback plan.
- [ ] PR size is within limits (≤400 lines, ≤15 files — actual: ~295 lines, 7 files).
- [ ] PR is linked to Phase 0 task 0.3 and 0.5.

---

## 14. Reviewer Checklist

Use this checklist when reviewing PR-003.

### Architecture
- [ ] `notification/migrations/0003_migrate_notificationpreference.py` is additive (copies data, does not delete).
- [ ] `core/models.py` `NotificationPreference` is a deprecated shim, not a new model importing from `notification/`.
- [ ] `core/` may import from `notification/` per dependency matrix — verify imports are correct.
- [ ] `core/signals.py` and `core/tests/test_signals.py` updates comply with §6.2.
- [ ] No circular dependencies introduced.
- [ ] No new `apps/` or `config/` directories.
- [ ] `notification/models.py` matches original `core/models.py` schema field-for-field.
- [ ] Old `core_notificationpreference` table is retained (not dropped).

### Security
- [ ] No sensitive data exposure in migration code or logs.
- [ ] No secrets or API keys in migration files.
- [ ] `DeprecationWarning` is emitted for `core.models.NotificationPreference`.
- [ ] Bandit scan passes (0 high/medium).
- [ ] Safety scan passes (0 critical).

### Code Quality
- [ ] Ruff passes (0 errors, 0 formatting issues).
- [ ] MyPy passes (0 errors).
- [ ] No `print()` statements.
- [ ] No `# TODO` or `# FIXME` comments.
- [ ] No commented-out code.
- [ ] No empty `except:` clauses.
- [ ] Migration code is readable and follows Django conventions.

### Testing
- [ ] `notification/tests/test_migrations.py` covers all required test cases.
- [ ] `notification/tests/test_models.py` covers all required test cases.
- [ ] `core/tests/test_signals.py` updated and passes.
- [ ] All new tests pass.
- [ ] All existing tests pass (no regressions).
- [ ] Migration forward test passes on staging data copy.
- [ ] Migration reverse test passes on test database.
- [ ] Data integrity verified (row counts, field values).
- [ ] No test uses `time.sleep()`.
- [ ] No test depends on execution order.
- [ ] Tests use factories, not hardcoded data.

### Migrations
- [ ] `notification/migrations/0003_migrate_notificationpreference.py` is reversible or marked irreversible with justification.
- [ ] Migration declares dependency on `core` migration that created `core_notificationpreference`.
- [ ] `core/migrations/XXXX_migrate_notificationpreference.py` exists only if migration graph requires it.
- [ ] Migration runs in <30 seconds on staging data copy.
- [ ] `python manage.py migrate --reverse` works on test database.

### Documentation
- [ ] `docs/architecture/contexts/notification.md` updated with migration details.
- [ ] ADR-011 updated to reflect PR-003 completion.
- [ ] CHANGELOG.md updated.
- [ ] PR description includes rollback plan and data integrity verification steps.

### CI
- [ ] All CI gates pass.
- [ ] No import-linter violations.
- [ ] No architecture test failures.
- [ ] No circular dependency warnings.

---

## 15. AI Checklist

Use this checklist when generating PR-003 with AI assistance.

### Pre-Generation
- [ ] Read `ENGINEERING_STANDARDS.md` sections: Model Rules, Import Rules, Migrations, Security.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Dependency Rules, Migration Rules, Files AI Must Never Modify Automatically.
- [ ] Verify PR-001 is merged to `phase-0-foundation` branch.
- [ ] Verify `notification` is in `INSTALLED_APPS`.
- [ ] Verify `notification_notificationpreference` table exists.
- [ ] Verify `core_notificationpreference` table exists and has data.
- [ ] Verify `core/migrations/` migration history to determine if `core/migrations/XXXX_migrate_notificationpreference.py` is needed.
- [ ] Confirm dependency matrix constraint: `core/` **can** import from `notification/` (§6.2).

### Code Generation
- [ ] Generate `notification/migrations/0003_migrate_notificationpreference.py` with forward and reverse functions.
- [ ] Generate `notification/tests/test_migrations.py` with all required test cases.
- [ ] Generate `notification/tests/test_models.py` with all required test cases.
- [ ] Update `notification/models.py` to match original schema.
- [ ] Update `core/models.py` with deprecation shim and `DeprecationWarning`.
- [ ] Update `core/signals.py` per §6.2 (direct import from `notification/` is allowed).
- [ ] Update `core/tests/test_signals.py` per §6.2.
- [ ] **Do NOT** generate `core/migrations/XXXX_migrate_notificationpreference.py` unless migration graph requires it.
- [ ] **Do NOT** drop `core_notificationpreference` table.
- [ ] **Do NOT** remove `NotificationPreference` from `core/models.py` entirely — retain shim.

### Test Generation
- [ ] Generate migration tests: forward, reverse, data integrity.
- [ ] Generate deprecation warning tests for `core.models.NotificationPreference`.
- [ ] Generate model tests for `notification` `NotificationPreference`.
- [ ] Update `core/tests/test_signals.py` to use `notification.models.NotificationPreference`.
- [ ] **Do NOT** generate tests for `ai_assistant/` or `dashboard/`.
- [ ] **Do NOT** use `time.sleep()` in tests.

### Validation
- [ ] Run `ruff check .` and fix all errors.
- [ ] Run `ruff format --check .` and fix all issues.
- [ ] Run `mypy .` and fix all errors.
- [ ] Run `import-linter check` and fix all violations.
- [ ] Run `pytest tests/ -v --cov` and verify all pass.
- [ ] Run `pytest tests/architecture/ -v` and verify 0 failures.
- [ ] Run `python manage.py check` and verify 0 errors.
- [ ] Run `python manage.py makemigrations --check` and verify 0 errors.
- [ ] Run `python manage.py migrate` and verify success.
- [ ] Run `python manage.py migrate --reverse notification 0003_migrate_notificationpreference` and verify success.
- [ ] Run `python manage.py migrate` again and verify data is present.
- [ ] Run `bandit -r notification/ core/` and verify 0 high/medium.
- [ ] Run `safety check` and verify 0 critical.
- [ ] Verify row counts match after forward migration.
- [ ] Verify `DeprecationWarning` is emitted for `core.models.NotificationPreference`.

### Stop and Ask Conditions
AI must **stop and ask human** before proceeding if:
- [ ] `core/migrations/XXXX_migrate_notificationpreference.py` is required by Django's migration graph.
- [ ] `core_notificationpreference` table is empty (migration is a no-op — ask if PR is still needed).
- [ ] `notification_notificationpreference` table already has data (duplicate migration risk).
- [ ] `makemigrations` generates an unexpected migration for `notification/` or `core/`.
- [ ] Any CI gate fails after 3 fix attempts.
- [ ] Dependency matrix exception is required to complete the task.

### Commit
- [ ] Commit message follows format: `feat(notification): migrate NotificationPreference from core to notification`
- [ ] Commit body explains: data migration approach, deprecation strategy, row count verification, reference to ADR-011.
- [ ] Branch name: `feature/phase-0-003-migrate-notificationpreference`.

---

## Appendix A: Architecture Decision References

| Decision | Reference |
|----------|-----------|
| `notification/` bounded context | ADR-001, ADR-011 |
| `core/` may import from `notification/` | ADR-001 §2.3, dependency matrix |
| Data migration additivity | ADR-007 §2.5 |
| Deprecated shim retention (1 release cycle) | ADR-007 §2.5 |
| Phase 0 is additive only | ADR-007 §2.1 |
| No `apps/` parent directory | ADR-001 |

---

## Appendix B: Related Documents

- [Architecture v1.1 Release Candidate](../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Architecture v1.1 Implementation Master Plan — Phase 0](../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Phase 0 Execution Plan — PR-003](../PHASE_0_EXECUTION_PLAN.md)
- [Engineering Backlog — Feature 0.3](../ENGINEERING_BACKLOG.md)
- [Engineering Standards](../ENGINEERING_STANDARDS.md)
- [AI Engineering Playbook](../AI_ENGINEERING_PLAYBOOK.md)
- [Notification Architecture ADR](../docs/architecture/adr/ADR-011_notification_strategy.md)
- [Migration Strategy ADR](../docs/architecture/adr/ADR-007_migration_strategy.md)
- [Bounded Context Strategy ADR](../docs/architecture/adr/ADR-001_bounded_context_strategy.md)

---

## Appendix C: Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-20 | Chief Software Architect | Initial PR-003 specification for v1.1 freeze |

**Next Review:** After PR-003 merge
**Approval Required:** Platform Team Lead, Security Lead

---

*End of PR-003 Implementation Specification*
