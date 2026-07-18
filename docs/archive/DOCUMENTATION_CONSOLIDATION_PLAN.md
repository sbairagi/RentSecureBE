# RentSecureBE Documentation Consolidation Plan

**Document:** Documentation Consolidation Plan — Phase 1 (Read Only + Safe Cleanup Plan)
**Version:** 1.0.0
**Date:** 2026-07-17
**Author:** Principal Software Architect (Kilo)
**Status:** DRAFT — READ-ONLY ANALYSIS
**Scope:** All documentation in `docs/`, `architecture/`, `.kilo/`, repository root, and module-level docs

---

## Executive Summary

The RentSecureBE repository contains **200+ documentation files** spread across multiple overlapping directories. There are three distinct generations of architecture documentation, duplicate ADR collections, multiple overlapping roadmaps, extensive generated reports at the repository root, and numerous outdated documents that contradict the current Year 1 architecture strategy.

**This plan proposes a single-source-of-truth documentation structure without modifying any files.**

---

## 1. Current Documentation Inventory

### 1.1 Top-Level Documentation (Repository Root)

| File | Size | Category | Status |
|------|------|----------|--------|
| `README.md` | ~5.0 KB | Canonical | Outdated (Cashfree refs, wrong feature flags) |
| `01_repository_inventory.md` | ~6.9 KB | Generated Report | Generated |
| `DOCUMENTATION_ANALYSIS_REPORT.md` | ~24.1 KB | Generated Report | Generated |
| `architecture-analysis-report.md` | ~36.7 KB | Generated Report | Generated |
| `architecture-compliance-report.md` | ~3.0 KB | Generated Report | Generated |
| `architecture-compliance-report.json` | ~5.8 KB | Generated Report | Generated |
| `architecture-dependency-graph.mmd` | ~1.6 KB | Generated Report | Generated |
| `architecture-dependency-graph.dot` | ~2.2 KB | Generated Report | Generated |
| `architecture-summary.txt` | ~108 B | Generated Report | Generated |
| `directory-structure-analysis.md` | ~40.1 KB | Generated Report | Generated |
| `coverage-report.txt` | 0 B | Generated Report | Empty placeholder |

### 1.2 `docs/` Directory

| Path | Files | Category |
|------|-------|----------|
| `docs/README.md` | 1 | Canonical |
| `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` | 1 | Canonical (partially outdated) |
| `docs/architecture-contract.md` | 1 | Canonical |
| `docs/ci-cd-pipeline.md` | 1 | Canonical (outdated) |
| `docs/ci-cd-upgrade-report.md` | 1 | Generated Report |
| `docs/governance.md` | 1 | Canonical |
| `docs/kilo-architecture-spec.md` | 1 | Canonical |
| `docs/adr/` | 18 | Duplicate ADR Collection |
| `docs/architecture/` | 14 | Active Planning / Generated |
| `docs/architecture/adr/` | 23 | Duplicate ADR Collection |
| `docs/architecture/future/` | 18 | Active Planning |
| `docs/architecture/reviews/` | 1 | Active Planning |
| `docs/ai-governance/` | 11 | Canonical |
| `docs/ai/` | 3 | Canonical |
| `docs/business-rules/` | 23 | Canonical (partially outdated) |
| `docs/diagrams/generated/` | 8 | Generated |
| `docs/history/` | 2 | Generated |
| `docs/rag/` | 23 | Obsolete (outdated Year 1 strategy) |
| `docs/refactoring/` | 13 | Active Planning / Duplicate |
| `docs/uml/generated/` | 11 | Generated |

### 1.3 `architecture/` Directory

| Path | Files | Category |
|------|-------|----------|
| `architecture/ARCHITECTURE_PRINCIPLES.md` | 1 | Canonical (duplicate of docs/refactoring) |
| `architecture/CODING_STANDARDS.md` | 1 | Canonical (duplicate) |
| `architecture/ROADMAP.md` | 1 | Canonical (duplicate of docs/refactoring) |
| `architecture/dependency-rules.md` | 1 | Canonical (duplicate) |
| `architecture/import-layers.md` | 1 | Canonical (duplicate) |
| `architecture/module-boundaries.md` | 1 | Canonical (duplicate) |
| `architecture/adr/` | 4 | Original ADR Collection |
| `architecture/baseline/` | 2 | Generated |
| `architecture/contracts/` | 0 | Empty (planned) |
| `architecture/diagrams/` | 2 | Generated |
| `architecture/generated/` | 1 | Generated |
| `architecture/reports/` | 1 | Generated |

### 1.4 `.kilo/instructions/` Directory

| File | Size | Category |
|------|------|----------|
| `README.md` | ~673 B | Canonical |
| `universal.md` | ~113 B | Canonical |
| `architecture.md` | ~124 B | Canonical |
| `backend.md` | ~1.3 KB | Canonical |
| `security.md` | ~234 B | Canonical |
| `testing.md` | ~86 B | Canonical |
| `frontend.md` | ~199 B | Canonical |
| `notifications.md` | ~2.3 KB | Canonical |
| `finance.md` | ~2.2 KB | Canonical |
| `smartbot.md` | ~93 B | Canonical |
| `onboarding.md` | ~103 B | Canonical |

