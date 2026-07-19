# PR-002 Implementation Specification

## Migrate OwnerBankDetails to payments

---

## 1. Purpose

Execute the data migration that copies all existing `OwnerBankDetails` records from the legacy `core_ownerbankdetails` table into the new `payment_ownerbankdetails` table created in PR-001. Deprecate the legacy `core.models.OwnerBankDetails` model and update all in-app references to use `payments.models.OwnerBankDetails`.

This PR is **blocked until PR-001 is merged** because:
1. `payments` must be in `INSTALLED_APPS`
2. `payment_ownerbankdetails` table must exist (created by PR-001 migration)
3. `payments/models.py` must contain the target `OwnerBankDetails` model with encrypted fields

---

## 2. Scope

### 2.1 In Scope

- Create `payments/migrations/0002_migrate_ownerbankdetails.py` — data migration copying `core_ownerbankdetails` → `payment_ownerbankdetails`
- Create `core/migrations/XXXX_migrate_ownerbankdetails.py` — source-table migration (per P0EP; see §9.4 for placement note)
- Create `payments/tests/test_migrations.py` — forward and reverse migration tests with data integrity verification
- Create `payments/tests/test_bank_details_service.py` — service tests for bank details operations (if service exists)
- Update `payments/models.py` — ensure `OwnerBankDetails` matches original `core/models.py` fields exactly
- Update `core/models.py` — deprecate `OwnerBankDetails` with `DeprecationWarning`; retain shim for 1 release cycle
- Update `core/views/bank_views.py` — delegate to `payments/` model (see §6.2 for dependency matrix constraint)
- Update `core/services/bank_details_service.py` — delegate to `payments/` model (see §6.2 for dependency matrix constraint)
- Verify all cross-app imports of `core.models.OwnerBankDetails` are updated to `payments.models.OwnerBankDetails`

### 2.2 Out of Scope

- Creating `payments/views/bank_details_views.py` (Phase 3, PR-030)
- Creating `payments/services/bank_details_service.py` (Phase 3, PR-031)
- Creating `payments/urls.py` for bank details endpoints (Phase 3)
- Moving webhook handlers (PR-004)
- Splitting `core/views.py` (PR-005)
- Moving management commands (PR-006)
- Any changes to `core/views/reporting_views.py` or other view modules
- Any changes to `notification/`, `properties/`, or other apps outside the OwnerBankDetails migration
- Dropping the `core_ownerbankdetails` table (deferred to Phase 5)
- Any changes to `rentsecure_be/services/cashfree_service.py` or other rentsecure_be utilities (Phase 3)

---

## 3. Files

### 3.1 Files to Create

| File | Purpose | Owner |
|------|---------|-------|
| `payments/migrations/0002_migrate_ownerbankdetails.py` | Data migration: copies `core_ownerbankdetails` → `payment_ownerbankdetails` | Platform Team |
| `core/migrations/XXXX_migrate_ownerbankdetails.py` | Source-table migration marker (see §9.4 for placement guidance) | Platform Team |
| `payments/tests/test_migrations.py` | Migration forward/reverse tests + data integrity tests | Platform Team |
| `payments/tests/test_bank_details_service.py` | Service tests for bank details CRUD and encryption | Platform Team |

### 3.2 Files to Modify

| File | Change | Owner |
|------|--------|-------|
| `payments/models.py` | Ensure `OwnerBankDetails` fields exactly match original `core/models.py` definition; add `__str__`, Meta class | Platform Team |
| `core/models.py` | Add `DeprecationWarning` to `OwnerBankDetails`; retain model as shim mapping to `core_ownerbankdetails` table | Platform Team |
| `core/views/bank_views.py` | Update imports to use `payments.models.OwnerBankDetails` (see §6.2 constraint) | Platform Team |
| `core/services/bank_details_service.py` | Update imports to use `payments.models.OwnerBankDetails` (see §6.2 constraint) | Platform Team |

### 3.3 Files to Delete

None.

**Note on `core/migrations/XXXX_migrate_ownerbankdetails.py`:** Django data migrations that copy data between apps typically live in the target app's migration chain. This file is listed in P0EP as a "source table" marker. The implementer must verify whether Django's migration dependency graph requires a companion migration in `core/`. If `payments/migrations/0002` can declare a dependency on the existing `core` migration that created `core_ownerbankdetails`, then the `core/` migration is unnecessary and must not be created. See §9.4.

---

## 4. Responsibilities

