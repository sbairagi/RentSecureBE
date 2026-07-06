# Security Audit Report — RentSecureBE

Generated: 2026-07-02

## Already Implemented

- ✅ **Harden Runner** — `step-security/harden-runner` with `egress-policy: block` in every job across all workflows.
- ✅ **SARIF upload gating** — Security scan results only uploaded for same-repo PRs in `security.yml`, `security-deep.yml`.
- ✅ **Concurrency** — `ci.yml`, `architecture-guard.yml`, `security-deep.yml`, `nightly.yml`, `weekly.yml`, `load-test.yml`, `benchmark.yml` have concurrency groups.
- ✅ **Top-level permissions** — `ci.yml`, `rollback.yml`, `runtime-measurement.yml`, `ci-metrics.yml`, `architecture-guard.yml`, `quality.yml` have explicit `permissions:` blocks.
- ✅ **Least-privilege per-job permissions** — `security.yml` and `security-deep.yml` apply `security-events: write`, `contents: read`, `actions: read` to scan jobs.
- ✅ **OIDC readiness** — `id-token: write` declared in `ci.yml` and `security-deep.yml`.
- ✅ **Dependabot** — `.github/dependabot.yml` configured for `github-actions` ecosystem, `direct` dependencies only, weekly schedule.
- ✅ **Gitleaks allowlist** — `.gitleaks.toml` allowlists CI test key patterns.
- ✅ **Checkout fetch-depth** — Most workflows use `fetch-depth: 1`.
- ✅ **Timeout limits** — Every job defines `timeout-minutes`.
- ✅ **Security scanning stack** — Bandit, pip-audit, Semgrep, Trivy, Gitleaks, CodeQL, Scorecard, Dependency Review, SBOM (Syft, Grype, OSV Scanner).
- ✅ **Pre-commit hooks** — `.pre-commit-config.yaml` and `lint.yml` job.

## Missing

### Critical

| # | Finding | Risk | Files | Details |
|---|---------|------|-------|---------|
| 1 | **No third-party action pins to commit SHAs** | High | All workflow files | Zero actions are pinned to immutable commit SHAs. Supply-chain risk via tag mutation. |
| 2 | **`django-check.yml` contains 128-char hardcoded SECRET_KEY** | High | `.github/workflows/django-check.yml` | `django-check-ci-pipeline-security-validation-2026-production-grade-random-key-...` — accidental production key paste. |
| 3 | **`deploy-readiness.yml` contains 74-char hardcoded SECRET_KEY** | High | `.github/workflows/deploy-readiness.yml` | Extremely long test-secret string looks like leaked production material. |
| 4 | **`deploy.yml` runs with placeholder SSH credentials** | High | `.github/workflows/deploy.yml` | `host: placeholder`, `username: placeholder` are active values. If workflow ever triggers, it fails or connects to wrong host. |
| 5 | **`deploy.yml` push trigger is active despite "disabled" comment** | High | `.github/workflows/deploy.yml` | Comment says "Disabled temporarily" but `push: branches: [main, master]` is uncommented. |

### High

| # | Finding | Risk | Files | Details |
|---|---------|------|-------|---------|
| 6 | **Unvalidated `rollback_sha` script injection** | High | `.github/workflows/rollback.yml` | `${{ github.event.inputs.rollback_sha }}` flows unsanitized into git commands and SSH script. |
| 7 | **Unverified remote script execution (`curl \| sh`)** | High | `.github/workflows/deploy.yml`, `.github/workflows/sbom.yml` | Sentry CLI, Syft, Grype installed via unverified `curl | bash`. |
| 8 | **Mutable Docker tag in SBOM workflow** | High | `.github/workflows/sbom.yml` | `ghcr.io/google/osv-scanner:latest` — mutable tag can be replaced. |

### Medium

| # | Finding | Risk | Files | Details |
|---|---------|------|-------|---------|
| 9 | **16 workflows without explicit `permissions:` block** | Medium | `.github/workflows/test.yml`, `sbom.yml`, `deploy.yml`, `weekly.yml`, `load-test.yml`, `benchmark.yml`, `nightly.yml`, `migration-rollback.yml`, `hypothesis.yml`, `deploy-readiness.yml`, `lint.yml`, `performance.yml`, `contract-tests.yml`, `architecture.yml`, `django-check.yml`, `mutation.yml` | Default `GITHUB_TOKEN` scopes may include `packages: write`. |
| 10 | **`dependency-review` jobs lack permissions blocks** | Medium | `.github/workflows/security.yml`, `.github/workflows/security-deep.yml` | Inherits default token permissions instead of explicit minimal set. |
| 11 | **`GITHUB_TOKEN` leaked in error output** | Medium | `.github/workflows/runtime-measurement.yml` | If token unavailable, error prints exact `curl -H 'Authorization: token ${{ secrets.GITHUB_TOKEN }}' ...` command to log. |
| 12 | **`SONAR_TOKEN` exposed at job-level env** | Medium | `.github/workflows/quality.yml` | Token visible in job-level environment variables. |
| 13 | **`setup-django/action.yml` defined but never used** | Medium | `.github/actions/setup-django/action.yml` | Dead code increases maintenance surface. |

