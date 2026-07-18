# Current Architecture

## Status
Accepted

## Date
2026-07-14

## Context
RentSecureBE is an existing Django + DRF backend that has reached a mature CI/CD state with 25+ GitHub Actions workflows, architecture guards, import-linter enforcement, and SonarCloud quality gates. The system is currently a modular monolith with well-defined Django apps.

## Problem
Document the current architecture accurately to serve as the baseline for a 30+ phase long-term architecture transformation.

## Decision
The current architecture is a **Modular Monolith** implemented with Django 5.2 + DRF, organized into domain-focused Django apps with a service layer pattern, Redis caching, Celery background tasks, and PostgreSQL persistence.

## Alternatives
1. **Microservices now**
   - Would require immediate infrastructure overhaul
   - High operational complexity for current team size
   - Rejected: too risky for a stable production system

2. **Leave undocumented**
   - Would make future refactoring impossible
   - Rejected: knowledge loss and architectural drift

3. **Document and evolve**
   - Accepted: establish baseline and transform in controlled phases

## Consequences
- All future phases build on this documented baseline
- No breaking changes to production APIs or models
- CI behavior, imports, and GitHub Actions remain unchanged
- Architecture reports are documented but left in current locations to avoid breaking CI scripts

## Migration Notes
No migration required. This is a documentation-only phase. Production code, APIs, serializers, models, migrations, CI behavior, GitHub Actions, Sonar configuration, and Import-Linter configuration remain untouched.

## References
- [Architecture README](../../docs/architecture/README.md)
- [Architecture Principles](../ARCHITECTURE_PRINCIPLES.md)
- [Coding Standards](../CODING_STANDARDS.md)
- [Roadmap](../ROADMAP.md)
- Existing ADRs in `docs/adr/`
