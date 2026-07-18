# Phase 2A Artifact Dependency Audit

**Date:** 2026-07-18
**Repository:** RentSecureBE
**Scope:** Read-only audit of all generated artifacts in architecture/, docs/, repository root, CI workflows, scripts, and tools
**Method:** Static analysis of workflow definitions, generator scripts, validator scripts, and documentation references

---

## Executive Summary

This audit inventories every generated artifact in the RentSecureBE repository, maps its complete dependency graph (producers, consumers, CI references, tooling references), and classifies each artifact for safe relocation. The audit covers 40+ distinct artifact types across 6 primary locations.

### Key Findings

- **Single Source of Truth:** `architecture/generated/architecture.json` is the central metadata file consumed by all 9 diagram generators. Any relocation of this file requires coordinated updates across all generators.
- **CI-Artifact Coupling:** 30+ artifact paths are hardcoded in GitHub Actions workflows (`.github/workflows/`). Moving any artifact requires parallel workflow updates.
- **Script-CI Coupling:** 12 diagram/architecture generator scripts in `scripts/diagrams/` write directly to specific output directories with hardcoded paths.
- **Ephemeral CI Artifacts:** Test coverage shards, mutation results, hypothesis reports, benchmark results, and security scans are uploaded as GitHub Actions artifacts with retention policies. These are inherently safe to relocate within CI context but break local developer workflows if paths change.
- **Historical Archives:** `docs/archive/` contains frozen snapshots of architecture state. These are standalone and safe to relocate, but contain stale metadata that should not be mixed with live generators.
- **Root-Level Generated Reports:** `architecture-compliance-report.*`, `architecture-dependency-graph.*`, and `architecture-summary.txt` are generated at the repository root by `scripts/architecture_contract.py`. The `architecture/reports/README.md` explicitly documents that these are intended to be migrated to `architecture/reports/` in a future phase.

### Risk Summary

| Classification | Count | Risk Level |
|----------------|-------|------------|
| SAFE | 15 | Low |
| SAFE AFTER SCRIPT UPDATE | 8 | Medium |
| SAFE AFTER CI UPDATE | 10 | Medium |
| SAFE AFTER BOTH | 7 | High |
| NEVER MOVE | 5 | Critical |

---

## Dependency Matrix