| Role | Responsibility |
|------|----------------|
| **Platform Team Lead** | Owns `payments/migrations/0002_migrate_ownerbankdetails.py`, `payments/tests/`, `core/models.py` deprecation. Approves PR. |
| **Security Lead** | Reviews data migration for encrypted field handling. Verifies no plaintext data exposure during migration. |
| **Developer** | Implements data migration, deprecation shim, test updates, and reference updates. Runs full validation. |
| **AI Assistant** | Generates migration, tests, and doc updates per this spec. Stops and asks if dependency matrix is violated. |

---

## 5. Acceptance Criteria

### 5.1 Functional

- [ ] `payments/migrations/0002_migrate_ownerbankdetails.py` exists and is generated/applied correctly.
- [ ] Migration copies **every row** from `core_ownerbankdetails` to `payment_ownerbankdetails` without loss.
- [ ] Encrypted fields (`bank_account_number`, `ifsc_code`) are preserved correctly during copy — ciphertext is copied as-is, not re-encrypted.
- [ ] `core/models.py` `OwnerBankDetails` emits `DeprecationWarning` when imported or instantiated.
- [ ] `core/models.py` `OwnerBankDetails` continues to map to `core_ownerbankdetails` table (shim).
- [ ] All cross-app imports of `core.models.OwnerBankDetails` are updated to `payments.models.OwnerBankDetails`.
- [ ] `core/views/bank_views.py` and `core/services/bank_details_service.py` reference `payments.models.OwnerBankDetails` or delegate appropriately.
- [ ] `python manage.py migrate` applies all migrations cleanly on a fresh database.
- [ ] `python manage.py migrate` applies all migrations cleanly on a database with existing `core_ownerbankdetails` data.
- [ ] `python manage.py migrate --reverse` reverses the data migration cleanly on test database.

### 5.2 Non-Functional

- [ ] Data migration runs in <30 seconds on production-like data volume (tested on staging copy).
- [ ] Row count after forward migration equals row count before migration.
- [ ] Checksum of sensitive fields matches before/after (ciphertext integrity).
- [ ] All tests pass (existing + new).
- [ ] No architecture test violations.
- [ ] No import-linter violations.
- [ ] No circular dependencies introduced.
- [ ] No security vulnerabilities (Bandit 0 high/medium).

---

## 6. Architecture Rules

### 6.1 Bounded Context Compliance

- `payments/` owns `OwnerBankDetails` from this point forward.
- `core/` retains a deprecated shim of `OwnerBankDetails` for exactly 1 release cycle. The shim maps to `core_ownerbankdetails` table, which remains in the database until Phase 5.
- `properties/`, `notification/`, `finance/`, and other apps must import `OwnerBankDetails` from `payments/models.py`, not `core/models.py`.
- The `core_ownerbankdetails` table is read-only during the transition period. All new writes go to `payment_ownerbankdetails`.

### 6.2 Import Rules

**Critical dependency matrix constraint:**

| Source | payment | identity (core) |
|--------|---------|-----------------|
| **payment** | ✗ | ✓ (payment may import from identity via `settings.AUTH_USER_MODEL`) |
| **identity** | ✗ | ✗ |

`identity/` (i.e., `core/`) **cannot** import from `payment/` per the v1.1 dependency matrix.

**Implications for this PR:**

1. `core/models.py` **must not** contain `from payments.models import OwnerBankDetails`. The deprecation shim must be a standalone model definition in `core/models.py` that maps to the `core_ownerbankdetails` table.
2. `core/views/bank_views.py` **must not** directly import `payments.models.OwnerBankDetails` unless the Architecture Review Board approves an exception via ADR.
3. `core/services/bank_details_service.py` **must not** directly import `payments.models.OwnerBankDetails` unless an ADR exception is granted.

**If the task requires `core/` to import from `payments/`, AI must STOP and ask for approval.**

**Permitted pattern for Phase 0:** `core/views/bank_views.py` and `core/services/bank_details_service.py` continue operating against the legacy `core_ownerbankdetails` table via the `core.models.OwnerBankDetails` shim. Full migration to `payments/` imports occurs in Phase 3 when the views/services are moved to `payments/`.

### 6.3 Model Rules

- `payments/models.py` `OwnerBankDetails` must match the original `core/models.py` definition field-for-field.
- `user` ForeignKey must use `settings.AUTH_USER_MODEL` string reference (not `from core.models import User`).
- `bank_account_number` and `ifsc_code` must use `EncryptedCharField` from `shared/fields.py`.
- Model file (`payments/models.py`) must not exceed 400 lines.
- Model must not contain business logic.
- `core/models.py` `OwnerBankDetails` shim must emit `DeprecationWarning` on import/instantiation.

### 6.4 Migration Rules

