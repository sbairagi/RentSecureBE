# ADR-009: Testing Strategy

**Status:** Accepted
**Date:** 2026-07-19
**Deciders:** Chief Software Architect, Staff Engineer, QA Lead, Platform Team Lead
**Supersedes:** ADR-007 (v1.0 — Testing Strategy)

---

## Context

The v1.0 testing strategy lacked:
- **Contract tests** at app boundaries (required but not implemented)
- **Architecture regression tests** (required but not implemented)
- **Migration tests** (required but not implemented)
- **Security testing** (Bandit, Safety) in CI (mentioned but not configured)
- **Mutation testing** (mentioned as "80% target" but not blocking)
- **Performance testing** (mentioned but not automated)

The v1.1 review found:
- `tests/contract/` directory is empty (no contract tests exist)
- No architecture tests verify import boundaries or god view/model limits
- No migration tests validate forward/reverse migrations
- `ai_assistant/` and `dashboard/` have tests for dead code (inflated coverage)
- No pre-commit hooks for local architecture validation

The v1.1 testing strategy must fill these gaps with automated, CI-enforced tests.

---

## Decision

RentSecureBE uses a **7-tier testing strategy** with automated enforcement in CI.

### Test Tiers

| Tier | Scope | Owner | Frequency | Blocking |
|------|-------|-------|-----------|----------|
| **Unit** | Services, models, utilities | App team | Every commit | Yes |
| **Integration** | View → Service → Model | App team | Every commit | Yes |
| **Contract** | App boundaries (public APIs) | Architecture team | Every PR | Yes |
| **Architecture** | Import rules, layer compliance, god views/models | Architecture team | Every commit | Yes |
| **Migration** | Forward + reverse + data integrity | App team | Every PR | Yes |
| **Security** | OWASP Top 10, secrets, webhooks | Security team | Every release | Yes |
| **Performance** | Query counts, response times | App team | Nightly | No |

### Coverage Requirements

| Metric | Requirement | Enforcement |
|--------|-------------|-------------|
| Unit test coverage | ≥90% | Blocking in CI |
| Integration test coverage | ≥80% | Blocking in CI |
| Architecture test pass rate | 100% | Blocking in CI |
| Mutation testing score | ≥80% | Blocking in CI (from Phase 0) |
| Performance p95 | <200ms | Non-blocking (nightly alert) |

### Architecture Test Requirements

All architecture tests run on every commit via CI and are colocated in `tests/architecture/`:

| Test File | Purpose | Enforcement |
|-----------|---------|-------------|
| `test_import_rules.py` | No `razorpay`/`cashfree` imports in non-adapter files; no `twilio`/`boto3` outside allowed adapters; no `Notification.objects.create` outside `notification/` | Blocking |
| `test_layer_compliance.py` | Views do not import models from other apps; views do not import services from other apps | Blocking |
| `test_sdk_placement.py` | Payment SDKs only in `payments/adapters/` | Blocking |
| `test_god_views.py` | No view file exceeds 300 lines | Blocking |
| `test_god_models.py` | No model file exceeds 400 lines | Blocking |
| `test_circular_deps.py` | No circular dependency cycles (AST analysis) | Blocking |
| `test_rentsecure_be_boundary.py` | No app imports from `rentsecure_be/` (except `rentsecure_be/` itself) | Blocking |
| `test_shared_purity.py` | `shared/` does not import Django or any app | Blocking |

### Contract Test Requirements

Contract tests verify that public APIs between bounded contexts remain stable:

| Contract | Created In | Test File |
|----------|-----------|-----------|
| Property → Subscription | Phase 0 | `tests/contract/test_property_subscription_contract.py` |
| Property → Notification | Phase 0 | `tests/contract/test_property_notification_contract.py` |
| Payment → Property | Phase 0 | `tests/contract/test_payment_property_contract.py` |
| Core → Identity | Phase 1 | `tests/contract/test_core_identity_contract.py` |
| Finance → Property | Phase 2 | `tests/contract/test_finance_property_contract.py` |

### Migration Test Requirements

Every migration is tested for forward and reverse operations:

| Test | Tool | Frequency |
|------|------|-----------|
| Forward migration | `manage.py migrate` on test DB | Every PR touching migrations |
| Reverse migration | `manage.py migrate --reverse` on test DB | Every PR touching migrations |
| Data integrity | Custom pytest (row counts, checksums) | Every PR with data migrations |
| Migration on production copy | Staging environment | Weekly |

### Security Test Requirements

| Test | Tool | Frequency |
|------|------|-----------|
| Bandit scan | Bandit | Every PR |
| Dependency audit | Safety | Every PR |
| Webhook replay test | Custom pytest | Every PR |
| Encryption verification | Custom management command | Every release |

---

## Alternatives Considered

### 1. Unit Tests Only