| Artifact | Created By | Read By | Referenced By | Can Be Relocated | Required Changes | Risk | Recommended Destination |
|----------|-----------|---------|---------------|------------------|------------------|------|------------------------|
| `architecture/generated/architecture.json` | `scripts/diagrams/generate_uml_from_ast.py` | All diagram generators, `validate_architecture_metadata.py`, `architecture.yml`, `uml.yml`, `uml-validation.yml` | `architecture-contract.py`, all `scripts/diagrams/generate_*.py`, CI workflows | No | Update all 9 generator scripts + 3 CI workflows + 1 validator | HIGH | Keep in `architecture/generated/` |
| `architecture/generated/architecture-metrics.json` | `scripts/diagrams/generate_architecture_metrics.py` | `architecture.yml` (upload artifact) | CI workflow only | Yes | Update `architecture.yml` output path | MEDIUM | `architecture/reports/architecture-metrics.json` |
| `architecture/generated/architecture-summary.md` | `scripts/diagrams/generate_architecture_summary.py` | `architecture.yml` (upload artifact) | CI workflow only | Yes | Update `architecture.yml` output path | MEDIUM | `architecture/reports/architecture-summary.md` |
| `architecture/generated/dependency-graph.{dot,mmd,puml}` | `scripts/diagrams/generate_dependency_graph.py` | `architecture.yml`, documentation | CI workflow, docs references | Yes | Update `architecture.yml` output path | MEDIUM | `architecture/reports/dependency-graph/` |
| `architecture/generated/module-dependency-graph.{dot,mmd}` | `scripts/diagrams/generate_dependency_graph.py` | `architecture.yml` (disabled job) | CI workflow only | Yes | Update `architecture.yml` output path | LOW | `architecture/reports/module-dependency-graph/` |
| `architecture/generated/component-dependency-graph.{dot,mmd,puml}` | `scripts/diagrams/generate_dependency_graph.py` | `architecture.yml` (disabled job) | CI workflow only | Yes | Update `architecture.yml` output path | LOW | `architecture/reports/component-dependency-graph/` |
| `docs/uml/generated/plantuml/*.puml` | `scripts/diagrams/generate_plantuml.py` | `uml.yml`, `uml-validation.yml`, documentation, `required_diagrams.txt` | CI workflows, `validate_diagrams.py`, `check_missing_diagrams.py` | No | Update generator + 2 CI workflows + 2 validators + `required_diagrams.txt` | HIGH | Keep in `docs/uml/generated/plantuml/` |
| `docs/uml/generated/mermaid/*.mmd` | `scripts/diagrams/generate_mermaid.py` | `uml.yml`, `uml-validation.yml`, documentation, `required_diagrams.txt` | CI workflows, `validate_diagrams.py`, `check_missing_diagrams.py` | No | Update generator + 2 CI workflows + 2 validators + `required_diagrams.txt` | HIGH | Keep in `docs/uml/generated/mermaid/` |
| `docs/uml/generated/domain/*.puml` | `scripts/diagrams/generate_domain_diagrams.py` | `uml.yml`, `uml-validation.yml`, documentation, `required_diagrams.txt` | CI workflows, `validate_diagrams.py`, `check_missing_diagrams.py` | No | Update generator + 2 CI workflows + 2 validators + `required_diagrams.txt` | HIGH | Keep in `docs/uml/generated/domain/` |
| `docs/uml/generated/ddd/*.puml` | `scripts/diagrams/generate_ddd_diagrams.py` | `uml.yml`, `uml-validation.yml`, documentation, `required_diagrams.txt` | CI workflows, `validate_diagrams.py`, `check_missing_diagrams.py` | No | Update generator + 2 CI workflows + 2 validators + `required_diagrams.txt` | HIGH | Keep in `docs/uml/generated/ddd/` |
| `docs/diagrams/generated/c4/*.puml` | `scripts/diagrams/generate_c4.py` | `uml.yml`, `uml-validation.yml`, documentation, `required_diagrams.txt` | CI workflows, `validate_diagrams.py`, `check_missing_diagrams.py` | No | Update generator + 2 CI workflows + 2 validators + `required_diagrams.txt` | HIGH | Keep in `docs/diagrams/generated/c4/` |
| `docs/diagrams/generated/flows/*.puml` | `scripts/diagrams/generate_flow_diagrams.py` | `uml.yml`, `uml-validation.yml`, documentation, `required_diagrams.txt` | CI workflows, `validate_diagrams.py`, `check_missing_diagrams.py` | No | Update generator + 2 CI workflows + 2 validators + `required_diagrams.txt` | HIGH | Keep in `docs/diagrams/generated/flows/` |
| `docs/diagrams/generated/infrastructure/*.puml` | `scripts/diagrams/generate_infrastructure_diagrams.py` | `uml.yml`, `uml-validation.yml`, documentation, `required_diagrams.txt` | CI workflows, `validate_diagrams.py`, `check_missing_diagrams.py` | No | Update generator + 2 CI workflows + 2 validators + `required_diagrams.txt` | HIGH | Keep in `docs/diagrams/generated/infrastructure/` |
| `architecture-compliance-report.json` | `scripts/architecture_contract.py` | `architecture-guard.yml`, CI artifacts | `architecture-guard.yml`, docs | Yes | Update script output path + CI workflow artifact path | MEDIUM | `architecture/reports/compliance/architecture-compliance-report.json` |
| `architecture-compliance-report.md` | `scripts/architecture_contract.py` | `architecture-guard.yml`, CI artifacts | `architecture-guard.yml`, docs | Yes | Update script output path + CI workflow artifact path | MEDIUM | `architecture/reports/compliance/architecture-compliance-report.md` |
| `architecture-dependency-graph.{dot,mmd}` | `scripts/architecture_contract.py` | `architecture.yml`, documentation | `architecture.yml`, docs, `architecture/reports/README.md` | Yes | Update script output path + CI workflow + docs references | MEDIUM | `architecture/reports/dependency-graph/` |
| `architecture-summary.txt` | `scripts/architecture_contract.py` | `architecture.yml`, documentation | `architecture.yml`, docs, `architecture/reports/README.md` | Yes | Update script output path + CI workflow + docs references | MEDIUM | `architecture/reports/architecture-summary.txt` |
| `docs/archive/generated/history-generated/architecture.json` | Historical snapshot (manual/CI) | Archive documentation | `docs/archive/` only | Yes | None (standalone archive) | LOW | Keep in `docs/archive/generated/history-generated/` |
| `docs/archive/audits/architecture-audit-report.md` | Manual/CI generation | Archive documentation | `docs/archive/` only | Yes | None (standalone archive) | LOW | Keep in `docs/archive/audits/` |
| `docs/archive/reports/baseline/*.md` | Manual/CI generation | Archive documentation | `docs/archive/` only | Yes | None (standalone archive) | LOW | Keep in `docs/archive/reports/baseline/` |
| `docs/archive/reports/ci-cd-upgrade-report.md` | Manual/CI generation | Archive documentation | `docs/archive/` only | Yes | None (standalone archive) | LOW | Keep in `docs/archive/reports/` |
| `runtime-metrics.json` | `runtime-measurement.yml` (inline Python) | `ci-metrics.yml` | CI workflow chain | No | Update inline script in both workflows | HIGH | Keep as ephemeral CI artifact |
| `runtime-report.md` | `runtime-measurement.yml` (inline Python) | PR comments, CI artifacts | CI workflow, sticky-comment action | No | Update inline script in workflow | HIGH | Keep as ephemeral CI artifact |
| `ci-metrics.json` | `ci-metrics.yml` (inline Python) | `ci-metrics.yml` summary generation | CI workflow chain | No | Update inline script in workflow | HIGH | Keep as ephemeral CI artifact |
| `ci-metrics-summary.md` | `ci-metrics.yml` (inline Python) | PR comments, `GITHUB_STEP_SUMMARY` | CI workflow, sticky-comment action | No | Update inline script in workflow | HIGH | Keep as ephemeral CI artifact |
| `coverage.xml` | `quality.yml` (coverage combine) | SonarCloud, coverage validation | `quality.yml`, SonarCloud action | No | Update workflow path if changed | HIGH | Keep as ephemeral CI artifact |
| `.coverage.{shard}` | `test.yml` (pytest-cov) | `quality.yml` (combine) | `test.yml`, `quality.yml` | No | Update `COVERAGE_FILE` env var + artifact paths | HIGH | Keep as ephemeral CI artifact |
| `shard-metrics.json` | `test.yml` (inline Python) | `ci.yml` (shard-validation) | `test.yml`, `ci.yml` | No | Update inline script + artifact name | HIGH | Keep as ephemeral CI artifact |
| `locust-report.{html,csv}` | `load-test.yml`, `performance.yml` | CI artifacts, `check_perf_thresholds.py` | Load test workflows | No | Update artifact upload paths + script references | MEDIUM | Keep as ephemeral CI artifact |
| `benchmark-results.json` | `benchmark.yml`, `performance.yml` | CI artifacts | Benchmark workflows | No | Update artifact upload paths | MEDIUM | Keep as ephemeral CI artifact |
| `mutmut-output.txt`, `.mutmut-cache/` | `mutation.yml` | CI artifacts | Mutation workflow | No | Update artifact upload paths | MEDIUM | Keep as ephemeral CI artifact |
| `.hypothesis/` | `hypothesis.yml` | CI artifacts | Hypothesis workflow | No | Update artifact upload paths | MEDIUM | Keep as ephemeral CI artifact |
| `semgrep.sarif` | `security.yml` | GitHub Security tab | Security workflow | No | Update SARIF upload path | MEDIUM | Keep as ephemeral CI artifact |
| `trivy-results.sarif`, `trivy-secrets.sarif` | `security.yml` | GitHub Security tab | Security workflow | No | Update SARIF upload paths | MEDIUM | Keep as ephemeral CI artifact |
| `scorecard-results.sarif` | `security-deep.yml` | GitHub Security tab | Security-deep workflow | No | Update SARIF upload path | MEDIUM | Keep as ephemeral CI artifact |
| `sbom.{cdx,spdx}.json` | `sbom.yml` | `sbom-scan` job, CI artifacts | SBOM workflow | No | Update artifact names + download paths | MEDIUM | Keep as ephemeral CI artifact |
| `grype-report.json`, `osv-report.json` | `sbom.yml` | CI artifacts | SBOM workflow | No | Update artifact upload paths | MEDIUM | Keep as ephemeral CI artifact |
| `dependency-risk-report.md` | `sbom.yml` (inline) | CI artifacts | SBOM workflow | No | Update inline script + artifact path | MEDIUM | Keep as ephemeral CI artifact |
| `branch-protection-report.{txt,json}` | `branch-protection-validator.yml` | CI artifacts | Branch protection workflow | No | Update script output path + artifact paths | MEDIUM | Keep as ephemeral CI artifact |
| `rollback-report.md` | `rollback.yml` (inline) | CI artifacts | Rollback workflow | No | Update inline script + artifact path | MEDIUM | Keep as ephemeral CI artifact |
| `vulture-report.txt` | `lint.yml` (inline) | CI artifacts | Lint workflow | No | Update tee output path | MEDIUM | Keep as ephemeral CI artifact |
| `db.sqlite3` | Django test runner | Django ORM | Test workflows, migration validation | NEVER MOVE | Would break all test/migration workflows | CRITICAL | Keep at repository root |
| `.mutmut-cache/` | `mutation.yml` | mutmut tool | Mutation workflow | NEVER MOVE | mutmut expects cache in CWD | CRITICAL | Keep at repository root |
| `.hypothesis/` | `hypothesis.yml` | Hypothesis tool | Hypothesis workflow | NEVER MOVE | Hypothesis expects cache in CWD | CRITICAL | Keep at repository root |
| `reports/` (local CI guard output) | `tools/ship.py`, `tools/report_generator.py` | Developer local workflow | `tools/ci_guard.py`, `tools/ship.py` | No | Update `ReportGenerator.save()` default path | MEDIUM | Keep at `reports/` |
| `mutants/` | `mutation.yml` | mutmut sandbox | Mutation workflow | NEVER MOVE | mutmut sandbox path | CRITICAL | Keep at repository root |