- Data migration must be **additive** (copy only, never delete).
- Old `core_ownerbankdetails` table must remain for 1 release cycle.
- Migration must be **reversible** — reverse operation must restore `core_ownerbankdetails` data or be marked irreversible with justification.
- Migration must include **data integrity checks**: row count, checksum of encrypted fields.
- Migration must be tested on a production-like data copy before merge.
- AI must **never** modify existing migration files that have already been applied to production.
- AI must **never** generate a migration that drops `core_ownerbankdetails` in this PR.

### 6.5 Security Rules

- Encrypted fields (`bank_account_number`, `ifsc_code`) must not be decrypted and re-encrypted during migration — copy ciphertext as-is.
- Migration must not log plaintext bank details or IFSC codes.
- Migration must not expose encrypted data in error messages or stack traces.
- `django-cryptography` fields must be handled transparently by the migration ORM layer.

### 6.6 Naming Rules

- Migration file: `0002_migrate_ownerbankdetails.py` (in `payments/migrations/`).
- Test files: `test_migrations.py`, `test_bank_details_service.py`.
- Test classes: `TestOwnerBankDetailsMigration`, `TestBankDetailsService`.
- Test methods: `test_migrates_all_rows`, `test_reverse_migration_restores_data`, `test_encrypted_fields_preserved`.

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
| Security | Bandit | 0 high/medium | `bandit -r payments/ core/` |
| Dependency | Safety | 0 critical | `safety check` |

### 7.2 Pipeline Order

```
Lint → Type Check → Import Rules → Tests → Architecture → Django Check → Migrations → Security → Dependency
```

### 7.3 Phase-Specific Architecture Tests

| Test | Purpose | Expected Result |
|------|---------|-----------------|
| `test_import_rules.py` | No forbidden SDK imports in new code | Pass |
| `test_layer_compliance.py` | No view imports from `payment/` in `core/` (see §6.2) | Pass |
| `test_rentsecure_be_boundary.py` | No app imports from `rentsecure_be/` | Pass |
| `test_god_models.py` | `payments/models.py` ≤400 lines | Pass |
| `test_circular_deps.py` | No new circular dependencies | Pass |

**Note on `test_layer_compliance.py`:** This test must verify that `core/` does not import from `payments/`. If the implementation requires such an import, an ADR exception must be obtained before proceeding.

---

## 8. Testing Strategy

### 8.1 Test Tiers Required

| Tier | Scope | Requirement |
|------|-------|-------------|
| **Unit** | Deprecation warning in `core/models.py` | ≥90% coverage |
| **Migration** | Forward + reverse data migration | Forward + reverse pass |
| **Integration** | Bank details API after migration | ≥80% coverage |
| **Architecture** | Import boundaries, layer compliance | 0 violations |
| **Security** | Bandit scan on changed files | 0 high/medium |

### 8.2 Unit Tests: `core/models.py` Deprecation Shim

Required test cases (`payments/tests/test_deprecation.py` or `core/tests/test_models.py`):
- `test_owner_bank_details_emits_deprecation_warning` — importing or instantiating `core.models.OwnerBankDetails` emits `DeprecationWarning`
- `test_owner_bank_details_shim_maps_to_core_table` — shim model maps to `core_ownerbankdetails` table
- `test_owner_bank_details_shim_has_all_fields` — shim has same fields as original model

### 8.3 Migration Tests: `payments/tests/test_migrations.py`

Required test cases:
- `test_migration_forward_copies_all_rows` — row count in `payment_ownerbankdetails` equals row count in `core_ownerbankdetails` before migration
- `test_migration_forward_preserves_encrypted_fields` — ciphertext of `bank_account_number` and `ifsc_code` is identical before/after copy
- `test_migration_forward_preserves_user_links` — `user_id` values are preserved
- `test_migration_forward_preserves_timestamps` — `created_at` and `updated_at` are preserved
- `test_migration_reverse_restores_data` — `migrate --reverse` restores original state (or marks irreversible with justification)
- `test_migration_on_empty_database` — migration runs cleanly when `core_ownerbankdetails` is empty
- `test_migration_on_production_like_data` — migration runs on a copy of production data without errors

### 8.4 Model Tests: `payments/tests/test_models.py`

Required test cases (in addition to those created in PR-001):
- `test_owner_bank_details_matches_original_schema` — field names, types, and constraints match `core/models.py` original
- `test_unique_together_user_and_bank_account` — duplicate `(user, bank_account_number)` raises `IntegrityError`
- `test_user_foreign_key_uses_auth_user_model_string` — `user` field uses `settings.AUTH_USER_MODEL`, not direct import

### 8.5 Service Tests: `payments/tests/test_bank_details_service.py`

