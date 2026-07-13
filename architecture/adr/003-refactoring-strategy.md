# Refactoring Strategy

## Status
Accepted

## Date
2026-07-14

## Context
A 30+ phase architecture transformation requires a disciplined, incremental strategy that never breaks production, never changes external APIs, and keeps CI green at every step.

## Problem
How do we evolve from the current modular monolith to a structured modular monolith with enforced bounded contexts without disrupting the business?

## Decision
Use an **Incremental Strangler Fig** pattern across 30+ phases:

1. **Phase 0 (Current)**: Establish architecture baseline and documentation
2. **Phases 1-5**: Shared foundation and infrastructure (no business logic changes)
3. **Phases 6-20**: Extract bounded contexts one at a time
4. **Phases 21-25**: Cross-cutting concerns and domain events
5. **Phases 26-30**: Preparation for service extraction (optional)
6. **Phase 31+**: Service extraction (only if business requires)

Each phase follows strict Definition of Done:
- [ ] CI remains green
- [ ] No production code logic changes
- [ ] No API changes
- [ ] No serializer changes
- [ ] No model changes
- [ ] No migration changes
- [ ] Import-linter contracts updated
- [ ] Architecture tests pass
- [ ] Documentation updated

## Alternatives
1. **Big-bang rewrite**
   - Rejected: too risky, long freeze period, high chance of failure

2. **Continuous refactoring without phases**
   - Rejected: no clear milestones, hard to track progress, risk of scope creep

3. **Incremental bounded context extraction**
   - Accepted: small, safe steps, reversible, measurable progress

## Consequences
- Each phase is independently reviewable
- Rollback is possible at any phase boundary
- Business value continues to ship during transformation
- Architecture debt is paid down systematically
- Team learns and adapts the process over time

## Migration Notes
Each phase produces only:
- New directory structures (empty or with moved non-production files)
- Updated documentation
- Updated architecture tests
- Updated import-linter contracts

No business logic moves, no API changes, no model changes.

## References
- [Architecture README](docs/architecture/README.md)
- [Roadmap](architecture/ROADMAP.md)
- [Architecture Principles](architecture/ARCHITECTURE_PRINCIPLES.md)