---

## Current Producers

### Script Producers (`scripts/`)

| Script | Artifacts Produced | Output Paths (hardcoded) |
|--------|-------------------|--------------------------|
| `scripts/diagrams/generate_uml_from_ast.py` | `architecture.json` | `architecture/generated/architecture.json` |
| `scripts/diagrams/generate_plantuml.py` | PlantUML diagrams | `docs/uml/generated/plantuml/` |
| `scripts/diagrams/generate_mermaid.py` | Mermaid diagrams | `docs/uml/generated/mermaid/` |
| `scripts/diagrams/generate_c4.py` | C4 diagrams | `docs/diagrams/generated/c4/` |
| `scripts/diagrams/generate_domain_diagrams.py` | ER diagrams | `docs/uml/generated/domain/` |
| `scripts/diagrams/generate_flow_diagrams.py` | Flow diagrams | `docs/diagrams/generated/flows/` |
| `scripts/diagrams/generate_infrastructure_diagrams.py` | Infrastructure diagrams | `docs/diagrams/generated/infrastructure/` |
| `scripts/diagrams/generate_ddd_diagrams.py` | DDD diagrams | `docs/uml/generated/ddd/` |
| `scripts/diagrams/generate_dependency_graph.py` | Dependency graphs | `architecture/generated/dependency-graph/`, `module-dependency-graph/`, `component-dependency-graph/` |
| `scripts/diagrams/generate_architecture_metrics.py` | Metrics JSON | `architecture/generated/architecture-metrics.json` |
| `scripts/diagrams/generate_architecture_summary.py` | Summary Markdown | `architecture/generated/architecture-summary.md` |
| `scripts/architecture_contract.py` | Compliance reports, dependency graphs | Root-level: `architecture-compliance-report.{json,md}`, `architecture-dependency-graph.{dot,mmd}`, `architecture-summary.txt` |
| `tools/report_generator.py` | CI guard reports | `reports/ci-report.{md,json}` |
| `tools/ship.py` | Orchestrates above | Indirect via `tools/ci_guard.py` |

### CI Workflow Producers (`.github/workflows/`)

| Workflow | Artifacts Produced | Output Mechanism |
|----------|-------------------|------------------|
| `ci.yml` | Orchestrates all workflows | Reusable workflow calls |
| `architecture.yml` | Architecture metrics, dependency graphs, component graphs, summary | Script execution + artifact upload |
| `uml.yml` | PlantUML, Mermaid, C4, domain, flow, infrastructure, DDD diagrams | Script execution + artifact upload |
| `uml-validation.yml` | Same as uml.yml (validation only, no upload) | Script execution (no artifact upload) |
| `architecture-guard.yml` | Compliance reports | `scripts/architecture_contract.py` + artifact upload |
| `quality.yml` | `coverage.xml` | Coverage combine + SonarCloud upload |
| `test.yml` | `.coverage.{shard}`, `shard-metrics.json` | pytest-cov + inline Python |
| `security.yml` | `semgrep.sarif`, `trivy-results.sarif`, `trivy-secrets.sarif` | Tool execution + SARIF upload |
| `security-deep.yml` | `scorecard-results.sarif` | Scorecard action + SARIF upload |
| `sbom.yml` | SBOMs, vulnerability reports, dependency risk report | Syft + CycloneDX + Grype + OSV |
| `runtime-measurement.yml` | `runtime-metrics.json`, `runtime-report.md` | Inline Python + artifact upload |
| `ci-metrics.yml` | `ci-metrics.json`, `ci-metrics-summary.md` | Inline Python + artifact upload |
| `mutation.yml` | `mutmut-output.txt`, `.mutmut-cache/` | mutmut execution + artifact upload |
| `hypothesis.yml` | `.hypothesis/` | Hypothesis execution + artifact upload |
| `benchmark.yml` | `benchmark-results.json` | pytest-benchmark + artifact upload |
| `performance.yml` | `locust-report.{html,csv}`, `benchmark-results.json` | Locust + pytest-benchmark |
| `load-test.yml` | `locust-report.{html,csv}` | Locust + artifact upload |
| `branch-protection-validator.yml` | `branch-protection-report.{txt,json}` | Script execution + artifact upload |
| `rollback.yml` | `rollback-report.md` | Inline Python + artifact upload |
| `lint.yml` | `vulture-report.txt` | Vulture execution + tee |
| `contract-tests.yml` | Contract validation (stdout) | pytest + schemathesis |
| `django-check.yml` | Migration validation (stdout) | Django management commands |
| `migration-rollback.yml` | Validation output (stdout) | `tools/migration_rollback_validator.py` |

