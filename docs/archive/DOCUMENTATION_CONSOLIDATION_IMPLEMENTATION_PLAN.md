# Documentation Consolidation Implementation Plan

**Document:** Documentation Consolidation Implementation Plan
**Version:** 1.0.0
**Date:** 2026-07-18
**Author:** Principal Documentation Architect
**Status:** FINAL — READ-ONLY IMPLEMENTATION PLAN
**Scope:** All documentation in `docs/`, `architecture/`, `.kilo/`, repository root, and module-level docs
**Authority:** `PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md`

---

## 1. Executive Summary

This plan translates the Phase 3.1 audit into an executable, reference-safe consolidation roadmap. Every recommendation has been validated against a complete 73-file dependency map with 2,403 lines of incoming/outgoing reference tracing.

**Key Principles:**
1. `docs/architecture/future/` is **immutable canonical documentation** — never archive, never delete.
2. `docs/refactoring/` is a **living architecture collection** — keep in place unless explicit justification emerges.
3. `architecture/` documents are **Phase 0 baseline references** — keep unless archival provides clear long-term value.
4. `docs/rag/` should be **deprecated in place** with a visible deprecation banner, not archived, unless repository analysis proves complete non-use.
5. All file movements use `git mv` to preserve history.
6. Reference updates precede archival — never break canonical documentation.

**Execution Strategy:**
- **Phase 0:** Governance setup (metadata frontmatter, validation tooling)
- **Phase 1:** Safe archive generated reports/diagrams (zero external references)
- **Phase 2:** Update references for medium-risk archives
- **Phase 3:** Archive superseded ADR collections (after reference updates)
- **Phase 4:** Archive `architecture/` files (after ADR reference updates)
- **Phase 5:** Deprecate `docs/rag/` in place
- **Phase 6:** Update outdated canonical documents in place
- **Phase 7:** Final validation and CI verification

---

## 2. Dependency Map Summary

### 2.1 Complete Dependency Map by Risk Tier

#### TIER 1 — IMMUTABLE CANONICAL (Do Not Move)

| File | Incoming | Outgoing | Risk | Rationale |
|------|----------|----------|------|-----------|
| `docs/architecture/future/` (11 files) | 15+ ADR refs | 0 | **IMMUTABLE** | Canonical reference material for ADR collection |
| `docs/architecture/adr/` (23 files) | 0 (self-contained) | 11+ future refs | **IMMUTABLE** | Canonical ADR collection |
| `docs/refactoring/` (13 files) | 12+ internal refs | 0 | **LIVING** | Tightly-coupled planning collection; keep as unit |
| `docs/architecture/production-architecture.md` | 0 | 0 | **IMMUTABLE** | Year 1 production strategy canonical |
| `docs/refactoring/00_architecture_principles.md` | 16 | 11 | **HIGH** | Ratified principles; 16 incoming refs |
| `docs/refactoring/12_architecture_implementation_master_plan.md` | 15 | 0 | **HIGH** | Master plan; 15 incoming refs |
| `docs/refactoring/09_target_architecture.md` | 9 | 0 | **HIGH** | Canonical target architecture |
| `docs/business-rules/README.md` | 38 | 24 | **HIGH** | Central business rules index |
| `docs/README.md` | 40 | 20 | **HIGH** | Documentation hub |
| `README.md` | 357 | 26 | **HIGH** | Project hub |
| `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` | 23 | 1 | **HIGH** | Business logic deep dive |
| `architecture/generated/architecture.json` | 50 | 0 | **CRITICAL** | SSOT for 9+ diagram generators |

#### TIER 2 — SAFE TO ARCHIVE (Zero External References)

| File | Incoming | Outgoing | Risk | Rationale |
|------|----------|----------|------|-----------|
| `docs/refactoring/03_dead_code_cleanup_execution_plan.md` | 0 | 0 | **NONE** | Isolated |
| `docs/refactoring/04_final_production_safety_report.md` | 0 | 0 | **NONE** | Isolated |
| `docs/refactoring/05_execution_report.md` | 0 | 0 | **NONE** | Isolated |
| `docs/refactoring/07_migration_plan.md` | 0 | 0 | **NONE** | Isolated |
| `docs/architecture/01_dependency_graph.md` | 0 | 0 | **NONE** | Generated report |
| `docs/architecture/02_import_matrix.md` | 0 | 0 | **NONE** | Generated report |
| `docs/architecture/03_circular_dependencies.md` | 0 | 0 | **NONE** | Generated report |
| `docs/architecture/04_cross_app_dependencies.md` | 0 | 0 | **NONE** | Generated report |
| `docs/architecture/05_architecture_boundary_violations.md` | 0 | 0 | **NONE** | Generated report |
| `docs/architecture/06_dead_modules.md` | 0 | 0 | **NONE** | Generated report |
| `docs/architecture/07_hotspots.md` | 0 | 0 | **NONE** | Generated report |
| `docs/architecture/08_import_linter_audit.md` | 0 | 0 | **NONE** | Generated report |
| `docs/architecture/09_dependency_metrics.md` | 0 | 0 | **NONE** | Generated report |
| `docs/ci-cd-upgrade-report.md` | 0 | 0 | **NONE** | One-time report (already in archive) |
| `docs/architecture/architecture-audit-report.md` | 0 | 0 | **NONE** | Already archived |
| All root-level generated reports | 0 | 0 | **NONE** | Only referenced in plans |
| `docs/diagrams/generated/` (8 files) | 0 | 0 | **NONE** | Generated diagrams |
| `docs/uml/generated/` (11 files) | 0 | 0 | **NONE** | Generated diagrams |
| `architecture/diagrams/` (2 files) | 0 | 0 | **NONE** | Generated diagrams |
| `architecture/reports/README.md` | 0 | 0 | **NONE** | Generated index |

#### TIER 3 — ARCHIVE AFTER REFERENCE UPDATES (Medium Risk)