### 1.5 Module-Level Documentation

| Path | Files | Category |
|------|-------|----------|
| `properties/TEST_DOCUMENTATION.md` | 1 | Canonical |
| `properties/business_rules.md` | 1 | Obsolete (legacy) |
| `properties/repositories/README.md` | 1 | Canonical |
| `properties/services/README.md` | 1 | Canonical |
| `core/services/README.md` | 1 | Canonical |
| `shared/README.md` | 1 | Canonical |

### 1.6 CI/CD Documentation (`.github/`)

| Path | Files | Category |
|------|-------|----------|
| `.github/SECURITY_AUDIT.md` | 1 | Generated Report |
| `.github/instructions/sonarqube_mcp.instructions.md` | 1 | Canonical |
| `.github/workflows/BRANCH_PROTECTION_VALIDATOR_README.md` | 1 | Canonical |
| `.github/workflows/*.yml` | 30 | CI/CD Configuration (not docs) |

---

## 2. Duplicate Documentation

### 2.1 Duplicate ADR Collections

| Collection | Location | Count | Description |
|------------|----------|-------|-------------|
| **Original ADRs** | `architecture/adr/` | 4 | Template + 3 initial ADRs (current/target/refactoring) |
| **Short ADRs** | `docs/adr/` | 18 | ADR-001 through ADR-012, ADR-031 through ADR-036 (short, templated) |
| **Detailed ADRs** | `docs/architecture/adr/` | 23 | ADR-001 through ADR-023 (detailed, well-structured) |

**Analysis:**
- All three collections contain different ADRs with different numbering schemes.
- `docs/architecture/adr/` contains the most detailed and comprehensive ADRs.
- `docs/adr/` ADRs are short stubs that reference non-existent files (ADR-013 through ADR-030 are listed in the index but do not exist).
- `architecture/adr/` contains the original 4 ADRs from Phase 0 baseline.

**Recommendation:**
- **KEEP** `docs/architecture/adr/` as the canonical ADR collection (most detailed, properly numbered).
- **ARCHIVE** `docs/adr/` (short stubs with missing files).
- **ARCHIVE** `architecture/adr/` (superseded by detailed collection).

### 2.2 Duplicate Architecture Principles

| Document | Location | Size | Description |
|----------|----------|------|-------------|
| `architecture/ARCHITECTURE_PRINCIPLES.md` | architecture/ | 2.6 KB | Concise principles (18 items) |
| `docs/refactoring/00_architecture_principles.md` | docs/refactoring/ | 51.7 KB | Detailed principles with full rationale |
| `docs/architecture/README.md` | docs/architecture/ | 8.0 KB | Architecture overview with embedded principles |

**Analysis:**
- `docs/refactoring/00_architecture_principles.md` is the most comprehensive (51.7 KB, ratified version).
- `architecture/ARCHITECTURE_PRINCIPLES.md` is a concise summary.
- `docs/architecture/README.md` embeds principles in an audit report.

**Recommendation:**
- **KEEP** `docs/refactoring/00_architecture_principles.md` as canonical.
- **ARCHIVE** `architecture/ARCHITECTURE_PRINCIPLES.md` (duplicate/summary).
- **ARCHIVE** principles section from `docs/architecture/README.md` or rewrite as pointer.

### 2.3 Duplicate Roadmaps

| Document | Location | Size | Description |
|----------|----------|------|-------------|
| `architecture/ROADMAP.md` | architecture/ | 8.8 KB | Concise roadmap (13 phases) |
| `docs/refactoring/02_migration_roadmap.md` | docs/refactoring/ | 84.5 KB | Detailed migration roadmap |
| `docs/refactoring/11_architecture_roadmap_review.md` | docs/refactoring/ | 63.2 KB | Roadmap review and assessment |
| `docs/refactoring/12_architecture_implementation_master_plan.md` | docs/refactoring/ | 92.4 KB | Master implementation plan |

**Analysis:**
- Four documents describe the architecture transformation roadmap with significant overlap.
- `docs/refactoring/12_architecture_implementation_master_plan.md` appears to be the most recent and comprehensive (92.4 KB, dated 2026-07-17).
- `architecture/ROADMAP.md` is referenced by `docs/architecture/README.md` but does not exist at the expected path.

**Recommendation:**
- **KEEP** `docs/refactoring/12_architecture_implementation_master_plan.md` as canonical (most recent, most comprehensive).
- **ARCHIVE** `architecture/ROADMAP.md` (superseded).
- **ARCHIVE** `docs/refactoring/02_migration_roadmap.md` (superseded).
- **ARCHIVE** `docs/refactoring/11_architecture_roadmap_review.md` (superseded).

### 2.4 Duplicate Dependency Rules

| Document | Location | Size | Description |
|----------|----------|------|-------------|
| `architecture/dependency-rules.md` | architecture/ | 5.5 KB | Concise dependency rules |
| `docs/refactoring/05_dependency_rules.md` | docs/refactoring/ | 7.9 KB | Detailed dependency rules |
| `docs/architecture/future/05_dependency_rules.md` | docs/architecture/future/ | 7.9 KB | **Exact duplicate** of above |