---

## Current Consumers

### CI Workflow Consumers

| Workflow | Artifacts Consumed | Consumption Method |
|----------|-------------------|--------------------|
| `ci.yml` | Shard metrics, coverage shards | `shard-validation` job downloads and validates |
| `quality.yml` | Coverage shards | `actions/download-artifact` + coverage combine |
| `architecture.yml` | `architecture.json` | Script execution (regenerates if missing) |
| `uml.yml` | `architecture.json` | Script execution (regenerates if missing) |
| `uml-validation.yml` | `architecture.json` | Script execution (regenerates if missing) |
| `architecture-guard.yml` | Workflow files, `architecture_contract.py` | Direct script execution |
| `runtime-measurement.yml` | GitHub Actions API | External API call (no file dependency) |
| `ci-metrics.yml` | GitHub Actions API | External API call (no file dependency) |
| `sbom.yml` | `sbom-weekly` artifacts | `actions/download-artifact` |
| `security.yml` | Source code | Direct checkout |
| `weekly.yml` | Calls `sbom.yml`, `benchmark.yml`, `load-test.yml`, `mutation.yml`, `hypothesis.yml` | Workflow composition |

### Script Consumers

| Script | Artifacts Consumed |
|--------|-------------------|
| `scripts/diagrams/generate_plantuml.py` | `architecture/generated/architecture.json` |
| `scripts/diagrams/generate_mermaid.py` | `architecture/generated/architecture.json` |
| `scripts/diagrams/generate_c4.py` | `architecture/generated/architecture.json` |
| `scripts/diagrams/generate_domain_diagrams.py` | `architecture/generated/architecture.json` |
| `scripts/diagrams/generate_flow_diagrams.py` | `architecture/generated/architecture.json` |
| `scripts/diagrams/generate_infrastructure_diagrams.py` | `architecture/generated/architecture.json` |
| `scripts/diagrams/generate_ddd_diagrams.py` | `architecture/generated/architecture.json` |
| `scripts/diagrams/generate_dependency_graph.py` | `architecture/generated/architecture.json` |
| `scripts/diagrams/generate_architecture_metrics.py` | `architecture/generated/architecture.json` |
| `scripts/diagrams/generate_architecture_summary.py` | `architecture/generated/architecture.json` |
| `scripts/diagrams/validate_diagrams.py` | Generated diagram files |
| `scripts/diagrams/validate_diagram_links.py` | Documentation markdown files |
| `scripts/diagrams/check_missing_diagrams.py` | `required_diagrams.txt`, docs directory |
| `scripts/diagrams/check_outdated_diagrams.py` | Source files + diagram files |
| `scripts/diagrams/validate_architecture_metadata.py` | `architecture/generated/architecture.json` |
| `scripts/architecture_contract.py` | `.github/workflows/ci.yml`, workflow files |
| `tools/ci_guard.py` | Source code (indirect) |
| `tools/report_generator.py` | CI check results (in-memory) |
| `tools/ship.py` | Orchestrates all above |

### Documentation Consumers

| Document | Artifacts Referenced |
|----------|---------------------|
| `architecture/reports/README.md` | Root-level generated reports |
| `docs/architecture/README.md` | `docs/architecture/audit_data.json`, `scripts/arch_audit.py` |
| `docs/history/README.md` | Architecture version history |
| `docs/archive/audits/architecture-audit-report.md` | Standalone audit report |
| Various ADRs in `docs/architecture/adr/` | Reference architecture decisions (not generated artifacts) |

---

## Recommended Migration Order

### Phase 1: Ephemeral CI Artifacts (No Relocation Needed)

These artifacts are inherently transient and managed by GitHub Actions artifact retention. No action required.

1. Coverage shards (`.coverage.*`)
2. Shard metrics (`shard-metrics.json`)
3. Mutation results (`mutmut-output.txt`, `.mutmut-cache/`)
4. Hypothesis reports (`.hypothesis/`)
5. Benchmark results (`benchmark-results.json`)
6. Locust reports (`locust-report.*`)
7. Security scans (`semgrep.sarif`, `trivy-results.sarif`, `trivy-secrets.sarif`, `scorecard-results.sarif`)
8. SBOMs and vulnerability reports
9. Runtime/CI metrics (`runtime-metrics.json`, `runtime-report.md`, `ci-metrics.json`, `ci-metrics-summary.md`)
10. Branch protection reports
11. Rollback reports
12. Vulture reports

### Phase 2: Root-Level Generated Reports (Update Scripts + CI)

These are currently generated at the repository root but are explicitly documented as intended for `architecture/reports/` in `architecture/reports/README.md`.

1. `architecture-compliance-report.json` → `architecture/reports/compliance/architecture-compliance-report.json`
2. `architecture-compliance-report.md` → `architecture/reports/compliance/architecture-compliance-report.md`
3. `architecture-dependency-graph.dot` → `architecture/reports/dependency-graph/architecture-dependency-graph.dot`
4. `architecture-dependency-graph.mmd` → `architecture/reports/dependency-graph/architecture-dependency-graph.mmd`
5. `architecture-summary.txt` → `architecture/reports/architecture-summary.txt`

**Required changes:**
- Update `scripts/architecture_contract.py` output paths
- Update `.github/workflows/architecture-guard.yml` artifact paths
- Update `architecture/reports/README.md` to reflect new locations (or remove stale references)

### Phase 3: Architecture Generated Metadata (Keep in Place)

`architecture/generated/architecture.json` is the single source of truth. **Do not relocate.** It is consumed by 9 generators and 3 CI workflows. The `architecture/generated/` directory is the correct location for this intermediate artifact.

### Phase 4: Diagram Outputs (Keep in Place)