| File | Incoming | Outgoing | Risk | Required Updates |
|------|----------|----------|------|------------------|
| `architecture/import-layers.md` | 27 | 0 | **LOW** | Verify 0 external refs (analysis confirms 0) |
| `docs/refactoring/01_target_architecture.md` | 12 | 21 | **MEDIUM** | Update `12_master_plan` reference |
| `docs/refactoring/02_migration_roadmap.md` | 14 | 18 | **MEDIUM** | Update `12_master_plan` reference |
| `docs/refactoring/11_architecture_roadmap_review.md` | 15 | 0 | **MEDIUM** | Update `12_master_plan` reference |
| `docs/refactoring/06_architecture_audit.md` | 13 | 0 | **MEDIUM** | Update `10_gap_analysis` and `05_execution_report` |
| `properties/business_rules.md` | 44 | 1 | **MEDIUM** | Update 4 refs in `docs/business-rules/` |
| `docs/adr/` (18 files) | 39 | 0 | **MEDIUM** | Update 6+ refs (README, guardian, 3 ADRs, AI governance) |
| `architecture/adr/` (4 files) | 19+ | 3+ | **MEDIUM** | Update 3 refs in `docs/architecture/README.md` |

#### TIER 4 — ARCHIVE AFTER SIGNIFICANT REFERENCE UPDATES (High Risk)

| File | Incoming | Outgoing | Risk | Required Updates |
|------|----------|----------|------|------------------|
| `architecture/ARCHITECTURE_PRINCIPLES.md` | 63 | 0 | **HIGH** | Update 14 ADR references |
| `architecture/ROADMAP.md` | 44 | 0 | **HIGH** | Update 3 ADR references |
| `architecture/dependency-rules.md` | 37 | 0 | **HIGH** | Update 4 refs (3 ADRs + 1 audit) |
| `architecture/module-boundaries.md` | 33 | 0 | **HIGH** | Update 1 ADR reference |
| `architecture/CODING_STANDARDS.md` | 39 | 0 | **HIGH** | Update 1 ADR reference |
| `docs/architecture/README.md` | 83 | 0 | **HIGH** | Fix 4 broken internal links first |

#### TIER 5 — DO NOT ARCHIVE (Immutable Canonical Reference)

| File | Incoming | Outgoing | Risk | Rationale |
|------|----------|----------|------|-----------|
| `docs/architecture/future/02_bounded_contexts.md` | 19 | 0 | **IMMUTABLE** | 11 ADR refs + canonical bounded contexts |
| `docs/architecture/future/05_dependency_rules.md` | 28 | 0 | **IMMUTABLE** | Exact duplicate but 3 ADR refs + canonical |
| `docs/architecture/future/` (all other files) | 2-8 | 0 | **IMMUTABLE** | Canonical future architecture vision |

#### TIER 6 — DEPRECATE IN PLACE (Do Not Archive Initially)

| File | Incoming | Outgoing | Risk | Rationale |
|------|----------|----------|------|-----------|
| `docs/rag/` (23 files + manifest.json) | 1-28 | 0-25 | **MEDIUM** | Deprecated content; verify AI/script dependencies before any move |

---

## 3. Validation of Audit Recommendations

### 3.1 Recommendations Validated as Correct

| Audit Recommendation | Validation Result | Evidence |
|---------------------|-------------------|----------|
| Archive top-level generated reports | **VALIDATED** | 0 external references; only referenced in plans |
| Archive generated diagrams | **VALIDATED** | 0 external references |
| Archive `docs/architecture/architecture-audit-report.md` | **VALIDATED** | File does not exist at path; already archived |
| Archive `docs/ci-cd-upgrade-report.md` | **VALIDATED** | File does not exist at path; already archived |
| Archive `docs/refactoring/` as complete unit OR keep all together | **VALIDATED** | 13 files with extensive internal cross-references |
| Archive `docs/refactoring/01_target_architecture.md` | **VALIDATED** | 12 incoming refs, all within refactoring folder |
| Archive `docs/refactoring/02_migration_roadmap.md` | **VALIDATED** | 14 incoming refs; 1 external ref from `12_master_plan` |
| Archive `docs/refactoring/11_architecture_roadmap_review.md` | **VALIDATED** | 15 incoming refs; 1 external ref from `12_master_plan` |
| Archive `architecture/import-layers.md` | **VALIDATED** | 27 incoming refs but 0 external canonical refs |
| Keep `docs/architecture/future/` entirely | **VALIDATED** | 15+ ADR references; immutable canonical |
| Do not delete `docs/architecture/future/05_dependency_rules.md` | **VALIDATED** | Exact duplicate but 28 incoming refs including 3 ADRs |
| Keep `docs/refactoring/08_architecture_decisions.md` | **VALIDATED** | 12 incoming refs from 4 kept files |
| Keep `docs/refactoring/06_architecture_audit.md` | **VALIDATED** | 13 incoming refs from 2 refactoring files |
| Archive `properties/business_rules.md` after reference updates | **VALIDATED** | 44 incoming refs; 4 docs must update first |

### 3.2 Recommendations Requiring Adjustment

| Audit Recommendation | Adjusted Recommendation | Rationale |
|---------------------|------------------------|-----------|
| Archive `docs/refactoring/` partially | **DO NOT ARCHIVE** | Tightly-coupled collection; explicit justification required |
| Archive `architecture/` files immediately | **KEEP IN PLACE** | Archival provides minimal long-term value; high risk |
| Delete `docs/architecture/future/05_dependency_rules.md` | **KEEP IN PLACE** | Exact duplicate but 28 incoming refs |
| Archive `docs/rag/` immediately | **DEPRECATE IN PLACE FIRST** | Verify AI/script dependencies before any move |
| Archive `architecture/ARCHITECTURE_PRINCIPLES.md` | **KEEP IN PLACE** | 63 incoming refs; archival risk outweighs benefit |
| Archive `architecture/ROADMAP.md` | **KEEP IN PLACE** | 44 incoming refs; superseded but still referenced |
| Archive `architecture/dependency-rules.md` | **KEEP IN PLACE** | 37 incoming refs; concise reference useful |
| Archive `architecture/module-boundaries.md` | **KEEP IN PLACE** | 33 incoming refs; 1 ADR depends on it |
| Archive `architecture/CODING_STANDARDS.md` | **KEEP IN PLACE** | 39 incoming refs; 1 ADR depends on it |
| Archive `docs/adr/` | **KEEP AS HISTORICAL** | 39 incoming refs; update references if moved |
| Archive `architecture/adr/` | **KEEP AS HISTORICAL** | 19+ incoming refs; Phase 0 baseline |

### 3.3 Recommendations Requiring Manual Review