**Analysis:**
- `docs/architecture/future/05_dependency_rules.md` is an exact duplicate of `docs/refactoring/05_dependency_rules.md` (same size, same date).
- `architecture/dependency-rules.md` is a concise version.

**Recommendation:**
- **KEEP** `docs/refactoring/05_dependency_rules.md` as canonical.
- **DELETE** `docs/architecture/future/05_dependency_rules.md` (exact duplicate).
- **ARCHIVE** `architecture/dependency-rules.md` (superseded).

### 2.5 Duplicate Module Boundaries

| Document | Location | Size | Description |
|----------|----------|------|-------------|
| `architecture/module-boundaries.md` | architecture/ | 4.6 KB | Concise module boundaries |
| `docs/refactoring/06_module_responsibilities.md` | docs/refactoring/ | 12.7 KB | Detailed module responsibilities |
| `docs/architecture/future/02_bounded_contexts.md` | docs/architecture/future/ | 16.6 KB | Detailed bounded contexts |

**Recommendation:**
- **KEEP** `docs/refactoring/06_module_responsibilities.md` as canonical.
- **ARCHIVE** `architecture/module-boundaries.md` (superseded).
- **ARCHIVE** `docs/architecture/future/02_bounded_contexts.md` (superseded).

### 2.6 Duplicate Layer Rules

| Document | Location | Size | Description |
|----------|----------|------|-------------|
| `architecture/import-layers.md` | architecture/ | 2.6 KB | Concise import layers |
| `docs/refactoring/04_layer_rules.md` | docs/refactoring/ | 10.0 KB | Detailed layer rules |

**Recommendation:**
- **KEEP** `docs/refactoring/04_layer_rules.md` as canonical.
- **ARCHIVE** `architecture/import-layers.md` (superseded).

### 2.7 Duplicate Coding Standards

| Document | Location | Size | Description |
|----------|----------|------|-------------|
| `architecture/CODING_STANDARDS.md` | architecture/ | 4.9 KB | Concise coding standards |
| `docs/refactoring/10_naming_conventions.md` | docs/refactoring/ | 8.1 KB | Naming conventions |

**Recommendation:**
- **KEEP** `docs/refactoring/10_naming_conventions.md` as canonical (more detailed).
- **ARCHIVE** `architecture/CODING_STANDARDS.md` (superseded).

### 2.8 Duplicate Architecture Audit Reports

| Document | Location | Size | Description |
|----------|----------|------|-------------|
| `docs/architecture/README.md` | docs/architecture/ | 8.0 KB | Architecture audit overview |
| `docs/architecture/architecture-audit-report.md` | docs/architecture/ | 40.1 KB | Full architecture audit report |
| `docs/architecture/production-architecture.md` | docs/architecture/ | 39.3 KB | Production architecture documentation |
| `docs/refactoring/06_architecture_audit.md` | docs/refactoring/ | 41.9 KB | Architecture audit findings |

**Recommendation:**
- **KEEP** `docs/architecture/production-architecture.md` as canonical (Year 1 strategy).
- **ARCHIVE** `docs/architecture/README.md` (audit overview, superseded).
- **ARCHIVE** `docs/architecture/architecture-audit-report.md` (superseded by production-architecture.md).
- **ARCHIVE** `docs/refactoring/06_architecture_audit.md` (superseded).

### 2.9 Duplicate Target Architecture

| Document | Location | Size | Description |
|----------|----------|------|-------------|
| `docs/refactoring/01_target_architecture.md` | docs/refactoring/ | 131.7 KB | Target architecture specification |
| `docs/refactoring/09_target_architecture.md` | docs/refactoring/ | 70.0 KB | Updated target architecture |

**Analysis:**
- Both files describe target architecture with significant overlap.
- `09_target_architecture.md` is more recent (2026-07-17) and likely supersedes `01_target_architecture.md`.

**Recommendation:**
- **KEEP** `docs/refactoring/09_target_architecture.md` as canonical (more recent).
- **ARCHIVE** `docs/refactoring/01_target_architecture.md` (superseded).

### 2.10 Duplicate Architecture Gap Analysis

| Document | Location | Size | Description |
|----------|----------|------|-------------|
| `docs/refactoring/10_architecture_gap_analysis.md` | docs/refactoring/ | 77.4 KB | Architecture gap analysis |
| `docs/architecture/audit_data.json` | docs/architecture/ | 198 KB | Raw audit data |

**Analysis:**
- `audit_data.json` is the raw data backing the gap analysis.
- The gap analysis document is the processed interpretation.

**Recommendation:**
- **KEEP** both (different purposes: raw data vs. analysis).

### 2.11 Duplicate Architecture JSON Data

| Document | Location | Size | Description |
|----------|----------|------|-------------|
| `architecture/generated/architecture.json` | architecture/ | 127.7 KB | Generated architecture data |
| `docs/architecture/audit_data.json` | docs/architecture/ | 198 KB | Audit raw data |
| `docs/history/generated/architecture.json` | docs/history/ | 122 KB | Historical architecture data |