All diagram outputs in `docs/uml/generated/` and `docs/diagrams/generated/` should remain in their current locations. These are:
- Referenced by `scripts/diagrams/required_diagrams.txt`
- Validated by `scripts/diagrams/check_missing_diagrams.py`
- Consumed by documentation
- Uploaded as CI artifacts

Relocating would require coordinated updates across 7 generator scripts, 2 CI workflows, 2 validator scripts, and `required_diagrams.txt`.

### Phase 5: Archive Artifacts (Keep in Place)

`docs/archive/` contains frozen historical snapshots. These are standalone and should not be mixed with live generation pipelines.

---

## Required CI Updates

### If Relocating Root-Level Reports (Phase 2)

**File:** `.github/workflows/architecture-guard.yml`

Current lines (67-81):
```yaml
- name: Upload JSON compliance report
  if: always()
  uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02  # v4
  with:
    name: architecture-compliance-report
    path: architecture-compliance-report.json
    retention-days: 90

- name: Upload Markdown compliance report
  if: always()
  uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02  # v4
  with:
    name: architecture-compliance-report-md
    path: architecture-compliance-report.md
    retention-days: 90
```

Required change: Update `path:` fields to new locations under `architecture/reports/`.

**File:** `.github/workflows/architecture.yml`

Current lines (223-228):
```yaml
- name: Upload metrics artifact
  uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4
  with:
    name: architecture-metrics
    path: architecture/generated/architecture-metrics.json
    retention-days: 30
```

This artifact is already in `architecture/generated/`. No change needed unless metrics are moved to `architecture/reports/`.

### If Relocating Diagram Outputs (Not Recommended)

Would require updates to:
- `.github/workflows/uml.yml` (lines 100-102, 147-149, 194-196, 243-245, 290-292, 338-340, 387-389)
- `.github/workflows/uml-validation.yml` (lines 93-95, 132-134, 171-173, 218-220, 257-259, 298-300, 337-339)
- All 7 generator scripts in `scripts/diagrams/`
- `scripts/diagrams/required_diagrams.txt`
- `scripts/diagrams/check_missing_diagrams.py`
- `scripts/diagrams/validate_diagrams.py`

---

## Required Script Updates

### If Relocating Root-Level Reports (Phase 2)

**File:** `scripts/architecture_contract.py`

Search for all hardcoded output paths:
- `architecture-compliance-report.json`
- `architecture-compliance-report.md`
- `architecture-dependency-graph.dot`
- `architecture-dependency-graph.mmd`
- `architecture-summary.txt`

Update all `open()`, `json.dump()`, and `write_text()` calls to use new paths under `architecture/reports/`.

### If Relocating architecture.json (Not Recommended)

Would require updates to:
- `scripts/diagrams/generate_plantuml.py` (default `--metadata` path)
- `scripts/diagrams/generate_mermaid.py` (default `--metadata` path)
- `scripts/diagrams/generate_c4.py` (default `--metadata` path)
- `scripts/diagrams/generate_domain_diagrams.py` (default `--metadata` path)
- `scripts/diagrams/generate_flow_diagrams.py` (default `--metadata` path)
- `scripts/diagrams/generate_infrastructure_diagrams.py` (default `--metadata` path)
- `scripts/diagrams/generate_ddd_diagrams.py` (default `--metadata` path)
- `scripts/diagrams/generate_dependency_graph.py` (default `--metadata` path)
- `scripts/diagrams/generate_architecture_metrics.py` (default `--metadata` path)
- `scripts/diagrams/generate_architecture_summary.py` (required `--metadata` arg)
- `scripts/diagrams/validate_architecture_metadata.py` (hardcoded path)
- `.github/workflows/architecture.yml` (6 occurrences)
- `.github/workflows/uml.yml` (7 occurrences)
- `.github/workflows/uml-validation.yml` (7 occurrences)

---

## Rollback Risk

| Artifact Group | Rollback Risk | Reason |
|----------------|--------------|--------|
| `architecture/generated/architecture.json` | **CRITICAL** | Single source of truth; all generators depend on it |
| Diagram outputs (`docs/uml/generated/`, `docs/diagrams/generated/`) | **HIGH** | 7 generators + 2 CI workflows + 2 validators + required_diagrams.txt |
| Root-level compliance reports | **MEDIUM** | 1 script + 1 CI workflow + docs references |
| `architecture/generated/` metrics/summary | **MEDIUM** | 2 scripts + 1 CI workflow |
| Ephemeral CI artifacts | **LOW** | GitHub Actions artifacts are ephemeral by design |
| Archive artifacts | **LOW** | Standalone historical snapshots |

### Rollback Procedure

If a relocation breaks CI:

1. **Immediate:** Revert the script/CI changes that modified artifact paths.
2. **Verification:** Re-run the affected CI workflow to confirm artifacts are generated at original paths.
3. **Cleanup:** Remove any partially generated artifacts from new locations.
4. **Root cause:** Identify missing references in scripts, workflows, or validators.
5. **Re-attempt:** Apply path changes incrementally (one artifact group at a time) with full CI validation between changes.

---

## Updated Archive Classification

### `docs/archive/`

| Artifact | Classification | Rationale |
|----------|---------------|-----------|
| `docs/archive/generated/history-generated/architecture.json` | **NEVER MOVE** (within archive) | Historical snapshot; moving would break archive integrity |
| `docs/archive/audits/architecture-audit-report.md` | **SAFE** | Standalone report; no live references |
| `docs/archive/reports/baseline/architecture-baseline.md` | **SAFE** | Standalone baseline report |
| `docs/archive/reports/baseline/architecture-baseline-validation.md` | **SAFE** | Standalone baseline validation |
| `docs/archive/reports/ci-cd-upgrade-report.md` | **SAFE** | Standalone upgrade report |

### `architecture/reports/` (Intended Destination)

This directory already contains a `README.md` documenting the intended migration of root-level generated reports. The README explicitly states:

> "During a future architecture phase, the CI scripts and GitHub Actions will be updated to write reports to this directory (`architecture/reports/`), at which point these files will be moved here without content modification."

This confirms that `architecture/reports/` is the designated destination for:
- `architecture-compliance-report.json`
- `architecture-compliance-report.md`
- `architecture-dependency-graph.dot`
- `architecture-dependency-graph.mmd`
- `architecture-summary.txt`

