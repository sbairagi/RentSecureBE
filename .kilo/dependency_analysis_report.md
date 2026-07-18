# Reference Tracing Analysis - Structured Dependency Map
Repository: /Users/sbairagi/Desktop/MVP Project/RentSecureBE
Analysis Date: 2026-07-18
Total files analyzed: 73

## Executive Summary

| # | File Path | Exists | Incoming | Outgoing | Risk Level | Notes |
|---|-----------|--------|----------|----------|------------|-------|
| 1 | README.md | YES | 357 | 26 | HIGH | Highly referenced (357); Heavy outgoing (26) |
| 2 | architecture/ARCHITECTURE_PRINCIPLES.md | YES | 63 | 0 | MEDIUM | Highly referenced (63) |
| 3 | architecture/CODING_STANDARDS.md | YES | 39 | 0 | MEDIUM | Highly referenced (39) |
| 4 | architecture/ROADMAP.md | YES | 44 | 0 | MEDIUM | Highly referenced (44) |
| 5 | architecture/adr/000-template.md | YES | 3 | 0 | MEDIUM | - |
| 6 | architecture/adr/001-current-architecture.md | YES | 19 | 4 | HIGH | Highly referenced (19) |
| 7 | architecture/adr/002-target-architecture.md | YES | 11 | 3 | HIGH | Highly referenced (11) |
| 8 | architecture/adr/003-refactoring-strategy.md | YES | 11 | 3 | HIGH | Highly referenced (11) |
| 9 | architecture/dependency-rules.md | YES | 37 | 0 | MEDIUM | Highly referenced (37) |
| 10 | architecture/generated/architecture.json | YES | 50 | 0 | MEDIUM | Highly referenced (50) |
| 11 | architecture/import-layers.md | YES | 27 | 0 | MEDIUM | Highly referenced (27) |
| 12 | architecture/module-boundaries.md | YES | 33 | 0 | MEDIUM | Highly referenced (33) |
| 13 | docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md | YES | 23 | 1 | HIGH | Highly referenced (23) |
| 14 | docs/README.md | YES | 40 | 20 | HIGH | Highly referenced (40); Heavy outgoing (20) |
| 15 | docs/adr/README.md | YES | 39 | 0 | MEDIUM | Highly referenced (39) |
| 16 | docs/ai-governance/AI-Architecture-Review.md | YES | 11 | 0 | MEDIUM | Highly referenced (11) |
| 17 | docs/architecture/README.md | YES | 83 | 0 | MEDIUM | Highly referenced (83) |
| 18 | docs/architecture/architecture-audit-report.md | NO | 21 | 0 | N/A | Missing at specified path; Highly referenced (21) |
| 19 | docs/architecture/audit_data.json | YES | 16 | 0 | MEDIUM | Highly referenced (16) |
| 20 | docs/architecture/future/02_bounded_contexts.md | YES | 19 | 0 | MEDIUM | Highly referenced (19) |
| 21 | docs/architecture/future/05_dependency_rules.md | YES | 28 | 0 | MEDIUM | Highly referenced (28) |
| 22 | docs/business-rules/00-overview.md | YES | 14 | 0 | MEDIUM | Highly referenced (14) |
| 23 | docs/business-rules/02-subscription-and-usage-limits.md | YES | 12 | 1 | HIGH | Highly referenced (12) |
| 24 | docs/business-rules/14-known-behaviors-and-edge-cases.md | YES | 9 | 2 | HIGH | - |
| 25 | docs/business-rules/15-authentication.md | YES | 9 | 1 | HIGH | - |
| 26 | docs/business-rules/16-payments-and-webhooks.md | YES | 10 | 2 | HIGH | - |
| 27 | docs/business-rules/17-notifications.md | YES | 6 | 2 | HIGH | - |
| 28 | docs/business-rules/22-signals-and-automation.md | YES | 12 | 2 | HIGH | Highly referenced (12) |
| 29 | docs/business-rules/README.md | YES | 38 | 24 | HIGH | Highly referenced (38); Heavy outgoing (24) |
| 30 | docs/ci-cd-upgrade-report.md | NO | 19 | 0 | N/A | Missing at specified path; Highly referenced (19) |
| 31 | docs/history/generated/architecture.json | NO | 14 | 0 | N/A | Missing at specified path; Highly referenced (14) |
| 32 | docs/rag/README.md | YES | 28 | 25 | HIGH | Highly referenced (28); Heavy outgoing (25) |
| 33 | docs/rag/api-authentication.md | YES | 1 | 0 | MEDIUM | - |
| 34 | docs/rag/api-finance-documents.md | YES | 1 | 0 | MEDIUM | - |
| 35 | docs/rag/api-properties-owner.md | YES | 1 | 0 | MEDIUM | - |
| 36 | docs/rag/api-properties-renter.md | YES | 1 | 0 | MEDIUM | - |
| 37 | docs/rag/business-rules-pointer.md | YES | 1 | 0 | MEDIUM | - |
| 38 | docs/rag/data-model-core.md | YES | 1 | 0 | MEDIUM | - |
| 39 | docs/rag/data-model-properties.md | YES | 1 | 0 | MEDIUM | - |
| 40 | docs/rag/development-runbook.md | YES | 1 | 0 | MEDIUM | - |
| 41 | docs/rag/django-apps-inventory.md | YES | 1 | 0 | MEDIUM | - |
| 42 | docs/rag/entity-relationships.md | YES | 1 | 0 | MEDIUM | - |
| 43 | docs/rag/environment-configuration.md | YES | 1 | 0 | MEDIUM | - |
| 44 | docs/rag/external-integrations.md | YES | 1 | 0 | MEDIUM | - |
| 45 | docs/rag/glossary.md | YES | 1 | 0 | MEDIUM | - |
| 46 | docs/rag/known-issues-for-ai.md | YES | 1 | 0 | MEDIUM | - |
| 47 | docs/rag/manifest.json | YES | 1 | 0 | MEDIUM | - |
| 48 | docs/rag/notifications-and-reminders.md | YES | 5 | 0 | MEDIUM | - |
| 49 | docs/rag/payments-razorpay-cashfree.md | YES | 8 | 0 | MEDIUM | - |
| 50 | docs/rag/project-summary.md | YES | 5 | 0 | MEDIUM | - |
| 51 | docs/rag/referral-program.md | YES | 3 | 0 | MEDIUM | - |
| 52 | docs/rag/repository-structure.md | YES | 2 | 0 | MEDIUM | - |
| 53 | docs/rag/signals-celery-commands.md | YES | 1 | 0 | MEDIUM | - |
| 54 | docs/rag/smartbot-and-ai-assistant.md | YES | 1 | 0 | MEDIUM | - |
| 55 | docs/rag/subscription-and-limits.md | YES | 1 | 0 | MEDIUM | - |
| 56 | docs/rag/tech-stack.md | YES | 3 | 0 | MEDIUM | - |
| 57 | docs/refactoring/00_architecture_principles.md | YES | 16 | 11 | HIGH | Highly referenced (16); Heavy outgoing (11) |
| 58 | docs/refactoring/01_target_architecture.md | YES | 12 | 21 | HIGH | Highly referenced (12); Heavy outgoing (21) |
| 59 | docs/refactoring/02_migration_roadmap.md | YES | 14 | 18 | HIGH | Highly referenced (14); Heavy outgoing (18) |
| 60 | docs/refactoring/02_verified_dead_code_report.md | YES | 4 | 0 | MEDIUM | - |
| 61 | docs/refactoring/03_dead_code_cleanup_execution_plan.md | YES | 0 | 0 | LOW | Isolated |
| 62 | docs/refactoring/04_final_production_safety_report.md | YES | 0 | 0 | LOW | Isolated |
| 63 | docs/refactoring/05_dependency_rules.md | NO | 16 | 0 | N/A | Missing at specified path; Highly referenced (16) |
| 64 | docs/refactoring/05_execution_report.md | YES | 0 | 0 | LOW | Isolated |
| 65 | docs/refactoring/06_architecture_audit.md | YES | 13 | 0 | MEDIUM | Highly referenced (13) |
| 66 | docs/refactoring/07_migration_plan.md | YES | 0 | 0 | LOW | Isolated |
| 67 | docs/refactoring/08_architecture_decisions.md | YES | 12 | 0 | MEDIUM | Highly referenced (12) |
| 68 | docs/refactoring/09_target_architecture.md | YES | 9 | 0 | MEDIUM | - |
| 69 | docs/refactoring/10_architecture_gap_analysis.md | YES | 5 | 0 | MEDIUM | - |
| 70 | docs/refactoring/11_architecture_roadmap_review.md | YES | 15 | 0 | MEDIUM | Highly referenced (15) |
| 71 | docs/refactoring/12_architecture_implementation_master_plan.md | YES | 15 | 0 | MEDIUM | Highly referenced (15) |
| 72 | properties/business_rules.md | YES | 44 | 1 | HIGH | Highly referenced (44) |
| 73 | scripts/diagrams/documentation_guardian.py | YES | 28 | 0 | MEDIUM | Highly referenced (28) |

## Detailed Dependency Map

### README.md

- **Exists:** YES
- **Incoming References:** 357
- **Outgoing References:** 26

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 21 | `- **Root-Level Generated Reports:** `architecture-compliance-report.*`, `architecture-dependency-graph.*`, and `archi...` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 54 | `\| `architecture-dependency-graph.{dot,mmd}` \| `scripts/architecture_contract.py` \| `architecture.yml`, documentati...` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 55 | `\| `architecture-summary.txt` \| `scripts/architecture_contract.py` \| `architecture.yml`, documentation \| `architec...` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 185 | `\| `architecture/reports/README.md` \| Root-level generated reports \|` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 186 | `\| `docs/architecture/README.md` \| `docs/architecture/audit_data.json`, `scripts/arch_audit.py` \|` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 187 | `\| `docs/history/README.md` \| Architecture version history \|` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 214 | `These are currently generated at the repository root but are explicitly documented as intended for `architecture/repo...` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 225 | `- Update `architecture/reports/README.md` to reflect new locations (or remove stale references)` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 372 | `This directory already contains a `README.md` documenting the intended migration of root-level generated reports. The...` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 674 | `- [ ] Update `architecture/reports/README.md` if root reports are moved` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 45 | `- `README.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 46 | `- `docs/README.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 58 | `- Module-level READMEs (`core/services/README.md`, `properties/repositories/README.md`, etc.)` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 163 | `\| `README.md` \| Project overview, quick start, tech stack \| Tech Lead \| All contributors \| Permanent \| NO \| NO...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 164 | `\| `docs/README.md` \| Documentation index \| Tech Lead \| All contributors \| Permanent \| NO \| NO \| CRITICAL \| N...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 347 | `- Documentation Guardian paths (e.g., `docs/adr/README.md`)` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 362 | `README.md (line 83)` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 363 | `└── docs/adr/README.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 367 | `└── docs/adr/README.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 371 | `└── docs/architecture/README.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 383 | `└── docs/architecture/README.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 386 | `└── docs/architecture/README.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 389 | `└── docs/adr/README.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 416 | `- Links from `docs/README.md` to subdirectories` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 417 | `- Links from `docs/business-rules/README.md` to individual files` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 472 | `1. **Create a README.md** in the original location with:` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 480 | `2. **Create a README.md** in the archive location with:` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 759 | `- 'README.md'` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 823 | `\| `README.md` \| **CANONICAL** \| Main project README, referenced by all \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 824 | `\| `docs/README.md` \| **CANONICAL** \| Documentation index \|` |
| ... | ... | *... and 327 more* |

**Outgoing References:**

| Line | Type | Target | Context |
|------|------|--------|---------|
| 3 | markdown_link | `https://img.shields.io/badge/Django-5.2-green` | `![Django](https://img.shields.io/badge/Django-5.2-green)` |
| 4 | markdown_link | `https://img.shields.io/badge/DRF-3.16-blue` | `![DRF](https://img.shields.io/badge/DRF-3.16-blue)` |
| 5 | markdown_link | `https://img.shields.io/badge/PostgreSQL-Production-blue` | `![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Production-blue)` |
| 6 | markdown_link | `https://img.shields.io/badge/AWS-EC2-orange` | `![AWS](https://img.shields.io/badge/AWS-EC2-orange)` |
| 7 | markdown_link | `https://img.shields.io/badge/CI-GitHub_Actions-black` | `![CI](https://img.shields.io/badge/CI-GitHub_Actions-black)` |
| 17 | markdown_link | `docs/diagrams/generated/infrastructure/cicd-pipeline.puml` | `![CI/CD Pipeline](docs/diagrams/generated/infrastructure/cicd-pipeline.puml)` |
| 18 | markdown_link | `docs/diagrams/generated/c4/c4-context.puml` | `![C4 Context](docs/diagrams/generated/c4/c4-context.puml)` |
| 19 | markdown_link | `docs/diagrams/generated/c4/c4-container.puml` | `![C4 Container](docs/diagrams/generated/c4/c4-container.puml)` |
| 67 | markdown_link | `docs/ci-cd-pipeline.md` | `See [docs/ci-cd-pipeline.md](docs/ci-cd-pipeline.md) for details.` |
| 73 | markdown_link | `docs/uml/` | `- [docs/uml/](docs/uml/) — PlantUML and Mermaid diagrams` |
| 74 | markdown_link | `docs/diagrams/` | `- [docs/diagrams/](docs/diagrams/) — C4, flow, infrastructure diagrams` |
| 78 | markdown_link | `docs/architecture-contract.md` | `- [Architecture Contract](docs/architecture-contract.md)` |
| 79 | markdown_link | `docs/governance.md` | `- [CI/CD Governance](docs/governance.md)` |
| 80 | markdown_link | `docs/business-rules/README.md` | `- [Business Rules](docs/business-rules/README.md)` |
| 81 | markdown_link | `docs/ai-governance/README.md` | `- [AI Governance](docs/ai-governance/README.md)` |
| 82 | markdown_link | `docs/adr/README.md` | `- [ADR Index](docs/adr/README.md)` |
| 139 | markdown_link | `docs/uml/` | `> Diagrams are generated automatically by CI. See the [UML Diagrams](docs/uml/) and [Diagrams](docs/diagrams/) sectio...` |
| 139 | markdown_link | `docs/diagrams/` | `> Diagrams are generated automatically by CI. See the [UML Diagrams](docs/uml/) and [Diagrams](docs/diagrams/) sectio...` |
| 141 | markdown_link | `docs/uml/` | `- [PlantUML Diagrams](docs/uml/)` |
| 142 | markdown_link | `docs/uml/` | `- [Mermaid Diagrams](docs/uml/)` |
| 143 | markdown_link | `docs/diagrams/generated/c4/` | `- [C4 Diagrams](docs/diagrams/generated/c4/)` |
| 144 | markdown_link | `docs/uml/generated/domain/` | `- [Domain Diagrams](docs/uml/generated/domain/)` |
| 145 | markdown_link | `docs/diagrams/generated/flows/` | `- [Flow Diagrams](docs/diagrams/generated/flows/)` |
| 146 | markdown_link | `docs/diagrams/generated/infrastructure/` | `- [Infrastructure Diagrams](docs/diagrams/generated/infrastructure/)` |
| 147 | markdown_link | `docs/uml/generated/ddd/` | `- [DDD Diagrams](docs/uml/generated/ddd/)` |
| 151 | markdown_link | `docs/ai-governance/AI-Contribution-Guide.md` | `See [docs/ai-governance/AI-Contribution-Guide.md](docs/ai-governance/AI-Contribution-Guide.md) for contribution guide...` |

---

### architecture/ARCHITECTURE_PRINCIPLES.md

- **Exists:** YES
- **Incoming References:** 63
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 59 | `- `architecture/ARCHITECTURE_PRINCIPLES.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 374 | `└── architecture/ARCHITECTURE_PRINCIPLES.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 838 | `\| `architecture/ARCHITECTURE_PRINCIPLES.md` \| **CANONICAL** \| Referenced by 4 architecture/adr files \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 915 | `\| `architecture/ARCHITECTURE_PRINCIPLES.md` \| **ARCHIVE CANDIDATE** \| Superseded by docs/refactoring/00, 14 ADR re...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 943 | `\| `architecture/ARCHITECTURE_PRINCIPLES.md` \| Referenced by 4 architecture/adr files. Must remain or all ADR refere...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 984 | `\| `architecture/ARCHITECTURE_PRINCIPLES.md` \| Update 4 architecture/adr file references \| Superseded by docs/refac...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1118 | `5. Update `architecture/adr/001-current-architecture.md` line 42: `architecture/ARCHITECTURE_PRINCIPLES.md` — keep re...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1156 | `- `architecture/ARCHITECTURE_PRINCIPLES.md` → `docs/archive/planning/architecture-principles-concise.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1698 | `├── architecture/ARCHITECTURE_PRINCIPLES.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1728 | `architecture/ARCHITECTURE_PRINCIPLES.md` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 67 | `\| `architecture/ARCHITECTURE_PRINCIPLES.md` \| 1 \| Canonical (duplicate of docs/refactoring) \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 143 | `\| `architecture/ARCHITECTURE_PRINCIPLES.md` \| architecture/ \| 2.6 KB \| Concise principles (18 items) \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 149 | `- `architecture/ARCHITECTURE_PRINCIPLES.md` is a concise summary.` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 154 | `- **ARCHIVE** `architecture/ARCHITECTURE_PRINCIPLES.md` (duplicate/summary).` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 385 | `\| `architecture/ARCHITECTURE_PRINCIPLES.md` \| ARCHIVE \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 472 | `\| B \| Two versions: concise (`architecture/ARCHITECTURE_PRINCIPLES.md`) + detailed (`docs/refactoring/...`) \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 624 | `│   │   ├── architecture-principles-concise.md  # From architecture/ARCHITECTURE_PRINCIPLES.md` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 742 | `9. Move `architecture/ARCHITECTURE_PRINCIPLES.md` to `docs/archive/planning/architecture-principles-concise.md`` |
| PHASE_2_1_ARCHIVE_REPORT.md | 164 | `\| `architecture/ARCHITECTURE_PRINCIPLES.md` \| **PENDING** \| Requires 4 ADR reference updates first \|` |
| PHASE_1_1_REPAIR_REPORT.md | 41 | `\| `architecture/adr/001-current-architecture.md` \| Modified \| Fixed relative paths: `architecture/ARCHITECTURE_PRI...` |
| PHASE_1_1_REPAIR_REPORT.md | 42 | `\| `architecture/adr/002-target-architecture.md` \| Modified \| Fixed relative paths: `architecture/ARCHITECTURE_PRIN...` |
| PHASE_1_1_REPAIR_REPORT.md | 43 | `\| `architecture/adr/003-refactoring-strategy.md` \| Modified \| Fixed relative paths: `docs/architecture/README.md` ...` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 71 | `\| `architecture/ARCHITECTURE_PRINCIPLES.md` \| OK \|` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 358 | `\| `architecture/ARCHITECTURE_PRINCIPLES.md` \| architecture/adr/* (4 files) \| Update 4 ADR references first \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 336 | `\| Architecture Principles \| `docs/refactoring/00_architecture_principles.md` \| `architecture/ARCHITECTURE_PRINCIPL...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 400 | `\| Concise Principles \| `architecture/ARCHITECTURE_PRINCIPLES.md` \| ~2.6 KB \| Summary \| No \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 403 | `**Analysis:** `docs/refactoring/00_architecture_principles.md` is the supreme authority (51.7 KB, ratified 2026-07-15...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 405 | `**Recommendation:** Keep `docs/refactoring/00_architecture_principles.md` as canonical. Archive `architecture/ARCHITE...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 715 | `\| `architecture/ARCHITECTURE_PRINCIPLES.md` \| Concise duplicate \| Update 14 ADR references \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 938 | `20. Update all 14 ADR files in `docs/architecture/adr/` that reference `architecture/ARCHITECTURE_PRINCIPLES.md`` |
| ... | ... | *... and 33 more* |