**Recommendation:**
- **KEEP** `docs/architecture/audit_data.json` as canonical raw data.
- **ARCHIVE** `architecture/generated/architecture.json` (superseded).
- **ARCHIVE** `docs/history/generated/architecture.json` (historical, archived in wrong location).

---

## 3. Canonical Documents (Must Remain)

These documents form the single source of truth and must be preserved in place or carefully moved:

### 3.1 Project-Level Canonical

| Document | Reason |
|----------|--------|
| `README.md` | Main project README — needs content updates but must remain |
| `docs/README.md` | Documentation index |
| `docs/architecture-contract.md` | Architecture governance contract |
| `docs/ci-cd-pipeline.md` | CI/CD pipeline documentation (needs update) |
| `docs/governance.md` | CI/CD governance policies |
| `docs/kilo-architecture-spec.md` | Kilo architecture specification |

### 3.2 Domain Canonical

| Document | Reason |
|----------|--------|
| `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` | Core business logic (needs accuracy updates) |
| `docs/business-rules/` (23 files) | Comprehensive business rules (needs strategy updates) |
| `docs/ai-governance/` (11 files) | AI governance standards |
| `docs/ai/` (3 files) | AI prompts and documentation |

### 3.3 Architecture Canonical

| Document | Reason |
|----------|--------|
| `docs/architecture/production-architecture.md` | Year 1 through Stage 4 infrastructure strategy |
| `docs/architecture/future/` (18 files) | Future architecture vision |
| `docs/architecture/adr/` (23 files) | Detailed ADR collection |
| `docs/refactoring/00_architecture_principles.md` | Ratified architecture principles |
| `docs/refactoring/09_target_architecture.md` | Updated target architecture |
| `docs/refactoring/12_architecture_implementation_master_plan.md` | Master implementation plan |

### 3.4 Instruction Canonical

| Document | Reason |
|----------|--------|
| `.kilo/instructions/*` (11 files) | Kilo AI session instructions — most accurate Year 1 strategy source |

### 3.5 Module-Level Canonical

| Document | Reason |
|----------|--------|
| `properties/TEST_DOCUMENTATION.md` | Properties module test documentation |
| `properties/repositories/README.md` | Properties repositories index |
| `properties/services/README.md` | Properties services index |
| `core/services/README.md` | Core services index |
| `shared/README.md` | Shared module documentation |

---

## 4. Archive Candidates

These documents should be moved to `docs/archive/` rather than deleted:

### 4.1 Generated Reports (Top-Level)

| File | Action |
|------|--------|
| `01_repository_inventory.md` | ARCHIVE |
| `DOCUMENTATION_ANALYSIS_REPORT.md` | ARCHIVE |
| `architecture-analysis-report.md` | ARCHIVE |
| `architecture-compliance-report.md` | ARCHIVE |
| `architecture-compliance-report.json` | ARCHIVE |
| `architecture-dependency-graph.mmd` | ARCHIVE |
| `architecture-dependency-graph.dot` | ARCHIVE |
| `architecture-summary.txt` | ARCHIVE |
| `directory-structure-analysis.md` | ARCHIVE |

### 4.2 Generated Architecture Data

| File | Action |
|------|--------|
| `architecture/generated/architecture.json` | ARCHIVE |
| `docs/history/generated/architecture.json` | ARCHIVE |

### 4.3 Generated Diagrams

| Files | Action |
|-------|--------|
| `docs/diagrams/generated/` (8 files) | ARCHIVE |
| `docs/uml/generated/` (11 files) | ARCHIVE |
| `architecture/diagrams/` (2 files) | ARCHIVE |

### 4.4 Superseded ADR Collections

| Files | Action |
|-------|--------|
| `docs/adr/` (18 files) | ARCHIVE |
| `architecture/adr/` (4 files) | ARCHIVE |

### 4.5 Superseded Architecture Documents

| File | Action |
|------|--------|
| `architecture/ARCHITECTURE_PRINCIPLES.md` | ARCHIVE |
| `architecture/CODING_STANDARDS.md` | ARCHIVE |
| `architecture/ROADMAP.md` | ARCHIVE |
| `architecture/dependency-rules.md` | ARCHIVE |
| `architecture/import-layers.md` | ARCHIVE |
| `architecture/module-boundaries.md` | ARCHIVE |
| `docs/architecture/README.md` | ARCHIVE |
| `docs/architecture/architecture-audit-report.md` | ARCHIVE |
| `docs/architecture/future/05_dependency_rules.md` | ARCHIVE (exact duplicate) |
| `docs/architecture/future/02_bounded_contexts.md` | ARCHIVE |
| `docs/refactoring/02_migration_roadmap.md` | ARCHIVE |
| `docs/refactoring/11_architecture_roadmap_review.md` | ARCHIVE |
| `docs/refactoring/06_architecture_audit.md` | ARCHIVE |
| `docs/refactoring/01_target_architecture.md` | ARCHIVE |

### 4.6 Obsolete Documentation

| File | Action |
|------|--------|
| `docs/ci-cd-upgrade-report.md` | ARCHIVE (generated/one-time report) |
| `docs/rag/` (23 files) | ARCHIVE (outdated Year 1 strategy) |
| `properties/business_rules.md` | ARCHIVE (legacy single-file, 311 bytes) |