| Item | Review Required | Decision Needed |
|------|----------------|-----------------|
| `docs/refactoring/` collection | **YES** | Explicit justification required before any archival |
| `docs/rag/` collection | **YES** | Verify AI/script dependencies; confirm non-use |
| `architecture/` directory files | **YES** | Confirm archival provides clear long-term value |
| `docs/adr/` collection | **YES** | Confirm historical value vs. maintenance burden |
| `architecture/adr/` collection | **YES** | Confirm Phase 0 baseline preservation strategy |

---

## 4. Complete Dependency Map

### 4.1 High-Impact Reference Chains

#### Chain 1: ADR → Future Architecture → Dependency Rules

```
docs/architecture/adr/ADR-006_import_rules.md
  → docs/architecture/future/05_dependency_rules.md (line 106)
  ← docs/refactoring/05_dependency_rules.md (exact duplicate, missing)
```

**Impact:** If `docs/architecture/future/05_dependency_rules.md` is moved, 3 ADR files break.

#### Chain 2: ADR → Future Architecture → Bounded Contexts

```
docs/architecture/adr/ADR-019_event_bus.md
docs/architecture/adr/ADR-011_notification_strategy.md
docs/architecture/adr/ADR-005_domain_events.md
docs/architecture/adr/ADR-010_payment_integration.md
docs/architecture/adr/ADR-012_document_generation.md
  → docs/architecture/future/02_bounded_contexts.md (11 refs total)
```

**Impact:** If `docs/architecture/future/02_bounded_contexts.md` is moved, 11 ADR files break.

#### Chain 3: Master Plan → Superseded Documents

```
docs/refactoring/12_architecture_implementation_master_plan.md
  → docs/refactoring/08_architecture_decisions.md (line 11)
  → docs/refactoring/09_target_architecture.md (line 12)
  → docs/refactoring/10_architecture_gap_analysis.md (line 13)
  → docs/refactoring/11_architecture_roadmap_review.md (line 14)
```

**Impact:** If any of these 4 files are moved without updating `12_master_plan`, references break.

#### Chain 4: ADR → Architecture Baseline

```
architecture/adr/001-current-architecture.md
  → ../../docs/architecture/README.md (line 41)
  → ../ARCHITECTURE_PRINCIPLES.md (line 42)
  → ../CODING_STANDARDS.md (line 43)
  → ../ROADMAP.md (line 44)

architecture/adr/002-target-architecture.md
  → ../../docs/architecture/README.md (line 58)
  → ../ARCHITECTURE_PRINCIPLES.md (line 59)
  → ../ROADMAP.md (line 60)

architecture/adr/003-refactoring-strategy.md
  → ../../docs/architecture/README.md (line 63)
  → ../ROADMAP.md (line 64)
  → ../ARCHITECTURE_PRINCIPLES.md (line 65)
```

**Impact:** If any of these 4 architecture/ files are moved, 3 original ADR files break.

#### Chain 5: Documentation Guardian → ADR Index

```
scripts/diagrams/documentation_guardian.py
  → docs/adr/README.md (lines 91, 97)
  ← README.md (line 83)
  ← docs/ai-governance/AI-Architecture-Review.md (line 39)
```

**Impact:** If `docs/adr/` is moved, CI script, README, and AI governance doc break.

#### Chain 6: Business Rules → Legacy File

```
docs/business-rules/00-overview.md
  → properties/business_rules.md (line 38)

docs/business-rules/README.md
  → properties/business_rules.md (line 36)

docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md
  → properties/business_rules.md (lines 41, 392)
```

**Impact:** If `properties/business_rules.md` is moved, 3 business rules docs break.

### 4.2 Critical Infrastructure Dependencies

| File | Dependencies | Impact |
|------|-------------|--------|
| `architecture/generated/architecture.json` | 9 diagram generators + 3 CI workflows | **DO NOT MOVE** — SSOT for all generated diagrams |
| `docs/architecture/audit_data.json` | `scripts/arch_audit.py`, `docs/architecture/README.md` | Keep in place — raw data for audit scripts |
| `scripts/diagrams/documentation_guardian.py` | `docs/adr/README.md` (hardcoded) | Must update before archiving `docs/adr/` |

---

## 5. File-by-File Execution Plan

### 5.1 Safe to Execute Immediately

These actions require no reference updates and carry zero risk of breaking canonical documentation.

| # | Action | File(s) | Risk | Effort | Rollback |
|---|--------|---------|------|--------|----------|
| 1 | Archive isolated refactoring docs | `docs/refactoring/03_dead_code_cleanup_execution_plan.md`, `04_final_production_safety_report.md`, `05_execution_report.md`, `07_migration_plan.md` | **NONE** | 15 min | `git mv` back |
| 2 | Archive generated architecture reports | `docs/architecture/01_dependency_graph.md` through `09_dependency_metrics.md` | **NONE** | 10 min | `git mv` back |
| 3 | Archive root-level generated reports | `PHASE_0_VALIDATION_REPORT.md`, `PHASE_1_1_REPAIR_REPORT.md`, `PHASE_1_2_GUARDIAN_REPAIR_REPORT.md`, `PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md`, `PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md`, `PHASE_2_1_ARCHIVE_REPORT.md`, `01_repository_inventory.md`, `architecture-analysis-report.md`, `architecture-compliance-report.md`, `architecture-compliance-report.json`, `architecture-dependency-graph.mmd`, `architecture-dependency-graph.dot`, `architecture-summary.txt`, `directory-structure-analysis.md`, `DOCUMENTATION_ANALYSIS_REPORT.md`, `DOCUMENTATION_CONSOLIDATION_PLAN.md`, `DOCUMENTATION_CONSOLIDATION_REVIEW.md` | **NONE** | 20 min | `git mv` back |
| 4 | Archive generated diagrams | `docs/diagrams/generated/` (8 files), `docs/uml/generated/` (11 files), `architecture/diagrams/` (2 files) | **NONE** | 15 min | `git mv` back |
| 5 | Archive `architecture/reports/README.md` | `architecture/reports/README.md` | **NONE** | 5 min | `git mv` back |
| 6 | Add deprecation banners to `docs/rag/` | All 23 RAG files + `manifest.json` | **LOW** | 30 min | Remove banners |

**Validation after Phase 1:**
```bash
# Run documentation guardian
python scripts/diagrams/documentation_guardian.py

# Check for broken markdown links
grep -r '\[.*?\](' docs/ architecture/ README.md | grep -v 'http' | head -50

# Verify no missing references
ls docs/architecture/01_dependency_graph.md docs/refactoring/03_dead_code_cleanup_execution_plan.md
```

