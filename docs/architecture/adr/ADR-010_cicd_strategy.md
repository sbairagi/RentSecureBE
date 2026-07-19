# ADR-010: CI/CD Strategy

**Status:** Accepted
**Date:** 2026-07-19
**Deciders:** Chief Software Architect, Staff Engineer, DevOps Engineer, Security Lead, QA Lead
**Supersedes:** ADR-007 (v1.0 — Testing Strategy, CI/CD portions)

---

## Context

The v1.0 CI/CD pipeline had critical gaps:
1. **import-linter was not enforced in CI** — the architecture compliance report showed "100/100 COMPLIANT" despite 145+ cross-app import violations because `rentsecure_be/` was configured as an allowed layer for all apps
2. **Mutation testing was not blocking** — SonarCloud mutation score target was 80% but marked "No" (not blocking), allowing mutant code to be merged
3. **No pre-commit hooks** — developers could commit architecture violations and only discover them after pushing to GitHub
4. **No security scanning in CI** — Bandit and Safety were mentioned but not configured as blocking gates
5. **No migration rollback tests in CI** — migrations that worked forward could fail backward in production
6. **No contract test execution in CI** — `tests/contract/` was empty and not referenced in pipeline

The v1.1 CI/CD strategy must address all gaps with a comprehensive, blocking pipeline.

---

## Decision

RentSecureBE uses a **13-stage CI pipeline** with all gates blocking. The pipeline runs on every commit to task branches and every PR to phase branches.

### Pipeline Stages

```
┌─────────────┐
│   Lint      │ Ruff, MyPy, import-linter
└──────┬──────┘
       │
┌──────▼──────┐
│   Test      │ Unit + Integration (4 shards)
└──────┬──────┘
       │
┌──────▼──────┐
│  Shard Val  │ Validate test distribution
└──────┬──────┘
       │
┌──────▼──────┐
│  Contract   │ API contract tests
└──────┬──────┘
       │
┌──────▼──────┐
│ Django Check│ System checks + migrations
└──────┬──────┘
       │
┌──────▼──────┐
│ Architecture│ AST-based architecture tests
└──────┬──────┘
       │
┌──────▼──────┐
│   Security  │ Bandit + Safety + dependency audit
└──────┬──────┘
       │
┌──────▼──────┐
│  Mutation   │ SonarCloud mutation testing (≥80%, blocking)
└──────┬──────┘
       │
┌──────▼──────┐
│  Hypothesis │ Property-based testing
└──────┬──────┘
       │
┌──────▼──────┐
│ Migration   │ Forward + reverse migration tests
└──────┬──────┘
       │
┌──────▼──────┐
│ Quality Gate│ Coverage, mutation score thresholds
└──────┬──────┘
       │
┌──────▼──────┐
│ Deploy Ready│ Pre-deployment validation
└──────┬──────┘
       │
┌──────▼──────┐
│   Deploy    │ Deploy to staging/production
└─────────────┘
```

### CI Gates (All PRs)

| Gate | Tool | Threshold | Blocking |
|------|------|-----------|----------|
| Lint | Ruff | 0 errors | Yes |
| Type Check | MyPy | 0 errors | Yes |
| Import Rules | import-linter | 0 violations | Yes |
| Tests | Pytest | All pass, ≥90% coverage | Yes |
| Django Check | `manage.py check` | 0 errors | Yes |
| Architecture | pytest `tests/architecture/` | 0 failures | Yes |
| Security | Bandit | 0 high/medium | Yes |
| Dependency Audit | Safety | 0 critical | Yes |
| Mutation | Sonar | ≥80% mutation score | Yes |
| Migration | pytest-django | Forward + reverse pass | Yes |

### Phase-Specific CI Gates

| Phase | Additional Gates |
|-------|------------------|
| Phase -1 | Circular dependency check, `rentsecure_be/` boundary check |
| Phase 0 | Migration forward/reverse tests, encrypted field verification, webhook idempotency tests |
| Phase 1 | Service ownership tests, identity flow regression |
| Phase 2 | Subscription flow regression, `FeatureEnforcer` import check |
| Phase 3 | Webhook security tests, payment flow regression, duplicate service removal check |
| Phase 4 | Dashboard API tests, notification adapter tests |
| Phase 5 | Breaking change tests, 404 validation for old URLs, migration guide validation |
| Phase 6 | Performance benchmarks, event bus tests, repository tests |

### Branch Strategy

| Branch Type | Naming | Purpose | Protection |
|-------------|--------|---------|------------|
| Main | `main` | Production-ready code | 2 approvals, all checks |
| Phase branch | `phase-{N}-{name}` | Long-lived branch for each phase | 1 approval, all checks |
| Task branch | `phase-{N}-{name}/{task-id}` | Short-lived branch for each task | Lint + Tests |
| Hotfix | `hotfix-{description}` | Production fixes | 2 approvals, all checks |
| Release | `release/v{N}.{M}.{Z}` | Release preparation | 2 approvals, all checks |

### PR Size Limits

| Metric | Limit |
|--------|-------|
| Lines changed per PR | Max 400 |
| Files changed per PR | Max 15 |
| PR lifetime | Max 7 days |

If a task exceeds these limits, split it into smaller PRs.

### Deployment Strategy

