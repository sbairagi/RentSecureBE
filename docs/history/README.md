# Architecture History

This directory contains the evolution history of the RentSecureBE architecture.

## Current Version

- **Version:** 2.4.0
- **Date:** 2026-07-13
- **Changed Modules:** settings, workflows, CI contract, ADR, AI governance, UML automation
- **Architecture Score:** See architecture scorecard
- **Updated Diagrams:** See architecture/ directory
- **Dependency Changes:** Added uml and uml-validation jobs

## History Log

| Version | Date | Changed Modules | Architecture Score | Updated Diagrams | Dependency Changes |
|---------|------|-----------------|-------------------|------------------|-------------------|
| 2.4.0 | 2026-07-13 | settings, workflows, CI contract, ADR, AI governance, UML automation | N/A | architecture/, docs/uml/, docs/diagrams/ | Added uml and uml-validation jobs |
| 2.3.0 | 2026-06-26 | CI contract, architecture guard | N/A | architecture-dependency-graph.dot, .mmd | Added architecture-guard.yml |
| 2.0.0 | 2026-01-15 | Initial architecture contract | N/A | N/A | Initial CI/CD pipeline |

## How to Update

When architecture changes:
1. Update version in scripts/architecture_contract.py
2. Add entry to this history log
3. Update architecture scorecard
4. Regenerate diagrams via CI