### 5.2 Requires Reference Updates

These actions require updating references before archival. Each step includes the exact files and lines to update.

#### 5.2.1 Update `README.md` ADR Reference

| Step | Action | File | Line | Old Reference | New Reference |
|------|--------|------|------|---------------|---------------|
| 1 | Update ADR index link | `README.md` | 83 | `docs/adr/README.md` | `docs/architecture/adr/README.md` |

**Validation:** Verify README.md renders correctly; check link resolves.

#### 5.2.2 Update `scripts/diagrams/documentation_guardian.py`

| Step | Action | File | Lines | Old Reference | New Reference |
|------|--------|------|-------|---------------|---------------|
| 1 | Update ADR index path | `scripts/diagrams/documentation_guardian.py` | 91, 97 | `docs/adr/` | `docs/architecture/adr/` |

**Validation:** Run `python scripts/diagrams/documentation_guardian.py` and verify ADR index check passes.

#### 5.2.3 Update `docs/ai-governance/AI-Architecture-Review.md`

| Step | Action | File | Line | Old Reference | New Reference |
|------|--------|------|------|---------------|---------------|
| 1 | Update ADR path | `docs/ai-governance/AI-Architecture-Review.md` | 39 | `docs/adr/` | `docs/architecture/adr/` |

**Validation:** Verify markdown link resolves correctly.

#### 5.2.4 Update `properties/business_rules.md` References

| Step | Action | File | Line | Old Reference | New Reference |
|------|--------|------|------|---------------|---------------|
| 1 | Update legacy reference | `docs/business-rules/00-overview.md` | 38 | `properties/business_rules.md` | `docs/business-rules/README.md` |
| 2 | Update legacy reference | `docs/business-rules/README.md` | 36 | `properties/business_rules.md` | Remove or update to canonical |
| 3 | Update legacy reference | `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` | 41, 392 | `properties/business_rules.md` | `docs/business-rules/README.md` |

**Validation:** Verify all 3 docs render correctly; check no broken links.

#### 5.2.5 Update `docs/architecture/README.md` Broken Links

| Step | Action | File | Lines | Old Reference | New Reference |
|------|--------|------|-------|---------------|---------------|
| 1 | Fix broken link | `docs/architecture/README.md` | 217-220 | `../ARCHITECTURE_PRINCIPLES.md` | `../refactoring/00_architecture_principles.md` |
| 2 | Fix broken link | `docs/architecture/README.md` | 217-220 | `../CODING_STANDARDS.md` | `../refactoring/10_naming_conventions.md` |
| 3 | Fix broken link | `docs/architecture/README.md` | 217-220 | `../ROADMAP.md` | `../refactoring/12_architecture_implementation_master_plan.md` |
| 4 | Fix broken link | `docs/architecture/README.md` | 217-220 | `../adr/ADR-template.md` | `../../architecture/adr/000-template.md` |

**Validation:** Run link checker; verify all internal links resolve.

#### 5.2.6 Update `architecture/adr/` References

| Step | Action | File | Lines | Old Reference | New Reference |
|------|--------|------|-------|---------------|---------------|
| 1 | Update architecture README ref | `architecture/adr/001-current-architecture.md` | 41 | `../../docs/architecture/README.md` | `../../docs/refactoring/12_architecture_implementation_master_plan.md` |
| 2 | Update principles ref | `architecture/adr/001-current-architecture.md` | 42 | `../ARCHITECTURE_PRINCIPLES.md` | Keep (if archiving, update to canonical) |
| 3 | Update coding standards ref | `architecture/adr/001-current-architecture.md` | 43 | `../CODING_STANDARDS.md` | Keep (if archiving, update to canonical) |
| 4 | Update roadmap ref | `architecture/adr/001-current-architecture.md` | 44 | `../ROADMAP.md` | Keep (if archiving, update to canonical) |
| 5 | Update architecture README ref | `architecture/adr/002-target-architecture.md` | 58 | `../../docs/architecture/README.md` | `../../docs/refactoring/12_architecture_implementation_master_plan.md` |
| 6 | Update principles ref | `architecture/adr/002-target-architecture.md` | 59 | `../ARCHITECTURE_PRINCIPLES.md` | Keep (if archiving, update to canonical) |
| 7 | Update roadmap ref | `architecture/adr/002-target-architecture.md` | 60 | `../ROADMAP.md` | Keep (if archiving, update to canonical) |
| 8 | Update architecture README ref | `architecture/adr/003-refactoring-strategy.md` | 63 | `../../docs/architecture/README.md` | `../../docs/refactoring/12_architecture_implementation_master_plan.md` |
| 9 | Update roadmap ref | `architecture/adr/003-refactoring-strategy.md` | 64 | `../ROADMAP.md` | Keep (if archiving, update to canonical) |
| 10 | Update principles ref | `architecture/adr/003-refactoring-strategy.md` | 65 | `../ARCHITECTURE_PRINCIPLES.md` | Keep (if archiving, update to canonical) |

**Validation:** Verify all 3 ADR files render correctly; check no broken links.

#### 5.2.7 Update `docs/refactoring/12_master_plan` References

| Step | Action | File | Lines | Old Reference | New Reference |
|------|--------|------|-------|---------------|---------------|
| 1 | Update target architecture ref | `docs/refactoring/12_architecture_implementation_master_plan.md` | 12 | `docs/refactoring/01_target_architecture.md` | `docs/refactoring/09_target_architecture.md` |
| 2 | Update migration roadmap ref | `docs/refactoring/12_architecture_implementation_master_plan.md` | 14 | `docs/refactoring/02_migration_roadmap.md` | Keep (if archiving, update to canonical) |
| 3 | Update roadmap review ref | `docs/refactoring/12_architecture_implementation_master_plan.md` | 14 | `docs/refactoring/11_architecture_roadmap_review.md` | Keep (if archiving, update to canonical) |

**Validation:** Verify `12_master_plan` renders correctly; check no broken links.

### 5.3 Requires Manual Review

These actions require explicit human approval before execution.

