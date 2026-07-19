# Architecture Decision Records

## Authority

This directory (`docs/architecture/adr/`) is the **canonical** ADR collection for the RentSecureBE project. All accepted architecture decisions are recorded here. This is the authoritative source for implementation decisions.

## Legacy / Baseline ADRs

A separate collection of baseline ADR templates and historical migration documents exists at `architecture/adr/`. That directory contains:
- `000-template.md` — Original ADR template (superseded by `docs/ai-governance/AI-Decision-Record.md`)
- `001-current-architecture.md` through `003-refactoring-strategy.md` — Baseline snapshots

These legacy documents are preserved for historical reference only and must not be used as the source of truth for new implementation decisions.

## Creating a New ADR

1. Create a new file: `ADR-XXX.md` (use next available number)
2. Use the template from `architecture/adr/000-template.md`
3. Fill in all sections
4. Submit PR for review
5. Update this index

## Guidelines

- One decision per ADR
- Include context, decision, and consequences
- Record alternatives considered
- Link related ADRs
- Update status as decision evolves

| ID | Title | Status | Date | Supersedes |
|----|-------|--------|------|------------|
| ADR-001 | Modular Monolith Architecture | Accepted | 2026-07-14 | — |
| ADR-001 | Bounded Context Strategy | Accepted | 2026-07-19 | ADR-001 (v1.0) |
| ADR-002 | Identity Strategy | Accepted | 2026-07-19 | — |
| ADR-003 | Subscription Strategy | Accepted | 2026-07-19 | — |
| ADR-004 | Payment Architecture | Accepted | 2026-07-19 | ADR-010 (v1.0) |
| ADR-005 | Shared Kernel Rules | Accepted | 2026-07-19 | ADR-008 (v1.0) |
| ADR-006 | Import Rules | Accepted | 2026-07-19 | ADR-006 (v1.0) |
| ADR-007 | Migration Strategy | Accepted | 2026-07-19 | ADR-008 (v1.0, partial) |
| ADR-008 | Repository Pattern | Accepted | 2026-07-19 | ADR-002 (v1.0) |
| ADR-009 | Testing Strategy | Accepted | 2026-07-19 | ADR-007 (v1.0) |
| ADR-010 | CI/CD Strategy | Accepted | 2026-07-19 | — |
| ADR-011 | Notification Strategy | Accepted | 2026-07-14 | — |
| ADR-012 | Document Generation | Accepted | 2026-07-14 | — |
| ADR-013 | Error Handling | Accepted | 2026-07-14 | — |
| ADR-014 | Background Jobs | Accepted | 2026-07-14 | — |
| ADR-015 | API Versioning | Accepted | 2026-07-14 | — |
| ADR-016 | Feature Flags | Accepted | 2026-07-14 | — |
| ADR-017 | CQRS Selective | Accepted | 2026-07-14 | — |
| ADR-018 | Dependency Injection | Accepted | 2026-07-14 | — |
| ADR-019 | Event Bus | Accepted | 2026-07-14 | — |
| ADR-020 | Vertical Slice | Accepted | 2026-07-14 | — |
| ADR-021 | Audit Logging | Accepted | 2026-07-14 | — |
| ADR-022 | Cache Strategy | Accepted | 2026-07-14 | — |
| ADR-023 | Search Strategy | Accepted | 2026-07-14 | — |

## Creating a New ADR

1. Create a new file: `ADR-XXX.md` (use next available number)
2. Use the template from `architecture/adr/000-template.md`
3. Fill in all sections
4. Submit PR for review
5. Update this index

## Guidelines

- One decision per ADR
- Include context, decision, and consequences
- Record alternatives considered
- Link related ADRs
- Update status as decision evolves