**Description:** Test only individual classes and functions in isolation.

**Pros:**
- Very fast
- Easy to write
- Clear failure isolation

**Cons:**
- Misses integration issues
- Does not catch architectural violations
- Does not validate migrations
- Does not catch cross-context contract breaks

**Decision:** Rejected. Insufficient confidence for production changes.

### 2. Integration Tests Only

**Description:** Test only through the Django stack.

**Pros:**
- Tests real behavior
- No mocking needed

**Cons:**
- Slow execution
- Hard to isolate failures
- Difficult to test edge cases
- Low feedback frequency
- Does not catch architectural violations

**Decision:** Rejected. Too slow for TDD and misses architecture enforcement.

### 3. 7-Tier Strategy with CI Enforcement (Selected)

**Description:** Unit + Integration + Contract + Architecture + Migration + Security + Performance tests. All blocking in CI except performance.

**Pros:**
- Fast feedback (unit tests run first)
- Confidence in integration (integration tests)
- Cross-context safety (contract tests)
- Architecture enforcement (architecture tests)
- Migration safety (migration tests)
- Security confidence (security scans)
- Performance regression detection (nightly)

**Cons:**
- More test code to maintain
- Requires test infrastructure investment
- CI time increases (mitigated by parallelization and sharding)

**Decision:** Accepted. Best balance of confidence and velocity.

---

## Consequences

### Positive
- High confidence in refactoring (architecture tests prevent drift)
- Migration failures caught before production (migration tests)
- Cross-context contracts are stable (contract tests)
- Security vulnerabilities caught early (Bandit, Safety)
- Performance regressions detected nightly
- Test failures are easy to diagnose (tiered structure)

### Negative
- More test code to maintain (~150+ technical tasks in backlog)
- Requires test infrastructure investment (test factories, fixtures, CI configuration)
- CI time increases (~5-10 minutes per PR, mitigated by sharding)
- Team must learn architecture test patterns

### Neutral
- Target coverage: ≥90% unit, ≥80% integration
- Tests run in CI on every commit/PR
- Architecture tests run on every commit (not just PR)
- Performance tests run nightly (non-blocking)

---

## Migration Notes

### Phase -1: Foundation Tests
- Add `test_circular_deps.py` (detects existing cycles, passes after Phase -1)
- Add `test_rentsecure_be_boundary.py` (detects existing violations, passes after Phase -1)

### Phase 0: Architecture Regression Tests
- Create `tests/architecture/` package with all 8 test files
- Add `test_import_rules.py`, `test_layer_compliance.py`, `test_sdk_placement.py`, `test_god_views.py`, `test_god_models.py`, `test_shared_purity.py`
- Add `tests/test_migrations.py` (forward + reverse migration tests)
- Add `tests/test_migration_data_integrity.py` (data integrity tests)
- Configure CI to run architecture tests on every commit
- Configure Bandit and Safety in CI (blocking)

### Phase 0: Contract Tests
- Create `tests/contract/` directory
- Add `test_property_contract.py`, `test_payment_contract.py`, `test_notification_contract.py`

### Phase 1-4: Service Tests
- Each extracted service gets unit tests (≥90% coverage) and integration tests
- All existing tests must continue to pass

### Phase 6: Mutation and Performance Tests
- Configure mutation testing (SonarCloud or equivalent) with ≥80% blocking threshold
- Add `tests/performance/` package with query count tests and Locust load tests
- Performance tests run nightly (non-blocking)

### Ongoing
- Pre-commit hooks run `import-linter check` and `ruff check` locally
- Every PR must pass all CI gates before merge
- Coverage reports generated on every PR
- Architecture test violations block merge

---

## Future Evolution

### Short-term (Phase 6)
- Mutation testing becomes blocking (currently non-blocking in v1.0)
- Property-based testing (Hypothesis) added for critical services
- Performance tests become blocking if p95 exceeds threshold for 3 consecutive runs

### Medium-term
- Contract tests expand to cover all public APIs between contexts
- Architecture tests add new rules as patterns emerge (e.g., event bus usage)
- Test factories move to a shared `tests/factories.py` library

### Long-term
- If microservices are extracted, contract tests become integration tests between services
- Performance tests expand to cover all critical endpoints
- Mutation testing threshold increases to 90%

---

## References

- [Architecture v1.1 Release Candidate — Part 9 (Testing Gaps), Part 2.8 (Testing Standards)](../../../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Implementation Master Plan — Section 13 (Testing Strategy), Phase 0, Phase 6](../../../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Phase 0 Execution Plan — PR-007, PR-009](../../../PHASE_0_EXECUTION_PLAN.md)
- [CI/CD Strategy](./ADR-010_cicd_strategy.md)
- [Migration Strategy](./ADR-007_migration_strategy.md)
- [Import Rules](./ADR-006_import_rules.md)