| # | Action | Rationale | Required Approval |
|---|--------|-----------|-------------------|
| 1 | Archive entire `docs/refactoring/` collection | Tightly-coupled 13-file collection; high internal cross-references | Principal Architect |
| 2 | Archive `architecture/` files | Phase 0 baseline; 63+ incoming refs; minimal long-term value | Tech Lead |
| 3 | Archive `docs/adr/` collection | 39 incoming refs; historical value; update burden | Principal Architect |
| 4 | Archive `architecture/adr/` collection | 19+ incoming refs; Phase 0 baseline | Principal Architect |
| 5 | Move `architecture/generated/architecture.json` | 50 incoming refs; SSOT for diagram generators | DevOps Lead |
| 6 | Archive `docs/rag/` collection | Verify AI/script dependencies first | AI/ML Lead |

### 5.4 Do Not Execute

These actions are explicitly prohibited based on the audit and dependency analysis.

| # | Action | Reason |
|------|--------|---------|
| 1 | Archive `docs/architecture/future/` | Immutable canonical; 15+ ADR references |
| 2 | Delete `docs/architecture/future/05_dependency_rules.md` | Exact duplicate but 28 incoming refs |
| 3 | Partially archive `docs/refactoring/` | Breaks internal reference chain |
| 4 | Archive `docs/architecture/production-architecture.md` | Year 1 strategy canonical |
| 5 | Archive `docs/architecture/adr/` without reference updates | 23-file canonical ADR collection |
| 6 | Delete `coverage-report.txt` | May be referenced by CI; archive instead |
| 7 | Move `architecture/generated/architecture.json` without CI update | 50 incoming refs; SSOT for generators |

---

## 6. Documentation Governance Improvements

### 6.1 Frontmatter Schema

Every canonical document must include YAML frontmatter:

```yaml
---
owner: Engineering
status: Canonical
canonical: true
superseded: false
generated: false
last_verified_commit: abc123def
review_cadence: Quarterly
archive_after: Never
---
```

### 6.2 Governance Matrix

| Attribute | Type | Values | Required |
|-----------|------|--------|----------|
| `owner` | String | Team/individual responsible | YES |
| `status` | Enum | `Canonical`, `Superseded`, `Deprecated`, `Archived`, `Generated` | YES |
| `canonical` | Boolean | `true` / `false` | YES |
| `superseded` | Boolean | `true` / `false` | YES |
| `superseded_by` | String | Path to superseding document | IF superseded=true |
| `generated` | Boolean | `true` / `false` | YES |
| `generated_by` | String | Script/tool that generates | IF generated=true |
| `last_verified_commit` | String | Git commit hash when last verified | YES |
| `review_cadence` | Enum | `Weekly`, `Monthly`, `Quarterly`, `Annually`, `Never` | YES |
| `archive_after` | Date | YYYY-MM-DD or `Never` | YES |
| `deprecated` | Boolean | `true` / `false` | IF status=Deprecated |
| `deprecation_reason` | String | Why deprecated | IF deprecated=true |
| `replacement` | String | Path to replacement document | IF deprecated=true |

### 6.3 Governance Application Order

| Phase | Documents to Tag | Priority |
|-------|------------------|----------|
| 0 | All canonical docs | HIGH |
| 1 | Generated reports/diagrams | MEDIUM |
| 2 | Superseded docs | MEDIUM |
| 3 | Deprecated docs (RAG) | LOW |

---

## 7. Validation Checks After Every Phase

### 7.1 Automated Validation Script

```bash
#!/bin/bash
# docs/validate_consolidation.sh

set -e

echo "=== Phase Validation ==="

# 1. Broken markdown links
echo "Checking markdown links..."
find docs/ architecture/ README.md -name "*.md" -exec grep -l '\[.*?\](' {} \; | \
  xargs -I {} python -c "
import re, sys
with open('{}') as f:
    content = f.read()
links = re.findall(r'\[.*?\]\((.*?)\)', content)
for link in links:
    if link.startswith('http'):
        continue
    path = link.split('#')[0]
    if not path:
        continue
    import os
    base = os.path.dirname('{}')
    full = os.path.join(base, path)
    if not os.path.exists(full):
        print(f'BROKEN: {} -> {link}')
        sys.exit(1)
"
echo "✓ No broken markdown links"

# 2. Broken relative paths
echo "Checking relative paths..."
# (similar to above but for image references, code blocks, etc.)

# 3. Missing references
echo "Checking for missing referenced files..."
# Verify all files referenced in documentation exist

# 4. Orphan documents
echo "Checking for orphan documents..."
# Find documents with 0 incoming references that are not marked as generated/deprecated

# 5. CI compatibility
echo "Checking CI compatibility..."
python scripts/diagrams/documentation_guardian.py

echo "=== Validation Complete ==="
```

### 7.2 Validation Checklist Per Phase

| Phase | Checks | Pass Criteria |
|-------|--------|---------------|
| 1 | Broken links, missing files, CI guardian | 0 broken links, 0 missing files, guardian passes |
| 2 | Reference updates verified | All updated links resolve correctly |
| 3 | ADR collection integrity | All ADR files present and referenced correctly |
| 4 | Architecture baseline integrity | All `architecture/` refs updated or preserved |
| 5 | RAG deprecation banners | All 23 RAG files have deprecation notice |
| 6 | Content accuracy | Outdated claims corrected; verified against code |
| 7 | Final CI run | All CI checks pass: guardian, links, architecture |

---

## 8. Final Implementation Checklist

### 8.1 Phase 0: Governance Setup

| # | Action | Risk | Effort | Rollback | Owner |
|---|--------|------|--------|----------|-------|
| 0.1 | Create `docs/CONSOLIDATION_REFERENCE_MAP.md` | LOW | 1 hour | Delete file | Architect |
| 0.2 | Add frontmatter to all canonical docs | LOW | 4 hours | Revert commits | Engineering |
| 0.3 | Set up `docs/validate_consolidation.sh` | LOW | 2 hours | Delete script | DevOps |
| 0.4 | Run baseline validation | LOW | 30 min | N/A | DevOps |

### 8.2 Phase 1: Safe Archive Generated Reports

