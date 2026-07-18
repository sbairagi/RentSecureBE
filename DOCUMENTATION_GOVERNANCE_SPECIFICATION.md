# RentSecureBE Documentation Governance Specification

**Document:** Documentation Governance Specification — Final
**Version:** 1.0.0
**Date:** 2026-07-18
**Status:** FINAL — PERMANENT GOVERNANCE STANDARD
**Authority:** RentSecure Engineering
**Applies To:** RentSecureBE repository and all future forks

---

## Table of Contents

1. [Documentation Governance Model (Tiers)](#1-documentation-governance-model-tiers)
2. [Ownership Matrix](#2-ownership-matrix)
3. [Documentation Lifecycle Rules](#3-documentation-lifecycle-rules)
4. [Documentation Dependency Rules](#4-documentation-dependency-rules)
5. [Archive Rules](#5-archive-rules)
6. [Delete Rules](#6-delete-rules)
7. [Documentation Validation Pipeline](#7-documentation-validation-pipeline)
8. [Final Directory Classification](#8-final-directory-classification)
9. [Archive Candidate Review](#9-archive-candidate-review)
10. [Safe Migration Strategy](#10-safe-migration-strategy)
11. [Documentation Constitution](#11-documentation-constitution)

---

## 1. Documentation Governance Model (Tiers)

Documentation is a dependency graph, not a collection of files. Classification is based on dependency graph analysis, not age or file count.

### Tier 1 — Canonical Documentation

**Definition:** Never archived. These documents constitute the single source of truth for the project. Any change to the codebase, architecture, or business rules MUST be reflected here.

**Classification Criteria:**
- Referenced by CI/CD pipelines, scripts, or governance workflows
- Referenced by ADRs as source of truth
- Referenced by AI instruction files (`.kilo/instructions/`)
- Contains business rules that drive implementation
- Contains architecture contracts enforced in CI
- Contains governance policies with legal/compliance implications

**Examples:**
- `README.md`
- `docs/README.md`
- `docs/architecture-contract.md`
- `docs/ci-cd-pipeline.md`
- `docs/governance.md`
- `docs/kilo-architecture-spec.md`
- `docs/architecture/production-architecture.md`
- `docs/architecture/adr/` (23 files) — canonical ADR collection
- `docs/architecture/future/` (17 files) — referenced by canonical ADRs
- `docs/business-rules/` (23 files)
- `docs/ai-governance/` (11 files)
- `docs/ai/` (3 files)
- `.kilo/instructions/*` (11 files)
- Module-level READMEs (`core/services/README.md`, `properties/repositories/README.md`, etc.)
- `architecture/ARCHITECTURE_PRINCIPLES.md`
- `architecture/ROADMAP.md`
- `architecture/dependency-rules.md`
- `architecture/module-boundaries.md`
- `architecture/import-layers.md`
- `architecture/CODING_STANDARDS.md`
- `architecture/adr/` (4 files)
- `docs/refactoring/` (13 files) — tightly-coupled planning collection
- `import-linter.ini`
- `.clinerules`

**Rules:**
- NEVER archive without explicit Architecture Review Board approval
- NEVER delete
- All changes must go through PR review with architecture owner approval
- Version bumps must be recorded in `docs/architecture-contract.md`

### Tier 2 — Reference Documentation

**Definition:** Stable references that inform canonical documents. Can move only after all dependent canonical documents have been updated.

**Classification Criteria:**
- Referenced by canonical documents but not by CI/CD directly
- Provides background, context, or supporting evidence for canonical docs
- May be superseded by canonical docs but retained for historical traceability
- Contains detailed analysis that backs canonical decisions

**Examples:**
- `docs/architecture/reviews/01_future_architecture_review.md`
- `docs/architecture/audit_data.json` — raw audit data used by scripts
- `docs/adr/` (18 files) — historical ADR collection with references
- `architecture/baseline/` (2 files)
- `properties/TEST_DOCUMENTATION.md`

**Rules:**
- Can archive after all references are updated to canonical locations
- Must preserve git history via `git mv`
- Cannot delete if any canonical document still references it
- Archive location must include redirect notice in README

### Tier 3 — Planning Documentation

**Definition:** Active planning artifacts that inform current or future work. These are NOT obsolete — they are design proposals that drive implementation.

**Classification Criteria:**
- Documents that describe planned architecture changes
- Documents that contain "target" or "future" architecture designs
- Documents that are referenced by canonical ADRs or planning documents
- Documents that are part of an active, coupled planning collection

**Examples:**
- `docs/refactoring/00_architecture_principles.md`
- `docs/refactoring/09_target_architecture.md`
- `docs/refactoring/12_architecture_implementation_master_plan.md`
- `docs/refactoring/` (all 13 files as a complete collection)
- `docs/architecture/future/` (all 17 files as a complete collection)

**Rules:**
- Must remain accessible to teams implementing architecture changes
- Can archive only when the planned work is complete AND all references are updated
- Must be treated as a unit — partial archival breaks the documentation chain
- Cannot delete without Architecture Review Board approval

### Tier 4 — Historical / Generated Documentation

**Definition:** Generated reports, audit outputs, historical snapshots. Safe to archive but not delete until proven orphaned.

**Classification Criteria:**
- Generated by CI/CD scripts (reports, diagrams, metrics)
- One-time analysis outputs that are no longer actively maintained
- Historical snapshots preserved for audit trails
- Empty placeholder files

**Examples:**
- `01_repository_inventory.md`
- `DOCUMENTATION_ANALYSIS_REPORT.md`
- `architecture-analysis-report.md`
- `architecture-compliance-report.md`
- `architecture-compliance-report.json`
- `architecture-dependency-graph.mmd`
- `architecture-dependency-graph.dot`
- `architecture-summary.txt`
- `directory-structure-analysis.md`
- `coverage-report.txt`
- `docs/diagrams/generated/` (8 files)
- `docs/uml/generated/` (11 files)
- `architecture/diagrams/` (2 files)
- `architecture/generated/architecture.json`
- `docs/history/generated/architecture.json`
- `docs/architecture/architecture-audit-report.md`
- `docs/ci-cd-upgrade-report.md`

**Rules:**
- Can archive after verifying zero references in canonical documents
- Can delete after passing full dependency graph analysis (see Delete Rules)
- Generated files should be regenerated from source if needed
- Git history must be preserved before deletion

---

## 2. Ownership Matrix

| Directory / File | Purpose | Owner | Audience | Lifetime | Can Archive? | Can Delete? | Reference Stability | CI Dependency | AI Dependency |
|------------------|---------|-------|----------|----------|--------------|-------------|---------------------|---------------|---------------|
| `README.md` | Project overview, quick start, tech stack | Tech Lead | All contributors | Permanent | NO | NO | CRITICAL | YES | YES |
| `docs/README.md` | Documentation index | Tech Lead | All contributors | Permanent | NO | NO | CRITICAL | NO | YES |
| `docs/architecture-contract.md` | CI/CD architecture governance contract | Senior DevOps | DevOps, Tech Lead | Permanent | NO | NO | CRITICAL | YES | YES |
| `docs/ci-cd-pipeline.md` | CI/CD pipeline overview and diagrams | Senior DevOps | DevOps | Permanent | NO | NO | CRITICAL | YES | YES |
| `docs/governance.md` | CI/CD governance policies | Senior DevOps | DevOps, Tech Lead | Permanent | NO | NO | CRITICAL | YES | YES |
| `docs/kilo-architecture-spec.md` | Kilo engineering platform architecture | Platform Architect | Platform team | Permanent | NO | NO | HIGH | NO | YES |
| `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` | Core business logic deep dive | Domain Owner (core) | Backend engineers | Permanent | NO | NO | HIGH | NO | YES |
| `docs/architecture/production-architecture.md` | Year 1 through Stage 4 infrastructure strategy | Platform Architect | All engineers | Permanent | NO | NO | CRITICAL | NO | YES |
| `docs/architecture/adr/` (23 files) | Canonical ADR collection | Tech Lead | All engineers | Permanent | NO | NO | CRITICAL | NO | YES |
| `docs/architecture/future/` (17 files) | Future architecture vision (referenced by ADRs) | Platform Architect | All engineers | Permanent | NO | NO | CRITICAL | NO | YES |
| `docs/architecture/reviews/` | Architecture review documents | Platform Architect | Architects | Until superseded | YES (after ref update) | NO | MEDIUM | NO | YES |
| `docs/business-rules/` (23 files) | Comprehensive business rules | Domain Owners (per file) | Backend engineers | Permanent | NO | NO | CRITICAL | NO | YES |
| `docs/ai-governance/` (11 files) | AI governance standards | AI Governance Lead | AI team, All engineers | Permanent | NO | NO | HIGH | NO | YES |
| `docs/ai/` (3 files) | AI prompts and documentation | AI Governance Lead | AI team | Permanent | NO | NO | HIGH | NO | YES |
| `docs/refactoring/` (13 files) | Complete refactoring planning collection | Platform Architect | Architects, Backend | Until complete | YES (as unit) | NO | CRITICAL | NO | YES |
| `architecture/` (7 files + adr/) | Phase 0 baseline documents | Platform Architect | Architects | Permanent | NO (without ADR updates) | NO | HIGH | NO | YES |
| `architecture/adr/` (4 files) | Phase 0 baseline ADRs | Tech Lead | Architects | Permanent | NO (without ref updates) | NO | HIGH | NO | YES |
| `architecture/baseline/` | Architecture baseline validation | Platform Architect | Architects | Until superseded | YES | NO | MEDIUM | NO | NO |
| `.kilo/instructions/*` (11 files) | Kilo AI session instructions | Platform Architect | AI agents | Permanent | NO | NO | CRITICAL | NO | YES |
| `docs/adr/` (18 files) | Historical ADR collection | Tech Lead | Historians | Permanent | NO (without ref updates) | NO | HIGH | NO | YES |
| `docs/rag/` (23 files) | RAG knowledge base (outdated) | AI Governance Lead | AI indexing | Until updated | YES (after verification) | NO | MEDIUM | NO | YES |
| `docs/history/` | Historical generated data | Platform Architect | Historians | Until superseded | YES | NO | LOW | NO | NO |
| `docs/diagrams/generated/` | Generated diagrams | CI/CD pipeline | DevOps | Regenerable | YES | YES (after orphan validation) | LOW | YES | NO |
| `docs/uml/generated/` | Generated UML diagrams | CI/CD pipeline | DevOps | Regenerable | YES | YES (after orphan validation) | LOW | YES | NO |
| `properties/business_rules.md` | Legacy single-file business rules | Domain Owner (properties) | Historians | Until archived | YES (after ref updates) | YES (after orphan validation) | LOW | NO | NO |
| `01_repository_inventory.md` | Generated repository inventory | CI/CD pipeline | DevOps | Regenerable | YES | YES (after orphan validation) | LOW | NO | NO |
| `DOCUMENTATION_ANALYSIS_REPORT.md` | Generated analysis report | CI/CD pipeline | Architects | Regenerable | YES | YES (after orphan validation) | LOW | NO | NO |
| `architecture-analysis-report.md` | Generated architecture analysis | CI/CD pipeline | Architects | Regenerable | YES | YES (after orphan validation) | LOW | NO | NO |
| `architecture-compliance-report.md` | Generated compliance report | CI/CD pipeline | Architects | Regenerable | YES | YES (after orphan validation) | LOW | NO | NO |
| `architecture-compliance-report.json` | Generated compliance JSON | CI/CD pipeline | Architects | Regenerable | YES | YES (after orphan validation) | LOW | NO | NO |
| `architecture-dependency-graph.mmd` | Generated dependency graph | CI/CD pipeline | Architects | Regenerable | YES | YES (after orphan validation) | LOW | NO | NO |
| `architecture-dependency-graph.dot` | Generated dependency graph (dot) | CI/CD pipeline | Architects | Regenerable | YES | YES (after orphan validation) | LOW | NO | NO |
| `architecture-summary.txt` | Generated architecture summary | CI/CD pipeline | Architects | Regenerable | YES | YES (after orphan validation) | LOW | NO | NO |
| `directory-structure-analysis.md` | Generated directory analysis | CI/CD pipeline | Architects | Regenerable | YES | YES (after orphan validation) | LOW | NO | NO |
| `coverage-report.txt` | Empty coverage placeholder | CI/CD pipeline | DevOps | Regenerable | YES | YES (after orphan validation) | LOW | YES | NO |
| `docs/ci-cd-upgrade-report.md` | Generated upgrade report | Senior DevOps | DevOps | Until superseded | YES | NO | LOW | NO | NO |
| `architecture/generated/` | Generated architecture data | CI/CD pipeline | Architects | Regenerable | YES | YES (after orphan validation) | LOW | NO | NO |
| `docs/history/generated/` | Historical generated data | CI/CD pipeline | Historians | Until superseded | YES | NO | LOW | NO | NO |
| `architecture/diagrams/` | Generated architecture diagrams | CI/CD pipeline | Architects | Regenerable | YES | YES (after orphan validation) | LOW | YES | NO |
| `architecture/contracts/` | Empty planned contracts directory | Platform Architect | Architects | Until populated | YES | NO | LOW | NO | NO |
| `scripts/diagrams/documentation_guardian.py` | Documentation drift detector | Senior DevOps | CI/CD | Permanent | NO | NO | CRITICAL | YES | NO |

**Legend:**
- **Reference Stability:** CRITICAL = deletion breaks canonical docs; HIGH = referenced by important docs; MEDIUM = referenced by secondary docs; LOW = no external references
- **CI Dependency:** YES = referenced by CI/CD workflows or scripts
- **AI Dependency:** YES = referenced by AI instructions or used for AI indexing

---

## 3. Documentation Lifecycle Rules

Every document follows this lifecycle. Movement between stages requires validation at each gate.

```
DRAFT
  │
  │ [PR Review + Architecture Owner Approval]
  │ [Reference Graph Validation]
  │ [CI Validation]
  ▼
PLANNING
  │
  │ [Canonical Document Reference]
  │ [ADR Dependency Check]
  │ [CI Script Dependency Check]
  ▼
CANONICAL
  │
  │ [Superseded by newer canonical doc]
  │ [All references updated]
  │ [Architecture Review Board Approval]
  ▼
HISTORICAL
  │
  │ [Zero references proven]
  │ [No ADR dependency]
  │ [No CI dependency]
  │ [No script dependency]
  │ [No AI dependency]
  │ [Git history preserved via git mv]
  ▼
ARCHIVE
  │
  │ [Archive README with redirect]
  │ [10-year minimum retention]
  │ [Legal/compliance check]
  ▼
DELETE (only if completely orphaned)
```

### Stage Definitions

**DRAFT**
- New documentation under active development
- May be incomplete or under review
- Not referenced by any canonical document
- Can be deleted without approval if never promoted to Planning

**PLANNING**
- Active planning artifacts (target architecture, roadmaps, gap analysis)
- Referenced by canonical documents or ADRs
- Cannot be archived without updating all references
- Examples: `docs/refactoring/`, `docs/architecture/future/`

**CANONICAL**
- Single source of truth
- Referenced by CI/CD, ADRs, AI instructions, business logic
- Never archived without Architecture Review Board approval
- Changes require PR review + architecture owner approval

**HISTORICAL**
- Superseded by canonical documents but retained for traceability
- All references updated to point to canonical replacement
- Git history preserved
- Read-only; no further edits

**ARCHIVE**
- Moved to `docs/archive/` with README redirect
- Minimum 10-year retention
- Git history preserved via `git mv`
- Can be restored if needed

**DELETE**
- Only after proving zero references across entire dependency graph
- Requires Documentation Guardian validation
- Requires CI verification
- Git history must be preserved in commit log before deletion
- Legal/compliance check required

### Lifecycle Gates

**Gate 1: DRAFT → PLANNING**
- [ ] Document has clear owner
- [ ] Document has been reviewed by at least one peer
- [ ] Document is referenced by at least one canonical document OR is an ADR
- [ ] No broken internal links

**Gate 2: PLANNING → CANONICAL**
- [ ] Document is the single source of truth for its domain
- [ ] All stakeholders have reviewed and approved
- [ ] Document is referenced by CI/CD, ADRs, or AI instructions
- [ ] Document has stable, permanent path
- [ ] ADR exists documenting this as canonical (if architectural)

**Gate 3: CANONICAL → HISTORICAL**
- [ ] Canonical replacement exists and is approved
- [ ] ALL references in canonical documents have been updated
- [ ] CI/CD scripts have been updated
- [ ] AI instruction files have been updated
- [ ] `git mv` used for archival (history preserved)
- [ ] Redirect notice added in original location
- [ ] Architecture Review Board approval obtained

**Gate 4: HISTORICAL → ARCHIVE**
- [ ] Document has been in Historical state for ≥ 6 months
- [ ] Zero references in canonical documents (proven via reference scan)
- [ ] Zero CI/CD dependencies (proven via CI script scan)
- [ ] Zero AI dependencies (proven via AI instruction scan)
- [ ] No legal/compliance retention requirements
- [ ] `git mv` to `docs/archive/` with category subdirectory

**Gate 5: ARCHIVE → DELETE**
- [ ] Document has been in Archive for ≥ 10 years
- [ ] Zero references proven via full repository scan
- [ ] Documentation Guardian validation passes
- [ ] CI verification passes (no broken links)
- [ ] Markdown validation passes
- [ ] Legal/compliance sign-off obtained
- [ ] Git history is preserved in commit log

---

## 4. Documentation Dependency Rules

References are classified by criticality. Migration requirements scale with criticality.

### Critical References

**Definition:** References where deletion or movement breaks CI/CD, governance, or canonical architecture documentation.

**Examples:**
- ADR links between canonical documents
- Architecture Contract references
- CI/CD script paths (e.g., `scripts/architecture_contract.py` referencing docs)
- Documentation Guardian paths (e.g., `docs/adr/README.md`)
- `.kilo/instructions/` file paths referenced by Kilo sessions
- `import-linter.ini` configuration
- `.clinerules` project context

**Migration Requirements:**
1. Identify ALL critical references before any move
2. Update ALL canonical documents in the SAME PR as the move
3. Update ALL CI/CD scripts in the SAME PR as the move
4. Update ALL AI instruction files in the SAME PR as the move
5. Run full CI validation before merge
6. No merge until ALL validation passes

**Current Critical Reference Graph:**
```
README.md (line 83)
  └── docs/adr/README.md
       └── [18 ADR files]

scripts/diagrams/documentation_guardian.py (lines 91, 97)
  └── docs/adr/README.md
       └── [18 ADR files]

architecture/adr/001-current-architecture.md (line 45)
  └── docs/architecture/README.md

architecture/adr/001-current-architecture.md (line 42)
  └── architecture/ARCHITECTURE_PRINCIPLES.md

architecture/adr/001-current-architecture.md (line 43)
  └── architecture/CODING_STANDARDS.md

architecture/adr/001-current-architecture.md (line 44)
  └── architecture/ROADMAP.md

architecture/adr/002-target-architecture.md (line 61)
  └── docs/architecture/README.md

architecture/adr/003-refactoring-strategy.md (line 65)
  └── docs/architecture/README.md

docs/ai-governance/AI-Architecture-Review.md (line 39)
  └── docs/adr/README.md

docs/architecture/adr/ADR-XXX.md (multiple files)
  └── docs/architecture/future/XX_*.md (15+ references)
```

### High References

**Definition:** References between canonical documents that are not directly tied to CI/CD but are essential for architectural understanding.

**Examples:**
- Links between ADRs in `docs/architecture/adr/`
- Links from `docs/architecture/future/` to ADRs
- Links from `docs/refactoring/` documents to each other
- Links from business-rules to architecture docs

**Migration Requirements:**
1. Identify all high references before any move
2. Update references in SAME PR or in prerequisite PR
3. No partial moves of coupled document collections
4. Run link validation after move

### Medium References

**Definition:** References within documentation that support understanding but are not critical for CI/CD or governance.

**Examples:**
- Links from `docs/README.md` to subdirectories
- Links from `docs/business-rules/README.md` to individual files
- Internal links within `docs/refactoring/` documents

**Migration Requirements:**
1. Identify references before move
2. Update references in same PR or follow-up PR
3. Run link validation

### Low References

**Definition:** References in generated, historical, or planning documents with no canonical impact.

**Examples:**
- Internal links within generated reports
- Links between generated diagrams
- Self-references in historical documents

**Migration Requirements:**
1. No mandatory pre-migration updates
2. Update if convenient during move
3. Run link validation as part of CI

---

## 5. Archive Rules

### When Archive Is Allowed

Archive is permitted ONLY when ALL of the following conditions are met:

1. **Document is Tier 2, 3, or 4** (not Tier 1 Canonical)
2. **All critical references have been updated** in canonical documents
3. **All high references have been updated** or the target document is being archived as a unit
4. **CI/CD scripts have been updated** (if they reference the document)
5. **AI instruction files have been updated** (if they reference the document)
6. **Zero active references remain** after updates
7. **`git mv` is used** (never delete and recreate)
8. **Redirect README remains** in the original location

### When Archive Is Forbidden

Archive is FORBIDDEN if ANY of the following conditions are true:

1. Document is Tier 1 Canonical
2. Document is referenced by CI/CD scripts
3. Document is referenced by AI instruction files
4. Document is part of a tightly-coupled collection being partially archived
5. Document is an exact duplicate that is ALSO referenced by canonical documents
6. Document is the only copy of an ADR or architectural decision
7. Document has been in the repository for less than 6 months (unless clearly generated)

### Redirect README Rules

When a directory or file is archived:

1. **Create a README.md** in the original location with:
   - Title: "Archived: [Original Name]"
   - Reason for archival
   - Date of archival
   - Link to canonical replacement (if exists)
   - Link to archive location
   - "Do not edit — this content has moved" notice

2. **Create a README.md** in the archive location with:
   - Title: "Archive: [Original Name]"
   - Original path and date moved
   - Description of why it was archived
   - List of files in the archive

### When `git mv` Must Be Used

`git mv` is MANDATORY for:
- All Tier 1 and Tier 2 document moves
- All ADR moves
- All moves that are referenced by canonical documents
- All moves that preserve architectural knowledge

`git mv` is RECOMMENDED for:
- All Tier 3 document moves
- All Tier 4 document moves

### When Symlinks Should Never Be Used

Symlinks are FORBIDDEN for:
- Documentation files (Markdown, JSON, etc.)
- Files referenced by CI/CD pipelines
- Files referenced by Python scripts
- ADR files
- Any file that needs to be rendered on GitHub web UI
- Any file that needs to be indexed by search

Symlinks are PERMITTED only for:
- Binary artifacts that are not source-documented (e.g., generated diagrams that are not meant to be edited)

**Rationale:** Symlinks break on GitHub web UI, break in zip/tar exports, confuse AI agents, and create fragility in CI/CD. Use copy + redirect README instead.

---

## 6. Delete Rules

Deletion is the MOST RISKY operation and requires the STRICTEST validation.

### Deletion Prerequisites

Before ANY file can be deleted, ALL of the following must be proven:

1. **Zero References in Canonical Documents**
   - Full-text search across all Tier 1 documents
   - Must return zero matches for the file path (excluding archive/delete proposals)
   - Must include relative path variations (e.g., `../`, `./`, absolute paths)

2. **Zero ADR Dependency**
   - No ADR references the file
   - No ADR was created based on the file's content
   - If the file documents an ADR decision, the ADR itself must not reference the file

3. **Zero CI Dependency**
   - No GitHub Actions workflow references the file
   - No Python script in `scripts/` references the file
   - No shell script references the file
   - No configuration file references the file

4. **Zero Script Dependency**
   - No `tools/` script references the file
   - No `scripts/` script references the file
   - No management command references the file
   - No test references the file as test data

5. **Zero AI Dependency**
   - No `.kilo/instructions/` file references the file
   - No `docs/ai-governance/` file references the file
   - No RAG manifest references the file
   - No AI prompt references the file

6. **Documentation Guardian Validation**
   - `python scripts/diagrams/documentation_guardian.py` passes
   - No broken link warnings for the deleted file
   - All required docs still exist

7. **Markdown Validation**
   - All markdown files validate (no broken links to deleted file)
   - All markdown tables are well-formed
   - All markdown headings are properly structured

8. **Git History Preservation**
   - File content is preserved in git commit history
   - Deletion commit message clearly states what was deleted and why
   - Deletion is in a dedicated commit (not mixed with other changes)

### Deletion Prohibition

Deletion is PROHIBITED if ANY of the following are true:

1. The file is referenced by ANY canonical document
2. The file is referenced by ANY CI/CD script
3. The file is referenced by ANY AI instruction
4. The file contains ADR decisions or architectural knowledge
5. The file is the only copy of unique content (even if outdated)
6. The file is less than 1 year old
7. The file has never been archived first
8. The file is a duplicate that is ALSO referenced by canonical documents

### Deletion Process

1. **Proposal Phase:**
   - Create deletion proposal in GitHub Issue
   - Run full dependency scan
   - Document all findings
   - Obtain approval from architecture owner

2. **Validation Phase:**
   - Run Documentation Guardian
   - Run markdown validation
   - Run full CI pipeline
   - Verify zero references

3. **Execution Phase:**
   - Dedicated commit with clear message
   - Preserve git history (do not force-push, do not rewrite history)
   - Update any indexes that listed the deleted file

4. **Verification Phase:**
   - CI pipeline passes after deletion
   - Documentation Guardian passes after deletion
   - No broken links reported

---

## 7. Documentation Validation Pipeline

### Pre-Migration Validation Sequence

Before ANY documentation migration (archive, move, delete), run this sequence:

```
Reference Validation
       │
       ▼
Broken Markdown Links Check
       │
       ▼
Script Dependency Validation
       │
       ▼
ADR Dependency Validation
       │
       ▼
Documentation Guardian
       │
       ▼
CI Validation
       │
       ▼
Migration Execution
       │
       ▼
Post-Migration Repeat Validation
```

### Step 1: Reference Validation

**Purpose:** Identify all documents that reference the target file/directory.

**Tool:** Custom reference scanner (to be implemented)

**Checks:**
- Full-text search across all `.md` files for exact path matches
- Search for relative path variations (`./`, `../`, no prefix)
- Search for path fragments that could match
- Output: List of all referencing documents with line numbers

**Pass Criteria:**
- For archive: All critical and high references are identified and have update plans
- For delete: Zero references found

### Step 2: Broken Markdown Links Check

**Purpose:** Identify broken internal markdown links before and after migration.

**Tool:** `python scripts/diagrams/documentation_guardian.py`

**Checks:**
- All `[text](path)` links in all markdown files
- Exclude external HTTP links, anchors, mailto links
- Check file existence relative to markdown file location

**Pass Criteria:**
- Zero broken links before migration
- Zero broken links after migration

### Step 3: Script Dependency Validation

**Purpose:** Identify scripts that depend on the target file/directory.

**Tool:** Custom script scanner (to be implemented)

**Checks:**
- Search all `.py` files in `scripts/`, `tools/`, `management/` for path strings
- Search for file open operations targeting the path
- Search for glob patterns matching the path
- Search for configuration references

**Pass Criteria:**
- For archive: All scripts identified and have update plans
- For delete: Zero script dependencies found

### Step 4: ADR Dependency Validation

**Purpose:** Identify ADR dependencies on the target file/directory.

**Tool:** Custom ADR scanner (to be implemented)

**Checks:**
- Search all ADR files for references to the target
- Check if the target documents an ADR decision
- Check if the target is referenced as supporting evidence

**Pass Criteria:**
- For archive: All ADR references identified and have update plans
- For delete: Zero ADR dependencies found

### Step 5: Documentation Guardian

**Purpose:** Run full documentation guardian checks.

**Tool:** `python scripts/diagrams/documentation_guardian.py`

**Checks:**
- Broken links
- Required docs exist
- ADR index is updated

**Pass Criteria:**
- All checks pass

### Step 6: CI Validation

**Purpose:** Ensure CI pipeline is not broken by migration.

**Tool:** Full CI pipeline run

**Checks:**
- All GitHub Actions workflows pass
- All validation scripts pass
- All architecture checks pass

**Pass Criteria:**
- Full CI pipeline passes

### Step 7: Migration Execution

**Purpose:** Execute the migration with full traceability.

**Requirements:**
- Use `git mv` for all moves
- Dedicated commit with clear message
- All reference updates in same PR or prerequisite PRs
- No partial migrations of coupled collections

### Step 8: Post-Migration Repeat Validation

**Purpose:** Verify migration did not introduce new issues.

**Tool:** Repeat Steps 1-6

**Pass Criteria:**
- All checks pass after migration
- Redirect READMEs are in place
- Archive READMEs are in place

### CI Implementation Plan

**File:** `.github/workflows/documentation-validation.yml`

```yaml
name: Documentation Validation

on:
  pull_request:
    paths:
      - 'docs/**'
      - 'architecture/**'
      - 'README.md'
      - '*.md'
  push:
    branches:
      - main

jobs:
  reference-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate documentation references
        run: python scripts/diagrams/documentation_guardian.py

  link-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check for broken markdown links
        run: python -c "
          import re
          import os
          from pathlib import Path
          # Implementation of broken link checker
        "

  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Scan script dependencies
        run: python -c "
          # Scan scripts/ and tools/ for doc references
        "

  adr-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate ADR references
        run: python -c "
          # Validate all ADR references are valid
        "

  archive-integrity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Verify archive READMEs exist
        run: python -c "
          # Check all archived dirs have READMEs
        "
```

---

## 8. Final Directory Classification

Classification is based on dependency graph analysis, NOT age.

### Canonical (Tier 1)

| Path | Status | Reason |
|------|--------|--------|
| `README.md` | **CANONICAL** | Main project README, referenced by all |
| `docs/README.md` | **CANONICAL** | Documentation index |
| `docs/architecture-contract.md` | **CANONICAL** | CI/CD architecture governance contract |
| `docs/ci-cd-pipeline.md` | **CANONICAL** | CI/CD pipeline documentation |
| `docs/governance.md` | **CANONICAL** | CI/CD governance policies |
| `docs/kilo-architecture-spec.md` | **CANONICAL** | Kilo architecture specification |
| `docs/architecture/production-architecture.md` | **CANONICAL** | Year 1 through Stage 4 infrastructure strategy |
| `docs/architecture/adr/` (23 files) | **CANONICAL** | Canonical ADR collection, referenced by future docs |
| `docs/architecture/future/` (17 files) | **CANONICAL** | Referenced by 15+ canonical ADRs |
| `docs/architecture/reviews/01_future_architecture_review.md` | **CANONICAL** | Architecture review document |
| `docs/business-rules/` (23 files) | **CANONICAL** | Comprehensive business rules |
| `docs/ai-governance/` (11 files) | **CANONICAL** | AI governance standards |
| `docs/ai/` (3 files) | **CANONICAL** | AI prompts and documentation |
| `docs/refactoring/` (13 files) | **CANONICAL** | Tightly-coupled planning collection |
| `.kilo/instructions/*` (11 files) | **CANONICAL** | Kilo AI session instructions |
| `architecture/ARCHITECTURE_PRINCIPLES.md` | **CANONICAL** | Referenced by 4 architecture/adr files |
| `architecture/ROADMAP.md` | **CANONICAL** | Referenced by 3 architecture/adr files |
| `architecture/dependency-rules.md` | **CANONICAL** | Referenced by 3 architecture/adr files + 1 audit report |
| `architecture/module-boundaries.md` | **CANONICAL** | Referenced by 1 architecture/adr file |
| `architecture/import-layers.md` | **CANONICAL** | Part of architecture baseline |
| `architecture/CODING_STANDARDS.md` | **CANONICAL** | Referenced by 1 architecture/adr file |
| `architecture/adr/` (4 files) | **CANONICAL** | Referenced by docs/architecture/README.md |
| `properties/TEST_DOCUMENTATION.md` | **CANONICAL** | Properties module test documentation |
| `core/services/README.md` | **CANONICAL** | Core services index |
| `properties/repositories/README.md` | **CANONICAL** | Properties repositories index |
| `properties/services/README.md` | **CANONICAL** | Properties services index |
| `shared/README.md` | **CANONICAL** | Shared module documentation |
| `import-linter.ini` | **CANONICAL** | Architecture enforcement configuration |
| `.clinerules` | **CANONICAL** | Project context for AI agents |

### Reference (Tier 2)

| Path | Status | Reason |
|------|--------|--------|
| `docs/adr/` (18 files) | **REFERENCE** | Historical ADR collection with references |
| `docs/architecture/audit_data.json` | **REFERENCE** | Raw audit data used by scripts |
| `architecture/baseline/` (2 files) | **REFERENCE** | Phase 0 baseline validation |
| `properties/business_rules.md` | **REFERENCE** | Legacy single-file business rules |

### Planning (Tier 3)

| Path | Status | Reason |
|------|--------|--------|
| `docs/refactoring/` (13 files) | **PLANNING** | Tightly-coupled planning artifacts |
| `docs/architecture/future/` (17 files) | **PLANNING** | Future architecture vision referenced by ADRs |

### Generated (Tier 4)

| Path | Status | Reason |
|------|--------|--------|
| `01_repository_inventory.md` | **GENERATED** | Generated repository inventory |
| `DOCUMENTATION_ANALYSIS_REPORT.md` | **GENERATED** | Generated analysis report |
| `architecture-analysis-report.md` | **GENERATED** | Generated architecture analysis |
| `architecture-compliance-report.md` | **GENERATED** | Generated compliance report |
| `architecture-compliance-report.json` | **GENERATED** | Generated compliance JSON |
| `architecture-dependency-graph.mmd` | **GENERATED** | Generated dependency graph |
| `architecture-dependency-graph.dot` | **GENERATED** | Generated dependency graph |
| `architecture-summary.txt` | **GENERATED** | Generated architecture summary |
| `directory-structure-analysis.md` | **GENERATED** | Generated directory analysis |
| `coverage-report.txt` | **GENERATED** | Empty coverage placeholder |
| `docs/diagrams/generated/` (8 files) | **GENERATED** | Auto-generated diagrams |
| `docs/uml/generated/` (11 files) | **GENERATED** | Auto-generated UML diagrams |
| `architecture/diagrams/` (2 files) | **GENERATED** | Generated architecture diagrams |
| `architecture/generated/architecture.json` | **GENERATED** | Generated architecture data |
| `docs/history/generated/architecture.json` | **GENERATED** | Historical generated data |
| `docs/architecture/architecture-audit-report.md` | **GENERATED** | Generated architecture audit |
| `docs/ci-cd-upgrade-report.md` | **GENERATED** | Generated upgrade report |

### Historical

| Path | Status | Reason |
|------|--------|--------|
| N/A at present | — | — |

### Legacy

| Path | Status | Reason |
|------|--------|--------|
| `docs/rag/` (23 files) | **LEGACY** | Outdated Year 1 strategy descriptions |
| `architecture/contracts/` | **LEGACY** | Empty directory, planned but never populated |

### Deprecated

| Path | Status | Reason |
|------|--------|--------|
| N/A at present | — | — |

### Archive Candidate

| Path | Status | Reason |
|------|--------|--------|
| `docs/adr/` (18 files) | **ARCHIVE CANDIDATE** | Historical ADRs, 6+ references must be updated first |
| `architecture/ARCHITECTURE_PRINCIPLES.md` | **ARCHIVE CANDIDATE** | Superseded by docs/refactoring/00, 14 ADR refs must update |
| `architecture/ROADMAP.md` | **ARCHIVE CANDIDATE** | Superseded by docs/refactoring/12, 3 ADR refs must update |
| `architecture/dependency-rules.md` | **ARCHIVE CANDIDATE** | Superseded by docs/refactoring/05, 4 refs must update |
| `architecture/module-boundaries.md` | **ARCHIVE CANDIDATE** | Superseded by docs/refactoring/06, 1 ADR ref must update |
| `architecture/import-layers.md` | **ARCHIVE CANDIDATE** | Superseded by docs/refactoring/04, safe to archive |
| `architecture/CODING_STANDARDS.md` | **ARCHIVE CANDIDATE** | Superseded by docs/refactoring/10, 1 ADR ref must update |
| `architecture/adr/` (4 files) | **ARCHIVE CANDIDATE** | Superseded by docs/architecture/adr/, 1 ref must update |
| `architecture/baseline/` (2 files) | **ARCHIVE CANDIDATE** | Phase 0 baseline, safe to archive |
| `docs/architecture/README.md` | **ARCHIVE CANDIDATE** | Audit overview, broken references to missing files |
| `docs/architecture/architecture-audit-report.md` | **ARCHIVE CANDIDATE** | Superseded by production-architecture.md |
| `docs/ci-cd-upgrade-report.md` | **ARCHIVE CANDIDATE** | One-time report |
| `properties/business_rules.md` | **ARCHIVE CANDIDATE** | Legacy, 311 bytes, 4 references must update |

---

## 9. Archive Candidate Review

### KEEP (Do Not Archive)

| File/Directory | Reasoning |
|----------------|-----------|
| `docs/architecture/future/02_bounded_contexts.md` | Referenced by 11 canonical ADR files in `docs/architecture/adr/`. Archiving would break canonical ADR collection. |
| `docs/architecture/future/05_dependency_rules.md` | Referenced by 3 canonical ADR files. Even if exact duplicate of refactoring version, cannot delete without breaking canonical docs. |
| `docs/architecture/future/03_target_folder_structure.md` | Referenced by 4 canonical ADR files. |
| `docs/architecture/future/04_layer_rules.md` | Referenced by 4 canonical ADR files. |
| `docs/architecture/future/07_domain_events.md` | Referenced by 2 canonical ADR files. |
| `docs/architecture/future/08_repository_pattern.md` | Referenced by 2 canonical ADR files. |
| `docs/architecture/future/09_service_layer.md` | Referenced by 3 canonical ADR files. |
| `architecture/ARCHITECTURE_PRINCIPLES.md` | Referenced by 4 architecture/adr files. Must remain or all ADR references must update first. |
| `architecture/ROADMAP.md` | Referenced by 3 architecture/adr files. |
| `architecture/dependency-rules.md` | Referenced by 3 architecture/adr files + `docs/architecture/05_architecture_boundary_violations.md`. |
| `architecture/module-boundaries.md` | Referenced by 1 architecture/adr file. |
| `architecture/CODING_STANDARDS.md` | Referenced by 1 architecture/adr file. |
| `docs/refactoring/06_architecture_audit.md` | Referenced by `10_gap_analysis.md` and `05_execution_report.md`. Part of tightly-coupled collection. |
| `docs/refactoring/08_architecture_decisions.md` | Referenced by 4 files (09, 10, 11, 12). Part of tightly-coupled collection. |
| `docs/refactoring/02_verified_dead_code_report.md` | Referenced by 2 refactoring files. Part of tightly-coupled collection. |
| `docs/refactoring/` (all 13 files) | Tightly-coupled planning collection. Partial archival breaks internal references. |
| `docs/architecture/future/` (all 17 files) | Referenced by 15+ canonical ADRs. Cannot archive without breaking canonical docs. |

### ARCHIVE (Safe to Archive)

| File/Directory | Reasoning |
|----------------|-----------|
| `01_repository_inventory.md` | Only referenced in consolidation plans. Zero external references. |
| `DOCUMENTATION_ANALYSIS_REPORT.md` | Only referenced in consolidation plans. Zero external references. |
| `architecture-analysis-report.md` | Only referenced in consolidation plans. Zero external references. |
| `architecture-compliance-report.md` | Only referenced in consolidation plans. Zero external references. |
| `architecture-compliance-report.json` | Only referenced in consolidation plans. Zero external references. |
| `architecture-dependency-graph.mmd` | Only referenced in consolidation plans. Zero external references. |
| `architecture-dependency-graph.dot` | Only referenced in consolidation plans. Zero external references. |
| `architecture-summary.txt` | Only referenced in consolidation plans. Zero external references. |
| `directory-structure-analysis.md` | Only referenced in consolidation plans. Zero external references. |
| `coverage-report.txt` | Empty file. Only referenced in consolidation plans. |
| `docs/ci-cd-upgrade-report.md` | One-time generated report. Zero external references. |
| `docs/architecture/architecture-audit-report.md` | Superseded by `production-architecture.md`. Zero external references. |
| `docs/diagrams/generated/` (8 files) | Generated diagrams. No external references. |
| `docs/uml/generated/` (11 files) | Generated UML diagrams. No external references. |
| `architecture/diagrams/` (2 files) | Generated architecture diagrams. No external references. |
| `architecture/generated/architecture.json` | Generated architecture data. Zero external references. |
| `docs/history/generated/architecture.json` | Historical generated data. Zero external references. |
| `architecture/baseline/` (2 files) | Phase 0 baseline validation. Zero external references. |
| `architecture/contracts/` (empty) | Empty planned directory. Zero external references. |

### ARCHIVE AFTER REFERENCE UPDATE

| File/Directory | Required Updates | Reasoning |
|----------------|------------------|-----------|
| `docs/adr/` (18 files) | Update README.md line 83, documentation_guardian.py lines 91/97, architecture/adr/*, AI-Architecture-Review.md line 39 | Historical ADR collection with 6+ references. Safe to archive after all updates. |
| `architecture/adr/` (4 files) | Update docs/architecture/README.md references | Phase 0 ADRs superseded by detailed collection. |
| `architecture/ARCHITECTURE_PRINCIPLES.md` | Update 4 architecture/adr file references | Superseded by docs/refactoring/00_architecture_principles.md. |
| `architecture/ROADMAP.md` | Update 3 architecture/adr file references | Superseded by docs/refactoring/12_architecture_implementation_master_plan.md. |
| `architecture/dependency-rules.md` | Update 3 architecture/adr file references + docs/architecture/05 reference | Superseded by docs/refactoring/05_dependency_rules.md. |
| `architecture/module-boundaries.md` | Update 1 architecture/adr file reference | Superseded by docs/refactoring/06_module_responsibilities.md. |
| `architecture/CODING_STANDARDS.md` | Update 1 architecture/adr file reference | Superseded by docs/refactoring/10_naming_conventions.md. |
| `architecture/import-layers.md` | Verify zero references | Concise import layers. Superseded by docs/refactoring/04_layer_rules.md. |
| `docs/architecture/README.md` | Fix 4 broken internal links first, then archive | Architecture audit overview with broken references. |
| `docs/refactoring/01_target_architecture.md` | Update references in 09, 10, 11, 12 if needed | Superseded by 09_target_architecture.md. Part of collection — archive all together or keep all together. |
| `docs/refactoring/02_migration_roadmap.md` | Update reference in 12_master_plan | Superseded by 12_architecture_implementation_master_plan.md. |
| `docs/refactoring/11_architecture_roadmap_review.md` | Update reference in 12_master_plan | Superseded by 12_architecture_implementation_master_plan.md. |
| `properties/business_rules.md` | Update 4 references in docs/business-rules/* | Legacy single-file version. 311 bytes. |
| `docs/rag/` (23 files) | Verify no AI/script dependencies, then archive | Outdated Year 1 strategy descriptions. |

### DELETE AFTER VALIDATION

| File/Directory | Required Validation | Reasoning |
|----------------|---------------------|-----------|
| `docs/architecture/future/05_dependency_rules.md` | Full orphan validation | Exact duplicate of docs/refactoring/05_dependency_rules.md. Referenced by 3 canonical ADRs. Can delete ONLY after all 3 ADR references are updated. |
| `coverage-report.txt` | Full orphan validation | Empty file. May be referenced by CI. |

### NEVER DELETE

| File/Directory | Reasoning |
|----------------|-----------|
| All Tier 1 Canonical documents | Form the single source of truth |
| All ADR files (docs/architecture/adr/, docs/adr/, architecture/adr/) | Architectural decisions must be preserved |
| All generated reports that are referenced by CI | CI would break |
| Any file with active CI/CD dependencies | Would break pipeline |
| Any file referenced by `.kilo/instructions/` | Would break AI agent instructions |

---

## 10. Safe Migration Strategy

Migration must be incremental. Each phase is independently executable and verifiable.

### Phase 0: Pre-Migration Validation (MANDATORY)

**Objective:** Establish baseline before any changes.

**Actions:**
1. Run full Documentation Guardian scan: `python scripts/diagrams/documentation_guardian.py`
2. Run full link validation across all markdown files
3. Run full CI pipeline to establish green baseline
4. Document all current references to archive candidates
5. Create `docs/archive/README.md` with governance policy

**Exit Criteria:**
- Documentation Guardian passes
- CI pipeline is green
- Full reference map is documented

### Phase 1: Archive Generated Reports (No Risk)

**Objective:** Clean up repository root generated reports.

**Actions:**
1. Create `docs/archive/generated/` directory
2. Move the following files using `git mv`:
   - `01_repository_inventory.md` → `docs/archive/generated/repository-inventory.md`
   - `DOCUMENTATION_ANALYSIS_REPORT.md` → `docs/archive/generated/documentation-analysis-report.md`
   - `architecture-analysis-report.md` → `docs/archive/generated/architecture-analysis-report.md`
   - `architecture-compliance-report.md` → `docs/archive/generated/architecture-compliance-report.md`
   - `architecture-compliance-report.json` → `docs/archive/generated/architecture-compliance-report.json`
   - `architecture-dependency-graph.mmd` → `docs/archive/generated/architecture-dependency-graph.mmd`
   - `architecture-dependency-graph.dot` → `docs/archive/generated/architecture-dependency-graph.dot`
   - `architecture-summary.txt` → `docs/archive/generated/architecture-summary.txt`
   - `directory-structure-analysis.md` → `docs/archive/generated/directory-structure-analysis.md`
   - `coverage-report.txt` → `docs/archive/generated/coverage-report.txt`
3. Add redirect README at original locations

**Exit Criteria:**
- All files moved successfully
- Documentation Guardian passes
- CI pipeline passes
- No broken links

### Phase 2: Archive Generated Diagrams (No Risk)

**Objective:** Clean up generated diagram directories.

**Actions:**
1. Create `docs/archive/diagrams/` directory structure
2. Move generated diagrams:
   - `docs/diagrams/generated/` → `docs/archive/diagrams/generated-c4-flows-infrastructure/`
   - `docs/uml/generated/` → `docs/archive/diagrams/generated-uml/`
   - `architecture/diagrams/` → `docs/archive/diagrams/architecture/`
3. Add redirect READMEs

**Exit Criteria:**
- All diagrams moved successfully
- Documentation Guardian passes
- CI pipeline passes (diagram generation workflows still work)

### Phase 3: Archive Generated Architecture Data (No Risk)

**Objective:** Clean up generated architecture data.

**Actions:**
1. Create `docs/archive/generated/` subdirectories
2. Move generated data:
   - `architecture/generated/architecture.json` → `docs/archive/generated/architecture-generated/`
   - `docs/history/generated/architecture.json` → `docs/archive/generated/history-generated/`
3. Add redirect READMEs

**Exit Criteria:**
- All data moved successfully
- Documentation Guardian passes
- CI pipeline passes

### Phase 4: Archive Safe Generated Reports (Low Risk)

**Objective:** Archive reports with no external references.

**Actions:**
1. Move:
   - `docs/architecture/architecture-audit-report.md` → `docs/archive/audits/architecture-audit-report.md`
   - `docs/ci-cd-upgrade-report.md` → `docs/archive/generated/ci-cd-upgrade-report.md`
2. Add redirect READMEs

**Exit Criteria:**
- All reports moved successfully
- Documentation Guardian passes
- CI pipeline passes

### Phase 5: Update References Before Archiving ADRs (Medium Risk)

**Objective:** Update all references to `docs/adr/` and `architecture/adr/` before archiving.

**Actions:**
1. Update `README.md` line 83: `docs/adr/README.md` → `docs/architecture/adr/README.md`
2. Update `scripts/diagrams/documentation_guardian.py` lines 91, 97: `docs/adr/` → `docs/architecture/adr/`
3. Update `docs/ai-governance/AI-Architecture-Review.md` line 39: `docs/adr/` → `docs/architecture/adr/`
4. Update `architecture/adr/001-current-architecture.md` line 45: `docs/architecture/README.md` → `docs/refactoring/12_architecture_implementation_master_plan.md` (or appropriate canonical doc)
5. Update `architecture/adr/001-current-architecture.md` line 42: `architecture/ARCHITECTURE_PRINCIPLES.md` — keep reference (file stays canonical)
6. Update `architecture/adr/001-current-architecture.md` line 43: `architecture/CODING_STANDARDS.md` — keep reference (file stays canonical)
7. Update `architecture/adr/001-current-architecture.md` line 44: `architecture/ROADMAP.md` — keep reference (file stays canonical)
8. Update `architecture/adr/002-target-architecture.md` line 61: `docs/architecture/README.md` → canonical architecture doc
9. Update `architecture/adr/003-refactoring-strategy.md` line 65: `docs/architecture/README.md` → canonical architecture doc

**Exit Criteria:**
- All references updated
- Documentation Guardian passes
- CI pipeline passes
- No broken links

### Phase 6: Archive Historical ADR Collections (Low Risk After Phase 5)

**Objective:** Archive superseded ADR collections.

**Actions:**
1. Create `docs/archive/old-adr/` directory
2. Move using `git mv`:
   - `docs/adr/` → `docs/archive/old-adr/docs-adr/`
   - `architecture/adr/` → `docs/archive/old-adr/architecture-adr/`
3. Add redirect READMEs in original locations

**Exit Criteria:**
- All ADRs moved successfully
- Documentation Guardian passes
- CI pipeline passes
- No broken links

### Phase 7: Archive Architecture Baseline Files (Medium Risk)

**Objective:** Archive superseded architecture baseline documents.

**Prerequisites:** All ADR references to these files have been updated.

**Actions:**
1. Create `docs/archive/planning/` directory structure
2. Move using `git mv`:
   - `architecture/ARCHITECTURE_PRINCIPLES.md` → `docs/archive/planning/architecture-principles-concise.md`
   - `architecture/ROADMAP.md` → `docs/archive/planning/roadmap.md`
   - `architecture/dependency-rules.md` → `docs/archive/planning/dependency-rules.md`
   - `architecture/module-boundaries.md` → `docs/archive/planning/module-boundaries.md`
   - `architecture/CODING_STANDARDS.md` → `docs/archive/planning/coding-standards.md`
   - `architecture/import-layers.md` → `docs/archive/planning/import-layers.md`
3. Add redirect READMEs

**Exit Criteria:**
- All files moved successfully
- Documentation Guardian passes
- CI pipeline passes
- No broken links

### Phase 8: Archive Superseded Architecture Docs (Medium Risk)

**Objective:** Archive superseded architecture audit and review docs.

**Actions:**
1. Create `docs/archive/audits/` directory
2. Move using `git mv`:
   - `docs/architecture/README.md` → `docs/archive/audits/architecture-readme.md`
   - `docs/architecture/architecture-audit-report.md` → `docs/archive/audits/architecture-audit-report.md`
3. Add redirect READMEs

**Exit Criteria:**
- All files moved successfully
- Documentation Guardian passes
- CI pipeline passes

### Phase 9: Archive Superseded Refactoring Docs (Medium Risk)

**Objective:** Archive superseded refactoring planning docs.

**Prerequisite:** All references in remaining refactoring docs have been updated.

**Actions:**
1. Create `docs/archive/planning/refactoring-complete/` directory
2. Move using `git mv`:
   - `docs/refactoring/01_target_architecture.md` → `docs/archive/planning/refactoring-complete/01_target_architecture.md`
   - `docs/refactoring/02_migration_roadmap.md` → `docs/archive/planning/refactoring-complete/02_migration_roadmap.md`
   - `docs/refactoring/06_architecture_audit.md` → `docs/archive/planning/refactoring-complete/06_architecture_audit.md`
   - `docs/refactoring/08_architecture_decisions.md` → `docs/archive/planning/refactoring-complete/08_architecture_decisions.md`
   - `docs/refactoring/10_architecture_gap_analysis.md` → `docs/archive/planning/refactoring-complete/10_architecture_gap_analysis.md`
   - `docs/refactoring/11_architecture_roadmap_review.md` → `docs/archive/planning/refactoring-complete/11_architecture_roadmap_review.md`
3. Add redirect READMEs

**Alternative:** If the refactoring collection is still actively used, keep all 13 files together. Archive only when work is complete.

**Exit Criteria:**
- All files moved successfully (or decision made to keep all together)
- Documentation Guardian passes
- CI pipeline passes

### Phase 10: Archive Legacy Business Rules (Low Risk)

**Objective:** Archive legacy single-file business rules.

**Actions:**
1. Update all references to `properties/business_rules.md` to point to `docs/business-rules/`
2. Create `docs/archive/deprecated/` directory
3. Move using `git mv`:
   - `properties/business_rules.md` → `docs/archive/deprecated/legacy-business-rules.md`
4. Add redirect README

**Exit Criteria:**
- All references updated
- File moved successfully
- Documentation Guardian passes
- CI pipeline passes

### Phase 11: Archive Legacy RAG Knowledge Base (Medium Risk)

**Objective:** Archive outdated RAG knowledge base.

**Prerequisite:** Verify no AI systems or scripts depend on `docs/rag/`.

**Actions:**
1. Run dependency scan on `docs/rag/`
2. If no active dependencies, create `docs/archive/deprecated/rag-knowledge-base/` directory
3. Move using `git mv`:
   - `docs/rag/` → `docs/archive/deprecated/rag-knowledge-base/`
4. Add redirect README

**Exit Criteria:**
- Zero active dependencies verified
- All files moved successfully
- Documentation Guardian passes
- CI pipeline passes

---

## 11. Documentation Constitution

This Constitution becomes the permanent documentation governance document for the RentSecureBE repository.

### 11.1 Documentation Principles

**P1: Documentation is a Dependency Graph**
Documentation is not a collection of files. It is a dependency graph where documents reference, depend on, and validate each other. Any change to the graph must preserve all connections.

**P2: Knowledge Preservation Over Cleanliness**
Whenever there is a conflict between repository cleanliness and knowledge preservation, always choose knowledge preservation. A slightly messy repository with complete knowledge is better than a clean repository with lost knowledge.

**P3: Canonical Documents Are Immutable**
Canonical documents (Tier 1) are the single source of truth. They can be updated but never deleted, archived, or moved without Architecture Review Board approval.

**P4: References Are More Important Than Filenames**
Stable references are the backbone of documentation. Filenames can change, but references must be preserved or updated before any filename change.

**P5: Git History Must Be Preserved**
All document moves must use `git mv` to preserve git history. Deleting and recreating files destroys history and breaks traceability.

**P6: CI/CD Is a Documentation Stakeholder**
CI/CD pipelines, scripts, and tools are primary consumers of documentation. Any documentation change must consider CI/CD impact.

**P7: AI Agents Are Documentation Stakeholders**
AI agents (Kilo, Copilot, etc.) consume documentation for context. Documentation must be structured and referenced in ways that AI can reliably find and use.

**P8: Documentation Must Be Validated**
Before and after any documentation change, the Documentation Guardian must validate the repository state. Broken links and missing references are failures.

**P9: Documentation Evolution Is Expected**
Documentation will evolve as the codebase evolves. The governance model must accommodate evolution without losing historical knowledge.

**P10: Human Review Is Required for High-Impact Changes**
Architectural documentation changes require human review. AI agents can propose changes but cannot approve high-impact documentation changes.

### 11.2 Governance Rules

**G1: Tier Classification Authority**
Only the Architecture Review Board can reclassify documents between tiers. Individual contributors can propose reclassifications via GitHub Issues.

**G2: Canonical Document Changes**
Changes to Tier 1 Canonical documents require:
- PR review by at least one architecture owner
- Documentation Guardian validation
- CI pipeline passing
- If architectural: ADR documenting the change

**G3: Archive Approval**
Archiving Tier 1 documents requires Architecture Review Board unanimous approval.
Archiving Tier 2 documents requires architecture owner approval.
Archiving Tier 3 documents requires PR review by at least one peer.
Archiving Tier 4 documents does not require approval but must follow validation pipeline.

**G4: Delete Approval**
Deleting ANY documentation requires:
- Full dependency graph analysis
- Documentation Guardian validation
- CI verification
- Architecture Review Board approval (for Tier 1 and 2)
- Tech Lead approval (for Tier 3)
- PR review (for Tier 4)

**G5: Reference Stability**
Once a document path is referenced by a canonical document, that reference is considered stable. Changing the path requires updating ALL canonical references first.

**G6: ADR Integrity**
ADRs are permanent records of architectural decisions. They cannot be deleted, only superseded. Superseded ADRs must remain accessible and reference their replacement.

**G7: No Symlinks for Documentation**
Documentation files must never use symlinks. Use copy + redirect README instead.

**G8: Generated Documentation Must Be Regenerable**
Generated documentation (Tier 4) must have a reproducible generation process. If the generation process is lost, the documentation is not safe to delete.

### 11.3 Ownership

| Role | Responsibilities |
|------|-----------------|
| **Tech Lead** | Owns Tier 1 Canonical documents. Approves all documentation changes. |
| **Senior DevOps** | Owns CI/CD documentation (`docs/ci-cd-pipeline.md`, `docs/governance.md`, `docs/architecture-contract.md`). Approves CI-related doc changes. |
| **Platform Architect** | Owns architecture documentation (`docs/architecture/`, `architecture/`, `docs/refactoring/`). Approves architecture doc changes. |
| **Domain Owners** | Own business rules for their domain (`docs/business-rules/` per file). |
| **AI Governance Lead** | Owns AI documentation (`docs/ai-governance/`, `docs/ai/`, `.kilo/instructions/`). |
| **Documentation Guardian** | Automated role. Validates documentation state on every PR. |
| **Contributors** | Propose changes via PR. Must follow validation pipeline. |

### 11.4 Naming Rules

**N1: ADR Files**
- Format: `ADR-XXX_title_with_underscores.md` or `ADR-XXX_title-with-hyphens.md`
- Prefer underscores for consistency with existing collection
- Must include ADR number, title, and `.md` extension

**N2: Business Rules Files**
- Format: `NN-description-with-hyphens.md`
- Two-digit zero-padded number
- Hyphen-separated description

**N3: Architecture Files**
- Format: `NN_description_with_underscores.md` or `description-with-hyphens.md`
- Prefer consistent style within each directory

**N4: Module READMEs**
- Format: `README.md` (capital letters, `.md` extension)
- Must be named exactly `README.md` for GitHub rendering

**N5: Generated Files**
- Format: `kebab-case-description.md` or `snake_case_description.md`
- Must include generation date or version in content if relevant

### 11.5 Folder Rules

**F1: Documentation Root**
- All human-maintained documentation lives under `docs/`
- Generated documentation may live at repository root OR under `docs/archive/generated/`
- Never mix generated and canonical docs in the same directory

**F2: Architecture Directory**
- `architecture/` contains Phase 0 baseline documents
- `docs/architecture/` contains Year 1+ architecture documentation
- Both are canonical; do not merge without explicit decision

**F3: ADR Directories**
- `docs/architecture/adr/` is the canonical ADR collection
- `docs/adr/` is the historical ADR collection
- `architecture/adr/` is the Phase 0 baseline ADR collection
- All three must remain distinct

**F4: Archive Directory**
- `docs/archive/` contains all archived documentation
- Subdirectories by category: `generated/`, `audits/`, `planning/`, `deprecated/`, `old-adr/`
- Each subdirectory contains a README explaining the archive policy

**F5: RAG Directory**
- `docs/rag/` contains RAG knowledge base (legacy)
- If updated, must reflect current Year 1 architecture
- If archived, must be moved to `docs/archive/deprecated/`

**F6: Scripts Directory**
- `scripts/` contains executable scripts
- `scripts/diagrams/` contains diagram generation scripts
- `tools/` contains CI/CD and development tools
- Scripts that reference documentation must be updated when documentation moves

### 11.6 ADR Rules

**ADR-1: ADR Numbering**
- Canonical ADRs use format `ADR-XXX` where XXX is a three-digit number
- Numbers are assigned sequentially
- Gaps in numbering are acceptable (missing ADRs should be noted in index)
- ADRs cannot be renumbered after publication

**ADR-2: ADR Status**
- **Proposed**: Under discussion
- **Accepted**: Approved and implemented
- **Rejected**: Not approved
- **Deprecated**: No longer relevant
- **Superseded**: Replaced by another ADR

**ADR-3: ADR Content**
Every ADR must include:
- Title
- Status
- Date
- Deciders
- Context
- Decision
- Alternatives Considered
- Consequences
- References (related ADRs, documentation)

**ADR-4: ADR Index**
- `docs/architecture/adr/README.md` is the canonical ADR index
- Must be updated when new ADRs are added
- Must reference all ADR files
- Missing ADR files must be noted or created

**ADR-5: ADR Supersession**
- Superseded ADRs must remain in the repository
- Must update status to "Superseded"
- Must reference the replacing ADR
- Cannot be deleted

### 11.7 Archive Policy

**A1: Archive Location**
- All archived documentation goes under `docs/archive/`
- Subdirectories by category: `generated/`, `audits/`, `planning/`, `deprecated/`, `old-adr/`
- Category determined by original document type, not content

**A2: Archive README**
- Every archived directory must contain a `README.md`
- README must state:
  - Original path
  - Date archived
  - Reason for archival
  - Canonical replacement (if exists)
  - Link to archive location
  - "Do not edit — this content has moved" notice

**A3: Archive Retention**
- Minimum 10-year retention period
- Legal/compliance requirements may extend retention
- Archive contents are read-only
- No edits to archived documents

**A4: Archive Git History**
- All archives must use `git mv`
- Git history must be preserved
- Commit message must state: `docs: archive [path] — [reason]`

### 11.8 Deletion Policy

**D1: Deletion Requires Full Validation**
Before deletion, ALL of the following must pass:
- Zero references in canonical documents
- Zero ADR dependencies
- Zero CI dependencies
- Zero script dependencies
- Zero AI dependencies
- Documentation Guardian validation
- Markdown validation
- CI verification

**D2: Deletion Process**
1. Create GitHub Issue with deletion proposal
2. Run full dependency scan
3. Obtain required approvals
4. Execute deletion in dedicated commit
5. Verify CI passes after deletion
6. Document deletion in commit message

**D3: Deletion Prohibition**
Deletion is PROHIBITED for:
- Tier 1 Canonical documents
- Any document with active CI/CD dependencies
- Any document referenced by AI instructions
- Any document containing unique architectural knowledge
- Any ADR (can only be superseded, not deleted)

### 11.9 Reference Policy

**R1: Reference Stability**
- References from canonical documents are considered stable
- Changing a referenced path requires updating ALL referencing canonical documents first
- Use relative paths for internal references
- Use absolute paths for root-level references

**R2: Reference Format**
- Markdown links: `[text](relative/path.md)`
- No bare URLs for internal documents
- No symlinks for internal references
- Use `.md` extension explicitly

**R3: Reference Updates**
- Reference updates must be in the same PR as the document move
- Or in a prerequisite PR that merges first
- Never leave broken references in canonical documents

**R4: Cross-Repository References**
- If referencing another repository, use full URL
- Document the dependency in `docs/architecture-contract.md`
- Monitor external references for link rot

### 11.10 Validation Policy

**V1: Pre-Migration Validation**
Before ANY documentation migration:
1. Run Documentation Guardian
2. Run link validation
3. Run dependency scan
4. Identify all references to affected documents
5. Document update plan

**V2: Post-Migration Validation**
After EVERY documentation migration:
1. Run Documentation Guardian
2. Run link validation
3. Run full CI pipeline
4. Verify redirect READMEs are in place
5. Verify no broken links

**V3: CI Validation**
Documentation validation runs on:
- Every PR that modifies `*.md` files
- Every push to `main`
- Nightly scheduled run

**V4: Validation Failures**
- Documentation Guardian warnings are non-blocking but must be addressed
- Documentation Guardian errors are blocking
- Broken links in canonical documents are blocking
- Broken links in generated documents are non-blocking

### 11.11 Review Policy

**REV1: PR Review Requirements**
- All documentation changes require PR review
- Tier 1 changes require architecture owner review
- Tier 2 changes require peer review
- Tier 3 changes require at least one reviewer
- Tier 4 changes do not require review but must pass CI

**REV2: Architecture Review Board**
- Composed of Tech Lead, Senior DevOps, Platform Architect
- Approves all Tier 1 changes
- Approves all archive/delete operations for Tier 1 and 2
- Meets on demand for documentation governance issues

**REV3: Review Checklist**
Reviewers must verify:
- [ ] Change is justified
- [ ] References are updated
- [ ] Documentation Guardian passes
- [ ] CI pipeline passes
- [ ] No broken links
- [ ] No orphaned references
- [ ] Git history will be preserved

### 11.12 AI Documentation Rules

**AI1: AI Instruction Files**
- `.kilo/instructions/*.md` are AI instruction files
- Changes require Platform Architect approval
- Must be validated by AI agent testing
- Must not reference files that will be archived

**AI2: RAG Documentation**
- `docs/rag/*` is RAG knowledge base
- Must be kept up-to-date with current architecture
- If outdated, must be archived or updated
- Changes require AI Governance Lead approval

**AI3: AI Agent Compatibility**
- All documentation must be parseable by AI agents
- Use clear headings, lists, and tables
- Avoid ambiguous pronouns ("it", "they")
- Include explicit cross-references
- Use consistent terminology

**AI4: AI Validation**
- AI agents must validate documentation changes
- AI agents must not approve high-impact changes
- AI agents must flag broken references and contradictions

### 11.13 CI Documentation Rules

**CI1: CI Script Dependencies**
- All CI scripts that reference documentation must be identified
- Changes to documentation paths must update CI scripts in the same PR
- CI must validate documentation state on every run

**CI2: Documentation Guardian in CI**
- `scripts/diagrams/documentation_guardian.py` runs on every PR
- Broken links are reported as warnings or errors
- Missing required docs are reported as errors

**CI3: Generated Documentation**
- Generated docs must have reproducible generation process
- Generation must be documented in the doc itself or in `docs/ci-cd-pipeline.md`
- If generation fails, CI must fail

**CI4: CI Documentation**
- `docs/ci-cd-pipeline.md` must be updated when CI changes
- `docs/architecture-contract.md` must be updated when architecture enforcement changes
- `docs/governance.md` must be updated when governance policies change

### 11.14 Knowledge Preservation Rules

**KP1: No Silent Deletions**
- No documentation can be deleted without explicit approval and documentation
- Deletion must be recorded in git commit message
- Deletion must be recorded in this Constitution's changelog

**KP2: Historical Traceability**
- All architectural decisions must have an ADR
- All ADRs must remain accessible
- Superseded ADRs must reference their replacement

**KP3: Version Preservation**
- Documentation versions must be recorded
- Significant changes must bump version
- Version history must be preserved in git

**KP4: Context Preservation**
- Documentation must include context (why, not just what)
- Rationale for decisions must be preserved
- Alternatives considered must be documented

**KP5: Dependency Preservation**
- All dependencies between documents must be explicit
- All references must be stable
- Broken references are treated as bugs

### 11.15 Future Evolution Rules

**FE1: Governance Evolution**
- This Constitution can be updated via PR
- Updates require Architecture Review Board approval
- Changes must be documented in the Constitution itself

**FE2: Technology Evolution**
- As the codebase evolves, documentation structure may need to evolve
- Structural changes must follow the Safe Migration Strategy
- No breaking changes to canonical document paths without explicit decision

**FE3: Scale Evolution**
- As the team grows, ownership may need to be distributed
- Domain owners may be added for new bounded contexts
- The ownership matrix must be updated accordingly

**FE4: Tooling Evolution**
- New validation tools may be added
- New CI checks may be added
- The validation pipeline must accommodate new tools

**FE5: AI Evolution**
- As AI capabilities evolve, AI documentation rules may need to evolve
- Changes require AI Governance Lead approval
- Must maintain backward compatibility with existing AI agents

---

## Appendix A: Current Reference Map

### Critical Reference Map (Tier 1)

```
README.md
  ├── docs/architecture-contract.md
  ├── docs/ci-cd-pipeline.md
  ├── docs/governance.md
  ├── docs/business-rules/README.md
  ├── docs/ai-governance/AI-Contribution-Guide.md
  ├── docs/adr/README.md (line 83) ← MUST UPDATE IF ARCHIVED
  ├── docs/uml/ (directory reference)
  └── docs/diagrams/ (directory reference)

docs/architecture/adr/ (23 files)
  ├── docs/architecture/future/02_bounded_contexts.md (11 refs)
  ├── docs/architecture/future/03_target_folder_structure.md (4 refs)
  ├── docs/architecture/future/04_layer_rules.md (4 refs)
  ├── docs/architecture/future/05_dependency_rules.md (3 refs)
  ├── docs/architecture/future/07_domain_events.md (2 refs)
  ├── docs/architecture/future/08_repository_pattern.md (2 refs)
  ├── docs/architecture/future/09_service_layer.md (3 refs)
  └── [other internal references]

architecture/adr/ (4 files)
  ├── architecture/ARCHITECTURE_PRINCIPLES.md
  ├── architecture/CODING_STANDARDS.md
  ├── architecture/ROADMAP.md
  └── docs/architecture/README.md

scripts/diagrams/documentation_guardian.py
  ├── docs/adr/README.md (lines 91, 97) ← MUST UPDATE IF ARCHIVED
  ├── docs/README.md
  ├── docs/architecture-contract.md
  ├── docs/ci-cd-pipeline.md
  └── docs/governance.md

.kilo/instructions/* (11 files)
  └── Various code paths (implicit reference via AI context)
```

### Archive Reference Map

```
docs/adr/README.md (18 files)
  ← README.md (line 83)
  ← scripts/diagrams/documentation_guardian.py (lines 91, 97)
  ← architecture/adr/001-current-architecture.md (line 45)
  ← architecture/adr/002-target-architecture.md (line 61)
  ← architecture/adr/003-refactoring-strategy.md (line 65)
  ← docs/ai-governance/AI-Architecture-Review.md (line 39)

architecture/adr/ (4 files)
  ← docs/architecture/README.md

architecture/ARCHITECTURE_PRINCIPLES.md
  ← architecture/adr/001-current-architecture.md (line 42)
  ← architecture/adr/002-target-architecture.md
  ← architecture/adr/003-refactoring-strategy.md
  ← [1 more in architecture/adr/]

architecture/ROADMAP.md
  ← architecture/adr/001-current-architecture.md (line 44)
  ← architecture/adr/002-target-architecture.md
  ← architecture/adr/003-refactoring-strategy.md

architecture/dependency-rules.md
  ← architecture/adr/001-current-architecture.md
  ← architecture/adr/002-target-architecture.md
  ← architecture/adr/003-refactoring-strategy.md
  ← docs/architecture/05_architecture_boundary_violations.md

architecture/module-boundaries.md
  ← architecture/adr/001-current-architecture.md

architecture/CODING_STANDARDS.md
  ← architecture/adr/001-current-architecture.md

docs/refactoring/ (13 files, tightly coupled)
  ├── 00_architecture_principles.md
  │   └── [referenced by ADRs]
  ├── 08_architecture_decisions.md
  │   ├── 09_target_architecture.md
  │   ├── 10_architecture_gap_analysis.md
  │   ├── 11_architecture_roadmap_review.md
  │   └── 12_architecture_implementation_master_plan.md
  ├── 09_target_architecture.md
  │   └── 08_architecture_decisions.md
  ├── 10_architecture_gap_analysis.md
  │   ├── 06_architecture_audit.md
  │   └── 08_architecture_decisions.md
  ├── 11_architecture_roadmap_review.md
  │   ├── 09_target_architecture.md
  │   └── 08_architecture_decisions.md
  └── 12_architecture_implementation_master_plan.md
      ├── 08_architecture_decisions.md
      ├── 09_target_architecture.md
      ├── 10_architecture_gap_analysis.md
      └── 11_architecture_roadmap_review.md
```

---

## Appendix B: Document Classification Summary

| Classification | Count | Examples |
|----------------|-------|----------|
| **Canonical** | 28 | README.md, docs/architecture/adr/, .kilo/instructions/ |
| **Reference** | 4 | docs/adr/, architecture/baseline/, properties/business_rules.md |
| **Planning** | 30 | docs/refactoring/, docs/architecture/future/ |
| **Generated** | 23 | Generated reports, diagrams, JSON data |
| **Historical** | 0 | — |
| **Legacy** | 24 | docs/rag/, architecture/contracts/ (empty) |
| **Deprecated** | 0 | — |
| **Archive Candidate** | 14 | Various superseded documents |

**Total:** ~123 documentation files

---

## Appendix C: Quick Reference — Do's and Don'ts

| Action | Do | Don't |
|--------|----|-------|
| Archive Tier 1 | NEVER | EVER |
| Delete Tier 1 | NEVER | EVER |
| Partial archive of coupled collection | NEVER | EVER |
| Move without `git mv` | NEVER | EVER |
| Use symlinks for docs | NEVER | EVER |
| Archive without updating references | NEVER | EVER |
| Delete without full dependency scan | NEVER | EVER |
| Modify canonical docs without review | NEVER | EVER |
| Tier 2 archive | Update references first | Move without updates |
| Tier 3 archive | Treat as unit | Partial moves |
| Tier 4 archive | Verify zero refs first | Blindly delete |
| CI script updates | Same PR as doc move | Separate PR |
| Redirect README | Always include | Omit redirect |

---

*End of Documentation Governance Specification*

**Changelog:**
- v1.0.0 (2026-07-18): Initial specification based on repository analysis and previous consolidation review.