---

## Artifact Classification Summary

### SAFE (15 artifacts)

These artifacts are either ephemeral CI artifacts with no persistent local consumers, or standalone archive files with no live references:

- All ephemeral CI artifacts (coverage, mutation, hypothesis, benchmark, locust, security scans, SBOMs, metrics, branch protection, rollback, vulture)
- All archive artifacts in `docs/archive/`
- `architecture/generated/architecture-metrics.json` (if kept in place)
- `architecture/generated/architecture-summary.md` (if kept in place)
- `architecture/generated/dependency-graph.*` (if kept in place)
- `architecture/generated/module-dependency-graph.*` (if kept in place)
- `architecture/generated/component-dependency-graph.*` (if kept in place)

### SAFE AFTER SCRIPT UPDATE (8 artifacts)

These artifacts are produced by scripts with hardcoded output paths, but are not consumed by other scripts. Updating the producer script is sufficient:

- `architecture/generated/architecture-metrics.json` → move to `architecture/reports/`
- `architecture/generated/architecture-summary.md` → move to `architecture/reports/`
- `architecture/generated/dependency-graph.*` → move to `architecture/reports/dependency-graph/`
- `architecture/generated/module-dependency-graph.*` → move to `architecture/reports/module-dependency-graph/`
- `architecture/generated/component-dependency-graph.*` → move to `architecture/reports/component-dependency-graph/`
- `architecture-compliance-report.json` → move to `architecture/reports/compliance/`
- `architecture-compliance-report.md` → move to `architecture/reports/compliance/`
- `architecture-summary.txt` → move to `architecture/reports/`

### SAFE AFTER CI UPDATE (10 artifacts)

These artifacts are consumed by CI workflows but produced by inline scripts (not standalone producer scripts). Updating the CI workflow is sufficient:

- `runtime-metrics.json` (produced inline in `runtime-measurement.yml`)
- `runtime-report.md` (produced inline in `runtime-measurement.yml`)
- `ci-metrics.json` (produced inline in `ci-metrics.yml`)
- `ci-metrics-summary.md` (produced inline in `ci-metrics.yml`)
- `coverage.xml` (produced inline in `quality.yml`)
- `.coverage.{shard}` (produced by pytest-cov in `test.yml`)
- `shard-metrics.json` (produced inline in `test.yml`)
- `locust-report.{html,csv}` (produced by Locust in `load-test.yml`/`performance.yml`)
- `benchmark-results.json` (produced by pytest-benchmark in `benchmark.yml`/`performance.yml`)
- `rollback-report.md` (produced inline in `rollback.yml`)

### SAFE AFTER BOTH (7 artifacts)

These artifacts are produced by standalone scripts AND consumed by CI workflows. Both must be updated:

- `architecture-compliance-report.json` (produced by `scripts/architecture_contract.py`, consumed by `architecture-guard.yml`)
- `architecture-compliance-report.md` (produced by `scripts/architecture_contract.py`, consumed by `architecture-guard.yml`)
- `architecture-dependency-graph.dot` (produced by `scripts/architecture_contract.py`, consumed by `architecture.yml`)
- `architecture-dependency-graph.mmd` (produced by `scripts/architecture_contract.py`, consumed by `architecture.yml`)
- `architecture-summary.txt` (produced by `scripts/architecture_contract.py`, consumed by `architecture.yml`)
- `architecture/generated/architecture-metrics.json` (produced by `scripts/diagrams/generate_architecture_metrics.py`, consumed by `architecture.yml`)
- `architecture/generated/architecture-summary.md` (produced by `scripts/diagrams/generate_architecture_summary.py`, consumed by `architecture.yml`)

Note: Some artifacts appear in both SAFE AFTER SCRIPT UPDATE and SAFE AFTER BOTH because they have both standalone script producers AND CI workflow consumers. The SAFE AFTER BOTH classification is more accurate for these.

### NEVER MOVE (5 artifacts)

These artifacts are either runtime-generated in-place by tools that expect specific working directories, or are database files that would break all test/migration workflows:

| Artifact | Reason |
|----------|--------|
| `db.sqlite3` | Django test database; all test/migration workflows assume it at repo root |
| `.mutmut-cache/` | mutmut expects cache directory in current working directory |
| `.hypothesis/` | Hypothesis expects cache directory in current working directory |
| `mutants/` | mutmut sandbox directory expected at repo root |
| `architecture/generated/architecture.json` | Single source of truth consumed by 9 generators + 3 CI workflows |

---

## Appendix A: Complete Artifact Inventory

### Architecture Generated Artifacts

| Path | Type | Producer | Consumer(s) | Classification |
|------|------|----------|-------------|----------------|
| `architecture/generated/architecture.json` | JSON metadata | `generate_uml_from_ast.py` | 9 generators, 3 CI workflows, 1 validator | NEVER MOVE |
| `architecture/generated/architecture-metrics.json` | JSON metrics | `generate_architecture_metrics.py` | `architecture.yml` | SAFE AFTER BOTH |
| `architecture/generated/architecture-summary.md` | Markdown | `generate_architecture_summary.py` | `architecture.yml` | SAFE AFTER BOTH |
| `architecture/generated/dependency-graph.{dot,mmd,puml}` | Graph files | `generate_dependency_graph.py` | `architecture.yml` | SAFE AFTER SCRIPT UPDATE |
| `architecture/generated/module-dependency-graph.{dot,mmd}` | Graph files | `generate_dependency_graph.py` | `architecture.yml` (disabled) | SAFE AFTER SCRIPT UPDATE |
| `architecture/generated/component-dependency-graph.{dot,mmd,puml}` | Graph files | `generate_dependency_graph.py` | `architecture.yml` (disabled) | SAFE AFTER SCRIPT UPDATE |

### UML Generated Artifacts

