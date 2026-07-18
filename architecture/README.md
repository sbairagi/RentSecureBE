# Architecture Workspace

This directory contains the architecture baseline, principles, and standards that govern the RentSecureBE transformation.

## Contents

| Path | Purpose |
|------|---------|
| `ARCHITECTURE_PRINCIPLES.md` | 16 architecture principles |
| `CODING_STANDARDS.md` | Folder conventions, naming rules |
| `module-boundaries.md` | Bounded context definitions |
| `dependency-rules.md` | Dependency direction rules |
| `import-layers.md` | Layered import rules |
| `ROADMAP.md` | Phase definitions and infrastructure stages |
| `adr/` | Legacy/baseline ADR templates and historical migration documents |

## ADR Collections

### Canonical ADRs

**Location:** `docs/architecture/adr/`

`docs/architecture/adr/` contains all accepted architecture decisions and is the authoritative source for implementation decisions. All new ADRs must be created here. All implementation references must point to this location.

### Legacy / Baseline ADRs

**Location:** `architecture/adr/`

`architecture/adr/` contains initial baseline templates and historical migration documents. It must not be used as the source of truth for new implementation decisions. The four files in this directory are:

- `000-template.md` — Original ADR template (superseded by `docs/ai-governance/AI-Decision-Record.md`)
- `001-current-architecture.md` — Baseline current architecture snapshot
- `002-target-architecture.md` — Baseline target architecture snapshot
- `003-refactoring-strategy.md` — Baseline refactoring strategy snapshot

## Reference

- Implementation Master Checklist: `RentSecureBE_Implementation_Master_Checklist.md`
- Architecture audit: `docs/architecture/README.md`
- ADR index (canonical): `docs/architecture/adr/README.md`
- ADR index (legacy): `architecture/adr/` (historical only)