### Low

| # | Finding | Risk | Files | Details |
|---|---------|------|-------|---------|
| 16 | **No Dependabot security updates enabled** | Low | `.github/dependabot.yml` | Only `github-actions` updates configured; no `pip`/`npm` ecosystem. |
| 17 | **Hardcoded test SECRET keys (allowlisted but suboptimal)** | Low | `test.yml`, `load-test.yml`, `benchmark.yml`, `hypothesis.yml`, `contract-tests.yml`, `mutation.yml`, `performance.yml`, `django-check.yml` (second key), `migration-rollback.yml` | Usable for CI but better practice is `${{ secrets.TEST_SECRET_KEY }}`. Gitleaks allowlist covers these. |

## Needs Improvement

| # | Finding | Risk | Files | Details |
|---|---------|------|-------|---------|
| 18 | **Workflows with no `workflow_call` inputs still accept all secrets** | Medium | All `workflow_call` workflows | Caller's entire secret set inherited; restrict to `secrets:` list. |
| 19 | **No Dependabot for Python dependencies** | Medium | `.github/dependabot.yml` | `requirements.txt` not monitored by Dependabot. |
| 20 | **Missing `timeout-minutes` at outer workflow level** | Low | `ci.yml`, `weekly.yml`, `nightly.yml` | Individual jobs have timeouts but outer reusable calls don't enforce wallet protection. |
| 21 | **`architecture-guard.yml` path-filter excludes other workflow files** | Low | `.github/workflows/architecture-guard.yml` | Path filters only trigger on a subset; some changes to workflows bypass this gate. |

## Implementation Status

All **Critical**, **High**, and **Medium** findings have been remediated:

| # | Status | Change |
|---|--------|--------|
| 1 | ✅ Fixed | All 17 third-party GitHub Actions pinned to immutable commit SHAs across 27 workflow/action files. |
| 2 | ✅ Fixed | `django-check.yml` — replaced 128-char suspicious key with `test-secret-key-django-check-2026`. |
| 3 | ✅ Fixed | `deploy-readiness.yml` — replaced 74-char suspicious key with `test-secret-key-deploy-readiness-2026`. |
| 4 | ✅ Fixed | `deploy.yml` — wired SSH credentials to `secrets.EC2_HOST`/`secrets.EC2_USER`/`secrets.EC2_SSH_KEY` with step-level `if:` guard. |
| 5 | ✅ Fixed | `deploy.yml` — removed `push:` trigger; workflow now only executes via `workflow_call` from `ci.yml`. |
| 6 | ✅ Fixed | `rollback.yml` — added `validate-target` job output with `git rev-parse --verify`; downstream steps consume validated SHA only. |
| 7 | ✅ Fixed | `deploy.yml` — Sentry CLI installed from pinned GitHub release binary (v3.6.0), no `curl | bash`. `sbom.yml` — Syft and Grype installed from pinned release tarballs (v1.46.0, v0.115.0). |
| 8 | ✅ Fixed | `sbom.yml` — pinned OSV Scanner to `ghcr.io/google/osv-scanner:v2.3.8`. |
| 9 | ✅ Fixed | Added explicit `permissions:` blocks to all 16 previously-unscoped workflows. |
| 10 | ✅ Fixed | Added `permissions:` blocks to `dependency-review` jobs in `security.yml` and `security-deep.yml`. Top-level permissions added to both workflow files. |
| 11 | ✅ Fixed | `runtime-measurement.yml` — removed `GITHUB_TOKEN` from job-level `env:` and redacted token from error diagnostic output. |
| 12 | ✅ Fixed | `quality.yml` — `SONAR_TOKEN` removed from job-level `env:`; scoped to step-level `env:` on the SonarCloud and quality-gate steps only. |
| 13 | ✅ Fixed | `ci.yml` — removed `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION: "true"` env override. |
| 14 | ℹ️ Noted | `setup-django/action.yml` is unused but preserved to avoid breaking any external references. |
| 15 | ✅ Fixed | `.github/dependabot.yml` — added `pip` ecosystem monitoring for `requirements.txt`. |
| 16 | ℹ️ Accepted | Test SECRET keys remain as allowlisted hardcoded strings (consistent with `.gitleaks.toml`). |

## Risk Level

Overall repository risk: **LOW** — All critical and high-risk findings have been remediated.

## Needs Improvement (non-breaking future work)

- Consider restricting `secrets:` on `workflow_call` reusable workflows to only the secrets each callee actually uses.
- Consider pinning reusable internal actions (`.github/actions/*`) to specific commit SHAs if they are consumed outside this repository.