If `payments/services/bank_details_service.py` exists (Phase 3 creates it; if not yet present, this test file is created in anticipation):
- `test_creates_owner_bank_details_with_encryption` — service creates record with encrypted fields
- `test_retrieves_owner_bank_details` — service retrieves by user
- `test_updates_owner_bank_details` — service updates bank details
- `test_deletes_owner_bank_details` — service deletes bank details

**If `payments/services/bank_details_service.py` does not exist yet, create the test file with placeholder tests that will be filled in Phase 3.**

### 8.6 Contract Tests

No new contract tests are required in this PR. The `payment ↔ property` contract is already covered by existing tests. Contract tests for bank details API are added in Phase 3 when `payments/views/bank_details_views.py` is created.

### 8.7 Architecture Tests

AI must verify the following architecture tests pass after changes:
- `test_import_rules.py` — no forbidden imports in new/modified files
- `test_layer_compliance.py` — `core/` does not import from `payments/` (unless ADR exception granted)
- `test_rentsecure_be_boundary.py` — no `rentsecure_be/` imports in new/modified files
- `test_shared_purity.py` — `shared/fields.py` still passes (no regressions from PR-001)
- `test_god_models.py` — `payments/models.py` ≤400 lines
- `test_circular_deps.py` — no new circular dependencies

### 8.8 Security Tests

- Run `bandit -r payments/ core/` and verify 0 high/medium findings.
- Verify no plaintext `bank_account_number` or `ifsc_code` appears in migration test output.
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
Verifies `payment_ownerbankdetails` table exists.

**Step 2: Apply PR-002 data migration**
```bash
python manage.py migrate payments
```
Runs `0002_migrate_ownerbankdetails.py`. Copies all rows from `core_ownerbankdetails` to `payment_ownerbankdetails`.

**Step 3: Verify data integrity**
```bash
python manage.py shell -c "
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('SELECT COUNT(*) FROM core_ownerbankdetails')
    core_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM payment_ownerbankdetails')
    payment_count = cursor.fetchone()[0]
    assert core_count == payment_count, f'Row count mismatch: {core_count} vs {payment_count}'
"
```

### 9.2 Data Migration Details

**Source:** `core_ownerbankdetails`
**Target:** `payment_ownerbankdetails`
**Operation:** `INSERT INTO payment_ownerbankdetails SELECT * FROM core_ownerbankdetails`

**Field mapping (must be exact):**

| Source (`core_ownerbankdetails`) | Target (`payment_ownerbankdetails`) | Notes |
|--------------------------------|-------------------------------------|-------|
| `id` | `id` | Preserve original PK |
| `user_id` | `user_id` | ForeignKey to `core_user` |
| `bank_account_number` | `bank_account_number` | Encrypted field — copy ciphertext as-is |
| `ifsc_code` | `ifsc_code` | Encrypted field — copy ciphertext as-is |
| `created_at` | `created_at` | Preserve original timestamp |
| `updated_at` | `updated_at` | Preserve original timestamp |

**Critical constraint:** Encrypted fields must not be decrypted and re-encrypted during migration. Copy the raw ciphertext from the database to preserve encryption integrity and avoid keying issues.

### 9.3 Reverse Migration

**Operation:** `DELETE FROM payment_ownerbankdetails` (or mark migration as irreversible with justification).

**Preferred approach:** Reverse migration deletes rows from `payment_ownerbankdetails` that were added by the forward migration. Since the old `core_ownerbankdetails` table remains untouched, data is not lost.

```python
# In payments/migrations/0002_migrate_ownerbankdetails.py
def reverse(apps, schema_editor):
    # Delete rows that were copied from core
    # WARNING: This deletes data from payment_ownerbankdetails
    # Core data remains in core_ownerbankdetails
    pass
```

**If reverse migration is marked irreversible:** Provide justification in migration file docstring:
```python
"""
This migration is irreversible because it copies encrypted data
between tables and the reverse operation cannot reliably determine
which rows were copied vs. newly created.
The core_ownerbankdetails table is retained for reference.
"""
```

### 9.4 Migration Placement Note

The P0EP lists two migration files:
- `payments/migrations/0002_migrate_ownerbankdetails.py` — primary data migration
- `core/migrations/XXXX_migrate_ownerbankdetails.py` — source-table migration

**Standard Django pattern:** Cross-app data migrations live in the **target app's** migration chain. The target migration declares a dependency on the source app's migration that created the source table.

**Decision for this PR:** Create **only** `payments/migrations/0002_migrate_ownerbankdetails.py` with a dependency on the `core` migration that created `core_ownerbankdetails`. Do **not** create `core/migrations/XXXX_migrate_ownerbankdetails.py` unless Django's migration graph requires it (e.g., if `payments/0002` cannot declare a dependency on `core/` due to circular migration dependencies). If such a circular dependency exists, stop and ask the human to resolve the migration graph before proceeding.