### 4.7 Outdated Documentation (Pending Update)

| File | Action |
|------|--------|
| `README.md` | KEEP but update content |
| `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` | KEEP but update content |
| `docs/business-rules/*` (23 files) | KEEP but update content |
| `docs/ci-cd-pipeline.md` | KEEP but update content |

---

## 5. Delete Candidates

### 5.1 Exact Duplicates

| File | Reason |
|------|--------|
| `docs/architecture/future/05_dependency_rules.md` | Exact duplicate of `docs/refactoring/05_dependency_rules.md` (same size, same date) |

### 5.2 Empty/Degenerate Files

| File | Reason |
|------|--------|
| `coverage-report.txt` | Empty file (0 bytes), placeholder |

### 5.3 Missing Referenced Files

These files are referenced in documentation but do not exist. They are not files to delete, but the references to them must be fixed:

| Referenced Path | Document | Action |
|-----------------|----------|--------|
| `docs/adr/ADR-013.md` through `ADR-030.md` | `docs/adr/README.md` | Remove from index or create files |
| `docs/bugs/` | Multiple | Create directory or remove references |
| `docs/business-gaps/` | Multiple | Create directory or remove references |
| `../ARCHITECTURE_PRINCIPLES.md` | `docs/architecture/README.md` | Fix path to `docs/refactoring/00_architecture_principles.md` |
| `../CODING_STANDARDS.md` | `docs/architecture/README.md` | Fix path to `docs/refactoring/10_naming_conventions.md` |
| `../ROADMAP.md` | `docs/architecture/README.md` | Fix path to `docs/refactoring/12_architecture_implementation_master_plan.md` |
| `../adr/ADR-template.md` | `docs/architecture/README.md` | Fix path to `architecture/adr/000-template.md` |

---

## 6. Human Decision Items

These items require human review before any action is taken:

### 6.1 ADR Collection Consolidation

**Decision Required:** Which ADR collection should be the canonical source?

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A | `docs/architecture/adr/` (23 detailed ADRs) | Most comprehensive, well-structured | Different numbering from original |
| B | `docs/adr/` (18 short ADRs) | Matches original ADR-001-036 numbering | Missing ADR-013 through ADR-030 |
| C | `architecture/adr/` (4 original ADRs) | Original Phase 0 ADRs | Too few, too brief |

**Recommendation:** Option A (`docs/architecture/adr/`) with renumbering to match ADR-001-036 scheme.

### 6.2 Architecture Principles Document

**Decision Required:** Should there be two versions (concise + detailed) or one canonical version?

| Option | Description |
|--------|-------------|
| A | Single canonical: `docs/refactoring/00_architecture_principles.md` (51.7 KB) |
| B | Two versions: concise (`architecture/ARCHITECTURE_PRINCIPLES.md`) + detailed (`docs/refactoring/...`) |

**Recommendation:** Option A (single source of truth). Move concise version to archive.

### 6.3 RAG Knowledge Base

**Decision Required:** The `docs/rag/` documents are outdated (reference old payment/notification flows). Should they be:
- Updated to reflect current Year 1 architecture?
- Archived as historical reference?
- Deleted?

**Recommendation:** Archive as historical reference (docs/archive/rag/).

### 6.4 Business Rules Documentation

**Decision Required:** `docs/business-rules/` contains outdated payment/notification references. Should they be:
- Updated in place?
- Archived and replaced with updated versions?

**Recommendation:** Update in place with correct Year 1 strategy references.

### 6.5 Top-Level Generated Reports

**Decision Required:** Should generated reports at the repository root be:
- Archived to `docs/archive/generated/`?
- Deleted (they can be regenerated)?
- Kept at root for easy access?

**Recommendation:** Archive to `docs/archive/generated/` for historical reference.

### 6.6 `properties/business_rules.md`

**Decision Required:** This 311-byte legacy file is referenced in `docs/business-rules/00-overview.md`. Should it be:
- Updated to point to the new `docs/business-rules/` collection?
- Deleted?
- Kept as-is?

**Recommendation:** Update reference in `docs/business-rules/00-overview.md` and delete the legacy file.

---

## 7. Broken References

### 7.1 Broken Internal Links

| Source Document | Broken Reference | Issue | Fix Required |
|-----------------|------------------|-------|--------------|
| `README.md` | `docs/diagrams/generated/c4/c4-context.puml` | Diagram may not exist at path | Verify or update path |
| `README.md` | `architecture/architecture-dependency-graph.dot` | File may not exist | Verify or update path |
| `docs/architecture/README.md` | `../ARCHITECTURE_PRINCIPLES.md` | File does not exist at root | Update to `docs/refactoring/00_architecture_principles.md` |
| `docs/architecture/README.md` | `../CODING_STANDARDS.md` | File does not exist at root | Update to `docs/refactoring/10_naming_conventions.md` |
| `docs/architecture/README.md` | `../ROADMAP.md` | File does not exist at root | Update to `docs/refactoring/12_architecture_implementation_master_plan.md` |
| `docs/architecture/README.md` | `../adr/ADR-template.md` | File does not exist | Update to `architecture/adr/000-template.md` |
| `docs/business-rules/README.md` | `../business-gaps/BUSINESS_GAPS_AUDIT.md` | Directory does not exist | Create directory or remove reference |
| `docs/rag/README.md` | `../business-gaps/BUSINESS_GAPS_AUDIT.md` | Directory does not exist | Create directory or remove reference |
| `docs/rag/project-summary.md` | `docs/bugs/` | Directory does not exist | Create directory or remove reference |
| `docs/rag/payments-razorpay-cashfree.md` | `docs/bugs/rentsecure_be.md`, `docs/bugs/core.md` | Files do not exist | Create files or remove references |
| `docs/business-rules/00-overview.md` | `properties/business_rules.md` | Legacy file, 311 bytes | Update or remove reference |