| # | Action | Risk | Effort | Rollback | Owner |
|---|--------|------|--------|----------|-------|
| 1.1 | Archive `docs/refactoring/03_dead_code_cleanup_execution_plan.md` | NONE | 5 min | `git mv` back | Engineering |
| 1.2 | Archive `docs/refactoring/04_final_production_safety_report.md` | NONE | 5 min | `git mv` back | Engineering |
| 1.3 | Archive `docs/refactoring/05_execution_report.md` | NONE | 5 min | `git mv` back | Engineering |
| 1.4 | Archive `docs/refactoring/07_migration_plan.md` | NONE | 5 min | `git mv` back | Engineering |
| 1.5 | Archive `docs/architecture/01_dependency_graph.md` through `09_dependency_metrics.md` | NONE | 10 min | `git mv` back | Engineering |
| 1.6 | Archive root-level generated reports (17 files) | NONE | 20 min | `git mv` back | Engineering |
| 1.7 | Archive generated diagrams (21 files) | NONE | 15 min | `git mv` back | Engineering |
| 1.8 | Archive `architecture/reports/README.md` | NONE | 5 min | `git mv` back | Engineering |
| 1.9 | Run validation script | LOW | 10 min | N/A | DevOps |
| 1.10 | Commit with message "docs: archive generated reports and diagrams" | LOW | 10 min | `git revert` | Engineering |

**Total Phase 1 Effort:** ~1.5 hours
**Total Phase 1 Risk:** NONE

### 8.3 Phase 2: Update References

| # | Action | Risk | Effort | Rollback | Owner |
|---|--------|------|--------|----------|-------|
| 2.1 | Update `README.md` ADR link | LOW | 5 min | `git revert` | Engineering |
| 2.2 | Update `scripts/diagrams/documentation_guardian.py` | LOW | 10 min | `git revert` | Engineering |
| 2.3 | Update `docs/ai-governance/AI-Architecture-Review.md` | LOW | 5 min | `git revert` | Engineering |
| 2.4 | Update `docs/business-rules/00-overview.md` | LOW | 5 min | `git revert` | Engineering |
| 2.5 | Update `docs/business-rules/README.md` | LOW | 5 min | `git revert` | Engineering |
| 2.6 | Update `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` | LOW | 10 min | `git revert` | Engineering |
| 2.7 | Update `docs/architecture/README.md` broken links | MEDIUM | 15 min | `git revert` | Engineering |
| 2.8 | Update `architecture/adr/001-current-architecture.md` | MEDIUM | 10 min | `git revert` | Engineering |
| 2.9 | Update `architecture/adr/002-target-architecture.md` | MEDIUM | 10 min | `git revert` | Engineering |
| 2.10 | Update `architecture/adr/003-refactoring-strategy.md` | MEDIUM | 10 min | `git revert` | Engineering |
| 2.11 | Update `docs/refactoring/12_master_plan` references | MEDIUM | 15 min | `git revert` | Engineering |
| 2.12 | Run validation script | LOW | 10 min | N/A | DevOps |
| 2.13 | Commit with message "docs: update references for consolidation" | LOW | 10 min | `git revert` | Engineering |

**Total Phase 2 Effort:** ~2 hours
**Total Phase 2 Risk:** LOW-MEDIUM

### 8.4 Phase 3: Archive Superseded ADR Collections

| # | Action | Risk | Effort | Rollback | Owner |
|---|--------|------|--------|----------|-------|
| 3.1 | Archive `docs/adr/` (18 files) | MEDIUM | 30 min | `git mv` back | Engineering |
| 3.2 | Archive `architecture/adr/` (4 files) | MEDIUM | 10 min | `git mv` back | Engineering |
| 3.3 | Run validation script | LOW | 10 min | N/A | DevOps |
| 3.4 | Commit with message "docs: archive superseded ADR collections" | LOW | 10 min | `git revert` | Engineering |

**Total Phase 3 Effort:** ~1 hour
**Total Phase 3 Risk:** MEDIUM

### 8.5 Phase 4: Archive `architecture/` Files

**PREREQUISITE:** Explicit approval from Principal Architect and Tech Lead.

| # | Action | Risk | Effort | Rollback | Owner |
|---|--------|------|--------|----------|-------|
| 4.1 | Archive `architecture/ARCHITECTURE_PRINCIPLES.md` | HIGH | 10 min | `git mv` back | Engineering |
| 4.2 | Archive `architecture/ROADMAP.md` | HIGH | 10 min | `git mv` back | Engineering |
| 4.3 | Archive `architecture/dependency-rules.md` | HIGH | 10 min | `git mv` back | Engineering |
| 4.4 | Archive `architecture/module-boundaries.md` | HIGH | 10 min | `git mv` back | Engineering |
| 4.5 | Archive `architecture/CODING_STANDARDS.md` | HIGH | 10 min | `git mv` back | Engineering |
| 4.6 | Archive `architecture/import-layers.md` | LOW | 10 min | `git mv` back | Engineering |
| 4.7 | Archive `docs/architecture/README.md` | HIGH | 10 min | `git mv` back | Engineering |
| 4.8 | Run validation script | LOW | 10 min | N/A | DevOps |
| 4.9 | Commit with message "docs: archive superseded architecture baseline" | LOW | 10 min | `git revert` | Engineering |

**Total Phase 4 Effort:** ~1.5 hours
**Total Phase 4 Risk:** HIGH

### 8.6 Phase 5: Deprecate `docs/rag/`

**PREREQUISITE:** Verify AI/script dependencies with AI/ML Lead.

| # | Action | Risk | Effort | Rollback | Owner |
|---|--------|------|--------|----------|-------|
| 5.1 | Add deprecation banner to `docs/rag/README.md` | LOW | 10 min | Remove banner | Engineering |
| 5.2 | Add deprecation banner to all 23 RAG chunk files | LOW | 30 min | Remove banners | Engineering |
| 5.3 | Add deprecation banner to `docs/rag/manifest.json` header | LOW | 5 min | Remove banner | Engineering |
| 5.4 | Update `docs/README.md` to mark RAG as deprecated | LOW | 5 min | `git revert` | Engineering |
| 5.5 | Run validation script | LOW | 10 min | N/A | DevOps |
| 5.6 | Commit with message "docs: deprecate RAG knowledge base (outdated Year 1 strategy)" | LOW | 10 min | `git revert` | Engineering |

**Total Phase 5 Effort:** ~1 hour
**Total Phase 5 Risk:** LOW

**Future Decision:** After 30 days of deprecation, if no AI/script dependencies are found, archive to `docs/archive/deprecated/rag-knowledge-base/`.

### 8.7 Phase 6: Update Outdated Canonical Documents