### 9.5 Data Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Row count mismatch | Low | High | Verify row counts before/after in test and staging |
| Ciphertext corruption | Low | High | Copy ciphertext as-is; do not decrypt/re-encrypt |
| Partial migration (crash mid-run) | Low | Medium | Migration runs in single transaction; Django wraps in atomic |
| Reverse migration data loss | Medium | Medium | Mark as irreversible OR delete only copied rows |
| Duplicate rows on re-run | Low | Low | Use `get_or_create` or check for existing rows |

---

## 10. Rollback Plan

### 10.1 Rollback Triggers

Rollback is triggered if any of the following occur:
- Data migration fails on staging or production (`OperationalError`, `ProgrammingError`).
- Row count after migration does not match row count before migration.
- Encrypted field values are corrupted (ciphertext changed during copy).
- `core/models.py` deprecation shim causes `ImportError` or `AttributeError` in existing code.
- Any CI gate fails after merge and cannot be fixed within 30 minutes.
- Production incident: bank details API returns 500 errors after deployment.
- Security finding: plaintext bank details exposed in migration logs or error messages.

### 10.2 Rollback Steps

1. **Deploy decision:** Confirm rollback decision with Platform Team Lead.
2. **Git revert:**
   ```bash
   git revert <PR-002-merge-commit-sha>
   git push origin main
   ```
3. **Reverse migration:**
   ```bash
   python manage.py migrate --reverse payments 0002_migrate_ownerbankdetails
   ```
   If reverse migration is marked irreversible, skip this step. The `payment_ownerbankdetails` table will remain but will be empty or contain stale data. Old `core_ownerbankdetails` table is unaffected.
4. **Restore `core/models.py`:** If `OwnerBankDetails` was removed (not just deprecated), restore it from the `main` branch pre-PR-002 state.
5. **Deploy reverted code:** Deploy the reverted commit to staging, then production.
6. **Smoke tests:**
   ```bash
   python manage.py check
   python manage.py migrate
   python manage.py shell -c "from core.models import OwnerBankDetails; print(OwnerBankDetails.objects.count())"
   ```
7. **Verify production health:** Check that bank details API endpoints return 200 (not 500). Verify that `core_ownerbankdetails` table is accessible.
8. **Notify team:** Post rollback completion notice with root cause and fix plan.

### 10.3 Estimated Rollback Time

**30 minutes** (git revert + migrate --reverse + deploy + smoke tests).

### 10.4 Data Risk

**Low.** The data migration is additive — it copies data from `core_ownerbankdetails` to `payment_ownerbankdetails` without deleting source data. Reverse migration removes copied rows from `payment_ownerbankdetails`. The original `core_ownerbankdetails` table is never modified by this PR.

### 10.5 Rollback Validation

- Rollback must be tested on staging **before** production deploy.
- Test sequence:
  1. Apply PR-002 to staging.
  2. Run data migration.
  3. Verify `payment_ownerbankdetails` has all rows.
  4. Execute rollback steps 2-7 above.
  5. Verify `core_ownerbankdetails` is still accessible and unchanged.
  6. Re-apply PR-002 after successful rollback test.

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
| `payments/migrations/0002_migrate_ownerbankdetails.py` | ~45 | Data migration with forward and reverse functions |
| `core/migrations/XXXX_migrate_ownerbankdetails.py` | ~0–40 | Source-table migration marker (see §9.4; may not be needed) |
| `payments/tests/test_migrations.py` | ~90 | Forward/reverse tests + data integrity tests |
| `payments/tests/test_bank_details_service.py` | ~75 | Service tests (placeholder or full, depending on service existence) |

### 11.3 Files Modified (~100 lines)

| File | Approx Lines Changed | Description |
|------|----------------------|-------------|
| `payments/models.py` | +8, -0 | Ensure field definitions match original; add `__str__` and Meta if missing |
| `core/models.py` | +12, -5 | Add `DeprecationWarning` to `OwnerBankDetails`; retain shim |
| `core/views/bank_views.py` | +5, -5 | Update imports to reference `payments.models.OwnerBankDetails` (if dependency matrix allows) |
| `core/services/bank_details_service.py` | +5, -5 | Update imports to reference `payments.models.OwnerBankDetails` (if dependency matrix allows) |

### 11.4 Diff Constraints

- No file in the diff may exceed 400 lines total after modification.
- No more than 15 files changed (actual count: 7 — well within limit).
- No deletions of existing functionality.

---

## 12. Definition of Done

PR-002 is **Done** when ALL of the following are true.