| Path | Type | Producer | Consumer(s) | Classification |
|------|------|----------|-------------|----------------|
| `docs/uml/generated/plantuml/*.puml` | PlantUML | `generate_plantuml.py` | `uml.yml`, `uml-validation.yml`, docs | SAFE (keep in place) |
| `docs/uml/generated/mermaid/*.mmd` | Mermaid | `generate_mermaid.py` | `uml.yml`, `uml-validation.yml`, docs | SAFE (keep in place) |
| `docs/uml/generated/domain/*.puml` | PlantUML | `generate_domain_diagrams.py` | `uml.yml`, `uml-validation.yml`, docs | SAFE (keep in place) |
| `docs/uml/generated/ddd/*.puml` | PlantUML | `generate_ddd_diagrams.py` | `uml.yml`, `uml-validation.yml`, docs | SAFE (keep in place) |

### Diagrams Generated Artifacts

| Path | Type | Producer | Consumer(s) | Classification |
|------|------|----------|-------------|----------------|
| `docs/diagrams/generated/c4/*.puml` | PlantUML/C4 | `generate_c4.py` | `uml.yml`, `uml-validation.yml`, docs | SAFE (keep in place) |
| `docs/diagrams/generated/flows/*.puml` | PlantUML | `generate_flow_diagrams.py` | `uml.yml`, `uml-validation.yml`, docs | SAFE (keep in place) |
| `docs/diagrams/generated/infrastructure/*.puml` | PlantUML | `generate_infrastructure_diagrams.py` | `uml.yml`, `uml-validation.yml`, docs | SAFE (keep in place) |

### Root-Level Generated Reports

| Path | Type | Producer | Consumer(s) | Classification |
|------|------|----------|-------------|----------------|
| `architecture-compliance-report.json` | JSON | `architecture_contract.py` | `architecture-guard.yml` | SAFE AFTER BOTH |
| `architecture-compliance-report.md` | Markdown | `architecture_contract.py` | `architecture-guard.yml` | SAFE AFTER BOTH |
| `architecture-dependency-graph.dot` | Graphviz | `architecture_contract.py` | `architecture.yml` | SAFE AFTER BOTH |
| `architecture-dependency-graph.mmd` | Mermaid | `architecture_contract.py` | `architecture.yml` | SAFE AFTER BOTH |
| `architecture-summary.txt` | Text | `architecture_contract.py` | `architecture.yml` | SAFE AFTER BOTH |

### CI Ephemeral Artifacts

| Path | Type | Producer | Consumer(s) | Classification |
|------|------|----------|-------------|----------------|
| `coverage.xml` | XML | `quality.yml` | SonarCloud | SAFE AFTER CI UPDATE |
| `.coverage.{1,2,3,4}` | Coverage | `test.yml` | `quality.yml` | SAFE AFTER CI UPDATE |
| `shard-metrics.json` | JSON | `test.yml` | `ci.yml` | SAFE AFTER CI UPDATE |
| `runtime-metrics.json` | JSON | `runtime-measurement.yml` | `ci-metrics.yml` | SAFE AFTER CI UPDATE |
| `runtime-report.md` | Markdown | `runtime-measurement.yml` | PR comments | SAFE AFTER CI UPDATE |
| `ci-metrics.json` | JSON | `ci-metrics.yml` | Internal | SAFE AFTER CI UPDATE |
| `ci-metrics-summary.md` | Markdown | `ci-metrics.yml` | PR comments | SAFE AFTER CI UPDATE |
| `mutmut-output.txt` | Text | `mutation.yml` | CI artifacts | SAFE AFTER CI UPDATE |
| `.mutmut-cache/` | Directory | `mutation.yml` | mutmut | NEVER MOVE |
| `.hypothesis/` | Directory | `hypothesis.yml` | Hypothesis | NEVER MOVE |
| `benchmark-results.json` | JSON | `benchmark.yml` | CI artifacts | SAFE AFTER CI UPDATE |
| `locust-report.{html,csv}` | HTML/CSV | `load-test.yml` | CI artifacts | SAFE AFTER CI UPDATE |
| `semgrep.sarif` | SARIF | `security.yml` | GitHub Security | SAFE AFTER CI UPDATE |
| `trivy-results.sarif` | SARIF | `security.yml` | GitHub Security | SAFE AFTER CI UPDATE |
| `trivy-secrets.sarif` | SARIF | `security.yml` | GitHub Security | SAFE AFTER CI UPDATE |
| `scorecard-results.sarif` | SARIF | `security-deep.yml` | GitHub Security | SAFE AFTER CI UPDATE |
| `sbom.cdx.json` | JSON | `sbom.yml` | `sbom-scan` | SAFE AFTER CI UPDATE |
| `sbom.spdx.json` | JSON | `sbom.yml` | CI artifacts | SAFE AFTER CI UPDATE |
| `sbom-syft.cdx.json` | JSON | `sbom.yml` | `sbom-scan` | SAFE AFTER CI UPDATE |
| `grype-report.json` | JSON | `sbom.yml` | CI artifacts | SAFE AFTER CI UPDATE |
| `osv-report.json` | JSON | `sbom.yml` | CI artifacts | SAFE AFTER CI UPDATE |
| `dependency-risk-report.md` | Markdown | `sbom.yml` | CI artifacts | SAFE AFTER CI UPDATE |
| `branch-protection-report.txt` | Text | `branch-protection-validator.yml` | CI artifacts | SAFE AFTER CI UPDATE |
| `branch-protection-report.json` | JSON | `branch-protection-validator.yml` | CI artifacts | SAFE AFTER CI UPDATE |
| `rollback-report.md` | Markdown | `rollback.yml` | CI artifacts | SAFE AFTER CI UPDATE |
| `vulture-report.txt` | Text | `lint.yml` | CI artifacts | SAFE AFTER CI UPDATE |

### Archive Artifacts

| Path | Type | Producer | Consumer(s) | Classification |
|------|------|----------|-------------|----------------|
| `docs/archive/generated/history-generated/architecture.json` | JSON | Historical CI | Archive docs | SAFE |
| `docs/archive/audits/architecture-audit-report.md` | Markdown | Manual/CI | Archive docs | SAFE |
| `docs/archive/reports/baseline/architecture-baseline.md` | Markdown | Manual/CI | Archive docs | SAFE |
| `docs/archive/reports/baseline/architecture-baseline-validation.md` | Markdown | Manual/CI | Archive docs | SAFE |
| `docs/archive/reports/ci-cd-upgrade-report.md` | Markdown | Manual/CI | Archive docs | SAFE |

### Runtime/Environment Artifacts