| # | Action | Risk | Effort | Rollback | Owner |
|---|--------|------|--------|----------|-------|
| 6.1 | Update `README.md` — remove Cashfree/Razorpay refs, fix diagram paths | MEDIUM | 30 min | `git revert` | Engineering |
| 6.2 | Update `docs/ci-cd-pipeline.md` — reflect Year 1 manual UPI strategy | MEDIUM | 45 min | `git revert` | Engineering |
| 6.3 | Update `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` — fix signal wiring, owner group, payment strategy | MEDIUM | 45 min | `git revert` | Engineering |
| 6.4 | Update `docs/business-rules/02-subscription-and-usage-limits.md` — fix signal wiring, command status | MEDIUM | 30 min | `git revert` | Engineering |
| 6.5 | Update `docs/business-rules/14-known-behaviors-and-edge-cases.md` — fix signal wiring, owner group | MEDIUM | 30 min | `git revert` | Engineering |
| 6.6 | Update `docs/business-rules/15-authentication.md` — fix owner group claim | MEDIUM | 20 min | `git revert` | Engineering |
| 6.7 | Update `docs/business-rules/16-payments-and-webhooks.md` — fix webhook count, payment strategy | MEDIUM | 30 min | `git revert` | Engineering |
| 6.8 | Update `docs/business-rules/17-notifications.md` — reflect Year 1 free channels only | MEDIUM | 30 min | `git revert` | Engineering |
| 6.9 | Update `docs/business-rules/22-signals-and-automation.md` — fix signal wiring, command status | MEDIUM | 30 min | `git revert` | Engineering |
| 6.10 | Run validation script | LOW | 10 min | N/A | DevOps |
| 6.11 | Commit with message "docs: update outdated canonical documents to Year 1 strategy" | LOW | 10 min | `git revert` | Engineering |

**Total Phase 6 Effort:** ~4 hours
**Total Phase 6 Risk:** MEDIUM

### 8.8 Phase 7: Final Validation

| # | Action | Risk | Effort | Rollback | Owner |
|---|--------|------|--------|----------|-------|
| 7.1 | Run full documentation guardian scan | LOW | 15 min | N/A | DevOps |
| 7.2 | Run link checker on all markdown files | LOW | 15 min | N/A | DevOps |
| 7.3 | Verify CI pipeline passes | LOW | 30 min | N/A | DevOps |
| 7.4 | Verify architecture contract tests pass | LOW | 15 min | N/A | DevOps |
| 7.5 | Verify import-linter passes | LOW | 10 min | N/A | DevOps |
| 7.6 | Generate final consolidation report | LOW | 1 hour | N/A | Architect |
| 7.7 | Tag release with consolidation snapshot | LOW | 10 min | `git tag -d` | Engineering |

**Total Phase 7 Effort:** ~2.5 hours
**Total Phase 7 Risk:** NONE

---

## 9. Governance Rollout Timeline

| Week | Phase | Actions | Milestone |
|------|-------|---------|-----------|
| Week 1 | Phase 0-1 | Governance setup, safe archive generated reports | Baseline established |
| Week 2 | Phase 2 | Reference updates | All references updated |
| Week 3 | Phase 3 | Archive superseded ADRs | ADR collections consolidated |
| Week 4 | Phase 4 | Archive `architecture/` files (if approved) | Architecture baseline archived |
| Week 5 | Phase 5 | Deprecate `docs/rag/` | RAG deprecated |
| Week 6 | Phase 6 | Update outdated canonical docs | Content accuracy restored |
| Week 7 | Phase 7 | Final validation | CI green, consolidation complete |

---

## 10. Risk Mitigation Strategies

### 10.1 High-Risk Mitigations

| Risk | Mitigation | Contingency |
|------|-----------|-------------|
| Breaking ADR references | Update ALL references before archival; use `git grep` to verify | `git revert` to restore |
| Breaking CI pipeline | Run guardian script after every phase; verify CI passes | Pause consolidation; fix CI |
| Losing architecture history | Use `git mv` (not `rm`); preserve full history | Restore from git history |
| Breaking canonical documentation | Never move immutable canonical docs without explicit approval | Revert and re-plan |
| Content accuracy degradation | Review all content updates against actual code before committing | Revert content changes |

### 10.2 Medium-Risk Mitigations

| Risk | Mitigation | Contingency |
|------|-----------|-------------|
| Incomplete reference updates | Use dependency analysis report to verify 100% coverage | Run grep post-update |
| Orphan documents | Run orphan detection script after every phase | Move orphans to archive |
| Broken relative paths | Use absolute path validation in script | Manual verification |
| CI script incompatibility | Update `documentation_guardian.py` before archiving | Revert script changes |

---

## 11. Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Broken markdown links | 0 | `grep -r '\[.*?\](' docs/ | grep -v http` |
| Missing referenced files | 0 | `find . -name "*.md" -exec grep -l '\[.*?\](.*\.md)' {} \;` |
| Orphan documents (non-generated) | 0 | Custom orphan detection script |
| CI pipeline passes | 100% | GitHub Actions status |
| Documentation guardian passes | 100% | `python scripts/diagrams/documentation_guardian.py` |
| Import-linter passes | 100% | `lint-imports --config import-linter.ini` |
| Architecture contract tests pass | 100% | `python scripts/architecture_contract.py` |
| Canonical docs with frontmatter | 100% | `grep -L '^---' docs/*.md` |
| Deprecated docs marked | 100% | `grep -L 'deprecated' docs/rag/*.md` |
| Git history preserved | 100% | `git log --follow -- <file>` |

---

## 12. Appendices

### 12.1 Complete File Movement Map