### Code
- [ ] `payments/migrations/0002_migrate_ownerbankdetails.py` created and tested.
- [ ] `core/models.py` `OwnerBankDetails` deprecated with `DeprecationWarning` (shim retained).
- [ ] `payments/models.py` `OwnerBankDetails` matches original schema exactly.
- [ ] All cross-app imports updated to `payments.models.OwnerBankDetails` where dependency matrix allows.
- [ ] `core/views/bank_views.py` and `core/services/bank_details_service.py` updated per §6.2 constraints.
- [ ] `core/migrations/XXXX_migrate_ownerbankdetails.py` created only if migration graph requires it.

### Tests
- [ ] `payments/tests/test_migrations.py` created with all required test cases.
- [ ] `payments/tests/test_bank_details_service.py` created (full or placeholder).
- [ ] All new tests pass.
- [ ] All existing tests pass (no regressions).
- [ ] Migration forward test passes (row count matches).
- [ ] Migration reverse test passes (or marked irreversible with justification).
- [ ] Data integrity verified (checksums, timestamps, user links).
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
- [ ] `bandit -r payments/ core/` passes (0 high/medium).
- [ ] `safety check` passes (0 critical).

### Architecture
- [ ] No `rentsecure_be/` imports in new/modified files.
- [ ] No circular dependencies introduced.
- [ ] `payments/models.py` ≤400 lines.
- [ ] `core/models.py` shim does not import from `payments/` (dependency matrix compliance).
- [ ] Data migration is reversible (or marked irreversible with justification).

### Documentation
- [ ] `docs/architecture/contexts/payment.md` updated with `OwnerBankDetails` migration info.
- [ ] ADR-004 updated to reflect PR-002 completion.
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
- [ ] Verify `payments` is in `INSTALLED_APPS`.
- [ ] Verify `payments/models.py` exists with `OwnerBankDetails`.
- [ ] Verify `payment_ownerbankdetails` table exists in database.
- [ ] Verify `core_ownerbankdetails` table exists and has data (check row count).
- [ ] Read `ENGINEERING_STANDARDS.md` sections: Model Rules, Import Rules, Migrations, Security.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Dependency Rules, Migration Rules, Files AI Must Never Modify Automatically.
- [ ] Verify `django-cryptography` is installed and working (from PR-001).
- [ ] Check current `core/models.py` for existing `OwnerBankDetails` definition.
- [ ] Check current `core/views/bank_views.py` for `OwnerBankDetails` imports.
- [ ] Check current `core/services/bank_details_service.py` for `OwnerBankDetails` imports.
- [ ] Confirm dependency matrix constraint: `core/` cannot import from `payment/` (see §6.2).

### Implementation
- [ ] Create `payments/migrations/0002_migrate_ownerbankdetails.py` with forward and reverse functions.
- [ ] Create `payments/tests/test_migrations.py` with all required test cases.
- [ ] Create `payments/tests/test_bank_details_service.py` (full or placeholder).
- [ ] Update `payments/models.py` to match original `OwnerBankDetails` schema exactly.
- [ ] Update `core/models.py` to add `DeprecationWarning` to `OwnerBankDetails` shim.
- [ ] Update `core/views/bank_views.py` imports per §6.2 (delegation pattern, no direct import if prohibited).
- [ ] Update `core/services/bank_details_service.py` imports per §6.2.
- [ ] Run `python manage.py makemigrations --check` (should not generate new migrations for existing models).
- [ ] Run `python manage.py migrate` and verify success.

### Testing
- [ ] Run `pytest payments/tests/test_migrations.py -v`.
- [ ] Run `pytest payments/tests/test_bank_details_service.py -v`.
- [ ] Run `pytest payments/tests/test_models.py -v` (from PR-001).
- [ ] Run `pytest tests/ -v --cov` and verify ≥90% coverage for new code.
- [ ] Run `pytest tests/architecture/ -v` and verify 0 failures.
- [ ] Run `python manage.py migrate --reverse payments 0002_migrate_ownerbankdetails` and verify success.
- [ ] Run `python manage.py migrate` again and verify data is restored.
- [ ] Verify row counts: `core_ownerbankdetails` count == `payment_ownerbankdetails` count after forward migration.
- [ ] Verify encrypted fields: ciphertext in `payment_ownerbankdetails` matches ciphertext in `core_ownerbankdetails`.
- [ ] Verify `DeprecationWarning` is emitted when importing `core.models.OwnerBankDetails`.