| Path | Type | Producer | Consumer(s) | Classification |
|------|------|----------|-------------|----------------|
| `db.sqlite3` | SQLite DB | Django test runner | All test/migration workflows | NEVER MOVE |
| `mutants/` | Directory | mutmut | mutmut sandbox | NEVER MOVE |

---

## Appendix B: Artifact Dependency Graph

```
architecture/generated/architecture.json (SSOT)
    ├── scripts/diagrams/generate_plantuml.py
    │   └── docs/uml/generated/plantuml/*.puml
    │       ├── uml.yml (upload artifact)
    │       ├── uml-validation.yml (validate)
    │       └── check_missing_diagrams.py
    │
    ├── scripts/diagrams/generate_mermaid.py
    │   └── docs/uml/generated/mermaid/*.mmd
    │       ├── uml.yml (upload artifact)
    │       ├── uml-validation.yml (validate)
    │       └── check_missing_diagrams.py
    │
    ├── scripts/diagrams/generate_c4.py
    │   └── docs/diagrams/generated/c4/*.puml
    │       ├── uml.yml (upload artifact)
    │       ├── uml-validation.yml (validate)
    │       └── check_missing_diagrams.py
    │
    ├── scripts/diagrams/generate_domain_diagrams.py
    │   └── docs/uml/generated/domain/*.puml
    │       ├── uml.yml (upload artifact)
    │       ├── uml-validation.yml (validate)
    │       └── check_missing_diagrams.py
    │
    ├── scripts/diagrams/generate_flow_diagrams.py
    │   └── docs/diagrams/generated/flows/*.puml
    │       ├── uml.yml (upload artifact)
    │       ├── uml-validation.yml (validate)
    │       └── check_missing_diagrams.py
    │
    ├── scripts/diagrams/generate_infrastructure_diagrams.py
    │   └── docs/diagrams/generated/infrastructure/*.puml
    │       ├── uml.yml (upload artifact)
    │       ├── uml-validation.yml (validate)
    │       └── check_missing_diagrams.py
    │
    ├── scripts/diagrams/generate_ddd_diagrams.py
    │   └── docs/uml/generated/ddd/*.puml
    │       ├── uml.yml (upload artifact)
    │       ├── uml-validation.yml (validate)
    │       └── check_missing_diagrams.py
    │
    ├── scripts/diagrams/generate_dependency_graph.py
    │   └── architecture/generated/dependency-graph.*
    │       └── architecture.yml
    │
    ├── scripts/diagrams/generate_architecture_metrics.py
    │   └── architecture/generated/architecture-metrics.json
    │       └── architecture.yml
    │
    ├── scripts/diagrams/generate_architecture_summary.py
    │   └── architecture/generated/architecture-summary.md
    │       └── architecture.yml
    │
    └── scripts/diagrams/validate_architecture_metadata.py
        └── architecture/generated/architecture.json

scripts/architecture_contract.py
    ├── architecture-compliance-report.json
    │   └── architecture-guard.yml
    ├── architecture-compliance-report.md
    │   └── architecture-guard.yml
    ├── architecture-dependency-graph.{dot,mmd}
    │   └── architecture.yml
    └── architecture-summary.txt
        └── architecture.yml
```

---

## Appendix C: CI Workflow Artifact Flow

```
ci.yml (orchestrator)
    ├── lint.yml → vulture-report.txt (artifact)
    ├── test.yml → .coverage.{1-4}, shard-metrics.json (artifacts)
    │   └── ci.yml shard-validation → downloads + validates
    ├── architecture.yml → architecture-metrics.json, dependency-graph.*, summary (artifacts)
    ├── uml.yml → plantuml/, mermaid/, c4/, domain/, flows/, infrastructure/, ddd/ (artifacts)
    ├── uml-validation.yml → (no artifacts, validation only)
    ├── security.yml → semgrep.sarif, trivy-results.sarif, trivy-secrets.sarif (artifacts)
    ├── quality.yml
    │   ├── downloads coverage shards
    │   ├── combines → coverage.xml
    │   └── uploads to SonarCloud
    ├── deploy-readiness.yml → (validation only)
    └── deploy.yml → (deployment only)

nightly.yml (orchestrator)
    ├── hypothesis.yml → .hypothesis/ (artifact)
    ├── mutation.yml → mutmut-output.txt, .mutmut-cache/ (artifacts)
    └── security-deep.yml → scorecard-results.sarif (artifact)

weekly.yml (orchestrator)
    ├── mutation.yml (exhaustive) → mutmut-output.txt (artifact)
    ├── hypothesis.yml (stress) → .hypothesis/ (artifact)
    ├── sbom.yml → sbom.{cdx,spdx}.json, grype-report.json, osv-report.json, dependency-risk-report.md (artifacts)
    ├── benchmark.yml → benchmark-results.json (artifact)
    └── load-test.yml → locust-report.{html,csv} (artifact)

runtime-measurement.yml (workflow_run trigger)
    ├── runtime-metrics.json (artifact)
    ├── runtime-report.md (artifact)
    └── PR comment (sticky-pull-request-comment)

ci-metrics.yml (workflow_run trigger)
    ├── ci-metrics.json (artifact)
    ├── ci-metrics-summary.md (artifact)
    ├── GITHUB_STEP_SUMMARY
    └── PR comment (sticky-pull-request-comment)
```

---

## Appendix D: Safe Relocation Checklist

If relocating any artifact, complete the following checklist:

- [ ] Update producer script output path
- [ ] Update all CI workflow `run:` commands that call the producer script
- [ ] Update all CI workflow `actions/upload-artifact` `path:` fields
- [ ] Update all CI workflow `actions/download-artifact` `path:` fields
- [ ] Update any validator scripts that reference the artifact path
- [ ] Update `required_diagrams.txt` if diagram artifacts are moved
- [ ] Update any documentation that references the artifact path
- [ ] Update `architecture/reports/README.md` if root reports are moved
- [ ] Run full CI pipeline to verify all artifact paths resolve correctly
- [ ] Verify `architecture-guard.yml` compliance check passes
- [ ] Verify `uml-validation.yml` passes after diagram relocation
- [ ] Verify `architecture.yml` passes after report relocation

---

*End of Phase 2A Artifact Dependency Audit*