```
Source → Destination
─────────────────────────────────────────────────────────────────────────────
docs/refactoring/03_dead_code_cleanup_execution_plan.md → docs/archive/planning/refactoring-complete/
docs/refactoring/04_final_production_safety_report.md → docs/archive/planning/refactoring-complete/
docs/refactoring/05_execution_report.md → docs/archive/planning/refactoring-complete/
docs/refactoring/07_migration_plan.md → docs/archive/planning/refactoring-complete/
docs/architecture/01_dependency_graph.md → docs/archive/generated/
docs/architecture/02_import_matrix.md → docs/archive/generated/
docs/architecture/03_circular_dependencies.md → docs/archive/generated/
docs/architecture/04_cross_app_dependencies.md → docs/archive/generated/
docs/architecture/05_architecture_boundary_violations.md → docs/archive/generated/
docs/architecture/06_dead_modules.md → docs/archive/generated/
docs/architecture/07_hotspots.md → docs/archive/generated/
docs/architecture/08_import_linter_audit.md → docs/archive/generated/
docs/architecture/09_dependency_metrics.md → docs/archive/generated/
PHASE_0_VALIDATION_REPORT.md → docs/archive/generated/root-reports/
PHASE_1_1_REPAIR_REPORT.md → docs/archive/generated/root-reports/
PHASE_1_2_GUARDIAN_REPAIR_REPORT.md → docs/archive/generated/root-reports/
PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md → docs/archive/generated/root-reports/
PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md → docs/archive/generated/root-reports/
PHASE_2_1_ARCHIVE_REPORT.md → docs/archive/generated/root-reports/
01_repository_inventory.md → docs/archive/generated/root-reports/
architecture-analysis-report.md → docs/archive/generated/root-reports/
architecture-compliance-report.md → docs/archive/generated/root-reports/
architecture-compliance-report.json → docs/archive/generated/root-reports/
architecture-dependency-graph.mmd → docs/archive/generated/root-reports/
architecture-dependency-graph.dot → docs/archive/generated/root-reports/
architecture-summary.txt → docs/archive/generated/root-reports/
directory-structure-analysis.md → docs/archive/generated/root-reports/
DOCUMENTATION_ANALYSIS_REPORT.md → docs/archive/generated/root-reports/
DOCUMENTATION_CONSOLIDATION_PLAN.md → docs/archive/generated/root-reports/
DOCUMENTATION_CONSOLIDATION_REVIEW.md → docs/archive/generated/root-reports/
docs/diagrams/generated/* → docs/archive/generated/diagrams/
docs/uml/generated/* → docs/archive/generated/diagrams/generated-uml/
architecture/diagrams/* → docs/archive/generated/diagrams/architecture/
architecture/reports/README.md → docs/archive/generated/
docs/ci-cd-upgrade-report.md → docs/archive/generated/ (already archived)
docs/architecture/architecture-audit-report.md → docs/archive/audits/ (already archived)
─────────────────────────────────────────────────────────────────────────────
REQUIRES REFERENCE UPDATES BEFORE MOVE:
─────────────────────────────────────────────────────────────────────────────
docs/adr/ (18 files) → docs/archive/old-adr/docs-adr/
architecture/adr/ (4 files) → docs/archive/old-adr/architecture-adr/
architecture/ARCHITECTURE_PRINCIPLES.md → docs/archive/planning/architecture-principles-concise.md
architecture/ROADMAP.md → docs/archive/planning/roadmap.md
architecture/dependency-rules.md → docs/archive/planning/dependency-rules.md
architecture/module-boundaries.md → docs/archive/planning/module-boundaries.md
architecture/CODING_STANDARDS.md → docs/archive/planning/coding-standards.md
architecture/import-layers.md → docs/archive/planning/import-layers.md
docs/architecture/README.md → docs/archive/audits/architecture-readme.md
docs/refactoring/01_target_architecture.md → docs/archive/planning/refactoring-complete/
docs/refactoring/02_migration_roadmap.md → docs/archive/planning/refactoring-complete/
docs/refactoring/06_architecture_audit.md → docs/archive/audits/architecture-audit-findings.md
docs/refactoring/08_architecture_decisions.md → docs/archive/planning/refactoring-complete/
docs/refactoring/10_architecture_gap_analysis.md → docs/archive/planning/refactoring-complete/
docs/refactoring/11_architecture_roadmap_review.md → docs/archive/planning/refactoring-complete/
properties/business_rules.md → docs/archive/deprecated/legacy-business-rules.md
─────────────────────────────────────────────────────────────────────────────
DO NOT MOVE:
─────────────────────────────────────────────────────────────────────────────
docs/architecture/future/ (all 11 files) — immutable canonical
docs/refactoring/00_architecture_principles.md — living canonical
docs/refactoring/09_target_architecture.md — living canonical
docs/refactoring/12_architecture_implementation_master_plan.md — living canonical
docs/architecture/adr/ (23 files) — immutable canonical
docs/architecture/production-architecture.md — immutable canonical
docs/architecture/audit_data.json — canonical raw data
architecture/generated/architecture.json — SSOT for generators
─────────────────────────────────────────────────────────────────────────────
```

### 12.2 Reference Update Checklist

Use this checklist to verify all references are updated before archival:

```bash
# Verify no references to archived files remain
git grep -l 'docs/adr/README.md' -- '*.md' '*.py'
git grep -l 'architecture/ARCHITECTURE_PRINCIPLES.md' -- '*.md' '*.py'
git grep -l 'architecture/ROADMAP.md' -- '*.md' '*.py'
git grep -l 'architecture/dependency-rules.md' -- '*.md' '*.py'
git grep -l 'architecture/module-boundaries.md' -- '*.md' '*.py'
git grep -l 'architecture/CODING_STANDARDS.md' -- '*.md' '*.py'
git grep -l 'architecture/import-layers.md' -- '*.md' '*.py'
git grep -l 'properties/business_rules.md' -- '*.md'
git grep -l 'docs/refactoring/01_target_architecture.md' -- '*.md'
git grep -l 'docs/refactoring/02_migration_roadmap.md' -- '*.md'
git grep -l 'docs/refactoring/06_architecture_audit.md' -- '*.md'
```

### 12.3 Governance Frontmatter Template

```yaml
---
# Documentation Governance Frontmatter
# Required for all canonical documents

owner: Engineering  # Team/individual responsible
status: Canonical  # Canonical | Superseded | Deprecated | Archived | Generated
canonical: true  # true | false
superseded: false  # true | false
superseded_by: ""  # Path to superseding document (if superseded=true)
generated: false  # true | false
generated_by: ""  # Script/tool that generates (if generated=true)
last_verified_commit: ""  # Git commit hash when last verified
review_cadence: Quarterly  # Weekly | Monthly | Quarterly | Annually | Never
archive_after: Never  # YYYY-MM-DD or Never
deprecated: false  # true | false
deprecation_reason: ""  # Why deprecated (if deprecated=true)
replacement: ""  # Path to replacement document (if deprecated=true)
---
```

---

## 13. Final Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Principal Documentation Architect | | | |
| Tech Lead | | | |
| DevOps Lead | | | |
| AI/ML Lead (for RAG) | | | |

---

*End of Documentation Consolidation Implementation Plan*
