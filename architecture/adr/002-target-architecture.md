# Target Architecture

## Status
Proposed

## Date
2026-07-14

## Context
The current modular monolith has served well but has accumulated technical debt, cross-app coupling in some areas, and lacks clear bounded context boundaries. The long-term vision is a modular monolith with strict bounded contexts, preparing for eventual service extraction without forcing premature microservice complexity.

## Problem
Define the target architecture that balances current stability with long-term maintainability, testability, and team autonomy.

## Decision
The target architecture is a **Structured Modular Monolith** with:

- Clear bounded contexts per domain
- Strict dependency direction (no circular imports)
- Service layer as the only entry point for business logic
- Thin views and fat services
- Domain events for cross-context communication
- Shared kernel for truly common utilities only
- Preparation layers for future service extraction

## Alternatives
1. **Full microservices**
   - High operational overhead
   - Distributed system complexity (transactions, consistency, latency)
   - Rejected for current scale and team size

2. **Keep status quo indefinitely**
   - Accumulating coupling makes future extraction harder
   - Rejected: architectural drift risk

3. **Modular monolith with enforced boundaries**
   - Single deployment, multiple deployable modules
   - Clear contracts between modules
   - Accepted: best balance for current maturity

## Consequences
- Teams can work on bounded contexts with minimal coordination overhead
- Future service extraction becomes a configuration change, not a rewrite
- Import-linter contracts become the architecture enforcement mechanism
- Shared kernel is minimized to prevent coupling
- Domain events replace direct cross-context calls over time

## Migration Notes
Transformation occurs across 30+ phases. Each phase:
1. Extracts a bounded context into its own package structure
2. Enforces dependency rules via import-linter
3. Adds contract tests between contexts
4. Keeps production behavior identical

No breaking changes to external APIs during the transformation.

## References
- [Architecture README](../../docs/architecture/README.md)
- [Architecture Principles](../ARCHITECTURE_PRINCIPLES.md)
- [Roadmap](../ROADMAP.md)
- Existing ADRs in `docs/adr/`