### 7.2 Broken Code References

| Source Document | Broken Reference | Issue | Fix Required |
|-----------------|------------------|-------|--------------|
| `docs/business-rules/16-payments-and-webhooks.md` | `rentsecure_be/services/razorpay_service.py` | Path may be incorrect | Verify path |
| `docs/business-rules/08-rent-records.md` | `apply_late_fee_if_needed()` in utils | Function may not exist | Verify function location |
| `docs/rag/payments-razorpay-cashfree.md` | `rent.renter.property.owner` | Uses `property` instead of `unit` | Fix to `rent.renter.unit.owner` |

---

## 8. Proposed Folder Hierarchy

```
docs/
├── README.md                          # Documentation index
├── architecture-contract.md           # Architecture governance contract
├── BUSINESS_LOGIC_AND_SUBSCRIPTION.md # Business logic rules
├── ci-cd-pipeline.md                  # CI/CD pipeline documentation
├── governance.md                      # CI/CD governance policies
├── kilo-architecture-spec.md          # Kilo architecture specification
│
├── architecture/
│   ├── README.md                      # Architecture documentation index
│   ├── production-architecture.md     # Year 1 through Stage 4 infrastructure strategy
│   ├── adr/                           # Detailed ADR collection (23 files)
│   │   ├── ADR-001_modular_monolith.md
│   │   ├── ADR-002_repository_pattern.md
│   │   └── ...
│   ├── future/                        # Future architecture vision
│   │   ├── 01_architecture_vision.md
│   │   ├── 02_bounded_contexts.md
│   │   ├── 03_target_folder_structure.md
│   │   ├── 04_layer_rules.md
│   │   ├── 05_dependency_rules.md
│   │   ├── 06_module_responsibilities.md
│   │   ├── 07_domain_events.md
│   │   ├── 08_repository_pattern.md
│   │   ├── 09_service_layer.md
│   │   ├── 10_naming_conventions.md
│   │   ├── 11_migration_strategy.md
│   │   └── diagrams/
│   ├── reviews/
│   │   └── 01_future_architecture_review.md
│   ├── generated/                     # Generated architecture data
│   │   └── audit_data.json
│   └── diagrams/
│       └── generated/
│           ├── c4/
│           ├── flows/
│           └── infrastructure/
│
├── refactoring/
│   ├── 00_architecture_principles.md   # Ratified architecture principles
│   ├── 09_target_architecture.md       # Updated target architecture
│   ├── 12_architecture_implementation_master_plan.md  # Master implementation plan
│   └── [other refactoring docs]
│
├── adr/                               # ARCHIVED — short ADR stubs
│   └── [18 files moved here]
│
├── business-rules/
│   ├── README.md
│   ├── 00-overview.md
│   ├── 01-ownership-and-access.md
│   └── ... (23 files)
│
├── ai-governance/
│   ├── AI-Architecture-Review.md
│   ├── AI-Code-Review.md
│   └── ... (11 files)
│
├── ai/
│   ├── README.md
│   └── prompts/
│
├── uml/
│   └── generated/
│       ├── ddd/
│       ├── domain/
│       ├── mermaid/
│       └── plantuml/
│
├── history/
│   └── README.md
│
├── archive/
│   ├── old-adr/
│   │   ├── docs-adr/                   # From docs/adr/
│   │   └── architecture-adr/           # From architecture/adr/
│   ├── planning/
│   │   ├── migration-roadmap.md        # From docs/refactoring/02_migration_roadmap.md
│   │   ├── roadmap-review.md           # From docs/refactoring/11_architecture_roadmap_review.md
│   │   ├── target-architecture-v1.md   # From docs/refactoring/01_target_architecture.md
│   │   ├── architecture-principles-concise.md  # From architecture/ARCHITECTURE_PRINCIPLES.md
│   │   ├── coding-standards.md         # From architecture/CODING_STANDARDS.md
│   │   ├── dependency-rules.md         # From architecture/dependency-rules.md
│   │   ├── import-layers.md            # From architecture/import-layers.md
│   │   ├── module-boundaries.md        # From architecture/module-boundaries.md
│   │   └── [other superseded docs]
│   ├── audits/
│   │   ├── architecture-audit-report.md
│   │   ├── architecture-audit-findings.md
│   │   ├── architecture-compliance-report.md
│   │   ├── architecture-compliance-report.json
│   │   └── architecture-readme.md
│   ├── generated/
│   │   ├── architecture-analysis-report.md
│   │   ├── architecture-dependency-graph.mmd
│   │   ├── architecture-dependency-graph.dot
│   │   ├── architecture-summary.txt
│   │   ├── architecture.json           # From architecture/generated/
│   │   ├── architecture-history.json   # From docs/history/generated/
│   │   ├── directory-structure-analysis.md
│   │   ├── documentation-analysis-report.md
│   │   ├── repository-inventory.md
│   │   └── ci-cd-upgrade-report.md
│   ├── deprecated/
│   │   ├── rag-knowledge-base/         # From docs/rag/ (23 files)
│   │   └── legacy-business-rules.md    # From properties/business_rules.md
│   └── diagrams/
│       ├── generated-c4/               # From docs/diagrams/generated/c4/
│       ├── generated-flows/            # From docs/diagrams/generated/flows/
│       ├── generated-infrastructure/   # From docs/diagrams/generated/infrastructure/
│       ├── generated-uml-ddd/          # From docs/uml/generated/ddd/
│       ├── generated-uml-domain/       # From docs/uml/generated/domain/
│       ├── generated-uml-mermaid/      # From docs/uml/generated/mermaid/
│       └── generated-uml-plantuml/     # From docs/uml/generated/plantuml/
│
├── development/
│   └── [future: development guides]
│
├── deployment/
│   └── [future: deployment guides]
│
├── operations/
│   └── [future: operations guides]
│
├── testing/
│   └── [future: testing guides]
│
├── security/
│   └── [future: security guides]
│
└── guides/
    └── [future: user guides]

architecture/
├── ARCHITECTURE_PRINCIPLES.md          # ARCHIVED — superseded by docs/refactoring/00_architecture_principles.md
├── CODING_STANDARDS.md                 # ARCHIVED — superseded by docs/refactoring/10_naming_conventions.md
├── ROADMAP.md                          # ARCHIVED — superseded by docs/refactoring/12_architecture_implementation_master_plan.md
├── dependency-rules.md                 # ARCHIVED — superseded by docs/refactoring/05_dependency_rules.md
├── import-layers.md                    # ARCHIVED — superseded by docs/refactoring/04_layer_rules.md
├── module-boundaries.md                # ARCHIVED — superseded by docs/refactoring/06_module_responsibilities.md
├── adr/
│   └── [4 files — ARCHIVED]
├── baseline/
│   └── [2 files — ARCHIVED]
├── diagrams/
│   └── [2 files — ARCHIVED]
├── generated/
│   └── architecture.json               # ARCHIVED
└── reports/
    └── README.md                       # ARCHIVED

.kilo/
├── instructions/
│   ├── README.md
│   ├── universal.md
│   ├── architecture.md
│   ├── backend.md
│   ├── security.md
│   ├── testing.md
│   ├── frontend.md
│   ├── notifications.md
│   ├── finance.md
│   ├── smartbot.md
│   └── onboarding.md
├── command/
│   ├── review-sec.md
│   └── test-shard.md
├── agent/
│   ├── README.md
│   └── backend-architect.md
└── prompts/
    └── backend-architecture.md
```

