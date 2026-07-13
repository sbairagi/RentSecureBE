# Architecture Documentation

This directory contains the high-level architecture documentation for RentSecureBE.

## Contents

- **[Architecture README](README.md)** — Current architecture, vision, principles, and process
- **[Principles](../ARCHITECTURE_PRINCIPLES.md)** — Architecture principles governing all phases
- **[Coding Standards](../CODING_STANDARDS.md)** — Coding conventions and standards
- **[Roadmap](../ROADMAP.md)** — 30+ phase transformation plan
- **[ADRs](../adr/)** — Architecture Decision Records

## Navigation

| Document | Purpose |
|----------|---------|
| `README.md` | Architecture overview and governance |
| `../ARCHITECTURE_PRINCIPLES.md` | Non-negotiable architecture principles |
| `../CODING_STANDARDS.md` | Coding conventions for all phases |
| `../ROADMAP.md` | Long-term transformation roadmap |
| `../adr/000-template.md` | ADR template |
| `../adr/001-current-architecture.md` | Current architecture baseline |
| `../adr/002-target-architecture.md` | Target architecture vision |
| `../adr/003-refactoring-strategy.md` | Incremental transformation strategy |

## Architecture Review Process

1. Each phase produces an ADR documenting the change
2. ADR is reviewed for alignment with architecture principles
3. Import-linter contracts are updated before implementation
4. Implementation proceeds in small, reversible steps
5. CI must remain green throughout
6. Post-phase review validates Definition of Done

## Definition of Done

Every architecture phase must satisfy:
- [ ] CI remains green
- [ ] No production code logic changes
- [ ] No API changes
- [ ] No serializer changes
- [ ] No model changes
- [ ] No migration changes
- [ ] No import changes
- [ ] Import-linter contracts updated
- [ ] Architecture tests pass
- [ ] Documentation updated
- [ ] ADR created and approved