**Outgoing References:**

*No outgoing references found.*

---

### architecture/CODING_STANDARDS.md

- **Exists:** YES
- **Incoming References:** 39
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 64 | `- `architecture/CODING_STANDARDS.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 377 | `└── architecture/CODING_STANDARDS.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 843 | `\| `architecture/CODING_STANDARDS.md` \| **CANONICAL** \| Referenced by 1 architecture/adr file \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 920 | `\| `architecture/CODING_STANDARDS.md` \| **ARCHIVE CANDIDATE** \| Superseded by docs/refactoring/10, 1 ADR ref must u...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 947 | `\| `architecture/CODING_STANDARDS.md` \| Referenced by 1 architecture/adr file. \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 988 | `\| `architecture/CODING_STANDARDS.md` \| Update 1 architecture/adr file reference \| Superseded by docs/refactoring/1...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1119 | `6. Update `architecture/adr/001-current-architecture.md` line 43: `architecture/CODING_STANDARDS.md` — keep reference...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1160 | `- `architecture/CODING_STANDARDS.md` → `docs/archive/planning/coding-standards.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1699 | `├── architecture/CODING_STANDARDS.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1748 | `architecture/CODING_STANDARDS.md` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 68 | `\| `architecture/CODING_STANDARDS.md` \| 1 \| Canonical (duplicate) \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 222 | `\| `architecture/CODING_STANDARDS.md` \| architecture/ \| 4.9 KB \| Concise coding standards \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 227 | `- **ARCHIVE** `architecture/CODING_STANDARDS.md` (superseded).` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 386 | `\| `architecture/CODING_STANDARDS.md` \| ARCHIVE \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 625 | `│   │   ├── coding-standards.md         # From architecture/CODING_STANDARDS.md` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 743 | `10. Move `architecture/CODING_STANDARDS.md` to `docs/archive/planning/coding-standards.md`` |
| PHASE_2_1_ARCHIVE_REPORT.md | 168 | `\| `architecture/CODING_STANDARDS.md` \| **PENDING** \| Requires 1 ADR reference update first \|` |
| PHASE_1_1_REPAIR_REPORT.md | 41 | `\| `architecture/adr/001-current-architecture.md` \| Modified \| Fixed relative paths: `architecture/ARCHITECTURE_PRI...` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 76 | `\| `architecture/CODING_STANDARDS.md` \| OK \|` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 362 | `\| `architecture/CODING_STANDARDS.md` \| architecture/adr/* (1 file) \| Update 1 ADR reference first \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 344 | `\| Naming Conventions \| `docs/refactoring/10_naming_conventions.md` \| `architecture/CODING_STANDARDS.md` \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 345 | `\| Coding Standards \| `docs/refactoring/10_naming_conventions.md` \| `architecture/CODING_STANDARDS.md` \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 458 | `\| Coding Standards \| `architecture/CODING_STANDARDS.md` \| ~4.9 KB \| Concise \| No \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 460 | `**Recommendation:** Keep `docs/refactoring/10_naming_conventions.md`. Archive `architecture/CODING_STANDARDS.md` afte...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 719 | `\| `architecture/CODING_STANDARDS.md` \| Concise duplicate \| Update 1 ADR reference \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 942 | `24. Update all 1 ADR file that references `architecture/CODING_STANDARDS.md`` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 964 | `31. Move `architecture/CODING_STANDARDS.md` to `docs/archive/planning/coding-standards.md`` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 77 | `\| `architecture/CODING_STANDARDS.md` \| ARCHIVE \| **KEEP** or update 1 ADR reference first \| Referenced by 1 ADR i...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 124 | `- `architecture/CODING_STANDARDS.md` → 1 ADR reference` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 272 | `27. Move `architecture/CODING_STANDARDS.md` to `docs/archive/planning/coding-standards.md`` |
| ... | ... | *... and 9 more* |

**Outgoing References:**

*No outgoing references found.*

---

### architecture/ROADMAP.md

- **Exists:** YES
- **Incoming References:** 44
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 60 | `- `architecture/ROADMAP.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 380 | `└── architecture/ROADMAP.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 839 | `\| `architecture/ROADMAP.md` \| **CANONICAL** \| Referenced by 3 architecture/adr files \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 916 | `\| `architecture/ROADMAP.md` \| **ARCHIVE CANDIDATE** \| Superseded by docs/refactoring/12, 3 ADR refs must update \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 944 | `\| `architecture/ROADMAP.md` \| Referenced by 3 architecture/adr files. \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 985 | `\| `architecture/ROADMAP.md` \| Update 3 architecture/adr file references \| Superseded by docs/refactoring/12_archit...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1120 | `7. Update `architecture/adr/001-current-architecture.md` line 44: `architecture/ROADMAP.md` — keep reference (file st...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1157 | `- `architecture/ROADMAP.md` → `docs/archive/planning/roadmap.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1700 | `├── architecture/ROADMAP.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1734 | `architecture/ROADMAP.md` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 69 | `\| `architecture/ROADMAP.md` \| 1 \| Canonical (duplicate of docs/refactoring) \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 161 | `\| `architecture/ROADMAP.md` \| architecture/ \| 8.8 KB \| Concise roadmap (13 phases) \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 169 | `- `architecture/ROADMAP.md` is referenced by `docs/architecture/README.md` but does not exist at the expected path.` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 173 | `- **ARCHIVE** `architecture/ROADMAP.md` (superseded).` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 387 | `\| `architecture/ROADMAP.md` \| ARCHIVE \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 744 | `11. Move `architecture/ROADMAP.md` to `docs/archive/planning/roadmap.md`` |
| PHASE_2_1_ARCHIVE_REPORT.md | 165 | `\| `architecture/ROADMAP.md` \| **PENDING** \| Requires 3 ADR reference updates first \|` |
| PHASE_1_1_REPAIR_REPORT.md | 41 | `\| `architecture/adr/001-current-architecture.md` \| Modified \| Fixed relative paths: `architecture/ARCHITECTURE_PRI...` |
| PHASE_1_1_REPAIR_REPORT.md | 42 | `\| `architecture/adr/002-target-architecture.md` \| Modified \| Fixed relative paths: `architecture/ARCHITECTURE_PRIN...` |
| PHASE_1_1_REPAIR_REPORT.md | 43 | `\| `architecture/adr/003-refactoring-strategy.md` \| Modified \| Fixed relative paths: `docs/architecture/README.md` ...` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 72 | `\| `architecture/ROADMAP.md` \| OK \|` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 359 | `\| `architecture/ROADMAP.md` \| architecture/adr/* (3 files) \| Update 3 ADR references first \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 338 | `\| Migration Roadmap \| `docs/refactoring/12_architecture_implementation_master_plan.md` \| `architecture/ROADMAP.md`...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 412 | `\| Concise Roadmap \| `architecture/ROADMAP.md` \| ~8.8 KB \| Phase 0 baseline \| No \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 416 | `**Analysis:** Four roadmap documents with significant overlap. `docs/refactoring/12_architecture_implementation_maste...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 418 | `**Recommendation:** Keep `docs/refactoring/12_architecture_implementation_master_plan.md` as canonical. Archive `arch...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 716 | `\| `architecture/ROADMAP.md` \| Concise roadmap \| Update 3 ADR references \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 939 | `21. Update all 3 ADR files that reference `architecture/ROADMAP.md`` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 961 | `28. Move `architecture/ROADMAP.md` to `docs/archive/planning/roadmap.md`` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 33 | `\| `architecture/ROADMAP.md` \| 3 files in `architecture/adr/` \| Breaks archived ADR references \|` |
| ... | ... | *... and 14 more* |

**Outgoing References:**

*No outgoing references found.*

---

### architecture/adr/000-template.md

- **Exists:** YES
- **Incoming References:** 3
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 445 | `\| `../adr/ADR-template.md` \| `docs/architecture/README.md` \| Fix path to `architecture/adr/000-template.md` \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 524 | `\| `docs/architecture/README.md` \| `../adr/ADR-template.md` \| File does not exist \| Update to `architecture/adr/00...` |
| docs/architecture/adr/README.md | 38 | `2. Use the template from `architecture/adr/000-template.md`` |

**Outgoing References:**

*No outgoing references found.*

---

### architecture/adr/001-current-architecture.md

- **Exists:** YES
- **Incoming References:** 19
- **Outgoing References:** 4

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 370 | `architecture/adr/001-current-architecture.md (line 45)` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 373 | `architecture/adr/001-current-architecture.md (line 42)` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 376 | `architecture/adr/001-current-architecture.md (line 43)` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 379 | `architecture/adr/001-current-architecture.md (line 44)` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1117 | `4. Update `architecture/adr/001-current-architecture.md` line 45: `docs/architecture/README.md` → `docs/refactoring/1...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1118 | `5. Update `architecture/adr/001-current-architecture.md` line 42: `architecture/ARCHITECTURE_PRINCIPLES.md` — keep re...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1119 | `6. Update `architecture/adr/001-current-architecture.md` line 43: `architecture/CODING_STANDARDS.md` — keep reference...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1120 | `7. Update `architecture/adr/001-current-architecture.md` line 44: `architecture/ROADMAP.md` — keep reference (file st...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1720 | `← architecture/adr/001-current-architecture.md (line 45)` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1729 | `← architecture/adr/001-current-architecture.md (line 42)` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1735 | `← architecture/adr/001-current-architecture.md (line 44)` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1740 | `← architecture/adr/001-current-architecture.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1746 | `← architecture/adr/001-current-architecture.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1749 | `← architecture/adr/001-current-architecture.md` |
| PHASE_1_1_REPAIR_REPORT.md | 41 | `\| `architecture/adr/001-current-architecture.md` \| Modified \| Fixed relative paths: `architecture/ARCHITECTURE_PRI...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 935 | `17. Update `architecture/adr/001-current-architecture.md` lines 41-45: Update references to archived files` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 151 | `- `architecture/adr/001-current-architecture.md` (line 45)` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 241 | `16. Update `architecture/adr/001-current-architecture.md` lines 41-45: Update references to archived files` |
| PHASE_0_VALIDATION_REPORT.md | 463 | `- Update `architecture/adr/001-current-architecture.md` line 45.` |

**Outgoing References:**

| Line | Type | Target | Context |
|------|------|--------|---------|
| 41 | markdown_link | `../../docs/architecture/README.md` | `- [Architecture README](../../docs/architecture/README.md)` |
| 42 | markdown_link | `../ARCHITECTURE_PRINCIPLES.md` | `- [Architecture Principles](../ARCHITECTURE_PRINCIPLES.md)` |
| 43 | markdown_link | `../CODING_STANDARDS.md` | `- [Coding Standards](../CODING_STANDARDS.md)` |
| 44 | markdown_link | `../ROADMAP.md` | `- [Roadmap](../ROADMAP.md)` |

---

### architecture/adr/002-target-architecture.md

- **Exists:** YES
- **Incoming References:** 11
- **Outgoing References:** 3

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 382 | `architecture/adr/002-target-architecture.md (line 61)` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1121 | `8. Update `architecture/adr/002-target-architecture.md` line 61: `docs/architecture/README.md` → canonical architectu...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1721 | `← architecture/adr/002-target-architecture.md (line 61)` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1730 | `← architecture/adr/002-target-architecture.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1736 | `← architecture/adr/002-target-architecture.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1741 | `← architecture/adr/002-target-architecture.md` |
| PHASE_1_1_REPAIR_REPORT.md | 42 | `\| `architecture/adr/002-target-architecture.md` \| Modified \| Fixed relative paths: `architecture/ARCHITECTURE_PRIN...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 936 | `18. Update `architecture/adr/002-target-architecture.md` lines 58-65: Update references to archived files` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 152 | `- `architecture/adr/002-target-architecture.md` (line 61)` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 242 | `17. Update `architecture/adr/002-target-architecture.md` lines 58-65: Update references to archived files` |
| PHASE_0_VALIDATION_REPORT.md | 464 | `- Update `architecture/adr/002-target-architecture.md` line 61.` |

**Outgoing References:**

| Line | Type | Target | Context |
|------|------|--------|---------|
| 58 | markdown_link | `../../docs/architecture/README.md` | `- [Architecture README](../../docs/architecture/README.md)` |
| 59 | markdown_link | `../ARCHITECTURE_PRINCIPLES.md` | `- [Architecture Principles](../ARCHITECTURE_PRINCIPLES.md)` |
| 60 | markdown_link | `../ROADMAP.md` | `- [Roadmap](../ROADMAP.md)` |

---

### architecture/adr/003-refactoring-strategy.md

- **Exists:** YES
- **Incoming References:** 11
- **Outgoing References:** 3

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 385 | `architecture/adr/003-refactoring-strategy.md (line 65)` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1122 | `9. Update `architecture/adr/003-refactoring-strategy.md` line 65: `docs/architecture/README.md` → canonical architect...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1722 | `← architecture/adr/003-refactoring-strategy.md (line 65)` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1731 | `← architecture/adr/003-refactoring-strategy.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1737 | `← architecture/adr/003-refactoring-strategy.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1742 | `← architecture/adr/003-refactoring-strategy.md` |
| PHASE_1_1_REPAIR_REPORT.md | 43 | `\| `architecture/adr/003-refactoring-strategy.md` \| Modified \| Fixed relative paths: `docs/architecture/README.md` ...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 937 | `19. Update `architecture/adr/003-refactoring-strategy.md` lines 63-66: Update references to archived files` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 153 | `- `architecture/adr/003-refactoring-strategy.md` (line 65)` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 243 | `18. Update `architecture/adr/003-refactoring-strategy.md` lines 63-66: Update references to archived files` |
| PHASE_0_VALIDATION_REPORT.md | 465 | `- Update `architecture/adr/003-refactoring-strategy.md` line 65.` |

**Outgoing References:**

| Line | Type | Target | Context |
|------|------|--------|---------|
| 63 | markdown_link | `../../docs/architecture/README.md` | `- [Architecture README](../../docs/architecture/README.md)` |
| 64 | markdown_link | `../ROADMAP.md` | `- [Roadmap](../ROADMAP.md)` |
| 65 | markdown_link | `../ARCHITECTURE_PRINCIPLES.md` | `- [Architecture Principles](../ARCHITECTURE_PRINCIPLES.md)` |

---

### architecture/dependency-rules.md

- **Exists:** YES
- **Incoming References:** 37
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 61 | `- `architecture/dependency-rules.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 840 | `\| `architecture/dependency-rules.md` \| **CANONICAL** \| Referenced by 3 architecture/adr files + 1 audit report \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 917 | `\| `architecture/dependency-rules.md` \| **ARCHIVE CANDIDATE** \| Superseded by docs/refactoring/05, 4 refs must upda...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 945 | `\| `architecture/dependency-rules.md` \| Referenced by 3 architecture/adr files + `docs/architecture/05_architecture_...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 986 | `\| `architecture/dependency-rules.md` \| Update 3 architecture/adr file references + docs/architecture/05 reference \...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1158 | `- `architecture/dependency-rules.md` → `docs/archive/planning/dependency-rules.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1739 | `architecture/dependency-rules.md` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 70 | `\| `architecture/dependency-rules.md` \| 1 \| Canonical (duplicate) \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 181 | `\| `architecture/dependency-rules.md` \| architecture/ \| 5.5 KB \| Concise dependency rules \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 187 | `- `architecture/dependency-rules.md` is a concise version.` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 192 | `- **ARCHIVE** `architecture/dependency-rules.md` (superseded).` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 388 | `\| `architecture/dependency-rules.md` \| ARCHIVE \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 626 | `│   │   ├── dependency-rules.md         # From architecture/dependency-rules.md` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 745 | `12. Move `architecture/dependency-rules.md` to `docs/archive/planning/dependency-rules.md`` |
| PHASE_2_1_ARCHIVE_REPORT.md | 166 | `\| `architecture/dependency-rules.md` \| **PENDING** \| Requires 4 reference updates first \|` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 73 | `\| `architecture/dependency-rules.md` \| OK \|` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 360 | `\| `architecture/dependency-rules.md` \| architecture/adr/* + docs/architecture/05 \| Update 4 references first \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 342 | `\| Dependency Rules \| `docs/refactoring/05_dependency_rules.md` \| `architecture/dependency-rules.md`, `docs/archite...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 426 | `\| Concise Dependency Rules \| `architecture/dependency-rules.md` \| ~5.5 KB \| Concise \| No \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 430 | `**Recommendation:** Keep both files in place (do not delete the duplicate). Archive `architecture/dependency-rules.md...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 717 | `\| `architecture/dependency-rules.md` \| Concise duplicate \| Update 4 references (3 ADRs + 1 audit) \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 940 | `22. Update all 3 ADR files that reference `architecture/dependency-rules.md`` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 962 | `29. Move `architecture/dependency-rules.md` to `docs/archive/planning/dependency-rules.md`` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 34 | `\| `architecture/dependency-rules.md` \| 3 canonical ADR files + `docs/architecture/05_architecture_boundary_violatio...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 74 | `\| `architecture/dependency-rules.md` \| ARCHIVE \| **KEEP** or update 4 references first \| Referenced by 3 ADRs + 1...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 122 | `- `architecture/dependency-rules.md` → 3 ADR references + 1 audit report` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 270 | `25. Move `architecture/dependency-rules.md` to `docs/archive/planning/dependency-rules.md`` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 347 | `\| `architecture/dependency-rules.md` \| Referenced by 3 ADRs + 1 audit report \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 378 | `\| Archive `architecture/dependency-rules.md` \| **LOW** \| 4 references must be updated first \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 444 | `- `architecture/dependency-rules.md`` |
| ... | ... | *... and 7 more* |

**Outgoing References:**

*No outgoing references found.*

---

### architecture/generated/architecture.json

- **Exists:** YES
- **Incoming References:** 50
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 16 | `- **Single Source of Truth:** `architecture/generated/architecture.json` is the central metadata file consumed by all...` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 39 | `\| `architecture/generated/architecture.json` \| `scripts/diagrams/generate_uml_from_ast.py` \| All diagram generator...` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 94 | `\| `scripts/diagrams/generate_uml_from_ast.py` \| `architecture.json` \| `architecture/generated/architecture.json` \|` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 161 | `\| `scripts/diagrams/generate_plantuml.py` \| `architecture/generated/architecture.json` \|` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 162 | `\| `scripts/diagrams/generate_mermaid.py` \| `architecture/generated/architecture.json` \|` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 163 | `\| `scripts/diagrams/generate_c4.py` \| `architecture/generated/architecture.json` \|` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 164 | `\| `scripts/diagrams/generate_domain_diagrams.py` \| `architecture/generated/architecture.json` \|` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 165 | `\| `scripts/diagrams/generate_flow_diagrams.py` \| `architecture/generated/architecture.json` \|` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 166 | `\| `scripts/diagrams/generate_infrastructure_diagrams.py` \| `architecture/generated/architecture.json` \|` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 167 | `\| `scripts/diagrams/generate_ddd_diagrams.py` \| `architecture/generated/architecture.json` \|` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 168 | `\| `scripts/diagrams/generate_dependency_graph.py` \| `architecture/generated/architecture.json` \|` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 169 | `\| `scripts/diagrams/generate_architecture_metrics.py` \| `architecture/generated/architecture.json` \|` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 170 | `\| `scripts/diagrams/generate_architecture_summary.py` \| `architecture/generated/architecture.json` \|` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 175 | `\| `scripts/diagrams/validate_architecture_metadata.py` \| `architecture/generated/architecture.json` \|` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 229 | ``architecture/generated/architecture.json` is the single source of truth. **Do not relocate.** It is consumed by 9 ge...` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 339 | `\| `architecture/generated/architecture.json` \| **CRITICAL** \| Single source of truth; all generators depend on it \|` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 451 | `\| `architecture/generated/architecture.json` \| Single source of truth consumed by 9 generators + 3 CI workflows \|` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 461 | `\| `architecture/generated/architecture.json` \| JSON metadata \| `generate_uml_from_ast.py` \| 9 generators, 3 CI wo...` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 548 | `architecture/generated/architecture.json (SSOT)` |
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 604 | `└── architecture/generated/architecture.json` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 146 | `- `architecture/generated/architecture.json`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 886 | `\| `architecture/generated/architecture.json` \| **GENERATED** \| Generated architecture data \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 973 | `\| `architecture/generated/architecture.json` \| Generated architecture data. Zero external references. \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1085 | `- `architecture/generated/architecture.json` → `docs/archive/generated/architecture-generated/`` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 277 | `\| `architecture/generated/architecture.json` \| architecture/ \| 127.7 KB \| Generated architecture data \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 283 | `- **ARCHIVE** `architecture/generated/architecture.json` (superseded).` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 363 | `\| `architecture/generated/architecture.json` \| ARCHIVE \|` |
| PHASE_2_1_ARCHIVE_REPORT.md | 45 | `\| `architecture/generated/architecture.json` \| `.github/workflows/uml.yml` writes here \| CI generates this file \|` |
| PHASE_2_1_ARCHIVE_REPORT.md | 161 | `\| `architecture/generated/architecture.json` \| **NOT ARCHIVED** \| CI generates this file at this path \|` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 347 | `\| `architecture/generated/architecture.json` \| None \| SAFE \|` |
| ... | ... | *... and 20 more* |

**Outgoing References:**

*No outgoing references found.*

---

### architecture/import-layers.md

- **Exists:** YES
- **Incoming References:** 27
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 63 | `- `architecture/import-layers.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 842 | `\| `architecture/import-layers.md` \| **CANONICAL** \| Part of architecture baseline \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 919 | `\| `architecture/import-layers.md` \| **ARCHIVE CANDIDATE** \| Superseded by docs/refactoring/04, safe to archive \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 989 | `\| `architecture/import-layers.md` \| Verify zero references \| Concise import layers. Superseded by docs/refactoring...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1161 | `- `architecture/import-layers.md` → `docs/archive/planning/import-layers.md`` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 71 | `\| `architecture/import-layers.md` \| 1 \| Canonical (duplicate) \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 211 | `\| `architecture/import-layers.md` \| architecture/ \| 2.6 KB \| Concise import layers \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 216 | `- **ARCHIVE** `architecture/import-layers.md` (superseded).` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 389 | `\| `architecture/import-layers.md` \| ARCHIVE \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 627 | `│   │   ├── import-layers.md            # From architecture/import-layers.md` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 746 | `13. Move `architecture/import-layers.md` to `docs/archive/planning/import-layers.md`` |
| PHASE_2_1_ARCHIVE_REPORT.md | 169 | `\| `architecture/import-layers.md` \| **PENDING** \| Safe to archive, no dependencies \|` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 75 | `\| `architecture/import-layers.md` \| OK \|` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 363 | `\| `architecture/import-layers.md` \| None verified \| Safe to archive \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 341 | `\| Layer Rules \| `docs/refactoring/04_layer_rules.md` \| `architecture/import-layers.md` \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 449 | `\| Import Layers \| `architecture/import-layers.md` \| ~2.6 KB \| Concise \| No \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 451 | `**Recommendation:** Keep `docs/refactoring/04_layer_rules.md`. Archive `architecture/import-layers.md` (safe, 0 exter...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 704 | `\| `architecture/import-layers.md` \| Concise duplicate of `docs/refactoring/04_layer_rules.md` \| Verify 0 external ...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 965 | `32. Move `architecture/import-layers.md` to `docs/archive/planning/import-layers.md`` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 1038 | `\| Archiving `architecture/import-layers.md` \| **LOW** \| 0 external references found \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 76 | `\| `architecture/import-layers.md` \| ARCHIVE \| **KEEP** or verify no references \| Only referenced in plan (safe to...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 125 | `- `architecture/import-layers.md` → 0 external references (safe to archive)` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 273 | `28. Move `architecture/import-layers.md` to `docs/archive/planning/import-layers.md`` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 371 | `\| Archive `architecture/import-layers.md` \| **HIGH** \| No external references found \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 446 | `- `architecture/import-layers.md`` |
| PHASE_0_VALIDATION_REPORT.md | 62 | `\| `architecture/import-layers.md` \| Yes \| Yes \| ✅ PASS \|` |
| PHASE_0_VALIDATION_REPORT.md | 348 | `\| `architecture/import-layers.md` \| 0 verified \| No \| No \| No \| **SAFE** \| Zero external references found \|` |

**Outgoing References:**

*No outgoing references found.*

---

### architecture/module-boundaries.md

- **Exists:** YES
- **Incoming References:** 33
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 62 | `- `architecture/module-boundaries.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 841 | `\| `architecture/module-boundaries.md` \| **CANONICAL** \| Referenced by 1 architecture/adr file \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 918 | `\| `architecture/module-boundaries.md` \| **ARCHIVE CANDIDATE** \| Superseded by docs/refactoring/06, 1 ADR ref must ...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 946 | `\| `architecture/module-boundaries.md` \| Referenced by 1 architecture/adr file. \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 987 | `\| `architecture/module-boundaries.md` \| Update 1 architecture/adr file reference \| Superseded by docs/refactoring/...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1159 | `- `architecture/module-boundaries.md` → `docs/archive/planning/module-boundaries.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1745 | `architecture/module-boundaries.md` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 72 | `\| `architecture/module-boundaries.md` \| 1 \| Canonical (duplicate) \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 198 | `\| `architecture/module-boundaries.md` \| architecture/ \| 4.6 KB \| Concise module boundaries \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 204 | `- **ARCHIVE** `architecture/module-boundaries.md` (superseded).` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 390 | `\| `architecture/module-boundaries.md` \| ARCHIVE \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 628 | `│   │   ├── module-boundaries.md        # From architecture/module-boundaries.md` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 747 | `14. Move `architecture/module-boundaries.md` to `docs/archive/planning/module-boundaries.md`` |
| PHASE_2_1_ARCHIVE_REPORT.md | 167 | `\| `architecture/module-boundaries.md` \| **PENDING** \| Requires 1 ADR reference update first \|` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 74 | `\| `architecture/module-boundaries.md` \| OK \|` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 361 | `\| `architecture/module-boundaries.md` \| architecture/adr/* (1 file) \| Update 1 ADR reference first \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 343 | `\| Module Responsibilities \| `docs/refactoring/06_module_responsibilities.md` \| `architecture/module-boundaries.md`...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 438 | `\| Concise Boundaries \| `architecture/module-boundaries.md` \| ~4.6 KB \| Concise \| No \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 442 | `**Recommendation:** Keep `docs/architecture/future/02_bounded_contexts.md` as canonical reference. Keep `docs/refacto...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 718 | `\| `architecture/module-boundaries.md` \| Concise duplicate \| Update 1 ADR reference \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 941 | `23. Update all 1 ADR file that references `architecture/module-boundaries.md`` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 963 | `30. Move `architecture/module-boundaries.md` to `docs/archive/planning/module-boundaries.md`` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 35 | `\| `architecture/module-boundaries.md` \| 1 canonical ADR file \| Breaks canonical ADR reference \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 75 | `\| `architecture/module-boundaries.md` \| ARCHIVE \| **KEEP** or update 1 ADR reference first \| Referenced by 1 cano...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 123 | `- `architecture/module-boundaries.md` → 1 ADR reference` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 271 | `26. Move `architecture/module-boundaries.md` to `docs/archive/planning/module-boundaries.md`` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 348 | `\| `architecture/module-boundaries.md` \| Referenced by 1 canonical ADR \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 379 | `\| Archive `architecture/module-boundaries.md` \| **LOW** \| 1 ADR reference must be updated first \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 445 | `- `architecture/module-boundaries.md`` |
| PHASE_0_VALIDATION_REPORT.md | 61 | `\| `architecture/module-boundaries.md` \| Yes \| Yes \| ✅ PASS \|` |
| ... | ... | *... and 3 more* |

**Outgoing References:**

*No outgoing references found.*

---

### docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md

- **Exists:** YES
- **Incoming References:** 23
- **Outgoing References:** 1

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 169 | `\| `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` \| Core business logic deep dive \| Domain Owner (core) \| Backend engin...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 43 | `\| `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` \| 1 \| Canonical (partially outdated) \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 307 | `\| `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` \| Core business logic (needs accuracy updates) \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 413 | `\| `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` \| KEEP but update content \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 783 | `35. Update `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` to fix signal/webhook/command documentation` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 78 | `- `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md`: "Signal exists; **not connected** in `AppConfig.ready()`"` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 100 | `- `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md`: "`razorpay_webhook` defined **three times** in `core/views.py`"` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 131 | `- `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md`: "Assigned `'tenant'` group"` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 251 | `- `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` — long-form deep dive (414 lines)` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 327 | `\| Business Logic Deep Dive \| `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` \| None (outdated but must update in place) \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 507 | `\| `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` \| "Signal exists; not connected in `AppConfig.ready()`" \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 530 | `\| `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` \| "`razorpay_webhook` defined three times in `core/views.py`" \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 546 | `\| `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` \| "Assigned `'tenant'` group" \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 608 | `\| `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` \| Claims signals not wired; claims owner group is "tenant"; references ...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 933 | `15. Update `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` lines 41, 392: `properties/business_rules.md` reference` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 996 | `41. Update `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` to fix signal wiring, owner group, and payment strategy claims` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 239 | `14. Update `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` lines 41, 392: `properties/business_rules.md` reference` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 315 | `\| `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` \| Core business logic \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 427 | `- `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md`` |
| docs/business-rules/02-subscription-and-usage-limits.md | 61 | `- [Deep dive](../BUSINESS_LOGIC_AND_SUBSCRIPTION.md)` |
| docs/business-rules/14-known-behaviors-and-edge-cases.md | 50 | `- [Deep dive](../BUSINESS_LOGIC_AND_SUBSCRIPTION.md)` |
| docs/business-rules/README.md | 33 | `- [Business logic & subscription (deep dive)](../BUSINESS_LOGIC_AND_SUBSCRIPTION.md)` |
| docs/rag/README.md | 43 | `- [BUSINESS_LOGIC_AND_SUBSCRIPTION.md](../BUSINESS_LOGIC_AND_SUBSCRIPTION.md) — long-form deep dive` |

**Outgoing References:**

| Line | Type | Target | Context |
|------|------|--------|---------|
| 3 | markdown_link | `./business-rules/README.md` | `> **Per-domain rules:** See [business-rules/README.md](./business-rules/README.md) for separate files (buildings, ren...` |

---

### docs/README.md

- **Exists:** YES
- **Incoming References:** 40
- **Outgoing References:** 20

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 46 | `- `docs/README.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 164 | `\| `docs/README.md` \| Documentation index \| Tech Lead \| All contributors \| Permanent \| NO \| NO \| CRITICAL \| N...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 416 | `- Links from `docs/README.md` to subdirectories` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 824 | `\| `docs/README.md` \| **CANONICAL** \| Documentation index \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1705 | `├── docs/README.md` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 42 | `\| `docs/README.md` \| 1 \| Canonical \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 297 | `\| `docs/README.md` \| Documentation index \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 824 | `\| `docs/README.md` \| Documentation index \|` |
| PHASE_1_1_REPAIR_REPORT.md | 17 | `- `docs/README.md`` |
| PHASE_1_1_REPAIR_REPORT.md | 76 | `\| `docs/ai-governance/README.md` \| Created \| Missing Tier 1 canonical document referenced by `README.md` and `docs...` |
| PHASE_1_1_REPAIR_REPORT.md | 100 | `\| `docs/README.md` \| 1 \| 0 \|` |
| PHASE_1_2_GUARDIAN_REPAIR_REPORT.md | 136 | `- docs/README.md: ./ai-governance/README.md` |
| PHASE_1_2_GUARDIAN_REPAIR_REPORT.md | 148 | `**Test:** Temporarily added broken link `[Broken Link](nonexistent/broken/path.md)` to `README.md`` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 48 | `\| `docs/README.md` \| OK \| 0 \|` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 61 | `\| `docs/README.md` \| OK \|` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 366 | `\| `docs/rag/` (23 files) \| docs/README.md, docs/business-rules/README.md \| Verify no AI/script deps, update 2 refe...` |
| README.md | 80 | `- [Business Rules](docs/business-rules/README.md)` |
| README.md | 81 | `- [AI Governance](docs/ai-governance/README.md)` |
| README.md | 82 | `- [ADR Index](docs/adr/README.md)` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 316 | `\| Documentation Index \| `docs/README.md` \| None \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 310 | `\| `docs/README.md` \| Documentation index \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 422 | `- `docs/README.md`` |
| PHASE_0_VALIDATION_REPORT.md | 46 | `\| `docs/README.md` \| Yes \| Yes \| ✅ PASS \|` |
| PHASE_0_VALIDATION_REPORT.md | 105 | `├── docs/README.md` |
| PHASE_0_VALIDATION_REPORT.md | 120 | `\| `docs/ai-governance/README.md` \| Referenced by `README.md` and `docs/README.md` but does not exist \|` |
| PHASE_0_VALIDATION_REPORT.md | 136 | `\| Medium \| 3 \| `docs/README.md` → missing `./ai-governance/README.md` \|` |
| PHASE_0_VALIDATION_REPORT.md | 153 | `\| `docs/README.md` \| `./ai-governance/README.md` \| `docs/ai-governance/README.md` \| File does not exist \|` |
| PHASE_0_VALIDATION_REPORT.md | 209 | `- Checks for `docs/README.md`, `docs/architecture-contract.md`, `docs/ci-cd-pipeline.md`, `docs/governance.md`, `READ...` |
| PHASE_0_VALIDATION_REPORT.md | 256 | `\| `scripts/diagrams/documentation_guardian.py` \| `docs/README.md` \| Hardcoded required doc \| Missing doc check fa...` |
| PHASE_0_VALIDATION_REPORT.md | 325 | `\| `docs/rag/` \| Referenced by `docs/README.md`; if archived, AI RAG index must be updated \|` |
| ... | ... | *... and 10 more* |

**Outgoing References:**

| Line | Type | Target | Context |
|------|------|--------|---------|
| 5 | markdown_link | `./architecture-contract.md` | `- [Architecture Contract](./architecture-contract.md) — CI/CD pipeline contract` |
| 6 | markdown_link | `./ci-cd-pipeline.md` | `- [CI/CD Pipeline & UML Overview](./ci-cd-pipeline.md) — pipeline diagrams and UML` |
| 7 | markdown_link | `./governance.md` | `- [Governance](./governance.md) — enterprise CI/CD governance` |
| 14 | markdown_link | `./business-rules/README.md` | `Full index: **[business-rules/README.md](./business-rules/README.md)**` |
| 18 | markdown_link | `./business-rules/00-overview.md` | `\| Overview \| [00-overview.md](./business-rules/00-overview.md) \|` |
| 19 | markdown_link | `./business-rules/01-ownership-and-access.md` | `\| Access control \| [01-ownership-and-access.md](./business-rules/01-ownership-and-access.md) \|` |
| 20 | markdown_link | `./business-rules/02-subscription-and-usage-limits.md` | `\| Subscriptions \| [02-subscription-and-usage-limits.md](./business-rules/02-subscription-and-usage-limits.md) \|` |
| 21 | markdown_link | `./business-rules/03-caching.md` | `\| Caching \| [03-caching.md](./business-rules/03-caching.md) \|` |
| 22 | markdown_link | `./business-rules/04-buildings.md` | `\| Buildings → Renters → Rent \| [04](./business-rules/04-buildings.md) – [08](./business-rules/08-rent-records.md) \|` |
| 22 | markdown_link | `./business-rules/08-rent-records.md` | `\| Buildings → Renters → Rent \| [04](./business-rules/04-buildings.md) – [08](./business-rules/08-rent-records.md) \|` |
| 23 | markdown_link | `./business-rules/09-unit-images-and-documents.md` | `\| Media & agreements \| [09](./business-rules/09-unit-images-and-documents.md) – [11](./business-rules/11-payout-ret...` |
| 23 | markdown_link | `./business-rules/11-payout-retry.md` | `\| Media & agreements \| [09](./business-rules/09-unit-images-and-documents.md) – [11](./business-rules/11-payout-ret...` |
| 24 | markdown_link | `./business-rules/12-owner-reporting.md` | `\| Reporting & APIs \| [12](./business-rules/12-owner-reporting.md) – [14](./business-rules/14-known-behaviors-and-ed...` |
| 24 | markdown_link | `./business-rules/14-known-behaviors-and-edge-cases.md` | `\| Reporting & APIs \| [12](./business-rules/12-owner-reporting.md) – [14](./business-rules/14-known-behaviors-and-ed...` |
| 25 | markdown_link | `./business-rules/15-authentication.md` | `\| Platform services \| [15](./business-rules/15-authentication.md) – [22](./business-rules/22-signals-and-automation...` |
| 25 | markdown_link | `./business-rules/22-signals-and-automation.md` | `\| Platform services \| [15](./business-rules/15-authentication.md) – [22](./business-rules/22-signals-and-automation...` |
| 29 | markdown_link | `./ai-governance/README.md` | `- [AI Governance](./ai-governance/README.md) — AI usage policies and standards` |
| 30 | markdown_link | `./ai/README.md` | `- [Prompt Versioning](./ai/README.md) — versioned AI prompts for all modules` |
| 34 | markdown_link | `./adr/README.md` | `- [ADR Index](./adr/README.md) — architectural decisions and rationale` |
| 38 | markdown_link | `./rag/README.md` | `- [rag/](./rag/README.md) — self-contained chunks for RAG indexing` |

---

### docs/adr/README.md

- **Exists:** YES
- **Incoming References:** 39
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 347 | `- Documentation Guardian paths (e.g., `docs/adr/README.md`)` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 363 | `└── docs/adr/README.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 367 | `└── docs/adr/README.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 389 | `└── docs/adr/README.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1114 | `1. Update `README.md` line 83: `docs/adr/README.md` → `docs/architecture/adr/README.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1683 | `├── docs/adr/README.md (line 83) ← MUST UPDATE IF ARCHIVED` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1704 | `├── docs/adr/README.md (lines 91, 97) ← MUST UPDATE IF ARCHIVED` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1717 | `docs/adr/README.md (18 files)` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 439 | `\| `docs/adr/ADR-013.md` through `ADR-030.md` \| `docs/adr/README.md` \| Remove from index or create files \|` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 25 | `The ADR index (`docs/adr/README.md`) lists ADR-013 through ADR-030 as "Accepted" with dates 2026-07-13, but **none of...` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 343 | `1. `docs/adr/README.md:58`: "Create a new file: `ADR-XXX.md`"` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 423 | `### 11.4 docs/adr/README.md` |
| PHASE_1_2_GUARDIAN_REPAIR_REPORT.md | 78 | `**Problem:** The method checked `docs/adr/README.md` as the ADR index. Canonical ADRs are in `docs/architecture/adr/`...` |
| PHASE_1_2_GUARDIAN_REPAIR_REPORT.md | 148 | `**Test:** Temporarily added broken link `[Broken Link](nonexistent/broken/path.md)` to `README.md`` |
| README.md | 80 | `- [Business Rules](docs/business-rules/README.md)` |
| README.md | 81 | `- [AI Governance](docs/ai-governance/README.md)` |
| README.md | 82 | `- [ADR Index](docs/adr/README.md)` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 928 | `10. Update `README.md` line 83: `docs/adr/README.md` → `docs/architecture/adr/README.md`` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 234 | `9. Update `README.md` line 83: `docs/adr/README.md` → `docs/architecture/adr/README.md`` |
| PHASE_0_VALIDATION_REPORT.md | 83 | `├── docs/adr/README.md` |
| PHASE_0_VALIDATION_REPORT.md | 104 | `├── docs/adr/README.md (lines 91, 97)` |
| PHASE_0_VALIDATION_REPORT.md | 199 | `\| ADR Index Updated \| Check `docs/architecture/adr/README.md` \| Checks `docs/adr/README.md` (wrong location) \| ❌ ...` |
| PHASE_0_VALIDATION_REPORT.md | 214 | `- Checks `docs/adr/README.md` as the ADR index.` |
| PHASE_0_VALIDATION_REPORT.md | 228 | `\| Wrong ADR index path \| 91, 97 \| Uses `docs/adr/README.md` instead of `docs/architecture/adr/README.md` \|` |
| PHASE_0_VALIDATION_REPORT.md | 255 | `\| `scripts/diagrams/documentation_guardian.py` \| `docs/adr/README.md` \| Hardcoded path \| ADR index check fails \|` |
| PHASE_0_VALIDATION_REPORT.md | 281 | `If `docs/adr/README.md` is moved:` |
| PHASE_0_VALIDATION_REPORT.md | 405 | `\| `docs/adr/README.md` \| `README.md`, `documentation_guardian.py`, `architecture/adr/*` \| HIGH \|` |
| PHASE_0_VALIDATION_REPORT.md | 422 | `- Update `check_adr_index_updated()` to check `docs/architecture/adr/README.md` instead of `docs/adr/README.md`.` |
| docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md | 3 | `> **Per-domain rules:** See [business-rules/README.md](./business-rules/README.md) for separate files (buildings, ren...` |
| docs/README.md | 14 | `Full index: **[business-rules/README.md](./business-rules/README.md)**` |
| ... | ... | *... and 9 more* |

**Outgoing References:**

*No outgoing references found.*

---

### docs/ai-governance/AI-Architecture-Review.md

- **Exists:** YES
- **Incoming References:** 11
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 388 | `docs/ai-governance/AI-Architecture-Review.md (line 39)` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1116 | `3. Update `docs/ai-governance/AI-Architecture-Review.md` line 39: `docs/adr/` → `docs/architecture/adr/`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1723 | `← docs/ai-governance/AI-Architecture-Review.md (line 39)` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 930 | `12. Update `docs/ai-governance/AI-Architecture-Review.md` line 39: `docs/adr/` → `docs/architecture/adr/`` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 154 | `- `docs/ai-governance/AI-Architecture-Review.md` (line 39)` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 236 | `11. Update `docs/ai-governance/AI-Architecture-Review.md` line 39: `docs/adr/` → `docs/architecture/adr/`` |
| PHASE_0_VALIDATION_REPORT.md | 318 | `\| `docs/ai-governance/AI-Architecture-Review.md` \| `docs/adr/` \| If `docs/adr/` is archived without redirect, this...` |
| PHASE_0_VALIDATION_REPORT.md | 332 | `\| `docs/adr/` (18 files) \| `docs/ai-governance/AI-Architecture-Review.md` line 39 \| **UNSAFE** \|` |
| PHASE_0_VALIDATION_REPORT.md | 466 | `- Update `docs/ai-governance/AI-Architecture-Review.md` line 39.` |
| docs/ai-governance/README.md | 9 | `\| [AI-Architecture-Review.md](./AI-Architecture-Review.md) \| Architecture review checklist for AI-generated code \|` |
| docs/ai-governance/README.md | 28 | `- `docs/ai-governance/AI-Architecture-Review.md` — cross-references ADRs` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/architecture/README.md

- **Exists:** YES
- **Incoming References:** 83
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 186 | `\| `docs/architecture/README.md` \| `docs/architecture/audit_data.json`, `scripts/arch_audit.py` \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 371 | `└── docs/architecture/README.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 383 | `└── docs/architecture/README.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 386 | `└── docs/architecture/README.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 844 | `\| `architecture/adr/` (4 files) \| **CANONICAL** \| Referenced by docs/architecture/README.md \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 923 | `\| `docs/architecture/README.md` \| **ARCHIVE CANDIDATE** \| Audit overview, broken references to missing files \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 983 | `\| `architecture/adr/` (4 files) \| Update docs/architecture/README.md references \| Phase 0 ADRs superseded by detai...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 990 | `\| `docs/architecture/README.md` \| Fix 4 broken internal links first, then archive \| Architecture audit overview wi...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1117 | `4. Update `architecture/adr/001-current-architecture.md` line 45: `docs/architecture/README.md` → `docs/refactoring/1...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1121 | `8. Update `architecture/adr/002-target-architecture.md` line 61: `docs/architecture/README.md` → canonical architectu...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1122 | `9. Update `architecture/adr/003-refactoring-strategy.md` line 65: `docs/architecture/README.md` → canonical architect...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1177 | `- `docs/architecture/README.md` → `docs/archive/audits/architecture-readme.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1701 | `└── docs/architecture/README.md` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1726 | `← docs/architecture/README.md` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 145 | `\| `docs/architecture/README.md` \| docs/architecture/ \| 8.0 KB \| Architecture overview with embedded principles \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 150 | `- `docs/architecture/README.md` embeds principles in an audit report.` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 155 | `- **ARCHIVE** principles section from `docs/architecture/README.md` or rewrite as pointer.` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 169 | `- `architecture/ROADMAP.md` is referenced by `docs/architecture/README.md` but does not exist at the expected path.` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 233 | `\| `docs/architecture/README.md` \| docs/architecture/ \| 8.0 KB \| Architecture audit overview \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 240 | `- **ARCHIVE** `docs/architecture/README.md` (audit overview, superseded).` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 391 | `\| `docs/architecture/README.md` \| ARCHIVE \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 442 | `\| `../ARCHITECTURE_PRINCIPLES.md` \| `docs/architecture/README.md` \| Fix path to `docs/refactoring/00_architecture_...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 443 | `\| `../CODING_STANDARDS.md` \| `docs/architecture/README.md` \| Fix path to `docs/refactoring/10_naming_conventions.m...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 444 | `\| `../ROADMAP.md` \| `docs/architecture/README.md` \| Fix path to `docs/refactoring/12_architecture_implementation_m...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 445 | `\| `../adr/ADR-template.md` \| `docs/architecture/README.md` \| Fix path to `architecture/adr/000-template.md` \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 521 | `\| `docs/architecture/README.md` \| `../ARCHITECTURE_PRINCIPLES.md` \| File does not exist at root \| Update to `docs...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 522 | `\| `docs/architecture/README.md` \| `../CODING_STANDARDS.md` \| File does not exist at root \| Update to `docs/refact...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 523 | `\| `docs/architecture/README.md` \| `../ROADMAP.md` \| File does not exist at root \| Update to `docs/refactoring/12_...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 524 | `\| `docs/architecture/README.md` \| `../adr/ADR-template.md` \| File does not exist \| Update to `architecture/adr/00...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 748 | `15. Move `docs/architecture/README.md` to `docs/archive/audits/architecture-readme.md`` |
| ... | ... | *... and 53 more* |

**Outgoing References:**

*No outgoing references found.*

---

### docs/architecture/architecture-audit-report.md

- **Exists:** NO
- **Incoming References:** 21
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 148 | `- `docs/architecture/architecture-audit-report.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 888 | `\| `docs/architecture/architecture-audit-report.md` \| **GENERATED** \| Generated architecture audit \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 924 | `\| `docs/architecture/architecture-audit-report.md` \| **ARCHIVE CANDIDATE** \| Superseded by production-architecture...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 969 | `\| `docs/architecture/architecture-audit-report.md` \| Superseded by `production-architecture.md`. Zero external refe...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1100 | `- `docs/architecture/architecture-audit-report.md` → `docs/archive/audits/architecture-audit-report.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1178 | `- `docs/architecture/architecture-audit-report.md` → `docs/archive/audits/architecture-audit-report.md`` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 234 | `\| `docs/architecture/architecture-audit-report.md` \| docs/architecture/ \| 40.1 KB \| Full architecture audit repor...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 241 | `- **ARCHIVE** `docs/architecture/architecture-audit-report.md` (superseded by production-architecture.md).` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 392 | `\| `docs/architecture/architecture-audit-report.md` \| ARCHIVE \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 749 | `16. Move `docs/architecture/architecture-audit-report.md` to `docs/archive/audits/architecture-audit-report.md`` |
| PHASE_2_1_ARCHIVE_REPORT.md | 15 | `\| 1 \| `docs/architecture/architecture-audit-report.md` \| `docs/archive/audits/architecture-audit-report.md` \| `gi...` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 343 | `\| `docs/architecture/architecture-audit-report.md` \| None \| SAFE \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 468 | `\| Architecture Audit Report \| `docs/architecture/architecture-audit-report.md` \| ~40.1 KB \| Generated report \| G...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 678 | `\| `docs/architecture/architecture-audit-report.md` \| Only referenced in plan itself \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 920 | `7. Move `docs/architecture/architecture-audit-report.md` to `docs/archive/audits/`` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 1036 | `\| Archiving `docs/architecture/architecture-audit-report.md` \| **LOW** \| No external references found \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 202 | `\| `docs/architecture/architecture-audit-report.md` \| ARCHIVE \| HIGH \| Only referenced in plan itself \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 227 | `7. Move `docs/architecture/architecture-audit-report.md` to `docs/archive/audits/`` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 365 | `\| Archive `docs/architecture/architecture-audit-report.md` \| **HIGH** \| No external references found \|` |
| PHASE_0_VALIDATION_REPORT.md | 353 | `\| `docs/architecture/architecture-audit-report.md` \| 0 verified \| No \| No \| No \| **SAFE** \| Superseded by prod...` |
| PHASE_0_VALIDATION_REPORT.md | 363 | `\| `docs/architecture/architecture-audit-report.md` \| Superseded; no canonical references \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/architecture/audit_data.json

- **Exists:** YES
- **Incoming References:** 16
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md | 186 | `\| `docs/architecture/README.md` \| `docs/architecture/audit_data.json`, `scripts/arch_audit.py` \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 88 | `- `docs/architecture/audit_data.json` — raw audit data used by scripts` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 858 | `\| `docs/architecture/audit_data.json` \| **REFERENCE** \| Raw audit data used by scripts \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 264 | `\| `docs/architecture/audit_data.json` \| docs/architecture/ \| 198 KB \| Raw audit data \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 278 | `\| `docs/architecture/audit_data.json` \| docs/architecture/ \| 198 KB \| Audit raw data \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 282 | `- **KEEP** `docs/architecture/audit_data.json` as canonical raw data.` |
| PHASE_1_1_REPAIR_REPORT.md | 152 | `\| `docs/architecture/README.md` references `docs/architecture/audit_data.json` \| Keep as-is / Update path / Remove ...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 477 | `\| Audit Data \| `docs/architecture/audit_data.json` \| ~198 KB \| Raw audit data \| Canonical (for scripts) \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 481 | `**Recommendation:** Keep `docs/architecture/audit_data.json`. Archive the other two.` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 323 | `\| `docs/architecture/audit_data.json` \| Raw audit data used by scripts \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 435 | `- `docs/architecture/audit_data.json`` |
| PHASE_0_VALIDATION_REPORT.md | 263 | `\| `scripts/arch_audit.py` \| `docs/architecture/audit_data.json` \| Hardcoded output \| Audit data written to wrong ...` |
| docs/architecture/README.md | 144 | `- `docs/architecture/audit_data.json` — Complete AST-based dependency data` |
| docs/architecture/02_import_matrix.md | 15 | `**Source:** `docs/architecture/audit_data.json`` |
| docs/architecture/01_dependency_graph.md | 383 | `- All diagrams are derived from `docs/architecture/audit_data.json` (AST-based analysis).` |
| scripts/arch_audit.py | 587 | `print("Analysis complete. Data written to docs/architecture/audit_data.json")` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/architecture/future/02_bounded_contexts.md

- **Exists:** YES
- **Incoming References:** 19
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 936 | `\| `docs/architecture/future/02_bounded_contexts.md` \| Referenced by 11 canonical ADR files in `docs/architecture/ad...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1688 | `├── docs/architecture/future/02_bounded_contexts.md (11 refs)` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 200 | `\| `docs/architecture/future/02_bounded_contexts.md` \| docs/architecture/future/ \| 16.6 KB \| Detailed bounded cont...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 205 | `- **ARCHIVE** `docs/architecture/future/02_bounded_contexts.md` (superseded).` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 394 | `\| `docs/architecture/future/02_bounded_contexts.md` \| ARCHIVE \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 755 | `22. Move `docs/architecture/future/02_bounded_contexts.md` to `docs/archive/planning/bounded-contexts.md`` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 343 | `\| Module Responsibilities \| `docs/refactoring/06_module_responsibilities.md` \| `architecture/module-boundaries.md`...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 437 | `\| Bounded Contexts \| `docs/architecture/future/02_bounded_contexts.md` \| ~16.6 KB \| Detailed, referenced by 11 AD...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 440 | `**Analysis:** `docs/architecture/future/02_bounded_contexts.md` is the most detailed and is referenced by 11 canonica...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 442 | `**Recommendation:** Keep `docs/architecture/future/02_bounded_contexts.md` as canonical reference. Keep `docs/refacto...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 30 | `\| `docs/architecture/future/02_bounded_contexts.md` \| 11 canonical ADR files in `docs/architecture/adr/` \| Breaks ...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 70 | `\| `docs/architecture/future/02_bounded_contexts.md` \| ARCHIVE \| **KEEP** \| Referenced by 11 canonical ADR files \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 135 | `- `docs/architecture/future/02_bounded_contexts.md` → 11 ADR references` |
| PHASE_0_VALIDATION_REPORT.md | 88 | `├── docs/architecture/future/02_bounded_contexts.md (11 refs)` |
| docs/architecture/adr/ADR-019_event_bus.md | 132 | `- [Bounded Contexts](../future/02_bounded_contexts.md)` |
| docs/architecture/adr/ADR-011_notification_strategy.md | 137 | `- [Bounded Contexts](../future/02_bounded_contexts.md)` |
| docs/architecture/adr/ADR-005_domain_events.md | 110 | `- [Bounded Contexts](../future/02_bounded_contexts.md)` |
| docs/architecture/adr/ADR-010_payment_integration.md | 144 | `- [Bounded Contexts](../future/02_bounded_contexts.md)` |
| docs/architecture/adr/ADR-012_document_generation.md | 133 | `- [Bounded Contexts](../future/02_bounded_contexts.md)` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/architecture/future/05_dependency_rules.md

- **Exists:** YES
- **Incoming References:** 28
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 937 | `\| `docs/architecture/future/05_dependency_rules.md` \| Referenced by 3 canonical ADR files. Even if exact duplicate ...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1001 | `\| `docs/architecture/future/05_dependency_rules.md` \| Full orphan validation \| Exact duplicate of docs/refactoring...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1691 | `├── docs/architecture/future/05_dependency_rules.md (3 refs)` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 183 | `\| `docs/architecture/future/05_dependency_rules.md` \| docs/architecture/future/ \| 7.9 KB \| **Exact duplicate** of...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 186 | `- `docs/architecture/future/05_dependency_rules.md` is an exact duplicate of `docs/refactoring/05_dependency_rules.md...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 191 | `- **DELETE** `docs/architecture/future/05_dependency_rules.md` (exact duplicate).` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 393 | `\| `docs/architecture/future/05_dependency_rules.md` \| ARCHIVE (exact duplicate) \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 425 | `\| `docs/architecture/future/05_dependency_rules.md` \| Exact duplicate of `docs/refactoring/05_dependency_rules.md` ...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 754 | `21. Delete exact duplicate: `docs/architecture/future/05_dependency_rules.md`` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 342 | `\| Dependency Rules \| `docs/refactoring/05_dependency_rules.md` \| `architecture/dependency-rules.md`, `docs/archite...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 425 | `\| Future Dependency Rules \| `docs/architecture/future/05_dependency_rules.md` \| ~7.9 KB \| **EXACT DUPLICATE** \| ...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 428 | `**Analysis:** `docs/architecture/future/05_dependency_rules.md` is an exact byte-for-byte duplicate of `docs/refactor...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 731 | `\| `docs/architecture/future/05_dependency_rules.md` \| Exact byte-for-byte duplicate of `docs/refactoring/05_depende...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 1017 | `\| Deleting `docs/architecture/future/05_dependency_rules.md` \| **VERY HIGH** \| Referenced by 3 canonical ADRs; NOT...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 1105 | `3. **DO NOT delete `docs/architecture/future/05_dependency_rules.md`** — even though it is an exact duplicate, it is ...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 31 | `\| `docs/architecture/future/05_dependency_rules.md` \| 3 canonical ADR files in `docs/architecture/adr/` \| Breaks c...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 60 | `The previous plan identified `docs/architecture/future/05_dependency_rules.md` as an "exact duplicate" of `docs/refac...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 62 | `**Reality:** While the content may be identical, `docs/architecture/future/05_dependency_rules.md` is **referenced by...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 71 | `\| `docs/architecture/future/05_dependency_rules.md` \| DELETE \| **KEEP** (or archive with reference update) \| Refe...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 91 | `\| `docs/architecture/future/05_dependency_rules.md` \| DELETE (exact duplicate) \| **ARCHIVE** or **KEEP** \| Refere...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 138 | `- `docs/architecture/future/05_dependency_rules.md` → 3 ADR references` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 342 | `\| `docs/architecture/future/05_dependency_rules.md` \| Referenced by 3 canonical ADR files \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 382 | `\| Delete `docs/architecture/future/05_dependency_rules.md` \| **VERY LOW** \| Referenced by 3 canonical ADRs; NOT RE...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 407 | `### 10.4 Do Not Delete `docs/architecture/future/05_dependency_rules.md`` |
| PHASE_0_VALIDATION_REPORT.md | 91 | `├── docs/architecture/future/05_dependency_rules.md (3 refs)` |
| docs/architecture/adr/ADR-006_import_rules.md | 106 | `- [Dependency Rules](../future/05_dependency_rules.md)` |
| docs/architecture/adr/ADR-008_shared_module_rules.md | 113 | `- [Dependency Rules](../future/05_dependency_rules.md)` |
| docs/architecture/adr/ADR-002_repository_pattern.md | 110 | `- [Dependency Rules](../future/05_dependency_rules.md)` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/business-rules/00-overview.md

- **Exists:** YES
- **Incoming References:** 14
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 504 | `**Decision Required:** This 311-byte legacy file is referenced in `docs/business-rules/00-overview.md`. Should it be:` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 509 | `**Recommendation:** Update reference in `docs/business-rules/00-overview.md` and delete the legacy file.` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 529 | `\| `docs/business-rules/00-overview.md` \| `properties/business_rules.md` \| Legacy file, 311 bytes \| Update or remo...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 773 | `30. Update `docs/business-rules/00-overview.md` reference to `properties/business_rules.md`` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 225 | `\| `docs/business-rules/00-overview.md` \| `properties/business_rules.md` \| File exists but is 311 bytes (likely ver...` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 303 | `\| `docs/business-rules/00-overview.md` \| Lists `/properties/` as "duplicate mount" — accurate but confusing \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 931 | `13. Update `docs/business-rules/00-overview.md` line 38: `properties/business_rules.md` reference` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 237 | `12. Update `docs/business-rules/00-overview.md` line 38: `properties/business_rules.md` reference` |
| docs/README.md | 18 | `\| Overview \| [00-overview.md](./business-rules/00-overview.md) \|` |
| docs/business-rules/README.md | 7 | `\| 00 \| [Overview](./00-overview.md) \| Cross-cutting \|` |
| docs/refactoring/04_final_production_safety_report.md | 313 | `\| `docs/business-rules/00-overview.md` \| Line 34: `/dashboard/` route \| Must be updated \|` |
| docs/refactoring/04_final_production_safety_report.md | 504 | `\| `docs/business-rules/00-overview.md` \| Update `/dashboard/` route reference \|` |
| docs/refactoring/05_execution_report.md | 94 | `\| `docs/business-rules/00-overview.md` \| Removed `/dashboard/` route reference \|` |
| docs/refactoring/05_execution_report.md | 133 | `- `docs/business-rules/00-overview.md` — RESTORED` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/business-rules/02-subscription-and-usage-limits.md

- **Exists:** YES
- **Incoming References:** 12
- **Outgoing References:** 1

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_ANALYSIS_REPORT.md | 75 | `- `docs/business-rules/02-subscription-and-usage-limits.md`: "`core/signals.assign_default_plan` exists but **`core/a...` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 117 | `- `docs/business-rules/02-subscription-and-usage-limits.md`: "`seed_subscription_plans` and `downgrade_expired_users`...` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 304 | `\| `docs/business-rules/02-subscription-and-usage-limits.md` \| Claims `core/apps.py` doesn't import signals — **FALS...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 504 | `\| `docs/business-rules/02-subscription-and-usage-limits.md` \| "`core/signals.assign_default_plan` exists but `core/...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 566 | `\| `docs/business-rules/02-subscription-and-usage-limits.md` \| "`seed_subscription_plans` and `downgrade_expired_use...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 602 | `\| `docs/business-rules/02-subscription-and-usage-limits.md` \| Claims signals are not wired; claims management comma...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 997 | `42. Update `docs/business-rules/02-subscription-and-usage-limits.md` to fix signal wiring and command status claims` |
| docs/README.md | 20 | `\| Subscriptions \| [02-subscription-and-usage-limits.md](./business-rules/02-subscription-and-usage-limits.md) \|` |
| docs/business-rules/README.md | 9 | `\| 02 \| [Subscription & usage limits](./02-subscription-and-usage-limits.md) \| `core`, `properties` \|` |
| docs/business-rules/09-unit-images-and-documents.md | 43 | `- [Subscription limits](./02-subscription-and-usage-limits.md)` |
| docs/business-rules/04-buildings.md | 37 | `- [Subscription limits](./02-subscription-and-usage-limits.md)` |
| docs/rag/subscription-and-limits.md | 47 | ``docs/business-rules/02-subscription-and-usage-limits.md`` |

**Outgoing References:**

| Line | Type | Target | Context |
|------|------|--------|---------|
| 61 | markdown_link | `../BUSINESS_LOGIC_AND_SUBSCRIPTION.md` | `- [Deep dive](../BUSINESS_LOGIC_AND_SUBSCRIPTION.md)` |

---

### docs/business-rules/14-known-behaviors-and-edge-cases.md

- **Exists:** YES
- **Incoming References:** 9
- **Outgoing References:** 2

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_ANALYSIS_REPORT.md | 76 | `- `docs/business-rules/14-known-behaviors-and-edge-cases.md`: "`core/apps.py` and `properties/apps.py` do not import ...` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 132 | `- `docs/business-rules/14-known-behaviors-and-edge-cases.md`: "Owner OTP assigns group **`tenant`** (likely wrong nam...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 505 | `\| `docs/business-rules/14-known-behaviors-and-edge-cases.md` \| "`core/apps.py` and `properties/apps.py` do not impo...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 547 | `\| `docs/business-rules/14-known-behaviors-and-edge-cases.md` \| "Owner OTP assigns group `tenant` (likely wrong name...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 603 | `\| `docs/business-rules/14-known-behaviors-and-edge-cases.md` \| Claims signals are not wired; claims owner group is ...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 998 | `43. Update `docs/business-rules/14-known-behaviors-and-edge-cases.md` to fix signal wiring and owner group claims` |
| docs/README.md | 24 | `\| Reporting & APIs \| [12](./business-rules/12-owner-reporting.md) – [14](./business-rules/14-known-behaviors-and-ed...` |
| docs/business-rules/22-signals-and-automation.md | 74 | `- [Known behaviors](./14-known-behaviors-and-edge-cases.md)` |
| docs/business-rules/README.md | 21 | `\| 14 \| [Known behaviors & edge cases](./14-known-behaviors-and-edge-cases.md) \| Cross-cutting \|` |

**Outgoing References:**

| Line | Type | Target | Context |
|------|------|--------|---------|
| 49 | markdown_link | `./22-signals-and-automation.md` | `- [Signals & automation](./22-signals-and-automation.md)` |
| 50 | markdown_link | `../BUSINESS_LOGIC_AND_SUBSCRIPTION.md` | `- [Deep dive](../BUSINESS_LOGIC_AND_SUBSCRIPTION.md)` |

---

### docs/business-rules/15-authentication.md

- **Exists:** YES
- **Incoming References:** 9
- **Outgoing References:** 1

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_ANALYSIS_REPORT.md | 130 | `- `docs/business-rules/15-authentication.md`: "Owner → group `tenant` (verify intended role name)"` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 545 | `\| `docs/business-rules/15-authentication.md` \| "Owner → group `tenant` (verify intended role name)" \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 604 | `\| `docs/business-rules/15-authentication.md` \| Claims owner group is "tenant" \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 999 | `44. Update `docs/business-rules/15-authentication.md` to fix owner group claim` |
| docs/README.md | 25 | `\| Platform services \| [15](./business-rules/15-authentication.md) – [22](./business-rules/22-signals-and-automation...` |
| docs/business-rules/13-renter-facing-apis.md | 42 | `- [Authentication](./15-authentication.md)` |
| docs/business-rules/19-referral-program.md | 38 | `- [Authentication](./15-authentication.md)` |
| docs/business-rules/README.md | 22 | `\| 15 \| [Authentication](./15-authentication.md) \| `core` \|` |
| docs/business-rules/01-ownership-and-access.md | 21 | `- JWT via `rest_framework_simplejwt` (see [Authentication](./15-authentication.md)).` |

**Outgoing References:**

| Line | Type | Target | Context |
|------|------|--------|---------|
| 25 | markdown_link | `./19-referral-program.md` | `5. Optional **referral_code** on send — validated on verify (see [Referral](./19-referral-program.md)).` |

---

### docs/business-rules/16-payments-and-webhooks.md

- **Exists:** YES
- **Incoming References:** 10
- **Outgoing References:** 2

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 535 | `\| `docs/business-rules/16-payments-and-webhooks.md` \| `rentsecure_be/services/razorpay_service.py` \| Path may be i...` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 99 | `- `docs/business-rules/16-payments-and-webhooks.md`: "`razorpay_webhook` defined 3 times in `core/views.py`"` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 231 | `\| `docs/business-rules/16-payments-and-webhooks.md` \| `rentsecure_be/services/razorpay_service.py` \| Path should b...` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 306 | `\| `docs/business-rules/16-payments-and-webhooks.md` \| References old payment gateway URLs and flows \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 529 | `\| `docs/business-rules/16-payments-and-webhooks.md` \| "`razorpay_webhook` defined 3 times in `core/views.py`" \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 605 | `\| `docs/business-rules/16-payments-and-webhooks.md` \| Claims webhook defined 3 times; references old payment strate...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 1000 | `45. Update `docs/business-rules/16-payments-and-webhooks.md` to fix webhook count and payment strategy claims` |
| docs/business-rules/08-rent-records.md | 53 | `- [Payments & webhooks](./16-payments-and-webhooks.md)` |
| docs/business-rules/README.md | 23 | `\| 16 \| [Payments & webhooks](./16-payments-and-webhooks.md) \| `core`, `rentsecure_be` \|` |
| docs/business-rules/11-payout-retry.md | 50 | `- [Payments & webhooks](./16-payments-and-webhooks.md)` |

**Outgoing References:**

| Line | Type | Target | Context |
|------|------|--------|---------|
| 72 | markdown_link | `./08-rent-records.md` | `- [Rent records](./08-rent-records.md)` |
| 73 | markdown_link | `./11-payout-retry.md` | `- [Payout retry](./11-payout-retry.md)` |

---

### docs/business-rules/17-notifications.md

- **Exists:** YES
- **Incoming References:** 6
- **Outgoing References:** 2

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_ANALYSIS_REPORT.md | 169 | `\| `docs/business-rules/17-notifications.md` \| Lists WhatsApp/SMS as active channels via Twilio \|` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 307 | `\| `docs/business-rules/17-notifications.md` \| Lists WhatsApp/SMS as active, not "Coming Soon" \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 606 | `\| `docs/business-rules/17-notifications.md` \| References WhatsApp/SMS as primary channels (now Stage 2) \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 1001 | `46. Update `docs/business-rules/17-notifications.md` to reflect Year 1 free channels only` |
| docs/business-rules/22-signals-and-automation.md | 75 | `- [Notifications](./17-notifications.md)` |
| docs/business-rules/README.md | 24 | `\| 17 \| [Notifications](./17-notifications.md) \| `notification` \|` |

**Outgoing References:**

| Line | Type | Target | Context |
|------|------|--------|---------|
| 60 | markdown_link | `./22-signals-and-automation.md` | `- [Signals & automation](./22-signals-and-automation.md)` |
| 61 | markdown_link | `./08-rent-records.md` | `- [Rent records](./08-rent-records.md)` |

---

### docs/business-rules/22-signals-and-automation.md

- **Exists:** YES
- **Incoming References:** 12
- **Outgoing References:** 2

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_ANALYSIS_REPORT.md | 77 | `- `docs/business-rules/22-signals-and-automation.md`: "**Status:** `core/apps.py` `ready()` does **not** import this ...` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 115 | `- `docs/business-rules/22-signals-and-automation.md`: "`generate_monthly_rent_records` — Broken (`rent.models` import)"` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 116 | `- `docs/business-rules/22-signals-and-automation.md`: "`daily_rent_reminder` — Broken import"` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 506 | `\| `docs/business-rules/22-signals-and-automation.md` \| "Status: `core/apps.py` `ready()` does not import this modul...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 564 | `\| `docs/business-rules/22-signals-and-automation.md` \| "`generate_monthly_rent_records` — Broken (`rent.models` imp...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 565 | `\| `docs/business-rules/22-signals-and-automation.md` \| "`daily_rent_reminder` — Broken import" \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 607 | `\| `docs/business-rules/22-signals-and-automation.md` \| Claims signals not wired; claims commands broken \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 1002 | `47. Update `docs/business-rules/22-signals-and-automation.md` to fix signal wiring and command status claims` |
| docs/README.md | 25 | `\| Platform services \| [15](./business-rules/15-authentication.md) – [22](./business-rules/22-signals-and-automation...` |
| docs/business-rules/17-notifications.md | 60 | `- [Signals & automation](./22-signals-and-automation.md)` |
| docs/business-rules/14-known-behaviors-and-edge-cases.md | 49 | `- [Signals & automation](./22-signals-and-automation.md)` |
| docs/business-rules/README.md | 29 | `\| 22 \| [Signals & automation](./22-signals-and-automation.md) \| `core`, `properties`, `management` \|` |

**Outgoing References:**

| Line | Type | Target | Context |
|------|------|--------|---------|
| 74 | markdown_link | `./14-known-behaviors-and-edge-cases.md` | `- [Known behaviors](./14-known-behaviors-and-edge-cases.md)` |
| 75 | markdown_link | `./17-notifications.md` | `- [Notifications](./17-notifications.md)` |

---

### docs/business-rules/README.md

- **Exists:** YES
- **Incoming References:** 38
- **Outgoing References:** 24

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 417 | `- Links from `docs/business-rules/README.md` to individual files` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1681 | `├── docs/business-rules/README.md` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 525 | `\| `docs/business-rules/README.md` \| `../business-gaps/BUSINESS_GAPS_AUDIT.md` \| Directory does not exist \| Create...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 771 | `28. Update `docs/business-rules/README.md` references` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 221 | `\| `docs/business-rules/README.md` \| `../business-gaps/BUSINESS_GAPS_AUDIT.md` \| Directory does not exist \|` |
| PHASE_1_1_REPAIR_REPORT.md | 22 | `- `docs/business-rules/README.md`` |
| PHASE_1_1_REPAIR_REPORT.md | 39 | `\| `docs/business-rules/README.md` \| Modified \| Removed broken reference to `../business-gaps/BUSINESS_GAPS_AUDIT.m...` |
| PHASE_1_1_REPAIR_REPORT.md | 105 | `\| `docs/business-rules/README.md` \| 1 \| 0 \|` |
| PHASE_1_1_REPAIR_REPORT.md | 155 | `\| `docs/business-rules/README.md` removed `business-gaps` reference \| Create `docs/business-gaps/` / Leave removed ...` |
| PHASE_1_2_GUARDIAN_REPAIR_REPORT.md | 148 | `**Test:** Temporarily added broken link `[Broken Link](nonexistent/broken/path.md)` to `README.md`` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 68 | `\| `docs/business-rules/README.md` \| OK \|` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 365 | `\| `properties/business_rules.md` \| docs/business-rules/README.md \| Update 1 reference first \|` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 366 | `\| `docs/rag/` (23 files) \| docs/README.md, docs/business-rules/README.md \| Verify no AI/script deps, update 2 refe...` |
| README.md | 80 | `- [Business Rules](docs/business-rules/README.md)` |
| README.md | 81 | `- [AI Governance](docs/ai-governance/README.md)` |
| README.md | 82 | `- [ADR Index](docs/adr/README.md)` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 328 | `\| Business Rules Index \| `docs/business-rules/README.md` \| `properties/business_rules.md` (legacy) \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 932 | `14. Update `docs/business-rules/README.md` line 36: `properties/business_rules.md` reference` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 238 | `13. Update `docs/business-rules/README.md` line 36: `properties/business_rules.md` reference` |
| PHASE_0_VALIDATION_REPORT.md | 81 | `├── docs/business-rules/README.md` |
| PHASE_0_VALIDATION_REPORT.md | 122 | `\| `docs/business-gaps/BUSINESS_GAPS_AUDIT.md` \| Referenced by `docs/business-rules/README.md` and `docs/rag/README....` |
| PHASE_0_VALIDATION_REPORT.md | 137 | `\| Medium \| 2 \| `docs/business-rules/README.md` and `docs/rag/README.md` → missing `../business-gaps/BUSINESS_GAPS_...` |
| PHASE_0_VALIDATION_REPORT.md | 180 | `\| `docs/business-rules/README.md` \| `../business-gaps/BUSINESS_GAPS_AUDIT.md` \| Directory/file does not exist \|` |
| PHASE_0_VALIDATION_REPORT.md | 355 | `\| `properties/business_rules.md` \| 1 (docs/business-rules/README.md) \| No \| No \| No \| **UPDATE REFERENCES FIRST...` |
| PHASE_0_VALIDATION_REPORT.md | 446 | `- Either create these directories/files or update `docs/business-rules/README.md` and `docs/rag/README.md` to remove ...` |
| docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md | 3 | `> **Per-domain rules:** See [business-rules/README.md](./business-rules/README.md) for separate files (buildings, ren...` |
| docs/README.md | 14 | `Full index: **[business-rules/README.md](./business-rules/README.md)**` |
| docs/README.md | 29 | `- [AI Governance](./ai-governance/README.md) — AI usage policies and standards` |
| docs/README.md | 30 | `- [Prompt Versioning](./ai/README.md) — versioned AI prompts for all modules` |
| docs/README.md | 34 | `- [ADR Index](./adr/README.md) — architectural decisions and rationale` |
| ... | ... | *... and 8 more* |

**Outgoing References:**

| Line | Type | Target | Context |
|------|------|--------|---------|
| 7 | markdown_link | `./00-overview.md` | `\| 00 \| [Overview](./00-overview.md) \| Cross-cutting \|` |
| 8 | markdown_link | `./01-ownership-and-access.md` | `\| 01 \| [Ownership & access](./01-ownership-and-access.md) \| All apps \|` |
| 9 | markdown_link | `./02-subscription-and-usage-limits.md` | `\| 02 \| [Subscription & usage limits](./02-subscription-and-usage-limits.md) \| `core`, `properties` \|` |
| 10 | markdown_link | `./03-caching.md` | `\| 03 \| [Caching](./03-caching.md) \| `properties` \|` |
| 11 | markdown_link | `./04-buildings.md` | `\| 04 \| [Buildings](./04-buildings.md) \| `properties` \|` |
| 12 | markdown_link | `./05-units.md` | `\| 05 \| [Units](./05-units.md) \| `properties` \|` |
| 13 | markdown_link | `./06-caretakers.md` | `\| 06 \| [Caretakers](./06-caretakers.md) \| `properties` \|` |
| 14 | markdown_link | `./07-renters.md` | `\| 07 \| [Renters](./07-renters.md) \| `properties` \|` |
| 15 | markdown_link | `./08-rent-records.md` | `\| 08 \| [Rent records](./08-rent-records.md) \| `properties` \|` |
| 16 | markdown_link | `./09-unit-images-and-documents.md` | `\| 09 \| [Unit images & documents](./09-unit-images-and-documents.md) \| `properties` \|` |
| 17 | markdown_link | `./10-rent-agreement-drafts.md` | `\| 10 \| [Rent agreement drafts](./10-rent-agreement-drafts.md) \| `properties` \|` |
| 18 | markdown_link | `./11-payout-retry.md` | `\| 11 \| [Payout retry](./11-payout-retry.md) \| `properties`, `core` \|` |
| 19 | markdown_link | `./12-owner-reporting.md` | `\| 12 \| [Owner reporting](./12-owner-reporting.md) \| `properties` \|` |
| 20 | markdown_link | `./13-renter-facing-apis.md` | `\| 13 \| [Renter-facing APIs](./13-renter-facing-apis.md) \| `properties` \|` |
| 21 | markdown_link | `./14-known-behaviors-and-edge-cases.md` | `\| 14 \| [Known behaviors & edge cases](./14-known-behaviors-and-edge-cases.md) \| Cross-cutting \|` |
| 22 | markdown_link | `./15-authentication.md` | `\| 15 \| [Authentication](./15-authentication.md) \| `core` \|` |
| 23 | markdown_link | `./16-payments-and-webhooks.md` | `\| 16 \| [Payments & webhooks](./16-payments-and-webhooks.md) \| `core`, `rentsecure_be` \|` |
| 24 | markdown_link | `./17-notifications.md` | `\| 17 \| [Notifications](./17-notifications.md) \| `notification` \|` |
| 25 | markdown_link | `./18-finance-and-tax.md` | `\| 18 \| [Finance & tax](./18-finance-and-tax.md) \| `finance` \|` |
| 26 | markdown_link | `./19-referral-program.md` | `\| 19 \| [Referral program](./19-referral-program.md) \| `referral_and_earn` \|` |
| 27 | markdown_link | `./20-documents-and-pdfs.md` | `\| 20 \| [Documents & PDFs](./20-documents-and-pdfs.md) \| `documents` \|` |
| 28 | markdown_link | `./21-smartbot.md` | `\| 21 \| [SmartBot](./21-smartbot.md) \| `smartbot` \|` |
| 29 | markdown_link | `./22-signals-and-automation.md` | `\| 22 \| [Signals & automation](./22-signals-and-automation.md) \| `core`, `properties`, `management` \|` |
| 33 | markdown_link | `../BUSINESS_LOGIC_AND_SUBSCRIPTION.md` | `- [Business logic & subscription (deep dive)](../BUSINESS_LOGIC_AND_SUBSCRIPTION.md)` |

---

### docs/ci-cd-upgrade-report.md

- **Exists:** NO
- **Incoming References:** 19
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 149 | `- `docs/ci-cd-upgrade-report.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 198 | `\| `docs/ci-cd-upgrade-report.md` \| Generated upgrade report \| Senior DevOps \| DevOps \| Until superseded \| YES \...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 889 | `\| `docs/ci-cd-upgrade-report.md` \| **GENERATED** \| Generated upgrade report \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 925 | `\| `docs/ci-cd-upgrade-report.md` \| **ARCHIVE CANDIDATE** \| One-time report \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 968 | `\| `docs/ci-cd-upgrade-report.md` \| One-time generated report. Zero external references. \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1101 | `- `docs/ci-cd-upgrade-report.md` → `docs/archive/generated/ci-cd-upgrade-report.md`` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 46 | `\| `docs/ci-cd-upgrade-report.md` \| 1 \| Generated Report \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 404 | `\| `docs/ci-cd-upgrade-report.md` \| ARCHIVE (generated/one-time report) \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 763 | `25. Move `docs/ci-cd-upgrade-report.md` to `docs/archive/generated/ci-cd-upgrade-report.md`` |
| PHASE_2_1_ARCHIVE_REPORT.md | 16 | `\| 2 \| `docs/ci-cd-upgrade-report.md` \| `docs/archive/reports/ci-cd-upgrade-report.md` \| `git mv` \| One-time gene...` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 342 | `\| `docs/ci-cd-upgrade-report.md` \| None \| SAFE \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 677 | `\| `docs/ci-cd-upgrade-report.md` \| Only referenced in plan itself \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 921 | `8. Move `docs/ci-cd-upgrade-report.md` to `docs/archive/generated/`` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 1037 | `\| Archiving `docs/ci-cd-upgrade-report.md` \| **LOW** \| No external references found \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 206 | `\| `docs/ci-cd-upgrade-report.md` \| ARCHIVE \| HIGH \| Only referenced in plan itself \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 228 | `8. Move `docs/ci-cd-upgrade-report.md` to `docs/archive/generated/`` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 366 | `\| Archive `docs/ci-cd-upgrade-report.md` \| **HIGH** \| No external references found \|` |
| PHASE_0_VALIDATION_REPORT.md | 354 | `\| `docs/ci-cd-upgrade-report.md` \| 0 verified \| No \| No \| No \| **SAFE** \| One-time generated report; zero exte...` |
| PHASE_0_VALIDATION_REPORT.md | 364 | `\| `docs/ci-cd-upgrade-report.md` \| One-time report; no canonical references \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/history/generated/architecture.json

- **Exists:** NO
- **Incoming References:** 14
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 147 | `- `docs/history/generated/architecture.json`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 887 | `\| `docs/history/generated/architecture.json` \| **GENERATED** \| Historical generated data \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 974 | `\| `docs/history/generated/architecture.json` \| Historical generated data. Zero external references. \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1086 | `- `docs/history/generated/architecture.json` → `docs/archive/generated/history-generated/`` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 279 | `\| `docs/history/generated/architecture.json` \| docs/history/ \| 122 KB \| Historical architecture data \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 284 | `- **ARCHIVE** `docs/history/generated/architecture.json` (historical, archived in wrong location).` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 364 | `\| `docs/history/generated/architecture.json` \| ARCHIVE \|` |
| PHASE_2_1_ARCHIVE_REPORT.md | 19 | `\| 5 \| `docs/history/generated/architecture.json` \| `docs/archive/generated/history-generated/architecture.json` \|...` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 348 | `\| `docs/history/generated/architecture.json` \| None \| SAFE \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 479 | `\| Historical Data \| `docs/history/generated/architecture.json` \| ~122 KB \| Historical \| No \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 689 | `\| `docs/history/generated/architecture.json` \| Only referenced in plan itself \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 916 | `3. Move `docs/history/generated/architecture.json` to `docs/archive/generated/history-generated/`` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 187 | `\| `docs/history/generated/architecture.json` \| ARCHIVE \| HIGH \| Only referenced in plan itself \|` |
| PHASE_0_VALIDATION_REPORT.md | 379 | `\| `docs/history/generated/architecture.json` \| Historical generated data; no canonical references \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/README.md

- **Exists:** YES
- **Incoming References:** 28
- **Outgoing References:** 25

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 526 | `\| `docs/rag/README.md` \| `../business-gaps/BUSINESS_GAPS_AUDIT.md` \| Directory does not exist \| Create directory ...` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 222 | `\| `docs/rag/README.md` \| `../business-gaps/BUSINESS_GAPS_AUDIT.md` \| Directory does not exist \|` |
| PHASE_1_1_REPAIR_REPORT.md | 23 | `- `docs/rag/README.md`` |
| PHASE_1_1_REPAIR_REPORT.md | 40 | `\| `docs/rag/README.md` \| Modified \| Removed broken references to `../business-gaps/BUSINESS_GAPS_AUDIT.md` and `.....` |
| PHASE_1_1_REPAIR_REPORT.md | 106 | `\| `docs/rag/README.md` \| 2 \| 0 \|` |
| PHASE_1_1_REPAIR_REPORT.md | 154 | `\| `docs/rag/README.md` describes outdated payment flow (Razorpay/Cashfree) \| Update to Year 1 manual UPI / Archive ...` |
| PHASE_1_2_GUARDIAN_REPAIR_REPORT.md | 148 | `**Test:** Temporarily added broken link `[Broken Link](nonexistent/broken/path.md)` to `README.md`` |
| README.md | 80 | `- [Business Rules](docs/business-rules/README.md)` |
| README.md | 81 | `- [AI Governance](docs/ai-governance/README.md)` |
| README.md | 82 | `- [ADR Index](docs/adr/README.md)` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 355 | `\| `docs/rag/README.md` \| RAG knowledge base index \|` |
| PHASE_0_VALIDATION_REPORT.md | 122 | `\| `docs/business-gaps/BUSINESS_GAPS_AUDIT.md` \| Referenced by `docs/business-rules/README.md` and `docs/rag/README....` |
| PHASE_0_VALIDATION_REPORT.md | 123 | `\| `docs/bugs/README.md` \| Referenced by `docs/rag/README.md` but does not exist \|` |
| PHASE_0_VALIDATION_REPORT.md | 137 | `\| Medium \| 2 \| `docs/business-rules/README.md` and `docs/rag/README.md` → missing `../business-gaps/BUSINESS_GAPS_...` |
| PHASE_0_VALIDATION_REPORT.md | 138 | `\| Medium \| 1 \| `docs/rag/README.md` → missing `../bugs/README.md` \|` |
| PHASE_0_VALIDATION_REPORT.md | 181 | `\| `docs/rag/README.md` \| `../bugs/README.md` \| Directory/file does not exist \|` |
| PHASE_0_VALIDATION_REPORT.md | 182 | `\| `docs/rag/README.md` \| `../business-gaps/BUSINESS_GAPS_AUDIT.md` \| Directory/file does not exist \|` |
| PHASE_0_VALIDATION_REPORT.md | 446 | `- Either create these directories/files or update `docs/business-rules/README.md` and `docs/rag/README.md` to remove ...` |
| docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md | 3 | `> **Per-domain rules:** See [business-rules/README.md](./business-rules/README.md) for separate files (buildings, ren...` |
| docs/README.md | 14 | `Full index: **[business-rules/README.md](./business-rules/README.md)**` |
| docs/README.md | 29 | `- [AI Governance](./ai-governance/README.md) — AI usage policies and standards` |
| docs/README.md | 30 | `- [Prompt Versioning](./ai/README.md) — versioned AI prompts for all modules` |
| docs/README.md | 34 | `- [ADR Index](./adr/README.md) — architectural decisions and rationale` |
| docs/README.md | 38 | `- [rag/](./rag/README.md) — self-contained chunks for RAG indexing` |
| architecture/adr/003-refactoring-strategy.md | 63 | `- [Architecture README](../../docs/architecture/README.md)` |
| architecture/adr/001-current-architecture.md | 41 | `- [Architecture README](../../docs/architecture/README.md)` |
| architecture/adr/002-target-architecture.md | 58 | `- [Architecture README](../../docs/architecture/README.md)` |
| properties/business_rules.md | 3 | `> **Moved:** Rules are split by domain under [`docs/business-rules/`](../docs/business-rules/README.md).` |

**Outgoing References:**

| Line | Type | Target | Context |
|------|------|--------|---------|
| 16 | markdown_link | `./project-summary.md` | `\| RAG-001 \| [project-summary.md](./project-summary.md) \| Product purpose, users, value \|` |
| 17 | markdown_link | `./tech-stack.md` | `\| RAG-002 \| [tech-stack.md](./tech-stack.md) \| Django, DRF, libraries, infra \|` |
| 18 | markdown_link | `./repository-structure.md` | `\| RAG-003 \| [repository-structure.md](./repository-structure.md) \| Where code lives \|` |
| 19 | markdown_link | `./django-apps-inventory.md` | `\| RAG-004 \| [django-apps-inventory.md](./django-apps-inventory.md) \| Installed apps, URL mounts \|` |
| 20 | markdown_link | `./data-model-core.md` | `\| RAG-005 \| [data-model-core.md](./data-model-core.md) \| User, subscription, OTP, bank \|` |
| 21 | markdown_link | `./data-model-properties.md` | `\| RAG-006 \| [data-model-properties.md](./data-model-properties.md) \| Building, Unit, Renter, RentRecord \|` |
| 22 | markdown_link | `./entity-relationships.md` | `\| RAG-007 \| [entity-relationships.md](./entity-relationships.md) \| FK graph, ownership \|` |
| 23 | markdown_link | `./api-authentication.md` | `\| RAG-008 \| [api-authentication.md](./api-authentication.md) \| OTP, JWT, password endpoints \|` |
| 24 | markdown_link | `./api-properties-owner.md` | `\| RAG-009 \| [api-properties-owner.md](./api-properties-owner.md) \| Owner CRUD & dashboard APIs \|` |
| 25 | markdown_link | `./api-properties-renter.md` | `\| RAG-010 \| [api-properties-renter.md](./api-properties-renter.md) \| Renter-facing rent APIs \|` |
| 26 | markdown_link | `./api-finance-documents.md` | `\| RAG-011 \| [api-finance-documents.md](./api-finance-documents.md) \| Tax, PDF, CA APIs \|` |
| 27 | markdown_link | `./subscription-and-limits.md` | `\| RAG-012 \| [subscription-and-limits.md](./subscription-and-limits.md) \| Plans, FeatureEnforcer, usage \|` |
| 28 | markdown_link | `./payments-razorpay-cashfree.md` | `\| RAG-013 \| [payments-razorpay-cashfree.md](./payments-razorpay-cashfree.md) \| Collect rent, payout, webhooks \|` |
| 29 | markdown_link | `./notifications-and-reminders.md` | `\| RAG-014 \| [notifications-and-reminders.md](./notifications-and-reminders.md) \| WhatsApp, email, FCM, voice \|` |
| 30 | markdown_link | `./external-integrations.md` | `\| RAG-015 \| [external-integrations.md](./external-integrations.md) \| Twilio, Leegality, OpenAI, S3 \|` |
| 31 | markdown_link | `./signals-celery-commands.md` | `\| RAG-016 \| [signals-celery-commands.md](./signals-celery-commands.md) \| Background jobs, automation \|` |
| 32 | markdown_link | `./smartbot-and-ai-assistant.md` | `\| RAG-017 \| [smartbot-and-ai-assistant.md](./smartbot-and-ai-assistant.md) \| Chatbot, AI services \|` |
| 33 | markdown_link | `./referral-program.md` | `\| RAG-018 \| [referral-program.md](./referral-program.md) \| Referral codes, bonuses \|` |
| 34 | markdown_link | `./glossary.md` | `\| RAG-019 \| [glossary.md](./glossary.md) \| Terms and enums \|` |
| 35 | markdown_link | `./environment-configuration.md` | `\| RAG-020 \| [environment-configuration.md](./environment-configuration.md) \| .env, settings keys \|` |
| 36 | markdown_link | `./known-issues-for-ai.md` | `\| RAG-021 \| [known-issues-for-ai.md](./known-issues-for-ai.md) \| Critical bugs summary (do not hallucinate fixes) \|` |
| 37 | markdown_link | `./business-rules-pointer.md` | `\| RAG-022 \| [business-rules-pointer.md](./business-rules-pointer.md) \| Index to human business-rules docs \|` |
| 38 | markdown_link | `./development-runbook.md` | `\| RAG-023 \| [development-runbook.md](./development-runbook.md) \| Run locally, test, migrate \|` |
| 42 | markdown_link | `../business-rules/README.md` | `- [business-rules/](../business-rules/README.md) — intended behavior by domain` |
| 43 | markdown_link | `../BUSINESS_LOGIC_AND_SUBSCRIPTION.md` | `- [BUSINESS_LOGIC_AND_SUBSCRIPTION.md](../BUSINESS_LOGIC_AND_SUBSCRIPTION.md) — long-form deep dive` |

---

### docs/rag/api-authentication.md

- **Exists:** YES
- **Incoming References:** 1
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| docs/rag/README.md | 23 | `\| RAG-008 \| [api-authentication.md](./api-authentication.md) \| OTP, JWT, password endpoints \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/api-finance-documents.md

- **Exists:** YES
- **Incoming References:** 1
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| docs/rag/README.md | 26 | `\| RAG-011 \| [api-finance-documents.md](./api-finance-documents.md) \| Tax, PDF, CA APIs \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/api-properties-owner.md

- **Exists:** YES
- **Incoming References:** 1
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| docs/rag/README.md | 24 | `\| RAG-009 \| [api-properties-owner.md](./api-properties-owner.md) \| Owner CRUD & dashboard APIs \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/api-properties-renter.md

- **Exists:** YES
- **Incoming References:** 1
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| docs/rag/README.md | 25 | `\| RAG-010 \| [api-properties-renter.md](./api-properties-renter.md) \| Renter-facing rent APIs \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/business-rules-pointer.md

- **Exists:** YES
- **Incoming References:** 1
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| docs/rag/README.md | 37 | `\| RAG-022 \| [business-rules-pointer.md](./business-rules-pointer.md) \| Index to human business-rules docs \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/data-model-core.md

- **Exists:** YES
- **Incoming References:** 1
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| docs/rag/README.md | 20 | `\| RAG-005 \| [data-model-core.md](./data-model-core.md) \| User, subscription, OTP, bank \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/data-model-properties.md

- **Exists:** YES
- **Incoming References:** 1
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| docs/rag/README.md | 21 | `\| RAG-006 \| [data-model-properties.md](./data-model-properties.md) \| Building, Unit, Renter, RentRecord \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/development-runbook.md

- **Exists:** YES
- **Incoming References:** 1
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| docs/rag/README.md | 38 | `\| RAG-023 \| [development-runbook.md](./development-runbook.md) \| Run locally, test, migrate \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/django-apps-inventory.md

- **Exists:** YES
- **Incoming References:** 1
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| docs/rag/README.md | 19 | `\| RAG-004 \| [django-apps-inventory.md](./django-apps-inventory.md) \| Installed apps, URL mounts \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/entity-relationships.md

- **Exists:** YES
- **Incoming References:** 1
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| docs/rag/README.md | 22 | `\| RAG-007 \| [entity-relationships.md](./entity-relationships.md) \| FK graph, ownership \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/environment-configuration.md

- **Exists:** YES
- **Incoming References:** 1
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| docs/rag/README.md | 35 | `\| RAG-020 \| [environment-configuration.md](./environment-configuration.md) \| .env, settings keys \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/external-integrations.md

- **Exists:** YES
- **Incoming References:** 1
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| docs/rag/README.md | 30 | `\| RAG-015 \| [external-integrations.md](./external-integrations.md) \| Twilio, Leegality, OpenAI, S3 \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/glossary.md

- **Exists:** YES
- **Incoming References:** 1
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| docs/rag/README.md | 34 | `\| RAG-019 \| [glossary.md](./glossary.md) \| Terms and enums \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/known-issues-for-ai.md

- **Exists:** YES
- **Incoming References:** 1
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| docs/rag/README.md | 36 | `\| RAG-021 \| [known-issues-for-ai.md](./known-issues-for-ai.md) \| Critical bugs summary (do not hallucinate fixes) \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/manifest.json

- **Exists:** YES
- **Incoming References:** 1
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 354 | `\| `docs/rag/manifest.json` \| RAG knowledge base manifest \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/notifications-and-reminders.md

- **Exists:** YES
- **Incoming References:** 5
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_ANALYSIS_REPORT.md | 79 | `- `docs/rag/notifications-and-reminders.md`: "**requires** `properties.apps.ready()` to import signals"` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 170 | `\| `docs/rag/notifications-and-reminders.md` \| Shows WhatsApp, SMS, Email, Push, Voice as active channels \|` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 296 | `\| `docs/rag/notifications-and-reminders.md` \| Describes WhatsApp/SMS as active channels, not "Coming Soon" \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 508 | `\| `docs/rag/notifications-and-reminders.md` \| "requires `properties.apps.ready()` to import signals" \|` |
| docs/rag/README.md | 29 | `\| RAG-014 \| [notifications-and-reminders.md](./notifications-and-reminders.md) \| WhatsApp, email, FCM, voice \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/payments-razorpay-cashfree.md

- **Exists:** YES
- **Incoming References:** 8
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 528 | `\| `docs/rag/payments-razorpay-cashfree.md` \| `docs/bugs/rentsecure_be.md`, `docs/bugs/core.md` \| Files do not exis...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 537 | `\| `docs/rag/payments-razorpay-cashfree.md` \| `rent.renter.property.owner` \| Uses `property` instead of `unit` \| F...` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 101 | `- `docs/rag/payments-razorpay-cashfree.md`: "**duplicate definitions** — last wins"` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 224 | `\| `docs/rag/payments-razorpay-cashfree.md` \| `docs/bugs/rentsecure_be.md`, `docs/bugs/core.md` \| Files do not exis...` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 234 | `\| `docs/rag/payments-razorpay-cashfree.md` \| `rent.renter.property.owner` \| Uses `property` instead of `unit` — po...` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 295 | `\| `docs/rag/payments-razorpay-cashfree.md` \| Focuses entirely on Razorpay/Cashfree, no mention of manual UPI \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 531 | `\| `docs/rag/payments-razorpay-cashfree.md` \| "duplicate definitions — last wins" \|` |
| docs/rag/README.md | 28 | `\| RAG-013 \| [payments-razorpay-cashfree.md](./payments-razorpay-cashfree.md) \| Collect rent, payout, webhooks \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/project-summary.md

- **Exists:** YES
- **Incoming References:** 5
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 527 | `\| `docs/rag/project-summary.md` \| `docs/bugs/` \| Directory does not exist \| Create directory or remove reference \|` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 171 | `\| `docs/rag/project-summary.md` \| "Notifications: WhatsApp, email, push (FCM), voice notes (gTTS)" \|` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 223 | `\| `docs/rag/project-summary.md` \| `docs/bugs/` \| Directory does not exist \|` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 293 | `\| `docs/rag/project-summary.md` \| Describes old payment flow: "renters pay rent via Razorpay; owners receive payout...` |
| docs/rag/README.md | 16 | `\| RAG-001 \| [project-summary.md](./project-summary.md) \| Product purpose, users, value \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/referral-program.md

- **Exists:** YES
- **Incoming References:** 3
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| docs/business-rules/15-authentication.md | 25 | `5. Optional **referral_code** on send — validated on verify (see [Referral](./19-referral-program.md)).` |
| docs/business-rules/README.md | 26 | `\| 19 \| [Referral program](./19-referral-program.md) \| `referral_and_earn` \|` |
| docs/rag/README.md | 33 | `\| RAG-018 \| [referral-program.md](./referral-program.md) \| Referral codes, bonuses \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/repository-structure.md

- **Exists:** YES
- **Incoming References:** 2
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_ANALYSIS_REPORT.md | 297 | `\| `docs/rag/repository-structure.md` \| Missing many top-level directories from actual structure \|` |
| docs/rag/README.md | 18 | `\| RAG-003 \| [repository-structure.md](./repository-structure.md) \| Where code lives \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/signals-celery-commands.md

- **Exists:** YES
- **Incoming References:** 1
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| docs/rag/README.md | 31 | `\| RAG-016 \| [signals-celery-commands.md](./signals-celery-commands.md) \| Background jobs, automation \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/smartbot-and-ai-assistant.md

- **Exists:** YES
- **Incoming References:** 1
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| docs/rag/README.md | 32 | `\| RAG-017 \| [smartbot-and-ai-assistant.md](./smartbot-and-ai-assistant.md) \| Chatbot, AI services \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/subscription-and-limits.md

- **Exists:** YES
- **Incoming References:** 1
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| docs/rag/README.md | 27 | `\| RAG-012 \| [subscription-and-limits.md](./subscription-and-limits.md) \| Plans, FeatureEnforcer, usage \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/rag/tech-stack.md

- **Exists:** YES
- **Incoming References:** 3
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_ANALYSIS_REPORT.md | 279 | `\| **Python version** \| Badge says Django 5.2, but `docs/rag/tech-stack.md` says Django 4.2.30 \|` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 294 | `\| `docs/rag/tech-stack.md` \| Lists Django 4.2.30 (outdated; README says 5.2) \|` |
| docs/rag/README.md | 17 | `\| RAG-002 \| [tech-stack.md](./tech-stack.md) \| Django, DRF, libraries, infra \|` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/refactoring/00_architecture_principles.md

- **Exists:** YES
- **Incoming References:** 16
- **Outgoing References:** 11

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 110 | `- `docs/refactoring/00_architecture_principles.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 984 | `\| `architecture/ARCHITECTURE_PRINCIPLES.md` \| Update 4 architecture/adr file references \| Superseded by docs/refac...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 144 | `\| `docs/refactoring/00_architecture_principles.md` \| docs/refactoring/ \| 51.7 KB \| Detailed principles with full ...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 148 | `- `docs/refactoring/00_architecture_principles.md` is the most comprehensive (51.7 KB, ratified version).` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 153 | `- **KEEP** `docs/refactoring/00_architecture_principles.md` as canonical.` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 319 | `\| `docs/refactoring/00_architecture_principles.md` \| Ratified architecture principles \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 442 | `\| `../ARCHITECTURE_PRINCIPLES.md` \| `docs/architecture/README.md` \| Fix path to `docs/refactoring/00_architecture_...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 471 | `\| A \| Single canonical: `docs/refactoring/00_architecture_principles.md` (51.7 KB) \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 521 | `\| `docs/architecture/README.md` \| `../ARCHITECTURE_PRINCIPLES.md` \| File does not exist at root \| Update to `docs...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 678 | `├── ARCHITECTURE_PRINCIPLES.md          # ARCHIVED — superseded by docs/refactoring/00_architecture_principles.md` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 828 | `\| `docs/refactoring/00_architecture_principles.md` \| Ratified architecture principles \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 336 | `\| Architecture Principles \| `docs/refactoring/00_architecture_principles.md` \| `architecture/ARCHITECTURE_PRINCIPL...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 399 | `\| Detailed Principles \| `docs/refactoring/00_architecture_principles.md` \| ~51.7 KB \| Ratified, comprehensive \| ...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 403 | `**Analysis:** `docs/refactoring/00_architecture_principles.md` is the supreme authority (51.7 KB, ratified 2026-07-15...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 405 | `**Recommendation:** Keep `docs/refactoring/00_architecture_principles.md` as canonical. Archive `architecture/ARCHITE...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 262 | `22. Update `docs/refactoring/00_architecture_principles.md` references if any external docs need to point to it` |

**Outgoing References:**

| Line | Type | Target | Context |
|------|------|--------|---------|
| 15 | markdown_link | `#1-purpose` | `1. [Purpose](#1-purpose)` |
| 16 | markdown_link | `#2-core-principles` | `2. [Core Principles](#2-core-principles)` |
| 17 | markdown_link | `#3-architectural-rules` | `3. [Architectural Rules](#3-architectural-rules)` |
| 18 | markdown_link | `#4-dependency-rules` | `4. [Dependency Rules](#4-dependency-rules)` |
| 19 | markdown_link | `#5-public-interface-rules` | `5. [Public Interface Rules](#5-public-interface-rules)` |
| 20 | markdown_link | `#6-error-handling-principles` | `6. [Error Handling Principles](#6-error-handling-principles)` |
| 21 | markdown_link | `#7-testing-principles` | `7. [Testing Principles](#7-testing-principles)` |
| 22 | markdown_link | `#8-refactoring-principles` | `8. [Refactoring Principles](#8-refactoring-principles)` |
| 23 | markdown_link | `#9-definition-of-done` | `9. [Definition of Done](#9-definition-of-done)` |
| 24 | markdown_link | `#10-future-architecture-vision` | `10. [Future Architecture Vision](#10-future-architecture-vision)` |
| 25 | markdown_link | `#11-appendix-architecture-commandments` | `11. [Appendix: Architecture Commandments](#11-appendix-architecture-commandments)` |

---

### docs/refactoring/01_target_architecture.md

- **Exists:** YES
- **Incoming References:** 12
- **Outgoing References:** 21

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 991 | `\| `docs/refactoring/01_target_architecture.md` \| Update references in 09, 10, 11, 12 if needed \| Superseded by 09_...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1195 | `- `docs/refactoring/01_target_architecture.md` → `docs/archive/planning/refactoring-complete/01_target_architecture.md`` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 248 | `\| `docs/refactoring/01_target_architecture.md` \| docs/refactoring/ \| 131.7 KB \| Target architecture specification \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 257 | `- **ARCHIVE** `docs/refactoring/01_target_architecture.md` (superseded).` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 398 | `\| `docs/refactoring/01_target_architecture.md` \| ARCHIVE \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 623 | `│   │   ├── target-architecture-v1.md   # From docs/refactoring/01_target_architecture.md` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 753 | `20. Move `docs/refactoring/01_target_architecture.md` to `docs/archive/planning/target-architecture-v1.md`` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 337 | `\| Target Architecture \| `docs/refactoring/09_target_architecture.md` \| `docs/refactoring/01_target_architecture.md...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 705 | `\| `docs/refactoring/01_target_architecture.md` \| Superseded by `09_target_architecture.md` \| Update `12_master_pla...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 81 | `\| `docs/refactoring/01_target_architecture.md` \| ARCHIVE \| **ARCHIVE** (safe) \| Only referenced within refactorin...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 205 | `\| `docs/refactoring/01_target_architecture.md` \| ARCHIVE \| HIGH \| Only referenced within refactoring folder \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 368 | `\| Archive `docs/refactoring/01_target_architecture.md` \| **HIGH** \| Only referenced within refactoring folder \|` |

**Outgoing References:**

| Line | Type | Target | Context |
|------|------|--------|---------|
| 15 | markdown_link | `#1-overall-architecture` | `1. [Overall Architecture](#1-overall-architecture)` |
| 16 | markdown_link | `#2-bounded-contexts` | `2. [Bounded Contexts](#2-bounded-contexts)` |
| 17 | markdown_link | `#3-folder-structure` | `3. [Folder Structure](#3-folder-structure)` |
| 18 | markdown_link | `#4-layer-architecture` | `4. [Layer Architecture](#4-layer-architecture)` |
| 19 | markdown_link | `#5-dependency-diagram` | `5. [Dependency Diagram](#5-dependency-diagram)` |
| 20 | markdown_link | `#6-request-lifecycle` | `6. [Request Lifecycle](#6-request-lifecycle)` |
| 21 | markdown_link | `#7-cross-context-communication` | `7. [Cross Context Communication](#7-cross-context-communication)` |
| 22 | markdown_link | `#8-shared-module` | `8. [Shared Module](#8-shared-module)` |
| 23 | markdown_link | `#9-external-integrations` | `9. [External Integrations](#9-external-integrations)` |
| 24 | markdown_link | `#10-caching-architecture` | `10. [Caching Architecture](#10-caching-architecture)` |
| 25 | markdown_link | `#11-background-processing` | `11. [Background Processing](#11-background-processing)` |
| 26 | markdown_link | `#12-error-architecture` | `12. [Error Architecture](#12-error-architecture)` |
| 27 | markdown_link | `#13-security-architecture` | `13. [Security Architecture](#13-security-architecture)` |
| 28 | markdown_link | `#14-performance-architecture` | `14. [Performance Architecture](#14-performance-architecture)` |
| 29 | markdown_link | `#15-scalability-vision` | `15. [Scalability Vision](#15-scalability-vision)` |
| 30 | markdown_link | `#16-testing-architecture` | `16. [Testing Architecture](#16-testing-architecture)` |
| 31 | markdown_link | `#17-coding-standards` | `17. [Coding Standards](#17-coding-standards)` |
| 32 | markdown_link | `#18-architecture-rules` | `18. [Architecture Rules](#18-architecture-rules)` |
| 33 | markdown_link | `#19-example-flows` | `19. [Example Flows](#19-example-flows)` |
| 34 | markdown_link | `#20-architecture-decision-summary` | `20. [Architecture Decision Summary](#20-architecture-decision-summary)` |
| 3006 | markdown_link | `#10-caching-architecture` | `See [Section 10: Caching Architecture](#10-caching-architecture).` |

---

### docs/refactoring/02_migration_roadmap.md

- **Exists:** YES
- **Incoming References:** 14
- **Outgoing References:** 18

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 992 | `\| `docs/refactoring/02_migration_roadmap.md` \| Update reference in 12_master_plan \| Superseded by 12_architecture_...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1196 | `- `docs/refactoring/02_migration_roadmap.md` → `docs/archive/planning/refactoring-complete/02_migration_roadmap.md`` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 162 | `\| `docs/refactoring/02_migration_roadmap.md` \| docs/refactoring/ \| 84.5 KB \| Detailed migration roadmap \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 174 | `- **ARCHIVE** `docs/refactoring/02_migration_roadmap.md` (superseded).` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 395 | `\| `docs/refactoring/02_migration_roadmap.md` \| ARCHIVE \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 621 | `│   │   ├── migration-roadmap.md        # From docs/refactoring/02_migration_roadmap.md` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 750 | `17. Move `docs/refactoring/02_migration_roadmap.md` to `docs/archive/planning/migration-roadmap.md`` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 338 | `\| Migration Roadmap \| `docs/refactoring/12_architecture_implementation_master_plan.md` \| `architecture/ROADMAP.md`...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 413 | `\| Migration Roadmap \| `docs/refactoring/02_migration_roadmap.md` \| ~84.5 KB \| Superseded \| No \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 418 | `**Recommendation:** Keep `docs/refactoring/12_architecture_implementation_master_plan.md` as canonical. Archive `arch...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 706 | `\| `docs/refactoring/02_migration_roadmap.md` \| Superseded by `12_master_plan.md` \| Update `12_master_plan` referen...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 82 | `\| `docs/refactoring/02_migration_roadmap.md` \| ARCHIVE \| **ARCHIVE** (safe) \| Only referenced within refactoring ...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 203 | `\| `docs/refactoring/02_migration_roadmap.md` \| ARCHIVE \| MEDIUM \| Referenced by `12_master_plan` (can update refe...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 369 | `\| Archive `docs/refactoring/02_migration_roadmap.md` \| **MEDIUM** \| Referenced by `12_master_plan` (can update) \|` |

**Outgoing References:**

| Line | Type | Target | Context |
|------|------|--------|---------|
| 15 | markdown_link | `#1-executive-summary` | `1. [Executive Summary](#1-executive-summary)` |
| 16 | markdown_link | `#2-current-state-assessment` | `2. [Current State Assessment](#2-current-state-assessment)` |
| 17 | markdown_link | `#3-migration-principles` | `3. [Migration Principles](#3-migration-principles)` |
| 18 | markdown_link | `#4-migration-phases` | `4. [Migration Phases](#4-migration-phases)` |
| 19 | markdown_link | `#5-pull-request-strategy` | `5. [Pull Request Strategy](#5-pull-request-strategy)` |
| 20 | markdown_link | `#6-git-workflow` | `6. [Git Workflow](#6-git-workflow)` |
| 21 | markdown_link | `#7-risk-register` | `7. [Risk Register](#7-risk-register)` |
| 22 | markdown_link | `#8-dependency-order` | `8. [Dependency Order](#8-dependency-order)` |
| 23 | markdown_link | `#9-testing-strategy-during-migration` | `9. [Testing Strategy During Migration](#9-testing-strategy-during-migration)` |
| 24 | markdown_link | `#10-ci-requirements` | `10. [CI Requirements](#10-ci-requirements)` |
| 25 | markdown_link | `#11-code-review-checklist` | `11. [Code Review Checklist](#11-code-review-checklist)` |
| 26 | markdown_link | `#12-definition-of-done` | `12. [Definition of Done](#12-definition-of-done)` |
| 27 | markdown_link | `#13-final-migration-checklist` | `13. [Final Migration Checklist](#13-final-migration-checklist)` |
| 28 | markdown_link | `#14-estimated-timeline` | `14. [Estimated Timeline](#14-estimated-timeline)` |
| 29 | markdown_link | `#15-ai-agent-workflow` | `15. [AI Agent Workflow](#15-ai-agent-workflow)` |
| 30 | markdown_link | `#16-long-term-maintenance-strategy` | `16. [Long-Term Maintenance Strategy](#16-long-term-maintenance-strategy)` |
| 1122 | markdown_link | `https://www.conventionalcommits.org/` | `Follows [Conventional Commits](https://www.conventionalcommits.org/):` |
| 1161 | markdown_link | `https://semver.org/` | `- Follows [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`.` |

---

### docs/refactoring/02_verified_dead_code_report.md

- **Exists:** YES
- **Incoming References:** 4
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 950 | `\| `docs/refactoring/02_verified_dead_code_report.md` \| Referenced by 2 refactoring files. Part of tightly-coupled c...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 352 | `\| `docs/refactoring/02_verified_dead_code_report.md` \| Referenced by 2 refactoring files \|` |
| docs/refactoring/03_dead_code_cleanup_execution_plan.md | 1196 | `- [ ] All stakeholders have approved `docs/refactoring/02_verified_dead_code_report.md`` |
| docs/refactoring/04_final_production_safety_report.md | 17 | `The 15 SAFE_DELETE candidates identified in `docs/refactoring/02_verified_dead_code_report.md` are confirmed safe to ...` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/refactoring/03_dead_code_cleanup_execution_plan.md

- **Exists:** YES
- **Incoming References:** 0
- **Outgoing References:** 0

**Incoming References:**

*No incoming references found.*

**Outgoing References:**

*No outgoing references found.*

---

### docs/refactoring/04_final_production_safety_report.md

- **Exists:** YES
- **Incoming References:** 0
- **Outgoing References:** 0

**Incoming References:**

*No incoming references found.*

**Outgoing References:**

*No outgoing references found.*

---

### docs/refactoring/05_dependency_rules.md

- **Exists:** NO
- **Incoming References:** 16
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 986 | `\| `architecture/dependency-rules.md` \| Update 3 architecture/adr file references + docs/architecture/05 reference \...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1001 | `\| `docs/architecture/future/05_dependency_rules.md` \| Full orphan validation \| Exact duplicate of docs/refactoring...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 182 | `\| `docs/refactoring/05_dependency_rules.md` \| docs/refactoring/ \| 7.9 KB \| Detailed dependency rules \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 186 | `- `docs/architecture/future/05_dependency_rules.md` is an exact duplicate of `docs/refactoring/05_dependency_rules.md...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 190 | `- **KEEP** `docs/refactoring/05_dependency_rules.md` as canonical.` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 425 | `\| `docs/architecture/future/05_dependency_rules.md` \| Exact duplicate of `docs/refactoring/05_dependency_rules.md` ...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 681 | `├── dependency-rules.md                 # ARCHIVED — superseded by docs/refactoring/05_dependency_rules.md` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 342 | `\| Dependency Rules \| `docs/refactoring/05_dependency_rules.md` \| `architecture/dependency-rules.md`, `docs/archite...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 424 | `\| Detailed Dependency Rules \| `docs/refactoring/05_dependency_rules.md` \| ~7.9 KB \| Comprehensive \| **YES** \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 428 | `**Analysis:** `docs/architecture/future/05_dependency_rules.md` is an exact byte-for-byte duplicate of `docs/refactor...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 731 | `\| `docs/architecture/future/05_dependency_rules.md` \| Exact byte-for-byte duplicate of `docs/refactoring/05_depende...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 60 | `The previous plan identified `docs/architecture/future/05_dependency_rules.md` as an "exact duplicate" of `docs/refac...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 409 | `Even if it is an exact duplicate of `docs/refactoring/05_dependency_rules.md`, it is **referenced by 3 canonical ADR ...` |
| docs/architecture/adr/ADR-006_import_rules.md | 106 | `- [Dependency Rules](../future/05_dependency_rules.md)` |
| docs/architecture/adr/ADR-008_shared_module_rules.md | 113 | `- [Dependency Rules](../future/05_dependency_rules.md)` |
| docs/architecture/adr/ADR-002_repository_pattern.md | 110 | `- [Dependency Rules](../future/05_dependency_rules.md)` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/refactoring/05_execution_report.md

- **Exists:** YES
- **Incoming References:** 0
- **Outgoing References:** 0

**Incoming References:**

*No incoming references found.*

**Outgoing References:**

*No outgoing references found.*

---

### docs/refactoring/06_architecture_audit.md

- **Exists:** YES
- **Incoming References:** 13
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 948 | `\| `docs/refactoring/06_architecture_audit.md` \| Referenced by `10_gap_analysis.md` and `05_execution_report.md`. Pa...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1197 | `- `docs/refactoring/06_architecture_audit.md` → `docs/archive/planning/refactoring-complete/06_architecture_audit.md`` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 236 | `\| `docs/refactoring/06_architecture_audit.md` \| docs/refactoring/ \| 41.9 KB \| Architecture audit findings \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 242 | `- **ARCHIVE** `docs/refactoring/06_architecture_audit.md` (superseded).` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 397 | `\| `docs/refactoring/06_architecture_audit.md` \| ARCHIVE \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 752 | `19. Move `docs/refactoring/06_architecture_audit.md` to `docs/archive/audits/architecture-audit-findings.md`` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 469 | `\| Refactoring Audit \| `docs/refactoring/06_architecture_audit.md` \| ~41.9 KB \| Superseded \| No \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 708 | `\| `docs/refactoring/06_architecture_audit.md` \| Superseded by `production-architecture.md` \| Update `10_gap_analys...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 36 | `\| `docs/refactoring/06_architecture_audit.md` \| `docs/refactoring/10_architecture_gap_analysis.md` + `05_execution_...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 78 | `\| `docs/refactoring/06_architecture_audit.md` \| ARCHIVE \| **KEEP** or update 2 references first \| Referenced by `...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 351 | `\| `docs/refactoring/06_architecture_audit.md` \| Referenced by 2 refactoring files \|` |
| docs/refactoring/10_architecture_gap_analysis.md | 10 | `**Baseline Audit:** `docs/refactoring/06_architecture_audit.md`` |
| docs/refactoring/05_execution_report.md | 197 | `3. **Complete the DDD architecture audit** (`docs/refactoring/06_architecture_audit.md`) to understand ideal module p...` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/refactoring/07_migration_plan.md

- **Exists:** YES
- **Incoming References:** 0
- **Outgoing References:** 0

**Incoming References:**

*No incoming references found.*

**Outgoing References:**

*No outgoing references found.*

---

### docs/refactoring/08_architecture_decisions.md

- **Exists:** YES
- **Incoming References:** 12
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 949 | `\| `docs/refactoring/08_architecture_decisions.md` \| Referenced by 4 files (09, 10, 11, 12). Part of tightly-coupled...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1198 | `- `docs/refactoring/08_architecture_decisions.md` → `docs/archive/planning/refactoring-complete/08_architecture_decis...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 37 | `\| `docs/refactoring/08_architecture_decisions.md` \| `09`, `10`, `11`, `12` (all kept files) \| Breaks 7+ references...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 79 | `\| `docs/refactoring/08_architecture_decisions.md` \| Not explicitly listed, but implied \| **KEEP** \| Referenced by...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 350 | `\| `docs/refactoring/08_architecture_decisions.md` \| Referenced by 4 kept refactoring files \|` |
| docs/refactoring/11_architecture_roadmap_review.md | 12 | `**ADRs:** `docs/refactoring/08_architecture_decisions.md`` |
| docs/refactoring/12_architecture_implementation_master_plan.md | 11 | `- `docs/refactoring/08_architecture_decisions.md` — ADRs (10 decisions)` |
| docs/refactoring/12_architecture_implementation_master_plan.md | 676 | `- `docs/refactoring/08_architecture_decisions.md` (append new ADRs)` |
| docs/refactoring/12_architecture_implementation_master_plan.md | 1375 | `- `docs/refactoring/08_architecture_decisions.md` (updated)` |
| docs/refactoring/09_target_architecture.md | 1642 | `**Location:** `docs/refactoring/08_architecture_decisions.md`` |
| docs/refactoring/10_architecture_gap_analysis.md | 11 | `**ADRs:** `docs/refactoring/08_architecture_decisions.md`` |
| docs/refactoring/10_architecture_gap_analysis.md | 53 | `\| **Existing ADRs** \| Architecture decisions are documented \| `docs/refactoring/08_architecture_decisions.md` with...` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/refactoring/09_target_architecture.md

- **Exists:** YES
- **Incoming References:** 9
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 111 | `- `docs/refactoring/09_target_architecture.md`` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 249 | `\| `docs/refactoring/09_target_architecture.md` \| docs/refactoring/ \| 70.0 KB \| Updated target architecture \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 256 | `- **KEEP** `docs/refactoring/09_target_architecture.md` as canonical (more recent).` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 320 | `\| `docs/refactoring/09_target_architecture.md` \| Updated target architecture \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 829 | `\| `docs/refactoring/09_target_architecture.md` \| Target architecture \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 337 | `\| Target Architecture \| `docs/refactoring/09_target_architecture.md` \| `docs/refactoring/01_target_architecture.md...` |
| docs/refactoring/11_architecture_roadmap_review.md | 11 | `**Target Architecture:** `docs/refactoring/09_target_architecture.md`` |
| docs/refactoring/12_architecture_implementation_master_plan.md | 12 | `- `docs/refactoring/09_target_architecture.md` — Target Architecture Design` |
| docs/refactoring/10_architecture_gap_analysis.md | 9 | `**Source Document:** `docs/refactoring/09_target_architecture.md`` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/refactoring/10_architecture_gap_analysis.md

- **Exists:** YES
- **Incoming References:** 5
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1199 | `- `docs/refactoring/10_architecture_gap_analysis.md` → `docs/archive/planning/refactoring-complete/10_architecture_ga...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 263 | `\| `docs/refactoring/10_architecture_gap_analysis.md` \| docs/refactoring/ \| 77.4 KB \| Architecture gap analysis \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 36 | `\| `docs/refactoring/06_architecture_audit.md` \| `docs/refactoring/10_architecture_gap_analysis.md` + `05_execution_...` |
| docs/refactoring/11_architecture_roadmap_review.md | 10 | `**Reviewed Document:** `docs/refactoring/10_architecture_gap_analysis.md`` |
| docs/refactoring/12_architecture_implementation_master_plan.md | 13 | `- `docs/refactoring/10_architecture_gap_analysis.md` — Gap Analysis (18/100 score)` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/refactoring/11_architecture_roadmap_review.md

- **Exists:** YES
- **Incoming References:** 15
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 993 | `\| `docs/refactoring/11_architecture_roadmap_review.md` \| Update reference in 12_master_plan \| Superseded by 12_arc...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1200 | `- `docs/refactoring/11_architecture_roadmap_review.md` → `docs/archive/planning/refactoring-complete/11_architecture_...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 163 | `\| `docs/refactoring/11_architecture_roadmap_review.md` \| docs/refactoring/ \| 63.2 KB \| Roadmap review and assessm...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 175 | `- **ARCHIVE** `docs/refactoring/11_architecture_roadmap_review.md` (superseded).` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 396 | `\| `docs/refactoring/11_architecture_roadmap_review.md` \| ARCHIVE \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 622 | `│   │   ├── roadmap-review.md           # From docs/refactoring/11_architecture_roadmap_review.md` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 751 | `18. Move `docs/refactoring/11_architecture_roadmap_review.md` to `docs/archive/planning/roadmap-review.md`` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 338 | `\| Migration Roadmap \| `docs/refactoring/12_architecture_implementation_master_plan.md` \| `architecture/ROADMAP.md`...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 414 | `\| Roadmap Review \| `docs/refactoring/11_architecture_roadmap_review.md` \| ~63.2 KB \| Superseded \| No \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 418 | `**Recommendation:** Keep `docs/refactoring/12_architecture_implementation_master_plan.md` as canonical. Archive `arch...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 707 | `\| `docs/refactoring/11_architecture_roadmap_review.md` \| Superseded by `12_master_plan.md` \| Update `12_master_pla...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 83 | `\| `docs/refactoring/11_architecture_roadmap_review.md` \| ARCHIVE \| **ARCHIVE** (safe) \| Only referenced by `12_ma...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 204 | `\| `docs/refactoring/11_architecture_roadmap_review.md` \| ARCHIVE \| MEDIUM \| Referenced by `12_master_plan` (can u...` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 370 | `\| Archive `docs/refactoring/11_architecture_roadmap_review.md` \| **MEDIUM** \| Referenced by `12_master_plan` (can ...` |
| docs/refactoring/12_architecture_implementation_master_plan.md | 14 | `- `docs/refactoring/11_architecture_roadmap_review.md` — Roadmap Review & Redesign` |

**Outgoing References:**

*No outgoing references found.*

---

### docs/refactoring/12_architecture_implementation_master_plan.md

- **Exists:** YES
- **Incoming References:** 15
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 112 | `- `docs/refactoring/12_architecture_implementation_master_plan.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 985 | `\| `architecture/ROADMAP.md` \| Update 3 architecture/adr file references \| Superseded by docs/refactoring/12_archit...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1117 | `4. Update `architecture/adr/001-current-architecture.md` line 45: `docs/architecture/README.md` → `docs/refactoring/1...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 164 | `\| `docs/refactoring/12_architecture_implementation_master_plan.md` \| docs/refactoring/ \| 92.4 KB \| Master impleme...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 168 | `- `docs/refactoring/12_architecture_implementation_master_plan.md` appears to be the most recent and comprehensive (9...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 172 | `- **KEEP** `docs/refactoring/12_architecture_implementation_master_plan.md` as canonical (most recent, most comprehen...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 321 | `\| `docs/refactoring/12_architecture_implementation_master_plan.md` \| Master implementation plan \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 444 | `\| `../ROADMAP.md` \| `docs/architecture/README.md` \| Fix path to `docs/refactoring/12_architecture_implementation_m...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 523 | `\| `docs/architecture/README.md` \| `../ROADMAP.md` \| File does not exist at root \| Update to `docs/refactoring/12_...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 680 | `├── ROADMAP.md                          # ARCHIVED — superseded by docs/refactoring/12_architecture_implementation_ma...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 830 | `\| `docs/refactoring/12_architecture_implementation_master_plan.md` \| Master implementation plan \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 338 | `\| Migration Roadmap \| `docs/refactoring/12_architecture_implementation_master_plan.md` \| `architecture/ROADMAP.md`...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 411 | `\| Master Plan \| `docs/refactoring/12_architecture_implementation_master_plan.md` \| ~92.4 KB \| Most recent, compre...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 416 | `**Analysis:** Four roadmap documents with significant overlap. `docs/refactoring/12_architecture_implementation_maste...` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 418 | `**Recommendation:** Keep `docs/refactoring/12_architecture_implementation_master_plan.md` as canonical. Archive `arch...` |

**Outgoing References:**

*No outgoing references found.*

---

### properties/business_rules.md

- **Exists:** YES
- **Incoming References:** 44
- **Outgoing References:** 1

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 187 | `\| `properties/business_rules.md` \| Legacy single-file business rules \| Domain Owner (properties) \| Historians \| ...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 860 | `\| `properties/business_rules.md` \| **REFERENCE** \| Legacy single-file business rules \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 926 | `\| `properties/business_rules.md` \| **ARCHIVE CANDIDATE** \| Legacy, 311 bytes, 4 references must update \|` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 994 | `\| `properties/business_rules.md` \| Update 4 references in docs/business-rules/* \| Legacy single-file version. 311 ...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1215 | `1. Update all references to `properties/business_rules.md` to point to `docs/business-rules/`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1218 | `- `properties/business_rules.md` → `docs/archive/deprecated/legacy-business-rules.md`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1781 | `\| **Reference** \| 4 \| docs/adr/, architecture/baseline/, properties/business_rules.md \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 101 | `\| `properties/business_rules.md` \| 1 \| Obsolete (legacy) \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 406 | `\| `properties/business_rules.md` \| ARCHIVE (legacy single-file, 311 bytes) \|` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 502 | `### 6.6 `properties/business_rules.md`` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 529 | `\| `docs/business-rules/00-overview.md` \| `properties/business_rules.md` \| Legacy file, 311 bytes \| Update or remo...` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 649 | `│   │   └── legacy-business-rules.md    # From properties/business_rules.md` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 762 | `24. Move `properties/business_rules.md` to `docs/archive/deprecated/legacy-business-rules.md`` |
| DOCUMENTATION_CONSOLIDATION_PLAN.md | 773 | `30. Update `docs/business-rules/00-overview.md` reference to `properties/business_rules.md`` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 225 | `\| `docs/business-rules/00-overview.md` \| `properties/business_rules.md` \| File exists but is 311 bytes (likely ver...` |
| DOCUMENTATION_ANALYSIS_REPORT.md | 249 | `- `properties/business_rules.md` — legacy single-file version (311 bytes)` |
| PHASE_2_1_ARCHIVE_REPORT.md | 171 | `\| `properties/business_rules.md` \| **PENDING** \| Requires 1 reference update first \|` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 365 | `\| `properties/business_rules.md` \| docs/business-rules/README.md \| Update 1 reference first \|` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 421 | `- Archive `properties/business_rules.md` (1 reference must update)` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 300 | `\| `properties/business_rules.md` \| ~311 B \| Legacy Business Rules \| Obsolete \| Engineering \| Obsolete \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 328 | `\| Business Rules Index \| `docs/business-rules/README.md` \| `properties/business_rules.md` (legacy) \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 648 | `\| `properties/business_rules.md` \| 311-byte legacy single-file version; superseded by `docs/business-rules/` \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 709 | `\| `properties/business_rules.md` \| Legacy single-file \| Update 4 references in `docs/business-rules/` \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 931 | `13. Update `docs/business-rules/00-overview.md` line 38: `properties/business_rules.md` reference` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 932 | `14. Update `docs/business-rules/README.md` line 36: `properties/business_rules.md` reference` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 933 | `15. Update `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` lines 41, 392: `properties/business_rules.md` reference` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 985 | `### Phase 8: Archive `properties/business_rules.md` (After References Updated)` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 988 | `38. Move `properties/business_rules.md` to `docs/archive/deprecated/legacy-business-rules.md`` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 1027 | `\| Archiving `properties/business_rules.md` \| **MEDIUM** \| Referenced by 4 docs; safe after reference updates \|` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 213 | `\| `properties/business_rules.md` \| ARCHIVE \| MEDIUM \| Referenced by 4 documents; archive after updating reference...` |
| ... | ... | *... and 14 more* |

**Outgoing References:**

| Line | Type | Target | Context |
|------|------|--------|---------|
| 3 | markdown_link | `../docs/business-rules/README.md` | `> **Moved:** Rules are split by domain under [`docs/business-rules/`](../docs/business-rules/README.md).` |

---

### scripts/diagrams/documentation_guardian.py

- **Exists:** YES
- **Incoming References:** 28
- **Outgoing References:** 0

**Incoming References:**

| Source File | Line | Context |
|-------------|------|---------|
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 203 | `\| `scripts/diagrams/documentation_guardian.py` \| Documentation drift detector \| Senior DevOps \| CI/CD \| Permanen...` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 366 | `scripts/diagrams/documentation_guardian.py (lines 91, 97)` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 552 | `- `python scripts/diagrams/documentation_guardian.py` passes` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 656 | `**Tool:** `python scripts/diagrams/documentation_guardian.py`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 702 | `**Tool:** `python scripts/diagrams/documentation_guardian.py`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 771 | `run: python scripts/diagrams/documentation_guardian.py` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1025 | `1. Run full Documentation Guardian scan: `python scripts/diagrams/documentation_guardian.py`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1115 | `2. Update `scripts/diagrams/documentation_guardian.py` lines 91, 97: `docs/adr/` → `docs/architecture/adr/`` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1602 | `- `scripts/diagrams/documentation_guardian.py` runs on every PR` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1703 | `scripts/diagrams/documentation_guardian.py` |
| DOCUMENTATION_GOVERNANCE_SPECIFICATION.md | 1719 | `← scripts/diagrams/documentation_guardian.py (lines 91, 97)` |
| PHASE_1_2_GUARDIAN_REPAIR_REPORT.md | 15 | `\| `scripts/diagrams/documentation_guardian.py` \| Modified \| Repaired broken link validation, required doc validati...` |
| PHASE_1_2_GUARDIAN_REPAIR_REPORT.md | 193 | `\| Script location \| ✅ Preserved \| Still at `scripts/diagrams/documentation_guardian.py` \|` |
| PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md | 177 | `\| `scripts/diagrams/documentation_guardian.py` \| Updated to `docs/architecture/adr/` \| OK \|` |
| PHASE_3_1_DOCUMENTATION_CONSOLIDATION_AUDIT.md | 929 | `11. Update `scripts/diagrams/documentation_guardian.py` lines 91-99: `docs/adr/` → `docs/architecture/adr/`` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 150 | `- `scripts/diagrams/documentation_guardian.py` (lines 93, 99)` |
| DOCUMENTATION_CONSOLIDATION_REVIEW.md | 235 | `10. Update `scripts/diagrams/documentation_guardian.py` lines 91-99: `docs/adr/` → `docs/architecture/adr/`` |
| PHASE_0_VALIDATION_REPORT.md | 103 | `scripts/diagrams/documentation_guardian.py` |
| PHASE_0_VALIDATION_REPORT.md | 191 | ``scripts/diagrams/documentation_guardian.py`` |
| PHASE_0_VALIDATION_REPORT.md | 255 | `\| `scripts/diagrams/documentation_guardian.py` \| `docs/adr/README.md` \| Hardcoded path \| ADR index check fails \|` |
| PHASE_0_VALIDATION_REPORT.md | 256 | `\| `scripts/diagrams/documentation_guardian.py` \| `docs/README.md` \| Hardcoded required doc \| Missing doc check fa...` |
| PHASE_0_VALIDATION_REPORT.md | 257 | `\| `scripts/diagrams/documentation_guardian.py` \| `docs/architecture-contract.md` \| Hardcoded required doc \| Missi...` |
| PHASE_0_VALIDATION_REPORT.md | 258 | `\| `scripts/diagrams/documentation_guardian.py` \| `docs/ci-cd-pipeline.md` \| Hardcoded required doc \| Missing doc ...` |
| PHASE_0_VALIDATION_REPORT.md | 259 | `\| `scripts/diagrams/documentation_guardian.py` \| `docs/governance.md` \| Hardcoded required doc \| Missing doc chec...` |
| PHASE_0_VALIDATION_REPORT.md | 282 | `- `scripts/diagrams/documentation_guardian.py` lines 91, 97 break.` |
| PHASE_0_VALIDATION_REPORT.md | 419 | `1. **Fix Documentation Guardian** (`scripts/diagrams/documentation_guardian.py`):` |
| PHASE_0_VALIDATION_REPORT.md | 462 | `- Update `scripts/diagrams/documentation_guardian.py` lines 91, 97.` |
| docs/architecture/audit_data.json | 275 | `"/Users/sbairagi/Desktop/MVP Project/RentSecureBE/scripts/diagrams/documentation_guardian.py",` |

**Outgoing References:**

*No outgoing references found.*

---