| Phase | Strategy |
|-------|----------|
| Phase -1 | Deploy to staging only. No production deploy. |
| Phase 0 | Blue-green deploy to staging. Production deploy after 3 days stable. |
| Phase 1-4 | Rolling deploy. Old code remains as deprecated shims. |
| Phase 5 | Blue-green deploy. Major version release (v2.0.0). |
| Phase 6 | Rolling deploy. |

### Pre-Commit Hooks

Local pre-commit hooks run before every commit:
- `import-linter check` — catches import violations before CI
- `ruff check` — catches lint errors before CI
- `ruff format --check` — catches formatting issues before CI

Configuration in `.pre-commit-config.yaml`:
```yaml
- repo: local
  hooks:
    - id: import-linter
      name: import-linter
      entry: import-linter check
      language: system
    - id: ruff
      name: ruff
      entry: ruff check .
      language: system
```

---

## Alternatives Considered

### 1. Simple CI (Lint + Tests Only)

**Description:** Run only linting and unit tests in CI. No architecture tests, no security scans, no mutation testing.

**Pros:**
- Fast pipeline (< 5 minutes)
- Simple to maintain
- Low CI cost

**Cons:**
- Architecture violations accumulate undetected
- Security vulnerabilities reach production
- Mutant code is merged
- Migration failures discovered in production
- Import-linter compliance is meaningless

**Decision:** Rejected. Insufficient quality gates for production system with financial data.

### 2. Manual Security Reviews

**Description:** Rely on manual security reviews instead of automated Bandit/Safety scans.

**Pros:**
- Human judgment for edge cases
- No tooling overhead

**Cons:**
- Inconsistent enforcement
- High reviewer burden
- Easy to miss vulnerabilities in large PRs
- Slow review cycle

**Decision:** Rejected. Automated scanning is faster and more consistent.

### 3. Comprehensive CI with Blocking Gates (Selected)

**Description:** 13-stage pipeline with all gates blocking. Architecture tests, security scans, mutation testing, and migration tests run on every commit.

**Pros:**
- High quality bar enforced automatically
- Architecture violations caught before merge
- Security vulnerabilities blocked in CI
- Mutation testing prevents semantic bugs
- Migration failures caught before production
- Fast feedback for developers

**Cons:**
- Longer pipeline time (~10-15 minutes)
- Higher CI cost (multiple parallel jobs)
- Requires CI infrastructure maintenance
- Developers must fix violations before merging

**Decision:** Accepted. Necessary for production system with financial data and regulatory requirements.

---

## Consequences

### Positive
- Architecture violations are caught in CI (not just code review)
- Security vulnerabilities are blocked before production
- Mutation testing prevents semantic bugs
- Migration failures are caught before deployment
- import-linter compliance is meaningful (0 violations = truly compliant)
- Pre-commit hooks catch violations locally before push
- High quality bar is enforced consistently across the team

### Negative
- Longer pipeline time (~10-15 minutes per PR)
- Higher CI cost (multiple parallel jobs)
- Developers must fix violations before merging (slower velocity)
- Requires CI infrastructure maintenance
- False positives in architecture tests require ADR exceptions

### Neutral
- Pipeline runs on every commit to task branches and every PR to phase branches
- Performance tests run nightly (non-blocking)
- Staging deploys automatically on phase branch merge
- Production deploys require 2 approvals + Security Lead sign-off

---

## Migration Notes

### Phase -1: Foundation
- Configure CI to run `import-linter check` on every commit
- Add circular dependency and `rentsecure_be/` boundary tests to CI

### Phase 0: Critical CI Additions
- Add Bandit and Safety as blocking gates
- Add migration forward/reverse tests as blocking gates
- Add architecture tests (`tests/architecture/`) as blocking gates
- Add pre-commit hooks (`.pre-commit-config.yaml`)
- Configure mutation testing (SonarCloud or equivalent) with ≥80% blocking threshold

### Phase 1-6: Ongoing
- Each phase adds phase-specific CI gates (see table above)
- Contract tests run on every PR after Phase 0
- Performance tests run nightly after Phase 6

### Rollback
- CI pipeline misconfiguration: revert `.github/workflows/ci.yml` changes
- False positives in architecture tests: adjust test thresholds via ADR
- Pre-commit hooks causing developer friction: disable locally with `SKIP=import-linter,ruff`

---

## Future Evolution

### Short-term (Phase 6)
- Performance tests become blocking if p95 exceeds threshold for 3 consecutive runs
- Hypothesis property-based testing added for critical services
- CI pipeline parallelization optimized to reduce runtime below 10 minutes

### Medium-term
- If microservices are extracted, CI pipeline adds service-specific jobs
- Contract tests expand to cover all public APIs
- Mutation testing threshold increases to 90%

### Long-term
- CI pipeline remains the primary quality gate
- Deployment automation increases (canary deployments, automated rollback)
- Observability and monitoring integrated into deployment pipeline

---

## References

- [Architecture v1.1 Release Candidate — Part 10 (CI/CD Gaps), Part 2.9 (CI Requirements)](../../../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Implementation Master Plan — Section 11 (CI/CD Pipeline), Section 13 (Testing Strategy)](../../../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Phase 0 Execution Plan — PR-009](../../../PHASE_0_EXECUTION_PLAN.md)
- [Testing Strategy](./ADR-009_testing_strategy.md)
- [Import Rules](./ADR-006_import_rules.md)
- [Migration Strategy](./ADR-007_migration_strategy.md)
- [Security Rules](../../../.kilo/instructions/security.md)