---

## 9. Migration Order

### Phase 1: Archive Generated Reports (No Risk)

1. Move top-level generated reports to `docs/archive/generated/`
2. Move `architecture/generated/` to `docs/archive/generated/architecture-generated/`
3. Move `docs/history/generated/` to `docs/archive/generated/history-generated/`
4. Move `docs/diagrams/generated/` to `docs/archive/diagrams/generated/`
5. Move `docs/uml/generated/` to `docs/archive/diagrams/generated-uml/`
6. Move `architecture/diagrams/` to `docs/archive/diagrams/architecture/`

**Risk:** None. Generated reports can be regenerated.

### Phase 2: Archive Duplicate ADR Collections (Low Risk)

7. Move `docs/adr/` to `docs/archive/old-adr/docs-adr/`
8. Move `architecture/adr/` to `docs/archive/old-adr/architecture-adr/`

**Risk:** Low. ADR index in `docs/architecture/adr/` must be updated to not reference these.

### Phase 3: Archive Superseded Architecture Documents (Medium Risk)

9. Move `architecture/ARCHITECTURE_PRINCIPLES.md` to `docs/archive/planning/architecture-principles-concise.md`
10. Move `architecture/CODING_STANDARDS.md` to `docs/archive/planning/coding-standards.md`
11. Move `architecture/ROADMAP.md` to `docs/archive/planning/roadmap.md`
12. Move `architecture/dependency-rules.md` to `docs/archive/planning/dependency-rules.md`
13. Move `architecture/import-layers.md` to `docs/archive/planning/import-layers.md`
14. Move `architecture/module-boundaries.md` to `docs/archive/planning/module-boundaries.md`
15. Move `docs/architecture/README.md` to `docs/archive/audits/architecture-readme.md`
16. Move `docs/architecture/architecture-audit-report.md` to `docs/archive/audits/architecture-audit-report.md`
17. Move `docs/refactoring/02_migration_roadmap.md` to `docs/archive/planning/migration-roadmap.md`
18. Move `docs/refactoring/11_architecture_roadmap_review.md` to `docs/archive/planning/roadmap-review.md`
19. Move `docs/refactoring/06_architecture_audit.md` to `docs/archive/audits/architecture-audit-findings.md`
20. Move `docs/refactoring/01_target_architecture.md` to `docs/archive/planning/target-architecture-v1.md`
21. Delete exact duplicate: `docs/architecture/future/05_dependency_rules.md`
22. Move `docs/architecture/future/02_bounded_contexts.md` to `docs/archive/planning/bounded-contexts.md`