### Validation
- [ ] Run `ruff check .` and verify 0 errors.
- [ ] Run `ruff format --check .` and verify 0 issues.
- [ ] Run `mypy .` and verify 0 errors.
- [ ] Run `import-linter check` and verify 0 violations.
- [ ] Run `python manage.py check` and verify 0 errors.
- [ ] Run `python manage.py makemigrations --check` and verify 0 errors.
- [ ] Run `bandit -r payments/ core/` and verify 0 high/medium.
- [ ] Run `safety check` and verify 0 critical.
- [ ] Verify no `print()` statements in new code.
- [ ] Verify no `# TODO` or `# FIXME` comments.
- [ ] Verify no commented-out code.
- [ ] Verify no hardcoded secrets.
- [ ] Verify no `from rentsecure_be.X import Y` in new code.
- [ ] Verify `core/models.py` shim does not import from `payments/`.

### Rollback
- [ ] Document rollback plan in PR description.
- [ ] Test rollback on staging: apply PR-002, verify data, execute rollback, verify `core_ownerbankdetails` intact.

### PR
- [ ] Commit message follows conventional commits format.
- [ ] Branch name follows `<type>/<ticket-id>-<description>` format.
- [ ] PR description includes: summary, motivation, changes, testing, rollback plan.
- [ ] PR size is within limits (≤400 lines, ≤15 files — actual: ~295 lines, 7 files).
- [ ] PR is linked to Phase 0 task 0.2 and 0.3.

---

## 14. Reviewer Checklist

Use this checklist when reviewing PR-002.

### Architecture
- [ ] `payments/migrations/0002_migrate_ownerbankdetails.py` is additive (copies data, does not delete).
- [ ] `core/models.py` `OwnerBankDetails` is a deprecated shim, not a new model importing from `payments/`.
- [ ] `core/` does NOT import from `payments/` (dependency matrix compliance).
- [ ] `core/views/bank_views.py` and `core/services/bank_details_service.py` updates comply with §6.2.
- [ ] No circular dependencies introduced.
- [ ] No new `apps/` or `config/` directories.
- [ ] `payments/models.py` matches original `core/models.py` schema field-for-field.
- [ ] Old `core_ownerbankdetails` table is retained (not dropped).

### Security
- [ ] Encrypted fields are copied as ciphertext (not decrypted/re-encrypted).
- [ ] No plaintext bank details or IFSC codes in migration code or logs.
- [ ] No secrets or API keys in migration files.
- [ ] `DeprecationWarning` is emitted for `core.models.OwnerBankDetails`.
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
- [ ] `payments/tests/test_migrations.py` covers all required test cases.
- [ ] `payments/tests/test_bank_details_service.py` covers all required test cases (or is a valid placeholder).
- [ ] All new tests pass.
- [ ] All existing tests pass (no regressions).
- [ ] Migration forward test passes on staging data copy.
- [ ] Migration reverse test passes on test database.
- [ ] Data integrity verified (row counts, checksums, timestamps).
- [ ] No test uses `time.sleep()`.
- [ ] No test depends on execution order.
- [ ] Tests use factories, not hardcoded data.

### Migrations
- [ ] `payments/migrations/0002_migrate_ownerbankdetails.py` is reversible or marked irreversible with justification.
- [ ] Migration declares dependency on `core` migration that created `core_ownerbankdetails`.
- [ ] `core/migrations/XXXX_migrate_ownerbankdetails.py` exists only if migration graph requires it.
- [ ] Migration runs in <30 seconds on staging data copy.
- [ ] `python manage.py migrate --reverse` works on test database.

### Documentation
- [ ] `docs/architecture/contexts/payment.md` updated with migration details.
- [ ] ADR-004 updated to reflect PR-002 completion.
- [ ] CHANGELOG.md updated.
- [ ] PR description includes rollback plan and data integrity verification steps.

### CI
- [ ] All CI gates pass.
- [ ] No import-linter violations.
- [ ] No architecture test failures.
- [ ] No circular dependency warnings.

---

## 15. AI Checklist

Use this checklist when generating PR-002 with AI assistance.

### Pre-Generation
- [ ] Read `ENGINEERING_STANDARDS.md` sections: Model Rules, Import Rules, Migrations, Security.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Dependency Rules, Migration Rules, Files AI Must Never Modify Automatically.
- [ ] Verify PR-001 is merged to `phase-0-foundation` branch.
- [ ] Verify `payments` is in `INSTALLED_APPS`.
- [ ] Verify `payment_ownerbankdetails` table exists.
- [ ] Verify `core_ownerbankdetails` table exists and has data.
- [ ] Verify `django-cryptography` is installed and functional.
- [ ] Verify `core/migrations/` migration history to determine if `core/migrations/XXXX_migrate_ownerbankdetails.py` is needed.
- [ ] Confirm dependency matrix constraint: `core/` cannot import from `payment/` (§6.2).

