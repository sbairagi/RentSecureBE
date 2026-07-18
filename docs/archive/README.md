# Archived Documentation

This directory contains documentation that has been superseded, consolidated, or is preserved for historical reference only. These documents are not the source of truth for current implementation decisions.

## Contents

### `refactoring-legacy/`

Historical architecture refactoring documents (15 files) created during earlier phases of the RentSecureBE architecture work. These documents predate the canonical architecture documentation in `docs/architecture/` and `architecture/`.

**Archived because:**
- Content superseded by current `docs/architecture/` analysis reports
- ADR decisions in these files have been formalized in `docs/architecture/adr/`
- These were working documents, not canonical architecture decisions

**Do not reference these documents for current implementation decisions.**

### `adr-legacy/`

Older ADR collection (36 ADRs, ADR-001 through ADR-036) that predates the canonical ADR collection in `docs/architecture/adr/` (ADR-001 through ADR-023).

**Archived because:**
- Superseded by `docs/architecture/adr/` which is the authoritative ADR collection
- Contains ADR-024 through ADR-036 that were created before the canonical collection was established
- Some ADRs in this collection have been superseded by later decisions in the canonical collection

**Do not reference these documents for current implementation decisions. Use `docs/architecture/adr/` instead.**

### `audits/`

Historical architecture audit reports and CI/CD upgrade reports preserved for reference.

### `reports/`

Baseline validation reports and architecture reports from earlier phases.

## Archive Policy

- Documents are archived, not deleted, to preserve project history
- Canonical documents are never archived
- ADR documents are never permanently deleted
- Implementation roadmap documents are never permanently deleted
- Archived documents may be removed after project completion with Architecture Review Board approval

## Canonical Documentation Locations

| Document Type | Canonical Location |
|---------------|-------------------|
| Architecture Principles | `architecture/ARCHITECTURE_PRINCIPLES.md` |
| Coding Standards | `architecture/CODING_STANDARDS.md` |
| Module Boundaries | `architecture/module-boundaries.md` |
| Dependency Rules | `architecture/dependency-rules.md` |
| Import Layers | `architecture/import-layers.md` |
| Roadmap | `architecture/ROADMAP.md` |
| ADRs (accepted) | `docs/architecture/adr/` |
| Architecture Audit | `docs/architecture/README.md` |
| Implementation Checklist | `RentSecureBE_Implementation_Master_Checklist.md` |
| Architecture Contracts | `docs/architecture/contracts/` |