**Risk:** Medium. Many documents reference these files. All references must be updated.

### Phase 4: Archive Obsolete Documentation (Medium Risk)

23. Move `docs/rag/` to `docs/archive/deprecated/rag-knowledge-base/`
24. Move `properties/business_rules.md` to `docs/archive/deprecated/legacy-business-rules.md`
25. Move `docs/ci-cd-upgrade-report.md` to `docs/archive/generated/ci-cd-upgrade-report.md`

**Risk:** Medium. RAG documents may be used by AI systems. Must verify no active dependencies.

### Phase 5: Update Broken References (High Risk)

26. Update `README.md` diagram references
27. Update `docs/architecture/README.md` references (if kept)
28. Update `docs/business-rules/README.md` references
29. Update `docs/rag/` references (if any remain)
30. Update `docs/business-rules/00-overview.md` reference to `properties/business_rules.md`
31. Fix code references in business-rules documents

**Risk:** High. Many cross-references exist. Must be done carefully.

### Phase 6: Update Outdated Content (High Risk)

32. Update `README.md` to remove Cashfree references and fix feature flags
33. Update `docs/ci-cd-pipeline.md` to remove Cashfree references
34. Update `docs/business-rules/*` to reflect current Year 1 strategy
35. Update `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` to fix signal/webhook/command documentation

**Risk:** High. Content updates require domain knowledge.

---

## 10. Risk Assessment

### 10.1 High-Risk Items

| Risk | Description | Mitigation |
|------|-------------|------------|
| Broken references after archiving | Many documents reference files that would be archived | Update all references before moving files |
| Outdated content in canonical docs | README, business-rules, CI/CD docs contain outdated info | Update content after archiving duplicates |
| RAG dependency | `docs/rag/` may be used by AI indexing systems | Verify AI system dependencies before archiving |
| ADR numbering confusion | Two ADR collections use different numbering | Choose canonical collection, update all references |

### 10.2 Medium-Risk Items

| Risk | Description | Mitigation |
|------|-------------|------------|
| Empty directory `architecture/contracts/` | Referenced in roadmap but empty | Document as "planned for Phase 1" or populate |
| Missing ADR files (013-030) | Listed in index but don't exist | Either create or remove from index |
| Broken diagram references | README references diagrams that may not exist | Verify all diagram paths before finalizing |

### 10.3 Low-Risk Items

| Risk | Description | Mitigation |
|------|-------------|------------|
| Generated reports at root | Easy to regenerate if needed | Archive rather than delete |
| Exact duplicate `dependency_rules.md` | Can be safely deleted | Delete after confirming exact match |

---

## 11. Files That Must Never Be Deleted

These files must always be preserved (archive if obsolete, but never delete):

| File | Reason |
|------|--------|
| `README.md` | Main project README |
| `docs/README.md` | Documentation index |
| `docs/architecture-contract.md` | Architecture governance contract |
| `docs/architecture/production-architecture.md` | Year 1 infrastructure strategy |
| `docs/architecture/adr/` (23 files) | Detailed ADR collection |
| `docs/refactoring/00_architecture_principles.md` | Ratified architecture principles |
| `docs/refactoring/09_target_architecture.md` | Target architecture |
| `docs/refactoring/12_architecture_implementation_master_plan.md` | Master implementation plan |
| `.kilo/instructions/*` (11 files) | Kilo AI session instructions |
| `docs/business-rules/` (23 files) | Business rules (needs updates but must remain) |
| `docs/ai-governance/` (11 files) | AI governance standards |
| `import-linter.ini` | Architecture enforcement configuration |
| `.github/workflows/*.yml` | CI/CD pipeline definitions |

---

## 12. Summary Statistics

| Category | Count | Action |
|----------|-------|--------|
| Total documentation files | ~200 | — |
| Canonical (keep in place) | ~80 | KEEP |
| Archive candidates | ~100 | ARCHIVE |
| Delete candidates | 2 | DELETE |
| Human decision items | 6 | HUMAN DECISION |
| Broken references | 15+ | FIX |
| Missing files | 8+ | CREATE or REMOVE REFERENCE |

---

## 13. Next Steps

1. **Obtain human decisions** on the 6 decision items in Section 6.
2. **Verify RAG dependencies** — confirm no active AI systems depend on `docs/rag/`.
3. **Create missing directories** (`docs/bugs/`, `docs/business-gaps/`) or remove all references to them.
4. **Update canonical documents** (README, CI/CD pipeline, business-rules) to reflect current Year 1 strategy.
5. **Execute Phase 1 migration** (archive generated reports) — lowest risk.
6. **Execute Phase 2-6 migrations** sequentially, verifying references at each step.
7. **Update documentation linting** in CI to prevent future broken references.

---

*End of Report*