### Code Generation
- [ ] Generate `payments/migrations/0002_migrate_ownerbankdetails.py` with forward and reverse functions.
- [ ] Generate `payments/tests/test_migrations.py` with all required test cases.
- [ ] Generate `payments/tests/test_bank_details_service.py` (full or placeholder).
- [ ] Update `payments/models.py` to match original schema.
- [ ] Update `core/models.py` with deprecation shim and `DeprecationWarning`.
- [ ] Update `core/views/bank_views.py` per §6.2 (delegation only, no direct import from `payments/`).
- [ ] Update `core/services/bank_details_service.py` per §6.2.
- [ ] **Do NOT** generate `core/migrations/XXXX_migrate_ownerbankdetails.py` unless migration graph requires it.
- [ ] **Do NOT** drop `core_ownerbankdetails` table.
- [ ] **Do NOT** remove `OwnerBankDetails` from `core/models.py` entirely — retain shim.

### Test Generation
- [ ] Generate migration tests: forward, reverse, data integrity.
- [ ] Generate deprecation warning tests for `core.models.OwnerBankDetails`.
- [ ] Generate service tests for `payments` bank details (if service exists).
- [ ] **Do NOT** generate tests for `ai_assistant/` or `dashboard/`.
- [ ] **Do NOT** use `time.sleep()` in tests.
- [ ] **Do NOT** hardcode test data — use factories.

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
- [ ] Run `python manage.py migrate --reverse payments 0002_migrate_ownerbankdetails` and verify success.
- [ ] Run `python manage.py migrate` again and verify data is present.
- [ ] Run `bandit -r payments/ core/` and verify 0 high/medium.
- [ ] Run `safety check` and verify 0 critical.
- [ ] Verify row counts match after forward migration.
- [ ] Verify `DeprecationWarning` is emitted for `core.models.OwnerBankDetails`.

### Stop and Ask Conditions
AI must **stop and ask human** before proceeding if:
- [ ] `core/views/bank_views.py` or `core/services/bank_details_service.py` **must** import from `payments/` and no delegation pattern satisfies the requirement.
- [ ] `core/migrations/XXXX_migrate_ownerbankdetails.py` is required by Django's migration graph.
- [ ] `core_ownerbankdetails` table is empty (migration is a no-op — ask if PR is still needed).
- [ ] `payment_ownerbankdetails` table already has data (duplicate migration risk).
- [ ] `makemigrations` generates an unexpected migration for `payments/` or `core/`.
- [ ] Any CI gate fails after 3 fix attempts.
- [ ] `django-cryptography` causes issues with the migration (e.g., fields cannot be copied as ciphertext).
- [ ] Dependency matrix exception is required to complete the task.

### Commit
- [ ] Commit message follows format: `feat(payments): migrate OwnerBankDetails from core to payments`
- [ ] Commit body explains: data migration approach, deprecation strategy, row count verification, reference to ADR-004.
- [ ] Branch name: `feature/phase-0-002-migrate-ownerbankdetails`.

---

## Appendix A: Architecture Decision References

| Decision | Reference |
|----------|-----------|
| `payments/` bounded context | ADR-001, ADR-004 |
| Encrypted bank fields | ADR-004, ADR-005 |
| Data migration additivity | ADR-007 §2.5 |
| `core/` cannot import from `payment/` | ADR-001 §2.3, dependency matrix |
| `core.User` as `AUTH_USER_MODEL` | ADR-002 |
| Deprecated shim retention (1 release cycle) | ADR-007 §2.5 |
| Phase 0 is additive only | ADR-007 §2.1 |
| No `apps/` parent directory | ADR-001 |
| No `rent/` bounded context | ADR-001 |

---

## Appendix B: Related Documents

- [Architecture v1.1 Release Candidate](../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Architecture v1.1 Implementation Master Plan — Phase 0](../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Phase 0 Execution Plan — PR-002](../PHASE_0_EXECUTION_PLAN.md)
- [Engineering Backlog — Feature 0.2](../ENGINEERING_BACKLOG.md)
- [Engineering Standards](../ENGINEERING_STANDARDS.md)
- [AI Engineering Playbook](../AI_ENGINEERING_PLAYBOOK.md)
- [Payment Architecture ADR](../docs/architecture/adr/ADR-004_payment_architecture.md)
- [Migration Strategy ADR](../docs/architecture/adr/ADR-007_migration_strategy.md)
- [Shared Kernel Rules ADR](../docs/architecture/adr/ADR-005_shared_kernel_rules.md)

---

## Appendix C: Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-19 | Chief Software Architect | Initial PR-002 specification for v1.1 freeze |

**Next Review:** After PR-002 merge
**Approval Required:** Platform Team Lead, Security Lead

---

*End of PR-002 Implementation Specification*
