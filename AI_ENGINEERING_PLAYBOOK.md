# RentSecure AI Engineering Playbook

**Status:** MANDATORY
**Effective Date:** 2026-07-19
**Applies To:** All AI coding assistants (ChatGPT, Codex, Claude Code, Gemini CLI, etc.) working on RentSecureBE
**Authority:** Chief Software Architect / Architecture Review Board
**Source of Truth:** ENGINEERING_STANDARDS.md, ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md, ADR-001 through ADR-010

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Architecture Constraints](#2-architecture-constraints)
3. [Allowed Modifications](#3-allowed-modifications)
4. [Forbidden Modifications](#4-forbidden-modifications)
5. [Dependency Rules](#5-dependency-rules)
6. [Import Rules](#6-import-rules)
7. [Migration Rules](#7-migration-rules)
8. [Testing Requirements](#8-testing-requirements)
9. [Documentation Requirements](#9-documentation-requirements)
10. [Code Review Checklist](#10-code-review-checklist)
11. [PR Checklist](#11-pr-checklist)
12. [Commit Message Standards](#12-commit-message-standards)
13. [Branch Naming](#13-branch-naming)
14. [Rollback Requirements](#14-rollback-requirements)
15. [Architecture Validation](#15-architecture-validation)
16. [When AI Must Stop and Ask for Approval](#16-when-ai-must-stop-and-ask-for-approval)
17. [Files AI Must Never Modify Automatically](#17-files-ai-must-never-modify-automatically)
18. [Definition of Completion](#18-definition-of-completion)
19. [Definition of Success](#19-definition-of-success)

---

## 1. Purpose

This playbook defines how AI coding assistants must operate on the RentSecureBE repository. It translates the Architecture v1.1, Engineering Standards, and ADRs into actionable rules for AI agents.

**Core principle:** AI assists with implementation, but the human engineer owns the architecture. When in doubt, AI must stop and ask.

---

## 2. Architecture Constraints

AI must understand and respect these non-negotiable architectural constraints.

### 2.1 Modular Monolith

- RentSecureBE is a **single Django project** with bounded contexts as Django apps.
- Apps live at the **project root** (not in `apps/` or `config/`).
- No microservices in Year 1. Service extraction is a configuration change, not a rewrite.
- The `rentsecure_be/` directory is **not a service locator**. No app may import from it.

### 2.2 Bounded Contexts

Active bounded contexts (Django apps):

| Context | App Directory | Owner |
|---------|--------------|-------|
| Identity | `core/` (models) + `identity/` (services) | Platform Team |
| Property | `properties/` | Product Team |
| Subscription | `subscription/` | Platform Team |
| Payment | `payments/` | Platform Team |
| Notification | `notification/` | Platform Team |
| Document | `documents/` | Product Team |
| Finance | `finance/` | Product Team |
| Referral | `referral/` | Product Team |

Deferred contexts:

| Context | App Directory | Status |
|---------|--------------|--------|
| Dashboard | `dashboard/` | Experimental / Not Deployed |
| AI Assistant | `smartbot/` (active), `ai_assistant/` (dead code) | Experimental / Not Deployed |

### 2.3 User Model

- `core.User` remains `AUTH_USER_MODEL` **permanently**.
- AI must **never** propose moving the Django user model between apps.
- All ForeignKeys must use `settings.AUTH_USER_MODEL` string references.
- Direct imports of `core.models.User` are FORBIDDEN in models, views, and services.

### 2.4 Rent Context

- The `rent/` bounded context is **rejected**.
- Rent logic stays in `properties/` permanently.
- AI must **never** create a `rent/` app or propose extracting rent logic into a separate context.

### 2.5 Phase Boundaries

- Phase -1: Break circular dependencies (no breaking changes).
- Phase 0: Foundation & critical fixes (no breaking changes).
- Phase 1-4: Service extraction (no breaking changes, backward-compatible shims).
- Phase 5: Deprecate Core — **ONLY BREAKING CHANGE** (v2.0.0).
- Phase 6: Optimization (no breaking changes).

AI must respect phase boundaries. Do not implement Phase 2 tasks before Phase 1 is complete.

### 2.6 Size Limits

| Artifact | Limit | Action if Exceeded |
|----------|-------|-------------------|
| View file | 300 lines | Split by domain responsibility |
| Model file | 400 lines | Split into `model.py`, `validators.py`, `choices.py` |

### 2.7 Forbidden Directories

AI must **never** create or propose:
- `apps/` parent directory
- `config/` app
- Root `management/commands/` directory (commands belong in app directories)

---

## 3. Allowed Modifications

AI may perform the following modifications **only** within the scope of the assigned task.

### 3.1 Code Changes

- Create new files in the owning app's subdirectories (`models/`, `services/`, `views/`, `tests/`, `management/commands/`).
- Edit existing files within the owning app.
- Move files between apps **only** when explicitly specified in the task and when the move is part of an approved phase.
- Refactor code within a single app to improve readability or reduce duplication.

### 3.2 Test Changes

- Create new test files in `app/tests/unit/`, `app/tests/integration/`, `app/tests/contract/`.
- Update existing tests to reflect code changes.
- Add architecture tests in `tests/architecture/` when explicitly requested.
- Update test factories in `tests/factories.py`.

### 3.3 Configuration Changes

- Edit `rentsecure_be/settings/` files when explicitly required.
- Edit `.github/workflows/ci.yml` when explicitly required.
- Edit `import-linter.ini` when explicitly required and in Phase 0.
- Edit `pyproject.toml`, `pytest.ini`, `mypy.ini`, `ruff.toml` for tooling configuration.

### 3.4 Documentation Changes

- Update `docs/architecture/contexts/<name>.md` when bounded context changes.
- Update `docs/api/` when API endpoints change.
- Update `CHANGELOG.md` for releases.
- Update `ENGINEERING_STANDARDS.md` when standards change (requires ADR).

### 3.5 Migration Changes

- Create migrations in the owning app's `migrations/` directory.
- Edit data migrations for additive data copies (no destructive operations).

---

## 4. Forbidden Modifications

AI must **never** perform these actions.

### 4.1 Architectural Changes

- Move the `AUTH_USER_MODEL` or create a new `User` model in a different app.
- Create a `rent/` bounded context or extract rent logic from `properties/`.
- Create an `apps/` parent directory or move apps into one.
- Create a `config/` app or move Django configuration out of `rentsecure_be/`.
- Introduce microservices or message brokers (Celery, Redis) in Year 1.
- Change the dependency matrix without an approved ADR.
- Activate `ai_assistant/` or `dashboard/` without explicit approval.

### 4.2 Code Changes

- Modify files outside the owning app without explicit approval.
- Import from `rentsecure_be/` in app code.
- Import `razorpay`, `cashfree`, `twilio`, `boto3` outside allowed adapter modules.
- Add business logic to views or serializers.
- Add `print()` statements (use `structlog`).
- Add `# TODO`, `# FIXME`, or commented-out code.
- Add `time.sleep()` or synchronous external API calls in request path.
- Use `pickle.loads()`, `os.system()`, `subprocess` with user input, or `md5`/`sha1` for security.

### 4.3 Data Changes

- Delete data fields without explicit approval and rollback plan.
- Perform destructive migrations (DROP TABLE, DELETE FROM) without Phase 5 approval.
- Modify `core_user` table directly (use Django migrations only).
- Cache financial data (payment status, bank details) without explicit approval.

### 4.4 Security Changes

- Log OTPs, bank account numbers, IFSC codes, API keys, or tokens.
- Disable webhook HMAC verification or idempotency.
- Store secrets in code, `.env` files (if committed), or settings files.
- Use `@csrf_exempt` without explicit ADR and security review.
- Change password hashing or OTP expiry logic without security review.

### 4.5 Infrastructure Changes

- Provision AWS resources (EC2, RDS, S3) without DevOps approval.
- Modify `terraform/` or `ansible/` without DevOps approval.
- Change database settings, cache settings, or search settings without architecture approval.
- Modify CI/CD pipeline without DevOps approval.

---

## 5. Dependency Rules

AI must respect the v1.1 dependency matrix.

### 5.1 Allowed Imports

| Source | shared | platform | identity | subscription | property | payment | notification | document | finance | referral | dashboard |
|--------|--------|----------|----------|--------------|----------|---------|--------------|----------|---------|----------|-----------|
| **shared** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **platform** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **identity** | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **subscription** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **property** | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **payment** | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **notification** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **document** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **finance** | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ |
| **referral** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **dashboard** | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ |
| **ai_assistant** | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ |

### 5.2 AI Enforcement Rules

1. **Never import from `rentsecure_be/`** in app code.
2. **Never import from `apps/` or `config/`** (these directories do not exist).
3. **Never import models directly from other apps** — use services or string references.
4. **Never create cross-app imports** that violate the matrix.
5. **If a task requires a cross-app import** that violates the matrix, STOP and ask for approval. The human may need to update the dependency matrix via ADR.

### 5.3 Adding Dependencies

- Adding a new third-party package requires:
  1. Checking if it already exists in `requirements.txt` / `pyproject.toml`.
  2. Verifying the license is compatible (MIT, BSD, Apache-2.0 preferred).
  3. Running `safety check` and `bandit` on the new dependency.
  4. Updating `requirements.txt` / `pyproject.toml` and `docs/architecture/contexts/<app>.md`.

---

## 6. Import Rules

AI must follow these import rules in all generated code.

### 6.1 Import Order

Use absolute imports in this order (enforced by `ruff` + `isort`):

1. Standard library
2. Third-party packages
3. Django imports
4. App imports (alphabetical within each group)

### 6.2 Forbidden Imports

| Import | Forbidden In | Allowed In |
|--------|-------------|------------|
| `from rentsecure_be.X import Y` | All apps | `rentsecure_be/` only |
| `from razorpay` | All files except `payments/adapters/razorpay.py` | `payments/adapters/` |
| `from cashfree` | All files except `payments/adapters/cashfree.py` | `payments/adapters/` |
| `from twilio` | All files except `notification/adapters/sms.py` | `notification/adapters/` |
| `from boto3` | All files except `notification/adapters/` and `documents/` | Adapter modules |
| `from core.models import User` | Models, views, services | `TYPE_CHECKING` blocks only |
| `from core.views import ...` | Direct `core.views` import | `core.views.auth_views`, etc. |
| `from properties.models import ...` | Apps other than `properties/` and tests | `properties/services/` interfaces |

### 6.3 Model Import Style

```python
from typing import TYPE_CHECKING
from django.conf import settings

if TYPE_CHECKING:
    from core.models import User

class RentRecord(models.Model):
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rent_records",
    )
```

AI must **never** generate `from core.models import User` in model files. Use `settings.AUTH_USER_MODEL` instead.

### 6.4 No Relative Imports

AI must **never** use relative imports (`from .models import User`). Always use absolute imports.

---

## 7. Migration Rules

AI must follow these rules when creating or modifying migrations.

### 7.1 General Rules

- Migrations MUST be reversible unless explicitly marked irreversible with justification.
- Data migrations MUST be additive (copy data, don't delete).
- Old tables MUST be retained for 1 release cycle before deletion.
- AI must **never** generate a migration that deletes data without explicit human approval.
- AI must **never** modify existing migration files that have already been applied to production.

### 7.2 Naming

- Auto-generated migrations: `XXXX_<auto_name>.py` (let Django generate).
- Data migrations: `XXXX_<descriptive_name>.py` (e.g., `0002_migrate_ownerbankdetails.py`).

### 7.3 Data Migration Requirements

When creating a data migration:

1. Include forward migration (copy data from source to target).
2. Include reverse migration (copy data back, or mark irreversible with justification).
3. Include integrity checks (row counts, checksums).
4. Test forward and reverse on a production-like database copy.
5. Document the migration in the PR description.

### 7.4 Migration Testing

AI must generate migration tests:

```python
# tests/test_migrations.py
def test_migration_forward():
    # Apply migration, verify data
    pass

def test_migration_reverse():
    # Reverse migration, verify data restored
    pass
```

---

## 8. Testing Requirements

AI must generate tests for all code changes.

### 8.1 Test Tiers

| Tier | When Required | Coverage |
|------|--------------|----------|
| Unit | Every new service, model, utility | ≥90% |
| Integration | Every new endpoint, workflow | ≥80% |
| Contract | Every cross-context API change | 100% pass |
| Architecture | Every PR | 0 violations |
| Migration | Every migration | Forward + reverse pass |
| Security | Every webhook, payment, auth change | 100% pass |
| Performance | Every query-heavy endpoint | p95 <200ms |

### 8.2 Test Location

- Unit tests: `app/tests/unit/test_<module>.py`
- Integration tests: `app/tests/integration/test_<workflow>.py`
- Contract tests: `app/tests/contract/` or `tests/contract/`
- Architecture tests: `tests/architecture/`
- Migration tests: `tests/test_migrations.py`

### 8.3 Test Naming

- Test files: `test_<module>.py`
- Test classes: `Test<Class>` (e.g., `TestAuthService`)
- Test methods: `test_<behavior>` (e.g., `test_send_otp_creates_record`)

### 8.4 Test Factories

- Use `factory_boy` for test data creation.
- Factories live in `tests/factories.py`.
- Each app may have app-specific factories in `app/tests/factories.py`.

### 8.5 Forbidden Test Patterns

- AI must **never** use `time.sleep()` in tests (use `freezegun` or mocking).
- AI must **never** write tests that depend on execution order.
- AI must **never** hardcode test data (use factories).
- AI must **never** mock the service layer in view integration tests (use real services with test database).
- AI must **never** exclude `ai_assistant/` or `dashboard/` tests from coverage without explicit approval.

---

## 9. Documentation Requirements

AI must update documentation for all changes.

### 9.1 Required Updates

| Change Type | Documentation Required |
|-------------|------------------------|
| New bounded context | `docs/architecture/contexts/<name>.md` |
| New endpoint | `docs/api/<endpoint>.md` |
| New service | `docs/architecture/contexts/<app>.md` |
| Architecture decision | ADR in `docs/architecture/adr/` |
| Breaking change | `docs/migration/v1-to-v2.md` |
| Release | `CHANGELOG.md` |

### 9.2 Context Documentation

Each context document must include:
- Ownership (team)
- Responsibilities
- Public APIs (endpoints and services)
- Dependencies (allowed imports)
- Data model (key entities)
- Sequence diagrams for key workflows (Mermaid or PlantUML)

### 9.3 ADR Requirements

When AI makes or suggests an architectural decision:
1. Create an ADR in `docs/architecture/adr/ADR-XXX.md`.
2. Include: Status, Context, Decision, Consequences, Alternatives Considered, Migration Notes, Future Evolution.
3. Update `docs/architecture/adr/README.md` index.
4. Do **not** mark ADR as `Accepted` — leave as `Proposed` for human review.

### 9.4 What AI Must Not Document

- AI must **never** generate marketing content or user-facing documentation.
- AI must **never** modify `README.md` without explicit approval.
- AI must **never** create documentation in `docs/` outside the approved structure.

---

## 10. Code Review Checklist

AI must run this checklist before submitting any code for review.

### Architecture

- [ ] No business logic in views or serializers (delegates to services)
- [ ] No `rentsecure_be/` imports in app code
- [ ] No payment SDK imports (`razorpay`, `cashfree`) outside `payments/adapters/`
- [ ] No `twilio`/`boto3` imports outside allowed adapter modules
- [ ] No `core.models.User` direct imports (use `settings.AUTH_USER_MODEL` string refs)
- [ ] No `core.views` direct imports (use submodules)
- [ ] No circular dependencies introduced
- [ ] No new `apps/` or `config/` directories
- [ ] No `ai_assistant/` activation without ADR
- [ ] View file ≤300 lines, model file ≤400 lines

### Security

- [ ] No secrets, API keys, or tokens in code or logs
- [ ] No OTPs logged or printed
- [ ] No bank account numbers or IFSC codes in plaintext
- [ ] All webhooks verify HMAC signatures (if webhook changed)
- [ ] All webhooks implement idempotency (if webhook changed)
- [ ] All financial operations use `@transaction.atomic()` (if payment flow changed)
- [ ] All permissions are explicit (if endpoint changed)
- [ ] No SQL injection vectors (use ORM, parameterized queries)
- [ ] No XSS vectors (escape output in templates)

### Testing

- [ ] All new code has unit tests (≥90% coverage for new code)
- [ ] All integration tests pass
- [ ] Architecture tests pass
- [ ] Migration tests pass (if migration included)
- [ ] No `ai_assistant/` or `dashboard/` tests inflate coverage
- [ ] Tests use factories, not hardcoded data
- [ ] No test depends on execution order
- [ ] No test uses `time.sleep()`

### Code Quality

- [ ] Ruff passes (0 errors)
- [ ] MyPy passes (0 errors)
- [ ] No `print()` statements (use `logger`)
- [ ] No commented-out code
- [ ] No `# TODO` without issue reference
- [ ] No `# FIXME` without owner and date
- [ ] No `pass` statements without comment
- [ ] No empty `except:` clauses
- [ ] No bare `except Exception:` without re-raise or logging

### Migrations

- [ ] Migration is reversible (or marked irreversible with justification)
- [ ] Data migration includes forward and reverse tests
- [ ] Data migration includes integrity checks (row counts, checksums)
- [ ] No destructive operations without explicit approval
- [ ] Migration naming is descriptive

### Documentation

- [ ] Context documentation updated (if bounded context changed)
- [ ] API documentation updated (if endpoint changed)
- [ ] ADR created (if architectural decision made)
- [ ] CHANGELOG.md updated (for releases)

---

## 11. PR Checklist

AI must include all of the following in every PR description.

### PR Title

Format: `<type>(<scope>): <description>`

| Type | Use For |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or updating tests |
| `docs` | Documentation only |
| `chore` | Build, CI, dependencies |
| `security` | Security fix or hardening |

Examples:
- `feat(payments): add webhook idempotency keys`
- `fix(properties): prevent negative rent amounts`
- `refactor(core): split god view into focused modules`

### PR Description Template

```markdown
## Summary
<1-3 sentences describing the change>

## Motivation
<Why is this change needed? Link to ADR if architectural.>

## Changes
- <Bullet list of changes>

## Testing
- <How was this tested?>
- <New tests added?>

## Documentation
- <Documentation updates?>

## Rollback
<How to rollback if this causes issues?>

## Checklist
- [ ] All CI gates pass
- [ ] Architecture tests pass
- [ ] No import-linter violations
- [ ] No circular dependencies
- [ ] Security scan passes (Bandit 0 high/medium)
- [ ] Mutation score ≥80%
- [ ] Documentation updated
```

### PR Size Limits

| Metric | Limit |
|--------|-------|
| Lines changed | Max 400 |
| Files changed | Max 15 |
| PR lifetime | Max 7 days |

If the change exceeds these limits, AI must split it into multiple PRs and **ask for approval** before proceeding.

---

## 12. Commit Message Standards

AI must follow these standards for all commit messages.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code change |
| `test` | Test change |
| `docs` | Documentation |
| `chore` | Build, CI, dependencies |
| `security` | Security fix |

### Subject

- Max 50 characters.
- Use imperative mood: "Add", "Fix", "Update", not "Added", "Fixed", "Updated".
- No period at the end.
- Capitalize first letter.

### Body

- Wrap at 72 characters.
- Explain **what** and **why**, not **how**.
- Reference ADR if applicable: `See ADR-004`.

### Footer

- Reference issues: `Fixes #123`, `Closes #456`.
- Reference breaking changes: `BREAKING CHANGE: <description>`.

### Examples

```
feat(payments): add webhook idempotency keys

Add WebhookEvent model with unique event_id constraint.
Webhook handlers check for existing events before processing.

Fixes #123
```

```
fix(properties): prevent negative rent amounts

Add validator to RentRecord.amount field to ensure
non-negative values. This prevents data corruption from
client-side validation bypass.

Fixes #456
```

---

## 13. Branch Naming

AI must use these branch naming conventions.

### Format

```
<type>/<ticket-id>-<description>
```

### Types

| Type | Use For |
|------|---------|
| `feature` | New features |
| `bugfix` | Bug fixes |
| `hotfix` | Production fixes |
| `refactor` | Refactoring |
| `test` | Test changes |
| `docs` | Documentation |
| `chore` | Build, CI, dependencies |

### Examples

- `feature/phase-0-add-encrypted-fields`
- `bugfix/property-negative-rent-amount`
- `hotfix/webhook-hmac-verification`
- `refactor/core-split-god-view`

### Rules

- Branch names must be lowercase.
- Branch names must use hyphens, not underscores.
- Branch names must reference the phase or ticket ID when applicable.
- AI must **never** push directly to `main` or `phase-{N}` branches.
- AI must **never** force-push to shared branches.

---

## 14. Rollback Requirements

AI must include a rollback plan in every PR.

### Rollback Plan Template

```markdown
## Rollback Plan

**Trigger:** <When would this need to be rolled back?>
**Method:** <git revert, migrate --reverse, restore from backup, etc.>
**Time Estimate:** <X minutes/hours>
**Data Risk:** <None / Low / Medium / High>
**Rollback Steps:**
1. <Step 1>
2. <Step 2>
3. <Step 3>
```

### Rollback Requirements by Phase

| Phase | Rollback Method | Data Risk | Time Limit |
|-------|-----------------|-----------|------------|
| Phase -1 | `git revert` | None | 10 minutes |
| Phase 0 | `git revert` + `migrate --reverse` | Low | 30 minutes |
| Phase 1-4 | `git revert` | None | 15 minutes |
| Phase 5 | Restore from backup + deploy previous version | High | 4 hours |
| Phase 6 | `git revert` | None | 15 minutes |

### AI Rollback Rules

- AI must **never** perform a rollback without explicit human approval.
- AI must **never** run `migrate --reverse` on production without human approval.
- AI must **never** delete data during rollback (restore from backup instead).
- AI must document the rollback procedure in the PR description.

---

## 15. Architecture Validation

AI must validate architecture compliance before submitting any PR.

### 15.1 Automated Validation

Run these commands and verify they pass:

```bash
# Lint
ruff check .
ruff format --check .

# Type check
mypy .

# Import rules
import-linter check

# Tests
pytest tests/ -v --cov

# Architecture tests
pytest tests/architecture/ -v

# Django check
python manage.py check

# Migrations
python manage.py makemigrations --check
python manage.py migrate --check
```

### 15.2 Manual Validation

AI must manually verify:

- [ ] No `print()` statements in code.
- [ ] No `# TODO` or `# FIXME` comments.
- [ ] No commented-out code.
- [ ] No hardcoded secrets or API keys.
- [ ] No sensitive data (OTP, bank details) in logs or error messages.
- [ ] No business logic in views or serializers.
- [ ] No direct model imports across apps (use string refs).
- [ ] No circular dependencies.
- [ ] No view file exceeds 300 lines.
- [ ] No model file exceeds 400 lines.

### 15.3 Architecture Test Validation

AI must verify these architecture tests pass:

| Test | Purpose |
|------|---------|
| `test_import_rules.py` | No forbidden SDK imports |
| `test_layer_compliance.py` | Views don't import models/services from other apps |
| `test_sdk_placement.py` | Payment SDKs only in adapters |
| `test_god_views.py` | No view file >300 lines |
| `test_god_models.py` | No model file >400 lines |
| `test_circular_deps.py` | No circular dependencies |
| `test_rentsecure_be_boundary.py` | No app imports from `rentsecure_be/` |
| `test_shared_purity.py` | `shared/` doesn't import Django or apps |

---

## 16. When AI Must Stop and Ask for Approval

AI must **immediately stop** and ask for human approval in the following situations.

### 16.1 Architectural Decisions

- Proposing to move `AUTH_USER_MODEL` or create a new `User` model.
- Proposing to create a `rent/` bounded context.
- Proposing to create `apps/` or `config/` directories.
- Proposing to introduce microservices, Celery, or Redis in Year 1.
- Proposing to change the dependency matrix.
- Proposing to activate `ai_assistant/` or `dashboard/`.
- Proposing to add a new bounded context.

### 16.2 Data Changes

- Proposing to delete data fields or tables.
- Proposing to perform destructive migrations (DROP TABLE, DELETE FROM).
- Proposing to modify `core_user` table directly.
- Proposing to cache financial data.

### 16.3 Security Changes

- Proposing to log OTPs, bank details, or secrets.
- Proposing to disable webhook HMAC or idempotency.
- Proposing to store secrets in code or settings.
- Proposing to use `@csrf_exempt`.
- Proposing to change password hashing or OTP logic.

### 16.4 Cross-App Changes

- Proposing an import that violates the dependency matrix.
- Proposing to move code between apps (outside approved phase tasks).
- Proposing to add a cross-app dependency.

### 16.5 Infrastructure Changes

- Proposing to provision AWS resources.
- Proposing to modify CI/CD pipeline.
- Proposing to change database, cache, or search settings.

### 16.6 Ambiguity

- Task requirements are unclear or contradictory.
- Task requires a decision that affects multiple bounded contexts.
- Task requires choosing between two valid architectural patterns.
- Task involves code that AI cannot find or understand after 3 search attempts.

### 16.7 Approval Process

When AI stops, it must:

1. State clearly what it was trying to do.
2. Explain why it stopped (reference the specific rule from this playbook).
3. Present 2-3 alternative approaches with trade-offs.
4. Wait for human decision before proceeding.

---

## 17. Files AI Must Never Modify Automatically

AI must **never** modify these files without explicit human approval.

### 17.1 Critical Configuration

| File | Reason |
|------|--------|
| `rentsecure_be/settings/production.py` | Production configuration; mistakes cause outages |
| `.env` | Secrets; AI must never read or write |
| `pyproject.toml` | Dependency changes require security review |
| `requirements.txt` | Dependency changes require security review |
| `import-linter.ini` | Architecture enforcement; mistakes break CI |
| `.github/workflows/ci.yml` | CI/CD pipeline; mistakes break all builds |
| `manage.py` | Django entry point; rarely needs changes |

### 17.2 Architecture Documents

| File | Reason |
|------|--------|
| `ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md` | Source of truth; requires Architecture Review Board approval |
| `ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md` | Implementation plan; requires Staff Engineer approval |
| `ENGINEERING_BACKLOG.md` | Backlog; requires Product/Platform Lead approval |
| `ENGINEERING_STANDARDS.md` | Standards; requires Architecture Review Board approval |
| `docs/architecture/adr/*.md` | ADRs; require ADR process |
| `docs/migration/v1-to-v2.md` | Migration guide; requires Staff Engineer approval |

### 17.3 Financial and Security Models

| File | Reason |
|------|--------|
| `payments/models.py` | Financial data; requires Security Lead review |
| `core/models.py` | User model; changes affect entire project |
| `notification/models.py` | Notification preferences; user-facing data |

### 17.4 Legacy / Dead Code

| File | Reason |
|------|--------|
| `ai_assistant/**/*.py` | Dead code; activation requires ADR |
| `dashboard/**/*.py` | Experimental; activation requires approval |
| `rentsecure_be/services/*.py` | Being removed in Phases 0-3; AI must not reintroduce |

### 17.5 Generated Files

| File | Reason |
|------|--------|
| `*/migrations/0001_initial.py` and other auto-generated migrations | Must be generated by Django, not AI |
| `db.sqlite3` | Local database; must not be committed |
| `__pycache__/`, `.pyc` files | Generated by Python |
| `staticfiles/`, `media/` | Generated by Django collectstatic |

---

## 18. Definition of Completion

A task is **complete** when ALL of the following are true.

### Code

- [ ] Code changes are implemented and committed.
- [ ] All CI gates pass: lint, type check, import rules, tests, architecture, security, mutation.
- [ ] No architecture test violations.
- [ ] No import-linter violations.
- [ ] No circular dependencies.
- [ ] No security vulnerabilities (Bandit 0 high/medium, Safety 0 critical).

### Tests

- [ ] Unit tests written for all new services, models, and utilities (≥90% coverage).
- [ ] Integration tests written for all new endpoints and workflows (≥80% coverage).
- [ ] Architecture tests pass (new code does not violate boundaries).
- [ ] Migration tests pass (if migration included).
- [ ] Contract tests pass (if cross-context API changed).
- [ ] All existing tests still pass (no regressions).

### Documentation

- [ ] Context documentation updated (if bounded context changed).
- [ ] API documentation updated (if endpoint changed).
- [ ] ADR created and marked `Proposed` (if architectural decision made).
- [ ] CHANGELOG.md updated (for releases).

### Security

- [ ] No secrets in code or logs.
- [ ] No sensitive data exposed in API responses.
- [ ] All webhooks verify HMAC (if webhook changed).
- [ ] All webhooks implement idempotency (if webhook changed).
- [ ] All financial operations use transactions (if payment flow changed).
- [ ] All permissions are explicit (if endpoint changed).

### PR

- [ ] PR description includes rollback plan.
- [ ] PR description references ADR if architectural.
- [ ] PR size is within limits (≤400 lines, ≤15 files).
- [ ] PR is linked to a ticket or phase task.

---

## 19. Definition of Success

A task is **successful** when ALL of the following are true.

### 19.1 Functional Success

- [ ] The code does what the task requires.
- [ ] No regressions in existing functionality.
- [ ] All tests pass (unit, integration, contract, architecture).
- [ ] All CI gates pass.

### 19.2 Architectural Success

- [ ] No new architecture violations introduced.
- [ ] No circular dependencies introduced.
- [ ] No new imports from `rentsecure_be/`.
- [ ] No new forbidden SDK imports.
- [ ] No view file exceeds 300 lines.
- [ ] No model file exceeds 400 lines.
- [ ] Changes are within the assigned bounded context.

### 19.3 Security Success

- [ ] No new security vulnerabilities introduced.
- [ ] No sensitive data exposed.
- [ ] All permissions are explicit.
- [ ] All webhooks verify HMAC and implement idempotency (if applicable).
- [ ] All financial operations use transactions (if applicable).

### 19.4 Operational Success

- [ ] Code is deployed to staging without incidents.
- [ ] Staging validation passes (duration depends on phase).
- [ ] Rollback procedure is documented and tested.
- [ ] No production incidents during staging validation.

### 19.5 Knowledge Success

- [ ] Documentation is updated.
- [ ] ADR is created if architectural decision was made.
- [ ] CHANGELOG.md is updated.
- [ ] Team understands the change (PR description is clear).

---

## Appendix A: Quick Reference

### AI Decision Tree

```
Is this an architectural change?
├── YES → STOP. Create ADR. Ask human.
└── NO → Continue.

Does this require a migration?
├── YES → Is it destructive?
│   ├── YES → STOP. Ask human.
│   └── NO → Continue. Generate additive migration.
└── NO → Continue.

Does this require a cross-app import?
├── YES → Does it violate the dependency matrix?
│   ├── YES → STOP. Ask human.
│   └── NO → Continue.
└── NO → Continue.

Is this a security-sensitive change?
├── YES → Is it webhooks, payments, or auth?
│   ├── YES → Generate code. Include tests. Ask human to review.
│   └── NO → Continue.
└── NO → Continue.

Is this within the assigned phase?
├── YES → Continue.
└── NO → STOP. Ask human.

Is the PR size within limits?
├── YES → Continue.
└── NO → STOP. Split into multiple PRs. Ask human.

Are all CI gates passing?
├── YES → Submit PR.
└── NO → Fix violations. Do NOT submit.
```

### AI Must Ask Human When

1. Architecture is unclear or contradictory.
2. Task requires a decision that affects multiple bounded contexts.
3. Task requires modifying files in the "never modify automatically" list.
4. Task requires a destructive operation (delete data, drop tables).
5. Task requires changing dependency rules or import-linter.ini.
6. Task requires activating deferred contexts (`ai_assistant/`, `dashboard/`).
7. Task requires introducing new infrastructure (Redis, Celery, microservices).
8. Task is ambiguous or could be interpreted multiple ways.
9. Task exceeds PR size limits.
10. Task requires a decision between two valid architectural patterns.

### AI Must Never Assume

- That a directory exists (verify with `ls` or `glob` first).
- That a file contains specific content (read it first).
- That the current phase allows the requested change (check phase boundaries).
- That a dependency is installed (check `requirements.txt` / `pyproject.toml` first).
- That a test passes (run it, don't assume).
- That the architecture document is up-to-date (read the latest version).

---

## Appendix B: Related Documents

- [Engineering Standards](./ENGINEERING_STANDARDS.md)
- [Architecture v1.1 Release Candidate](../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Architecture v1.1 Implementation Master Plan](../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Phase 0 Execution Plan](../PHASE_0_EXECUTION_PLAN.md)
- [Engineering Backlog](../ENGINEERING_BACKLOG.md)
- [Architecture Decision Records](../docs/architecture/adr/README.md)
- [Backend Engineering Rules](../.kilo/instructions/backend.md)
- [Security Rules](../.kilo/instructions/security.md)
- [Testing Rules](../.kilo/instructions/testing.md)
- [Finance Module Rules](../.kilo/instructions/finance.md)
- [Notification Module Rules](../.kilo/instructions/notifications.md)
- [Project Clinerules](../.clinerules)

---

## Appendix C: Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-19 | Chief Software Architect | Initial release for v1.1 freeze |

**Next Review:** After Phase 0 completion
**Approval Required:** Staff Engineer, Platform Team Lead, Product Team Lead, Security Lead, DevOps Engineer, QA Lead

---

*End of RentSecure AI Engineering Playbook*
