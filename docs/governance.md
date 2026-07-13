# Enterprise CI/CD Governance

> **Version:** 2.4.0
> **Scope:** RentSecureBE — Production-Grade Django Backend
> **Last Updated:** 26 June 2026

---

## 1. Overview

This document defines the **enterprise governance controls** for the RentSecureBE CI/CD pipeline. It covers status checks, code ownership, and the architecture guard workflow.

The governance system follows a **defense-in-depth** approach:

1. **CODEOWNERS** — Who can approve changes to critical paths
2. **Required Status Checks** — Which CI checks must pass before merging
3. **Architecture Guard** — Automated enforcement of the pipeline contract
4. **Change Approval** — Process for modifying the pipeline architecture

---

## 2. CODEOWNERS Protection

The `.github/CODEOWNERS` file must protect these paths:

```
# ── Architecture Contract ────────────────────────────────────────────
/scripts/architecture_contract.py    @senior-devops @tech-lead
/.github/workflows/architecture-guard.yml  @senior-devops @tech-lead
/docs/architecture-contract.md       @senior-devops @tech-lead
/docs/governance.md                  @senior-devops @tech-lead

# ── CI/CD Pipeline ───────────────────────────────────────────────────
/.github/workflows/ci.yml            @senior-devops @tech-lead
/.github/workflows/deploy.yml        @senior-devops @tech-lead
/.github/workflows/security.yml      @senior-devops @security-team

# ── Deployment & Infrastructure ──────────────────────────────────────
/scripts/deploy*.sh                  @senior-devops
/Dockerfile                           @senior-devops
/docker-compose*.yml                  @senior-devops
```

**Rule:** Any PR modifying these paths requires approval from at least one owner in each listed team.

---

## 3. Branch Protection Rules

The `main` and `master` branches must have the following protection rules enabled:

| Rule | Setting |
|------|---------|
| Require pull request before merging | ✅ Enabled |
| Require approvals | 2 |
| Dismiss stale reviews | ✅ Enabled |
| Require review from CODEOWNERS | ✅ Enabled |
| Require status checks | ✅ See Section 4 |
| Require branches up to date | ✅ Enabled |
| Require conversation resolution | ✅ Enabled |
| Do not allow bypassing | ✅ Enabled |
| Restrict push access | ✅ Admins only |
| Allow force pushes | ❌ Disabled |
| Allow deletions | ❌ Disabled |

---

## 4. Required Status Checks

Before a PR can be merged into `main` or `master`, **all** of the following checks must pass:

| # | Check Name | Source Workflow | Stage |
|---|------------|-----------------|-------|
| 1 | `Stage 1 │ Pre-commit` | `lint.yml` | 1-2 |
| 2 | `Stage 2a │ Black Format` | `lint.yml` | 1-2 |
| 3 | `Stage 2b │ Ruff Lint` | `lint.yml` | 1-2 |
| 4 | `Stage 2c │ Pylint Analysis` | `lint.yml` | 1-2 |
| 5 | `Stage 2d │ Mypy (Strict Typing)` | `lint.yml` | 1-2 |
| 6 | `Stage 2e │ Vulture (Dead Code Detection)` | `lint.yml` | 1-2 |
| 7 | `Stage 3a │ Pytest + Coverage (≥90%)` | `test.yml` | 3a |
| 8 | `Stage 3b │ Hypothesis Property Tests` | `hypothesis.yml` | 3b |
| 9 | `Stage 3c │ API Contract Tests` | `contract-tests.yml` | 3c |
| 10 | `Stage 3d │ Mutation Testing (mutmut)` | `mutation.yml` | 3d |
| 11 | `Stage 3e_i │ Locust Load Test` | `performance.yml` | 3e |
| 12 | `Stage 3e_ii │ Pytest Benchmark Regression` | `performance.yml` | 3e |
| 13 | `Stage 4a │ Django System & Migration Check` | `django-check.yml` | 4 |
| 14 | `Stage 4b │ Migration Rollback Validation` | `django-check.yml` | 4 |
| 15 | `Stage 5a │ Vulture (Dead Code)` | `architecture.yml` | 5 |
| 16 | `Stage 5b │ Import Linter (Architecture)` | `architecture.yml` | 5 |
| 17 | `Stage 6a-h │ Security (Bandit..CodeQL)` | `security.yml` | 6 |
| 18 | `Stage 7 │ SonarCloud Quality Gate` | `quality.yml` | 7 |
| 19 | `Stage 8a │ Deploy Readiness Check` | `deploy-readiness.yml` | 8a |
| 20 | **Enforce Architecture Contract** | `architecture-guard.yml` | Contract |

---

## 5. Architecture Guard Workflow

The architecture guard (`.github/workflows/architecture-guard.yml`) is the **enforcement mechanism** for the CI/CD contract.

### What it does

- **Triggers on:** Every PR that modifies `.github/workflows/**` or `scripts/architecture_contract.py`
- **Runs:** `python scripts/architecture_contract.py --verbose`
- **Fails on:** Any CRITICAL or ERROR-level violation
- **Protects:** The entire CI/CD pipeline structure from unauthorized modification

### Why it matters

Without the architecture guard:
- A developer could remove the security stage
- An AI agent could accidentally reorder stages
- A bad actor could bypass quality gates
- The documented architecture would drift from reality

The guard makes the architecture contract **self-enforcing**.

---

## 6. Change Approval Process

### Level 1: Routine Changes (e.g., adding a test)

- No approval needed beyond normal CODEOWNERS
- Architecture guard validates the change is safe

### Level 2: Pipeline Modifications (e.g., adding a new stage)

1. Developer modifies `scripts/architecture_contract.py`
2. Architecture guard detects the change
3. Developer must update `docs/architecture-contract.md`
4. Developer must update `docs/ci-cd-pipeline.md`
5. **Requires:** Approval from `@senior-devops`

### Level 3: Architecture Changes (e.g., removing security stage)

1. **Requires:** Architecture Review Board approval
2. **Requires:** Written justification
3. **Requires:** Security team sign-off (if security-adjacent)
4. All 3 documentation files must be updated
5. Version bump required (ARCHITECTURE_VERSION, PIPELINE_VERSION, CONTRACT_VERSION)

### Level 4: Contract Modification (e.g., relaxing bypass protection)

- **Cannot be done without unanimous approval** from:
  - Senior DevOps
  - Tech Lead
  - Security Lead
  - Engineering Manager

---

## 7. Compliance Score Interpretation

| Score | Meaning | Action Required |
|-------|---------|-----------------|
| **100** | Fully compliant | None |
| **86–99** | Minor warnings | Review and fix within 30 days |
| **71–85** | Degraded | Review and fix within 14 days |
| **51–70** | At risk | Immediate review required |
| **0–50** | Non-compliant | Pipeline blocked; emergency fix required |

---

## 8. Version Alignment

All three version constants must be **identical** at all times:

| Constant | Location | Example |
|----------|----------|---------|
| `ARCHITECTURE_VERSION` | `scripts/architecture_contract.py` | `2.0.0` |
| `PIPELINE_VERSION` | `scripts/architecture_contract.py` | `2.0.0` |
| `CONTRACT_VERSION` | `scripts/architecture_contract.py` | `2.0.0` |

The version must also appear in:
- `docs/architecture-contract.md` (header)
- `docs/ci-cd-pipeline.md` (header)
- `docs/governance.md` (header)

---

*This governance framework is enforced automatically by the Architecture Contract Validator and the Architecture Guard workflow.*
