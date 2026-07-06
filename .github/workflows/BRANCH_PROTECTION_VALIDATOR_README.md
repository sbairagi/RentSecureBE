# Branch Protection Validator

Read-only auditor for GitHub branch protection and repository security settings.

## Workflow

- `.github/workflows/branch-protection-validator.yml`

## Trigger strategy

- Daily at 04:00 UTC
- On push to `main` / `master` when `.github/**` changes
- On pull request when `.github/**` changes
- Manual via `workflow_dispatch`

## Behavior

- Uses `GITHUB_TOKEN` / `GH_TOKEN`
- Never modifies repository settings
- Fails only on critical drift

## Updating required checks

Edit `scripts/branch_protection_validator.py`:

```python
DEFAULT_REQUIRED_CHECKS = [
    "lint-fast",
    "test-shard-1",
    ...
]
```

For branch-specific overrides, add a workflow input mapping or environment override.

## Evidence of API endpoints used

- `GET /repos/{owner}/{repo}/branches/{branch}/protection`
- `GET /repos/{owner}/{repo}`
- `GET /repos/{owner}/{repo}/rulesets`
- `GET /repos/{owner}/{repo}/dependency-graph/snapshots`
- `GET /repos/{owner}/{repo}/code-scanning/setup`
- `GET /repos/{owner}/{repo}/secret-scanning`
- `GET /repos/{owner}/{repo}/dependabot/alerts`
- `GET /repos/{owner}/{repo}/dependabot/updates`
- `GET /repos/{owner}/{repo}/sbom`
- `GET /repos/{owner}/{repo}/attestations`
- `GET /repos/{owner}/{repo}/actions/oidc`

## Auth matrix

| Input | Source |
|-------|--------|
| `GITHUB_TOKEN` | Built-in workflow secret |
| `GH_TOKEN` | Optional override env var |
| Missing token | Skips validation; prints `SKIPPED` |

## Critical vs Warning policy

| Finding | Severity |
|---------|----------|
| Missing branch protection | FAIL |
| Required status checks drift | FAIL |
| Force push enabled | FAIL |
| Branch deletion enabled | FAIL |
| Admin enforcement disabled | FAIL |
| Required reviews removed | FAIL |
| Merge queue disabled | WARNING |
| Signed commits unavailable | WARNING |
| Secret scanning API unavailable | WARNING |

## How to update expected required checks safely

1. Update `DEFAULT_REQUIRED_CHECKS` in `scripts/branch_protection_validator.py`
2. Open a PR changing `.github/workflows/**`
3. This workflow runs on that PR and validates the new expectation
4. The workflow blocks the PR merge if the repository protection does not match
