# Phase 3.1 — Documentation Consolidation Audit

**Document:** Documentation Consolidation Audit — Phase 3.1
**Version:** 1.0.0
**Date:** 2026-07-18
**Analyst:** Kilo (Read-Only Analysis)
**Status:** AUDIT COMPLETE — READ-ONLY
**Scope:** All documentation in `docs/`, `architecture/`, `.kilo/`, repository root, and module-level docs

---

## 1. Executive Summary

The RentSecureBE repository contains **~215 documentation files** spread across **7 major directories** with significant sprawl, duplication, and obsolescence. Three distinct generations of architecture documentation exist simultaneously. Duplicate ADR collections, multiple overlapping roadmaps, extensive generated reports at the repository root, and numerous outdated documents contradict the current Year 1 architecture strategy.

This audit identifies:
- **3 duplicate ADR collections** (4 + 18 + 23 files)
- **6 duplicate architecture principle/roadmap/dependency-rule sets**
- **~40 safe archive candidates** (generated reports, diagrams, superseded docs)
- **2 safe deletion candidates** (1 exact duplicate + 1 empty placeholder)
- **1 tightly-coupled collection** (`docs/refactoring/`) that must be kept or archived as a unit
- **1 canonical reference collection** (`docs/architecture/future/`) that must remain in place
- **Multiple conflicting documents** (Cashfree/Razorpay references in `README.md` and `docs/ci-cd-pipeline.md` vs. Year 1 manual UPI strategy)
- **Multiple obsolete documents** (RAG knowledge base, outdated business rules)

**This report recommends a single-source-of-truth documentation structure without modifying any files.**

**Key finding from prior review:** The earlier `DOCUMENTATION_CONSOLIDATION_PLAN.md` (2026-07-17) correctly identified sprawl but contained **critical reference-tracing failures**. The subsequent `DOCUMENTATION_CONSOLIDATION_REVIEW.md` (2026-07-17) corrected those failures. This audit incorporates both analyses and adds additional findings.

---

## 2. Complete Document Inventory

### 2.1 Repository Root (`/Users/sbairagi/Desktop/MVP Project/RentSecureBE/`)

| File | Size (est.) | Category | Last Relevance | Owner | Status |
|------|-------------|----------|----------------|-------|--------|
| `README.md` | ~5.0 KB | Project README | Active | Engineering | Outdated (Cashfree refs) |
| `PHASE_0_VALIDATION_REPORT.md` | ~3.0 KB | Phase Report | Historical | Architect | Stale |
| `PHASE_1_1_REPAIR_REPORT.md` | ~2.0 KB | Phase Report | Historical | Architect | Stale |
| `PHASE_1_2_GUARDIAN_REPAIR_REPORT.md` | ~2.5 KB | Phase Report | Historical | Architect | Stale |
| `PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md` | ~4.0 KB | Phase Report | Historical | Architect | Stale |
| `PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md` | ~6.0 KB | Phase Report | Historical | Architect | Stale |
| `PHASE_2_1_ARCHIVE_REPORT.md` | ~3.5 KB | Phase Report | Historical | Architect | Stale |
| `DOCUMENTATION_GOVERNANCE_SPECIFICATION.md` | ~8.0 KB | Governance | Active | Architect | Canonical |
| `DOCUMENTATION_ANALYSIS_REPORT.md` | ~24.1 KB | Generated Report | 2026-07-14 | Kilo | Generated |
| `DOCUMENTATION_CONSOLIDATION_PLAN.md` | ~24.0 KB | Generated Report | 2026-07-17 | Kilo | Generated |
| `DOCUMENTATION_CONSOLIDATION_REVIEW.md` | ~16.5 KB | Generated Report | 2026-07-17 | Kilo | Generated |
| `01_repository_inventory.md` | ~6.9 KB | Generated Report | Historical | Kilo | Generated |
| `directory-structure-analysis.md` | ~40.1 KB | Generated Report | Historical | Kilo | Generated |
| `architecture-analysis-report.md` | ~36.7 KB | Generated Report | Historical | Kilo | Generated |
| `architecture-compliance-report.md` | ~3.0 KB | Generated Report | Historical | Kilo | Generated |
| `architecture-compliance-report.json` | ~5.8 KB | Generated Data | Historical | Kilo | Generated |
| `architecture-dependency-graph.mmd` | ~1.6 KB | Generated Diagram | Historical | Kilo | Generated |
| `architecture-dependency-graph.dot` | ~2.2 KB | Generated Diagram | Historical | Kilo | Generated |
| `architecture-summary.txt` | ~108 B | Generated Report | Historical | Kilo | Generated |
| `coverage-report.txt` | 0 B | Generated Placeholder | N/A | CI | Empty |
| `requirements.txt` | ~4.0 KB | Dependencies | Active | Engineering | Canonical |

### 2.2 `docs/` Directory

#### 2.2.1 Root-level docs

| File | Size (est.) | Category | Last Relevance | Owner | Status |
|------|-------------|----------|----------------|-------|--------|
| `README.md` | ~5.0 KB | Documentation Index | Active | Engineering | Canonical |
| `governance.md` | ~6.0 KB | CI/CD Governance | Active | Engineering | Canonical |
| `ci-cd-pipeline.md` | ~15.0 KB | CI/CD Pipeline Docs | Active | Engineering | Outdated |
| `architecture-contract.md` | ~8.0 KB | Architecture Contract | Active | Engineering | Canonical |
| `kilo-architecture-spec.md` | ~7.0 KB | Kilo Spec | Active | Engineering | Canonical |
| `BUSINESS_LOGIC_AND_SUBSCRIPTION.md` | ~14.0 KB | Business Logic | Active | Engineering | Outdated |

#### 2.2.2 `docs/adr/` — Short ADR Collection

| File | Size (est.) | Category | Last Relevance | Owner | Status |
|------|-------------|----------|----------------|-------|--------|
| `README.md` | ~2.5 KB | ADR Index | Active | Engineering | Duplicate |
| `ADR-001.md` – `ADR-012.md` | ~1.0 KB each | Short ADRs | 2026-01-15 | Engineering | Duplicate |
| `ADR-031.md` – `ADR-036.md` | ~1.0 KB each | Short ADRs | 2026-07-14 | Engineering | Duplicate |
| `ADR-013.md` – `ADR-030.md` | MISSING | Missing ADRs | N/A | Engineering | Gap |

#### 2.2.3 `docs/architecture/` — Architecture Analysis

| File | Size (est.) | Category | Last Relevance | Owner | Status |
|------|-------------|----------|----------------|-------|--------|
| `README.md` | ~8.0 KB | Architecture Index | 2026-07-14 | Kilo | Generated |
| `production-architecture.md` | ~39.3 KB | Production Strategy | Active | Engineering | Canonical |
| `architecture-audit-report.md` | ~40.1 KB | Audit Report | 2026-07-14 | Kilo | Generated |
| `audit_data.json` | ~198 KB | Audit Data | 2026-07-14 | Kilo | Generated |
| `01_dependency_graph.md` | ~3.0 KB | Generated Report | 2026-07-14 | Kilo | Generated |
| `02_import_matrix.md` | ~2.5 KB | Generated Report | 2026-07-14 | Kilo | Generated |
| `03_circular_dependencies.md` | ~1.5 KB | Generated Report | 2026-07-14 | Kilo | Generated |
| `04_cross_app_dependencies.md` | ~4.0 KB | Generated Report | 2026-07-14 | Kilo | Generated |
| `05_architecture_boundary_violations.md` | ~3.5 KB | Generated Report | 2026-07-14 | Kilo | Generated |
| `06_dead_modules.md` | ~2.0 KB | Generated Report | 2026-07-14 | Kilo | Generated |
| `07_hotspots.md` | ~2.5 KB | Generated Report | 2026-07-14 | Kilo | Generated |
| `08_import_linter_audit.md` | ~3.0 KB | Generated Report | 2026-07-14 | Kilo | Generated |
| `09_dependency_metrics.md` | ~2.0 KB | Generated Report | 2026-07-14 | Kilo | Generated |

#### 2.2.4 `docs/architecture/adr/` — Detailed ADR Collection

| File | Size (est.) | Category | Last Relevance | Owner | Status |
|------|-------------|----------|----------------|-------|--------|
| `README.md` | ~2.5 KB | ADR Index | Active | Engineering | Canonical |
| `ADR-001_modular_monolith.md` – `ADR-023_search_strategy.md` | ~3.0 KB each | Detailed ADRs | 2026-07-14 | Engineering | Canonical |

#### 2.2.5 `docs/architecture/future/` — Future Architecture Vision

| File | Size (est.) | Category | Last Relevance | Owner | Status |
|------|-------------|----------|----------------|-------|--------|
| `01_architecture_vision.md` | ~5.0 KB | Future Vision | Active | Engineering | Canonical |
| `02_bounded_contexts.md` | ~16.6 KB | Bounded Contexts | Active | Engineering | Canonical |
| `03_target_folder_structure.md` | ~4.0 KB | Folder Structure | Active | Engineering | Canonical |
| `04_layer_rules.md` | ~6.0 KB | Layer Rules | Active | Engineering | Canonical |
| `05_dependency_rules.md` | ~7.9 KB | Dependency Rules | Active | Engineering | Canonical |
| `06_module_responsibilities.md` | ~12.7 KB | Module Responsibilities | Active | Engineering | Canonical |
| `07_domain_events.md` | ~3.5 KB | Domain Events | Active | Engineering | Canonical |
| `08_repository_pattern.md` | ~4.0 KB | Repository Pattern | Active | Engineering | Canonical |
| `09_service_layer.md` | ~5.0 KB | Service Layer | Active | Engineering | Canonical |
| `10_naming_conventions.md` | ~3.0 KB | Naming Conventions | Active | Engineering | Canonical |
| `11_migration_strategy.md` | ~4.5 KB | Migration Strategy | Active | Engineering | Canonical |

#### 2.2.6 `docs/architecture/reviews/`

| File | Size (est.) | Category | Last Relevance | Owner | Status |
|------|-------------|----------|----------------|-------|--------|
| `01_future_architecture_review.md` | ~6.0 KB | Architecture Review | 2026-07-14 | Engineering | Canonical |

#### 2.2.7 `docs/archive/`

| File | Size (est.) | Category | Last Relevance | Owner | Status |
|------|-------------|----------|----------------|-------|--------|
| `audits/architecture-audit-report.md` | ~40.1 KB | Archived Audit | Historical | Kilo | Archived |
| `reports/ci-cd-upgrade-report.md` | ~3.0 KB | Archived Report | Historical | Kilo | Archived |
| `reports/baseline/architecture-baseline.md` | ~1270 lines | Archived Baseline | Historical | Architect | Archived |
| `reports/baseline/architecture-baseline-validation.md` | ~2.0 KB | Archived Baseline | Historical | Architect | Archived |

#### 2.2.8 `docs/ai/` — AI Prompts

| File | Size (est.) | Category | Last Relevance | Owner | Status |
|------|-------------|----------|----------------|-------|--------|
| `README.md` | ~1.5 KB | AI Prompt Index | Active | Engineering | Canonical |
| `prompts/v1/uml/class-diagram-generation.prompt.md` | ~2.0 KB | AI Prompt | Active | Engineering | Canonical |
| `prompts/v1/review/architecture-compliance.prompt.md` | ~2.5 KB | AI Prompt | Active | Engineering | Canonical |

#### 2.2.9 `docs/ai-governance/` — AI Governance

| File | Size (est.) | Category | Last Relevance | Owner | Status |
|------|-------------|----------|----------------|-------|--------|
| `README.md` | ~1.5 KB | AI Governance Index | Active | Engineering | Canonical |
| `AI-Architecture-Review.md` | ~2.0 KB | AI Policy | Active | Engineering | Canonical |
| `AI-Code-Review.md` | ~2.5 KB | AI Policy | Active | Engineering | Canonical |
| `AI-Contribution-Guide.md` | ~3.0 KB | AI Policy | Active | Engineering | Canonical |
| `AI-Decision-Record.md` | ~2.0 KB | AI Template | Active | Engineering | Canonical |
| `AI-Documentation-Standards.md` | ~2.5 KB | AI Standard | Active | Engineering | Canonical |
| `AI-Rules.md` | ~2.0 KB | AI Policy | Active | Engineering | Canonical |
| `AI-Security-Review.md` | ~2.5 KB | AI Policy | Active | Engineering | Canonical |
| `AI-UML-Standards.md` | ~3.0 KB | AI Standard | Active | Engineering | Canonical |
| `Principles.md` | ~2.0 KB | AI Principles | Active | Engineering | Canonical |
| `Prompt-Review-Checklist.md` | ~2.0 KB | AI Checklist | Active | Engineering | Canonical |
| `Prompt-Versioning.md` | ~2.5 KB | AI Standard | Active | Engineering | Canonical |

#### 2.2.10 `docs/business-rules/` — Business Rules

| File | Size (est.) | Category | Last Relevance | Owner | Status |
|------|-------------|----------|----------------|-------|--------|
| `README.md` | ~3.0 KB | Business Rules Index | Active | Engineering | Canonical (outdated) |
| `00-overview.md` | ~4.0 KB | Overview | Active | Engineering | Outdated |
| `01-ownership-and-access.md` | ~3.5 KB | Business Rules | Active | Engineering | Canonical |
| `02-subscription-and-usage-limits.md` | ~4.0 KB | Business Rules | Active | Engineering | Outdated |
| `03-caching.md` | ~2.0 KB | Business Rules | Active | Engineering | Canonical |
| `04-buildings.md` | ~3.0 KB | Business Rules | Active | Engineering | Canonical |
| `05-units.md` | ~2.5 KB | Business Rules | Active | Engineering | Canonical |
| `06-caretakers.md` | ~2.0 KB | Business Rules | Active | Engineering | Canonical |
| `07-renters.md` | ~3.5 KB | Business Rules | Active | Engineering | Canonical |
| `08-rent-records.md` | ~3.0 KB | Business Rules | Active | Engineering | Canonical |
| `09-unit-images-and-documents.md` | ~2.5 KB | Business Rules | Active | Engineering | Canonical |
| `10-rent-agreement-drafts.md` | ~2.0 KB | Business Rules | Active | Engineering | Canonical |
| `11-payout-retry.md` | ~2.5 KB | Business Rules | Active | Engineering | Canonical |
| `12-owner-reporting.md` | ~3.0 KB | Business Rules | Active | Engineering | Canonical |
| `13-renter-facing-apis.md` | ~3.5 KB | Business Rules | Active | Engineering | Canonical |
| `14-known-behaviors-and-edge-cases.md` | ~4.0 KB | Business Rules | Active | Engineering | Outdated |
| `15-authentication.md` | ~3.0 KB | Business Rules | Active | Engineering | Outdated |
| `16-payments-and-webhooks.md` | ~4.5 KB | Business Rules | Active | Engineering | Outdated |
| `17-notifications.md` | ~4.0 KB | Business Rules | Active | Engineering | Outdated |
| `18-finance-and-tax.md` | ~3.5 KB | Business Rules | Active | Engineering | Canonical |
| `19-referral-program.md` | ~2.5 KB | Business Rules | Active | Engineering | Canonical |
| `20-documents-and-pdfs.md` | ~3.0 KB | Business Rules | Active | Engineering | Canonical |
| `21-smartbot.md` | ~2.0 KB | Business Rules | Active | Engineering | Canonical |
| `22-signals-and-automation.md` | ~3.5 KB | Business Rules | Active | Engineering | Outdated |

#### 2.2.11 `docs/history/`

| File | Size (est.) | Category | Last Relevance | Owner | Status |
|------|-------------|----------|----------------|-------|--------|
| `README.md` | ~2.0 KB | Architecture History | Historical | Engineering | Canonical |
| `generated/architecture.json` | ~122 KB | Historical Data | Historical | Kilo | Generated |

#### 2.2.12 `docs/rag/` — RAG Knowledge Base

| File | Size (est.) | Category | Last Relevance | Owner | Status |
|------|-------------|----------|----------------|-------|--------|
| `README.md` | ~2.5 KB | RAG Index | 2026-07-14 | Kilo | Obsolete |
| `project-summary.md` | ~3.0 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `tech-stack.md` | ~2.5 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `repository-structure.md` | ~3.0 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `django-apps-inventory.md` | ~3.5 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `data-model-core.md` | ~4.0 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `data-model-properties.md` | ~3.5 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `entity-relationships.md` | ~3.0 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `api-authentication.md` | ~4.0 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `api-properties-owner.md` | ~4.5 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `api-properties-renter.md` | ~4.0 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `api-finance-documents.md` | ~3.5 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `subscription-and-limits.md` | ~3.0 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `payments-razorpay-cashfree.md` | ~3.5 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `notifications-and-reminders.md` | ~3.0 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `external-integrations.md` | ~3.5 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `business-rules-pointer.md` | ~1.0 KB | RAG Pointer | 2026-07-14 | Kilo | Obsolete |
| `development-runbook.md` | ~2.0 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `environment-configuration.md` | ~2.5 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `glossary.md` | ~2.0 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `known-issues-for-ai.md` | ~2.0 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `referral-program.md` | ~1.5 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `signals-celery-commands.md` | ~2.5 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `smartbot-and-ai-assistant.md` | ~2.0 KB | RAG Chunk | 2026-07-14 | Kilo | Obsolete |
| `manifest.json` | ~1.0 KB | RAG Manifest | 2026-07-14 | Kilo | Obsolete |

#### 2.2.13 `docs/refactoring/` — Refactoring & Migration Planning

| File | Size (est.) | Category | Last Relevance | Owner | Status |
|------|-------------|----------|----------------|-------|--------|
| `00_architecture_principles.md` | ~51.7 KB | Architecture Principles | Active | Architect | Canonical |
| `01_target_architecture.md` | ~131.7 KB | Target Architecture | Historical | Architect | Superseded |
| `02_migration_roadmap.md` | ~84.5 KB | Migration Roadmap | Historical | Architect | Superseded |
| `02_verified_dead_code_report.md` | ~2.0 KB | Dead Code Report | Historical | Architect | Superseded |
| `03_dead_code_cleanup_execution_plan.md` | ~4.0 KB | Execution Plan | Historical | Architect | Superseded |
| `04_final_production_safety_report.md` | ~3.5 KB | Safety Report | Historical | Architect | Superseded |
| `05_execution_report.md` | ~3.0 KB | Execution Report | Historical | Architect | Superseded |
| `06_architecture_audit.md` | ~41.9 KB | Architecture Audit | Historical | Architect | Superseded |
| `07_migration_plan.md` | ~15.0 KB | Migration Plan | Historical | Architect | Superseded |
| `08_architecture_decisions.md` | ~25.0 KB | Architecture ADRs | Historical | Architect | Superseded |
| `09_target_architecture.md` | ~70.0 KB | Target Architecture | Active | Architect | Canonical |
| `10_architecture_gap_analysis.md` | ~77.4 KB | Gap Analysis | Historical | Architect | Superseded |
| `11_architecture_roadmap_review.md` | ~63.2 KB | Roadmap Review | Historical | Architect | Superseded |
| `12_architecture_implementation_master_plan.md` | ~92.4 KB | Master Plan | Active | Architect | Canonical |

### 2.3 `architecture/` Directory

| File | Size (est.) | Category | Last Relevance | Owner | Status |
|------|-------------|----------|----------------|-------|--------|
| `ROADMAP.md` | ~8.8 KB | Architecture Roadmap | Active | Architect | Canonical (referenced) |
| `ARCHITECTURE_PRINCIPLES.md` | ~2.6 KB | Architecture Principles | Active | Architect | Canonical (referenced) |
| `CODING_STANDARDS.md` | ~4.9 KB | Coding Standards | Active | Architect | Canonical (referenced) |
| `dependency-rules.md` | ~5.5 KB | Dependency Rules | Active | Architect | Canonical (referenced) |
| `import-layers.md` | ~2.6 KB | Import Layers | Active | Architect | Safe Archive |
| `module-boundaries.md` | ~4.6 KB | Module Boundaries | Active | Architect | Canonical (referenced) |
| `adr/000-template.md` | ~1.5 KB | ADR Template | Active | Architect | Canonical |
| `adr/001-current-architecture.md` | ~2.0 KB | Original ADR | Historical | Architect | Canonical |
| `adr/002-target-architecture.md` | ~2.5 KB | Original ADR | Historical | Architect | Canonical |
| `adr/003-refactoring-strategy.md` | ~2.0 KB | Original ADR | Historical | Architect | Canonical |
| `reports/README.md` | ~1.0 KB | Reports Index | Active | Architect | Generated |
| `generated/architecture.json` | ~127.7 KB | Generated Data | Historical | Kilo | Generated |
| `contracts/` | 0 files | Planned Directory | N/A | Architect | Empty |

### 2.4 `.kilo/` Directory

| File | Size (est.) | Category | Last Relevance | Owner | Status |
|------|-------------|----------|----------------|-------|--------|
| `instructions/README.md` | ~673 B | Instruction Index | Active | Kilo | Canonical |
| `instructions/universal.md` | ~113 B | Universal Rules | Active | Kilo | Canonical |
| `instructions/architecture.md` | ~124 B | Architecture Rules | Active | Kilo | Canonical |
| `instructions/backend.md` | ~1.3 KB | Backend Rules | Active | Kilo | Canonical |
| `instructions/security.md` | ~234 B | Security Rules | Active | Kilo | Canonical |
| `instructions/testing.md` | ~86 B | Testing Rules | Active | Kilo | Canonical |
| `instructions/frontend.md` | ~199 B | Frontend Rules | Active | Kilo | Canonical |
| `instructions/notifications.md` | ~2.3 KB | Notifications Rules | Active | Kilo | Canonical |
| `instructions/finance.md` | ~2.2 KB | Finance Rules | Active | Kilo | Canonical |
| `instructions/smartbot.md` | ~93 B | SmartBot Rules | Active | Kilo | Canonical |
| `instructions/onboarding.md` | ~103 B | Onboarding Guidance | Active | Kilo | Canonical |
| `prompts/backend-architecture.md` | ~2.0 KB | Backend Guidance | Active | Kilo | Canonical |
| `command/review-sec.md` | ~1.5 KB | Command Config | Active | Kilo | Canonical |
| `command/test-shard.md` | ~1.0 KB | Command Config | Active | Kilo | Canonical |
| `agent/README.md` | ~1.0 KB | Agent Index | Active | Kilo | Canonical |
| `agent/backend-architect.md` | ~2.5 KB | Agent Config | Active | Kilo | Canonical |

### 2.5 `.github/` Directory

| File | Size (est.) | Category | Last Relevance | Owner | Status |
|------|-------------|----------|----------------|-------|--------|
| `SECURITY_AUDIT.md` | ~5.0 KB | Security Audit | Active | Engineering | Generated |
| `instructions/sonarqube_mcp.instructions.md` | ~2.0 KB | Tooling Instructions | Active | Engineering | Canonical |
| `workflows/BRANCH_PROTECTION_VALIDATOR_README.md` | ~1.5 KB | Workflow README | Active | Engineering | Canonical |

### 2.6 Module-Level Documentation

| File | Size (est.) | Category | Last Relevance | Owner | Status |
|------|-------------|----------|----------------|-------|--------|
| `properties/TEST_DOCUMENTATION.md` | ~6.0 KB | Test Docs | Active | Engineering | Canonical |
| `properties/business_rules.md` | ~311 B | Legacy Business Rules | Obsolete | Engineering | Obsolete |
| `properties/repositories/README.md` | ~1.5 KB | Repo Docs | Active | Engineering | Canonical |
| `properties/services/README.md` | ~1.5 KB | Service Docs | Active | Engineering | Canonical |
| `core/services/README.md` | ~1.5 KB | Service Docs | Active | Engineering | Canonical |
| `shared/README.md` | ~1.0 KB | Shared Docs | Active | Engineering | Canonical |
| `scripts/diagrams/required_diagrams.txt` | ~1.0 KB | Tooling Config | Active | Engineering | Canonical |

---

## 3. Canonical Documentation Map

### 3.1 Project-Level Canonical

| Topic | Canonical Document | Duplicates / Alternatives |
|-------|-------------------|---------------------------|
| Project Overview | `README.md` | None |
| Documentation Index | `docs/README.md` | None |
| CI/CD Governance | `docs/governance.md` | None |
| CI/CD Pipeline | `docs/ci-cd-pipeline.md` | None (outdated but must update in place) |
| Architecture Contract | `docs/architecture-contract.md` | None |
| Kilo Architecture Spec | `docs/kilo-architecture-spec.md` | None |
| Documentation Governance | `DOCUMENTATION_GOVERNANCE_SPECIFICATION.md` | None |

### 3.2 Business Logic Canonical

| Topic | Canonical Document | Duplicates / Alternatives |
|-------|-------------------|---------------------------|
| Business Logic Deep Dive | `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` | None (outdated but must update in place) |
| Business Rules Index | `docs/business-rules/README.md` | `properties/business_rules.md` (legacy) |
| Business Rules (23 domains) | `docs/business-rules/*.md` | None (outdated in places but must update in place) |

### 3.3 Architecture Canonical

| Topic | Canonical Document | Duplicates / Alternatives |
|-------|-------------------|---------------------------|
| Production Architecture | `docs/architecture/production-architecture.md` | None |
| Architecture Principles | `docs/refactoring/00_architecture_principles.md` | `architecture/ARCHITECTURE_PRINCIPLES.md` (concise duplicate) |
| Target Architecture | `docs/refactoring/09_target_architecture.md` | `docs/refactoring/01_target_architecture.md` (superseded) |
| Migration Roadmap | `docs/refactoring/12_architecture_implementation_master_plan.md` | `architecture/ROADMAP.md`, `docs/refactoring/02_migration_roadmap.md`, `docs/refactoring/11_architecture_roadmap_review.md` |
| ADR Collection (Detailed) | `docs/architecture/adr/` (23 files) | `docs/adr/` (18 short stubs), `architecture/adr/` (4 original) |
| Future Architecture Vision | `docs/architecture/future/` (11 files) | `docs/refactoring/` (partial overlap) |
| Layer Rules | `docs/refactoring/04_layer_rules.md` | `architecture/import-layers.md` |
| Dependency Rules | `docs/refactoring/05_dependency_rules.md` | `architecture/dependency-rules.md`, `docs/architecture/future/05_dependency_rules.md` (exact duplicate) |
| Module Responsibilities | `docs/refactoring/06_module_responsibilities.md` | `architecture/module-boundaries.md`, `docs/architecture/future/02_bounded_contexts.md` |
| Naming Conventions | `docs/refactoring/10_naming_conventions.md` | `architecture/CODING_STANDARDS.md` |
| Coding Standards | `docs/refactoring/10_naming_conventions.md` | `architecture/CODING_STANDARDS.md` |
| Domain Events | `docs/architecture/future/07_domain_events.md` | `docs/refactoring/` (partial) |
| Repository Pattern | `docs/architecture/future/08_repository_pattern.md` | `docs/refactoring/` (partial) |
| Service Layer | `docs/architecture/future/09_service_layer.md` | `docs/refactoring/` (partial) |

### 3.4 AI Governance Canonical

| Topic | Canonical Document | Duplicates / Alternatives |
|-------|-------------------|---------------------------|
| AI Governance Index | `docs/ai-governance/README.md` | None |
| AI Governance Standards | `docs/ai-governance/*.md` (11 files) | None |
| AI Prompts | `docs/ai/README.md` | None |
| AI Prompt Library | `docs/ai/prompts/v1/` | None |
| RAG Knowledge Base | `docs/rag/` (23 files) | None (obsolete) |

### 3.5 Instruction Canonical

| Topic | Canonical Document | Duplicates / Alternatives |
|-------|-------------------|---------------------------|
| Kilo Instructions | `.kilo/instructions/*.md` (11 files) | None |
| Kilo Agents | `.kilo/agent/*.md` | None |
| Kilo Commands | `.kilo/command/*.md` | None |
| Kilo Prompts | `.kilo/prompts/*.md` | None |

### 3.6 Module-Level Canonical

| Topic | Canonical Document | Duplicates / Alternatives |
|-------|-------------------|---------------------------|
| Properties Test Docs | `properties/TEST_DOCUMENTATION.md` | None |
| Properties Repositories | `properties/repositories/README.md` | None |
| Properties Services | `properties/services/README.md` | None |
| Core Services | `core/services/README.md` | None |
| Shared Module | `shared/README.md` | None |

---

## 4. Duplicate Documentation

### 4.1 Duplicate ADR Collections (CRITICAL)

| Collection | Location | Count | Status | Canonical? |
|------------|----------|-------|--------|------------|
| Original ADRs | `architecture/adr/` | 4 | Superseded | No |
| Short ADRs | `docs/adr/` | 18 | Incomplete (missing ADR-013–030) | No |
| Detailed ADRs | `docs/architecture/adr/` | 23 | Active, comprehensive | **YES** |

**Analysis:** Three ADR collections with different numbering schemes and detail levels exist. The `docs/architecture/adr/` collection is the most detailed and comprehensive (23 files, dated 2026-07-14). The `docs/adr/` collection is referenced by `README.md`, `documentation_guardian.py`, and `ai-governance/AI-Architecture-Review.md`. The `architecture/adr/` collection contains the original Phase 0 baseline ADRs.

**Recommendation:** Treat `docs/architecture/adr/` as canonical. Archive `docs/adr/` and `architecture/adr/` only after updating all references.

### 4.2 Duplicate Architecture Principles

| Document | Location | Size | Status | Canonical? |
|----------|----------|------|--------|------------|
| Detailed Principles | `docs/refactoring/00_architecture_principles.md` | ~51.7 KB | Ratified, comprehensive | **YES** |
| Concise Principles | `architecture/ARCHITECTURE_PRINCIPLES.md` | ~2.6 KB | Summary | No |
| Embedded Principles | `docs/architecture/README.md` | ~8.0 KB | Embedded in audit | No |

**Analysis:** `docs/refactoring/00_architecture_principles.md` is the supreme authority (51.7 KB, ratified 2026-07-15). `architecture/ARCHITECTURE_PRINCIPLES.md` is a 57-line concise summary. `docs/architecture/README.md` embeds principles in an audit overview.

**Recommendation:** Keep `docs/refactoring/00_architecture_principles.md` as canonical. Archive `architecture/ARCHITECTURE_PRINCIPLES.md` after updating 14 ADR references.

### 4.3 Duplicate Roadmaps

| Document | Location | Size | Status | Canonical? |
|----------|----------|------|--------|------------|
| Master Plan | `docs/refactoring/12_architecture_implementation_master_plan.md` | ~92.4 KB | Most recent, comprehensive | **YES** |
| Concise Roadmap | `architecture/ROADMAP.md` | ~8.8 KB | Phase 0 baseline | No |
| Migration Roadmap | `docs/refactoring/02_migration_roadmap.md` | ~84.5 KB | Superseded | No |
| Roadmap Review | `docs/refactoring/11_architecture_roadmap_review.md` | ~63.2 KB | Superseded | No |

**Analysis:** Four roadmap documents with significant overlap. `docs/refactoring/12_architecture_implementation_master_plan.md` is the most recent (2026-07-17) and comprehensive. `architecture/ROADMAP.md` is referenced by 3 ADR files in `architecture/adr/`.

**Recommendation:** Keep `docs/refactoring/12_architecture_implementation_master_plan.md` as canonical. Archive `architecture/ROADMAP.md`, `docs/refactoring/02_migration_roadmap.md`, and `docs/refactoring/11_architecture_roadmap_review.md` after updating references.

### 4.4 Duplicate Dependency Rules

| Document | Location | Size | Status | Canonical? |
|----------|----------|------|--------|------------|
| Detailed Dependency Rules | `docs/refactoring/05_dependency_rules.md` | ~7.9 KB | Comprehensive | **YES** |
| Future Dependency Rules | `docs/architecture/future/05_dependency_rules.md` | ~7.9 KB | **EXACT DUPLICATE** | Referenced by 3 ADRs |
| Concise Dependency Rules | `architecture/dependency-rules.md` | ~5.5 KB | Concise | No |

**Analysis:** `docs/architecture/future/05_dependency_rules.md` is an exact byte-for-byte duplicate of `docs/refactoring/05_dependency_rules.md`. However, it is referenced by 3 canonical ADR files (`docs/architecture/adr/ADR-006_import_rules.md`, etc.).

**Recommendation:** Keep both files in place (do not delete the duplicate). Archive `architecture/dependency-rules.md` after updating 4 references.

### 4.5 Duplicate Module Boundaries

| Document | Location | Size | Status | Canonical? |
|----------|----------|------|--------|------------|
| Module Responsibilities | `docs/refactoring/06_module_responsibilities.md` | ~12.7 KB | Detailed | **YES** |
| Bounded Contexts | `docs/architecture/future/02_bounded_contexts.md` | ~16.6 KB | Detailed, referenced by 11 ADRs | Canonical Reference |
| Concise Boundaries | `architecture/module-boundaries.md` | ~4.6 KB | Concise | No |

**Analysis:** `docs/architecture/future/02_bounded_contexts.md` is the most detailed and is referenced by 11 canonical ADR files. It must remain in place.

**Recommendation:** Keep `docs/architecture/future/02_bounded_contexts.md` as canonical reference. Keep `docs/refactoring/06_module_responsibilities.md` as canonical planning doc. Archive `architecture/module-boundaries.md` after updating 1 ADR reference.

### 4.6 Duplicate Layer Rules

| Document | Location | Size | Status | Canonical? |
|----------|----------|------|--------|------------|
| Layer Rules | `docs/refactoring/04_layer_rules.md` | ~10.0 KB | Detailed | **YES** |
| Import Layers | `architecture/import-layers.md` | ~2.6 KB | Concise | No |

**Recommendation:** Keep `docs/refactoring/04_layer_rules.md`. Archive `architecture/import-layers.md` (safe, 0 external references).

### 4.7 Duplicate Coding Standards

| Document | Location | Size | Status | Canonical? |
|----------|----------|------|--------|------------|
| Naming Conventions | `docs/refactoring/10_naming_conventions.md` | ~8.1 KB | Detailed | **YES** |
| Coding Standards | `architecture/CODING_STANDARDS.md` | ~4.9 KB | Concise | No |

**Recommendation:** Keep `docs/refactoring/10_naming_conventions.md`. Archive `architecture/CODING_STANDARDS.md` after updating 1 ADR reference.

### 4.8 Duplicate Architecture Audit Reports

| Document | Location | Size | Status | Canonical? |
|----------|----------|------|--------|------------|
| Production Architecture | `docs/architecture/production-architecture.md` | ~39.3 KB | Year 1 strategy | **YES** |
| Architecture README | `docs/architecture/README.md` | ~8.0 KB | Audit overview | Generated |
| Architecture Audit Report | `docs/architecture/architecture-audit-report.md` | ~40.1 KB | Generated report | Generated |
| Refactoring Audit | `docs/refactoring/06_architecture_audit.md` | ~41.9 KB | Superseded | No |

**Recommendation:** Keep `docs/architecture/production-architecture.md` as canonical. Archive the three generated/superseded audit reports.

### 4.9 Duplicate Architecture JSON Data

| Document | Location | Size | Status | Canonical? |
|----------|----------|------|--------|------------|
| Audit Data | `docs/architecture/audit_data.json` | ~198 KB | Raw audit data | Canonical (for scripts) |
| Generated Data | `architecture/generated/architecture.json` | ~127.7 KB | Generated | No |
| Historical Data | `docs/history/generated/architecture.json` | ~122 KB | Historical | No |

**Recommendation:** Keep `docs/architecture/audit_data.json`. Archive the other two.

---

## 5. Conflicting Documentation

### 5.1 Payment Strategy Contradiction (CRITICAL)

| Document | Claim |
|----------|-------|
| `docs/architecture/production-architecture.md` (Section 3.1) | "Year 1 uses a completely free, manual UPI-based payment flow" |
| `docs/architecture/adr/ADR-010_payment_integration.md` | "Year 1 uses a completely free manual UPI-based payment flow" |
| `.kilo/instructions/finance.md` | "Year 1 payment flow is completely free. Rent payment does NOT go through a payment gateway." |
| `docs/ci-cd-pipeline.md` (header) | "**Stack:** Django 5.2 / DRF / PostgreSQL / AWS EC2 / **Cashfree**" |
| `docs/ci-cd-pipeline.md` (diagrams) | Shows Cashfree as payment gateway in sequence diagrams |
| `README.md` (Feature Flags) | Lists `ENABLE_RAZORPAY` and `ENABLE_CASHFREE` flags |

**Verdict:** The CI/CD pipeline documentation and README still reference Cashfree/Razorpay as the primary stack, contradicting the new Year 1 manual UPI strategy documented in `production-architecture.md` and ADR-010.

### 5.2 Signal Wiring Contradiction (MAJOR)

| Document | Claim |
|----------|-------|
| `docs/business-rules/02-subscription-and-usage-limits.md` | "`core/signals.assign_default_plan` exists but `core/apps.py` does not import signals" |
| `docs/business-rules/14-known-behaviors-and-edge-cases.md` | "`core/apps.py` and `properties/apps.py` do not import signals in `ready()`" |
| `docs/business-rules/22-signals-and-automation.md` | "Status: `core/apps.py` `ready()` does not import this module" |
| `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` | "Signal exists; not connected in `AppConfig.ready()`" |
| `docs/rag/notifications-and-reminders.md` | "requires `properties.apps.ready()` to import signals" |

**Actual Code State:**
```python
# core/apps.py (lines 12-16)
def ready(self) -> None:
    if os.environ.get("SKIP_DJANGO_SIGNALS") == "1":
        return
    import core.signals  # noqa

# properties/apps.py (lines 12-14)
def ready(self) -> None:
    import properties.signals  # noqa
```

**Verdict:** Documentation is outdated. Signals ARE wired. The `SKIP_DJANGO_SIGNALS` environment variable provides an opt-out mechanism that the docs don't mention.

### 5.3 Razorpay Webhook Definitions Contradiction (MAJOR)

| Document | Claim |
|----------|-------|
| `docs/business-rules/16-payments-and-webhooks.md` | "`razorpay_webhook` defined 3 times in `core/views.py`" |
| `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` | "`razorpay_webhook` defined three times in `core/views.py`" |
| `docs/rag/payments-razorpay-cashfree.md` | "duplicate definitions — last wins" |

**Actual Code State:**
```python
# core/views.py:394
def razorpay_webhook(request: HttpRequest) -> JsonResponse:
```

**Verdict:** Documentation is inaccurate. The webhook is defined only once.

### 5.4 Owner Group Assignment Contradiction (MAJOR)

| Document | Claim |
|----------|-------|
| `docs/business-rules/15-authentication.md` | "Owner → group `tenant` (verify intended role name)" |
| `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` | "Assigned `'tenant'` group" |
| `docs/business-rules/14-known-behaviors-and-edge-cases.md` | "Owner OTP assigns group `tenant` (likely wrong name for owner role)." |

**Actual Code State:**
```python
# core/views.py:143
data, status = _verify_otp_and_login(phone, code, "owner")

# core/services/auth_service.py:29
group, _ = Group.objects.get_or_create(name=group_name)  # group_name = "owner"
```

**Verdict:** Documentation is inaccurate. The code correctly assigns the "owner" group, not "tenant".

### 5.5 Management Command Status Contradiction (MAJOR)

| Document | Claim |
|----------|-------|
| `docs/business-rules/22-signals-and-automation.md` | "`generate_monthly_rent_records` — Broken (`rent.models` import)" |
| `docs/business-rules/22-signals-and-automation.md` | "`daily_rent_reminder` — Broken import" |
| `docs/business-rules/02-subscription-and-usage-limits.md` | "`seed_subscription_plans` and `downgrade_expired_users` commands are commented out" |

**Actual Code State:**
- `management/commands/generate_monthly_rent_records.py`: Uses `from properties.models import Renter, RentRecord` — works correctly
- `management/commands/daily_rent_reminder.py`: Uses `from properties.models import Renter` — works correctly
- `management/commands/seed_subscription_plans.py`: Stub (1 line: `# # your_app/management/commands/seed_subscription_plans.py`)
- `management/commands/downgrade_expired_users.py`: Empty file (0 lines)

**Verdict:** Partially outdated. The broken import claims are false, but the seed/downgrade commands are indeed non-functional.

### 5.6 Architecture Score Contradiction

| Document | Claim |
|----------|-------|
| `docs/architecture/README.md` | "Architecture Score: 42 / 100" |
| `architecture-compliance-report.md` | "Score: 100 / 100" |
| `architecture-summary.txt` | "Score: 100 / 100, 0 violations" |

**Verdict:** Conflicting architecture scores. The `docs/architecture/README.md` audit report shows 42/100, while the root `architecture-compliance-report.md` and `architecture-summary.txt` show 100/100. These are from different tools/times and represent different metrics.

---

## 6. Obsolete Documentation

### 6.1 RAG Knowledge Base (HIGH PRIORITY)

| Document | Reason Obsolete |
|----------|-----------------|
| `docs/rag/*` (23 files + manifest.json) | References old payment flows (Razorpay/Cashfree as primary), old notification flows (WhatsApp/SMS as primary), outdated architecture. Year 1 strategy now uses manual UPI and free channels only. |

**Impact:** If RAG chunks are consumed by AI systems, they will provide outdated Year 1 strategy information.

### 6.2 Outdated Business Rules

| Document | Reason Obsolete |
|----------|-----------------|
| `docs/business-rules/02-subscription-and-usage-limits.md` | Claims signals are not wired; claims management commands are broken |
| `docs/business-rules/14-known-behaviors-and-edge-cases.md` | Claims signals are not wired; claims owner group is "tenant" |
| `docs/business-rules/15-authentication.md` | Claims owner group is "tenant" |
| `docs/business-rules/16-payments-and-webhooks.md` | Claims webhook defined 3 times; references old payment strategy |
| `docs/business-rules/17-notifications.md` | References WhatsApp/SMS as primary channels (now Stage 2) |
| `docs/business-rules/22-signals-and-automation.md` | Claims signals not wired; claims commands broken |
| `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` | Claims signals not wired; claims owner group is "tenant"; references Razorpay/Cashfree as primary |

### 6.3 Outdated README

| Document | Reason Obsolete |
|----------|-----------------|
| `README.md` | References Cashfree/Razorpay feature flags; references missing diagram paths |

### 6.4 Outdated CI/CD Pipeline Doc

| Document | Reason Obsolete |
|----------|-----------------|
| `docs/ci-cd-pipeline.md` | Header shows "Stack: Django 5.2 / DRF / PostgreSQL / AWS EC2 / Cashfree"; diagrams show Cashfree as payment gateway |

### 6.5 Generated Reports at Root

| Document | Reason Obsolete |
|----------|-----------------|
| `PHASE_0_VALIDATION_REPORT.md` | Phase 0 historical report |
| `PHASE_1_1_REPAIR_REPORT.md` | Phase 1.1 historical report |
| `PHASE_1_2_GUARDIAN_REPAIR_REPORT.md` | Phase 1.2 historical report |
| `PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md` | Phase 1.3 historical report |
| `PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md` | Phase 2A historical report |
| `PHASE_2_1_ARCHIVE_REPORT.md` | Phase 2.1 historical report |
| `01_repository_inventory.md` | Generated report |
| `architecture-analysis-report.md` | Generated report |
| `architecture-compliance-report.md` | Generated report |
| `architecture-compliance-report.json` | Generated data |
| `architecture-dependency-graph.mmd` | Generated diagram |
| `architecture-dependency-graph.dot` | Generated diagram |
| `architecture-summary.txt` | Generated report |
| `directory-structure-analysis.md` | Generated report |
| `DOCUMENTATION_ANALYSIS_REPORT.md` | Generated report (superseded by this audit) |
| `DOCUMENTATION_CONSOLIDATION_PLAN.md` | Generated report (superseded by this audit + review) |
| `DOCUMENTATION_CONSOLIDATION_REVIEW.md` | Generated report (superseded by this audit) |

### 6.6 Legacy Module Documentation

| Document | Reason Obsolete |
|----------|-----------------|
| `properties/business_rules.md` | 311-byte legacy single-file version; superseded by `docs/business-rules/` |

---

## 7. Safe Archive Candidates

These documents can be safely moved to `docs/archive/` without breaking canonical documentation, provided reference updates are made where noted.

### 7.1 High Confidence (No External References)

| Document | Reason |
|----------|--------|
| `PHASE_0_VALIDATION_REPORT.md` | Only referenced in plan itself |
| `PHASE_1_1_REPAIR_REPORT.md` | Only referenced in plan itself |
| `PHASE_1_2_GUARDIAN_REPAIR_REPORT.md` | Only referenced in plan itself |
| `PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md` | Only referenced in plan itself |
| `PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md` | Only referenced in plan itself |
| `PHASE_2_1_ARCHIVE_REPORT.md` | Only referenced in plan itself |
| `01_repository_inventory.md` | Only referenced in plan itself |
| `architecture-analysis-report.md` | Only referenced in plan itself |
| `architecture-compliance-report.md` | Only referenced in plan itself |
| `architecture-compliance-report.json` | Only referenced in plan itself |
| `architecture-dependency-graph.mmd` | Only referenced in plan itself |
| `architecture-dependency-graph.dot` | Only referenced in plan itself |
| `architecture-summary.txt` | Only referenced in plan itself |
| `directory-structure-analysis.md` | Only referenced in plan itself |
| `DOCUMENTATION_ANALYSIS_REPORT.md` | Only referenced in plan itself |
| `DOCUMENTATION_CONSOLIDATION_PLAN.md` | Only referenced in plan itself |
| `DOCUMENTATION_CONSOLIDATION_REVIEW.md` | Only referenced in plan itself |
| `docs/ci-cd-upgrade-report.md` | Only referenced in plan itself |
| `docs/architecture/architecture-audit-report.md` | Only referenced in plan itself |
| `docs/architecture/01_dependency_graph.md` | Generated report |
| `docs/architecture/02_import_matrix.md` | Generated report |
| `docs/architecture/03_circular_dependencies.md` | Generated report |
| `docs/architecture/04_cross_app_dependencies.md` | Generated report |
| `docs/architecture/05_architecture_boundary_violations.md` | Generated report |
| `docs/architecture/06_dead_modules.md` | Generated report |
| `docs/architecture/07_hotspots.md` | Generated report |
| `docs/architecture/08_import_linter_audit.md` | Generated report |
| `docs/architecture/09_dependency_metrics.md` | Generated report |
| `architecture/generated/architecture.json` | Only referenced in plan itself |
| `docs/history/generated/architecture.json` | Only referenced in plan itself |
| `docs/diagrams/generated/` (8 files) | No external references found |
| `docs/uml/generated/` (11 files) | No external references found |
| `architecture/diagrams/` (2 files) | No external references found |
| `docs/archive/audits/architecture-audit-report.md` | Already archived |
| `docs/archive/reports/ci-cd-upgrade-report.md` | Already archived |
| `docs/archive/reports/baseline/architecture-baseline.md` | Already archived |
| `docs/archive/reports/baseline/architecture-baseline-validation.md` | Already archived |
| `architecture/reports/README.md` | Generated index |
| `architecture/contracts/` | Empty directory |

### 7.2 Medium Confidence (Requires Reference Updates)

| Document | Reason | Required Updates |
|----------|--------|------------------|
| `architecture/import-layers.md` | Concise duplicate of `docs/refactoring/04_layer_rules.md` | Verify 0 external references |
| `docs/refactoring/01_target_architecture.md` | Superseded by `09_target_architecture.md` | Update `12_master_plan` reference |
| `docs/refactoring/02_migration_roadmap.md` | Superseded by `12_master_plan.md` | Update `12_master_plan` reference |
| `docs/refactoring/11_architecture_roadmap_review.md` | Superseded by `12_master_plan.md` | Update `12_master_plan` reference |
| `docs/refactoring/06_architecture_audit.md` | Superseded by `production-architecture.md` | Update `10_gap_analysis` and `05_execution_report` references |
| `properties/business_rules.md` | Legacy single-file | Update 4 references in `docs/business-rules/` |

### 7.3 Low Confidence (High Risk — Do Not Archive Without Full Reference Update)

| Document | Reason | Required Updates |
|----------|--------|------------------|
| `architecture/ARCHITECTURE_PRINCIPLES.md` | Concise duplicate | Update 14 ADR references |
| `architecture/ROADMAP.md` | Concise roadmap | Update 3 ADR references |
| `architecture/dependency-rules.md` | Concise duplicate | Update 4 references (3 ADRs + 1 audit) |
| `architecture/module-boundaries.md` | Concise duplicate | Update 1 ADR reference |
| `architecture/CODING_STANDARDS.md` | Concise duplicate | Update 1 ADR reference |
| `docs/adr/` (18 files) | Short ADR stubs | Update 6+ references (README, guardian script, 3 ADRs, AI governance) |
| `architecture/adr/` (4 files) | Original ADRs | Update 3 references in `docs/architecture/README.md` |

---

## 8. Safe Deletion Candidates

### 8.1 Exact Duplicate

| Document | Reason |
|----------|--------|
| `docs/architecture/future/05_dependency_rules.md` | Exact byte-for-byte duplicate of `docs/refactoring/05_dependency_rules.md` (same size, same date). **However, it is referenced by 3 canonical ADR files. Deletion is NOT recommended.** Archive after reference updates. |

### 8.2 Empty / Placeholder

| Document | Reason |
|----------|--------|
| `coverage-report.txt` | 0-byte empty file. **However, may be referenced by CI or scripts. Archive rather than delete.** |

**Recommendation:** No files are safe to delete outright. All duplicates that are referenced by canonical documents should be archived (not deleted) after reference updates.

---

## 9. Documents Requiring Merge

### 9.1 `docs/refactoring/` Collection

**Status:** Tightly-coupled 13-file collection with extensive internal cross-references.

**Current State:**
- `00_architecture_principles.md` — Ratified principles (51.7 KB)
- `01_target_architecture.md` — Superseded by `09` (131.7 KB)
- `02_migration_roadmap.md` — Superseded by `12` (84.5 KB)
- `02_verified_dead_code_report.md` — Historical (2.0 KB)
- `03_dead_code_cleanup_execution_plan.md` — Historical (4.0 KB)
- `04_final_production_safety_report.md` — Historical (3.5 KB)
- `05_execution_report.md` — Historical (3.0 KB)
- `06_architecture_audit.md` — Superseded (41.9 KB)
- `07_migration_plan.md` — Superseded (15.0 KB)
- `08_architecture_decisions.md` — Referenced by `09`, `10`, `11`, `12` (25.0 KB)
- `09_target_architecture.md` — Canonical (70.0 KB)
- `10_architecture_gap_analysis.md` — Historical (77.4 KB)
- `11_architecture_roadmap_review.md` — Historical (63.2 KB)
- `12_architecture_implementation_master_plan.md` — Canonical (92.4 KB)

**Recommendation:** Do NOT merge. Treat as a unit:
- **Option A:** Keep all 13 files together as a complete planning artifact collection.
- **Option B:** Archive all 13 files together to `docs/archive/planning/refactoring-complete/`.

### 9.2 Architecture Baseline Documents

**Status:** Two baseline documents in `docs/archive/reports/baseline/` that could be merged into a single document.

| Document | Size | Content |
|----------|------|---------|
| `architecture-baseline.md` | ~1270 lines | Current state before Phase 1 refactoring |
| `architecture-baseline-validation.md` | ~2.0 KB | Validation of baseline against actual source files |

**Recommendation:** Merge into `docs/archive/reports/baseline/architecture-baseline-complete.md` (low priority, already archived).

---

## 10. Recommended Final Documentation Structure

```
docs/
├── README.md                                          # Documentation index
├── architecture-contract.md                           # Architecture governance contract
├── BUSINESS_LOGIC_AND_SUBSCRIPTION.md                 # Business logic deep dive
├── ci-cd-pipeline.md                                  # CI/CD pipeline documentation
├── governance.md                                      # CI/CD governance policies
├── kilo-architecture-spec.md                          # Kilo architecture specification
│
├── architecture/
│   ├── README.md                                      # Architecture docs index
│   ├── production-architecture.md                     # Year 1 through Stage 4 strategy
│   ├── adr/                                           # Canonical ADR collection (23 files)
│   │   ├── ADR-001_modular_monolith.md
│   │   ├── ADR-002_repository_pattern.md
│   │   └── ...
│   ├── future/                                        # Future architecture vision (11 files)
│   │   ├── 01_architecture_vision.md
│   │   ├── 02_bounded_contexts.md
│   │   ├── 03_target_folder_structure.md
│   │   ├── 04_layer_rules.md
│   │   ├── 05_dependency_rules.md
│   │   ├── 06_module_responsibilities.md
│   │   ├── 07_domain_events.md
│   │   ├── 08_repository_pattern.md
│   │   ├── 09_service_layer.md
│   │   ├── 10_naming_conventions.md
│   │   ├── 11_migration_strategy.md
│   │   └── diagrams/
│   ├── reviews/
│   │   └── 01_future_architecture_review.md
│   ├── generated/
│   │   └── audit_data.json                            # Raw audit data
│   └── diagrams/
│       └── generated/                                 # Generated diagrams
│           ├── c4/
│           ├── flows/
│           └── infrastructure/
│
├── refactoring/                                       # Planning artifacts (keep as unit or archive all)
│   ├── 00_architecture_principles.md                  # Ratified principles
│   ├── 09_target_architecture.md                      # Updated target architecture
│   └── 12_architecture_implementation_master_plan.md  # Master implementation plan
│   # (Optionally keep all 13 files together)
│
├── adr/                                               # ARCHIVED — short ADR stubs
│   └── [18 files moved here]
│
├── business-rules/
│   ├── README.md
│   ├── 00-overview.md
│   ├── 01-ownership-and-access.md
│   └── ... (23 files)
│
├── ai-governance/
│   ├── README.md
│   ├── AI-Architecture-Review.md
│   ├── AI-Code-Review.md
│   ├── AI-Contribution-Guide.md
│   ├── AI-Decision-Record.md
│   ├── AI-Documentation-Standards.md
│   ├── AI-Rules.md
│   ├── AI-Security-Review.md
│   ├── AI-UML-Standards.md
│   ├── Principles.md
│   ├── Prompt-Review-Checklist.md
│   └── Prompt-Versioning.md
│
├── ai/
│   ├── README.md
│   └── prompts/
│       ├── v1/
│       │   ├── uml/
│       │   │   └── class-diagram-generation.prompt.md
│       │   └── review/
│       │       └── architecture-compliance.prompt.md
│       │   └── ...
│
├── uml/
│   └── generated/                                     # Generated UML diagrams
│       ├── ddd/
│       ├── domain/
│       ├── mermaid/
│       └── plantuml/
│
├── history/
│   └── README.md
│
├── archive/
│   ├── old-adr/
│   │   ├── docs-adr/                                  # From docs/adr/
│   │   └── architecture-adr/                          # From architecture/adr/
│   ├── planning/
│   │   ├── architecture-principles-concise.md         # From architecture/
│   │   ├── roadmap.md                                  # From architecture/
│   │   ├── dependency-rules.md                         # From architecture/
│   │   ├── module-boundaries.md                        # From architecture/
│   │   ├── coding-standards.md                         # From architecture/
│   │   ├── import-layers.md                            # From architecture/
│   │   └── refactoring-complete/                       # From docs/refactoring/
│   │       └── [13 files]
│   ├── generated/
│   │   ├── root-reports/                              # From repository root
│   │   ├── architecture-generated/                    # From architecture/generated/
│   │   ├── history-generated/                         # From docs/history/generated/
│   │   └── diagrams/
│   │       ├── generated/                             # From docs/diagrams/generated/
│   │       └── generated-uml/                         # From docs/uml/generated/
│   ├── audits/
│   │   └── architecture-audit-report.md               # From docs/architecture/
│   └── deprecated/
│       ├── rag-knowledge-base/                         # From docs/rag/
│       └── legacy-business-rules.md                   # From properties/
│
└── [other existing docs unchanged]
```

**Key Principles:**
1. `docs/architecture/future/` remains in place — it is canonical reference material.
2. `docs/refactoring/` is kept as a unit OR archived as a unit — never partially.
3. `architecture/` files are archived only after updating ADR references.
4. `docs/adr/` and `architecture/adr/` are archived only after updating references.
5. All generated reports/diagrams are moved to `docs/archive/generated/`.

---

## 11. Recommended Execution Order

### Phase 1: Archive Generated Reports (No Risk)

1. Move top-level generated reports to `docs/archive/generated/root-reports/`
2. Move `architecture/generated/architecture.json` to `docs/archive/generated/architecture-generated/`
3. Move `docs/history/generated/architecture.json` to `docs/archive/generated/history-generated/`
4. Move `docs/diagrams/generated/` to `docs/archive/generated/diagrams/`
5. Move `docs/uml/generated/` to `docs/archive/generated/diagrams/generated-uml/`
6. Move `architecture/diagrams/` to `docs/archive/generated/diagrams/architecture/`
7. Move `docs/architecture/architecture-audit-report.md` to `docs/archive/audits/`
8. Move `docs/ci-cd-upgrade-report.md` to `docs/archive/generated/`
9. Move `architecture/reports/README.md` to `docs/archive/generated/`

**Risk:** None. No external references found.

### Phase 2: Update References Before Archiving

10. Update `README.md` line 83: `docs/adr/README.md` → `docs/architecture/adr/README.md`
11. Update `scripts/diagrams/documentation_guardian.py` lines 91-99: `docs/adr/` → `docs/architecture/adr/`
12. Update `docs/ai-governance/AI-Architecture-Review.md` line 39: `docs/adr/` → `docs/architecture/adr/`
13. Update `docs/business-rules/00-overview.md` line 38: `properties/business_rules.md` reference
14. Update `docs/business-rules/README.md` line 36: `properties/business_rules.md` reference
15. Update `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` lines 41, 392: `properties/business_rules.md` reference
16. Update `docs/architecture/README.md` lines 217-220: Fix broken internal links
17. Update `architecture/adr/001-current-architecture.md` lines 41-45: Update references to archived files
18. Update `architecture/adr/002-target-architecture.md` lines 58-65: Update references to archived files
19. Update `architecture/adr/003-refactoring-strategy.md` lines 63-66: Update references to archived files
20. Update all 14 ADR files in `docs/architecture/adr/` that reference `architecture/ARCHITECTURE_PRINCIPLES.md`
21. Update all 3 ADR files that reference `architecture/ROADMAP.md`
22. Update all 3 ADR files that reference `architecture/dependency-rules.md`
23. Update all 1 ADR file that references `architecture/module-boundaries.md`
24. Update all 1 ADR file that references `architecture/CODING_STANDARDS.md`

**Risk:** Medium. Requires careful reference updates.

### Phase 3: Archive `docs/adr/` (After References Updated)

25. Move `docs/adr/` to `docs/archive/old-adr/docs-adr/`

**Risk:** Low after references updated.

### Phase 4: Archive `architecture/adr/` (After References Updated)

26. Move `architecture/adr/` to `docs/archive/old-adr/architecture-adr/`

**Risk:** Low after references updated.

### Phase 5: Archive `architecture/` Files (After ADR References Updated)

27. Move `architecture/ARCHITECTURE_PRINCIPLES.md` to `docs/archive/planning/architecture-principles-concise.md`
28. Move `architecture/ROADMAP.md` to `docs/archive/planning/roadmap.md`
29. Move `architecture/dependency-rules.md` to `docs/archive/planning/dependency-rules.md`
30. Move `architecture/module-boundaries.md` to `docs/archive/planning/module-boundaries.md`
31. Move `architecture/CODING_STANDARDS.md` to `docs/archive/planning/coding-standards.md`
32. Move `architecture/import-layers.md` to `docs/archive/planning/import-layers.md`

**Risk:** Medium. All ADR references must be updated first.

### Phase 6: Archive `docs/refactoring/` as Complete Collection

33. Move entire `docs/refactoring/` to `docs/archive/planning/refactoring-complete/`
34. Update any external references to point to archive location

**Risk:** Medium. The refactoring documents are a tightly-coupled collection. Archiving them as a unit preserves the internal link structure.

**Alternative:** Keep all 13 files together in place.

### Phase 7: Archive `docs/rag/` (After Verification)

35. Verify no AI systems or scripts depend on `docs/rag/`
36. Move `docs/rag/` to `docs/archive/deprecated/rag-knowledge-base/`

**Risk:** Medium. Requires verification of AI dependencies.

### Phase 8: Archive `properties/business_rules.md` (After References Updated)

37. Update all 4 references to point to `docs/business-rules/`
38. Move `properties/business_rules.md` to `docs/archive/deprecated/legacy-business-rules.md`

**Risk:** Low after references updated.

### Phase 9: Update Outdated Documents In-Place

39. Update `README.md` to remove Cashfree/Razorpay references and fix diagram paths
40. Update `docs/ci-cd-pipeline.md` to reflect Year 1 manual UPI strategy
41. Update `docs/BUSINESS_LOGIC_AND_SUBSCRIPTION.md` to fix signal wiring, owner group, and payment strategy claims
42. Update `docs/business-rules/02-subscription-and-usage-limits.md` to fix signal wiring and command status claims
43. Update `docs/business-rules/14-known-behaviors-and-edge-cases.md` to fix signal wiring and owner group claims
44. Update `docs/business-rules/15-authentication.md` to fix owner group claim
45. Update `docs/business-rules/16-payments-and-webhooks.md` to fix webhook count and payment strategy claims
46. Update `docs/business-rules/17-notifications.md` to reflect Year 1 free channels only
47. Update `docs/business-rules/22-signals-and-automation.md` to fix signal wiring and command status claims

**Risk:** Medium. Requires content accuracy updates across multiple documents.

---

## 12. Risk Analysis

### 12.1 High-Risk Recommendations

| Recommendation | Risk Level | Issue |
|----------------|------------|-------|
| Archiving `docs/refactoring/` partially | **HIGH** | Partially archiving breaks internal references between files |
| Archiving `architecture/` files | **HIGH** | 14+ ADR references must be updated first |
| Archiving `docs/architecture/future/` files | **VERY HIGH** | 15+ ADR references; NOT RECOMMENDED |
| Deleting `docs/architecture/future/05_dependency_rules.md` | **VERY HIGH** | Referenced by 3 canonical ADRs; NOT RECOMMENDED |
| Deleting `coverage-report.txt` | **MEDIUM** | Empty but may be referenced; archive instead |

### 12.2 Medium-Risk Recommendations

| Recommendation | Risk Level | Issue |
|----------------|------------|-------|
| Archiving `docs/adr/` | **MEDIUM** | 6+ references must be updated first |
| Archiving `architecture/adr/` | **MEDIUM** | 3 references in `docs/architecture/README.md` |
| Archiving `docs/rag/` | **MEDIUM** | No CI/AI script references found, but internal refs + manifest exist |
| Archiving `properties/business_rules.md` | **MEDIUM** | Referenced by 4 docs; safe after reference updates |
| Updating outdated business rules | **MEDIUM** | Multiple documents with conflicting claims |

### 12.3 Low-Risk Recommendations

| Recommendation | Risk Level | Issue |
|----------------|------------|-------|
| Archiving top-level generated reports | **LOW** | No external references found |
| Archiving generated diagrams | **LOW** | No external references found |
| Archiving `docs/architecture/architecture-audit-report.md` | **LOW** | No external references found |
| Archiving `docs/ci-cd-upgrade-report.md` | **LOW** | No external references found |
| Archiving `architecture/import-layers.md` | **LOW** | 0 external references found |

---

## 13. Rollback Considerations

### 13.1 Git-Based Rollback

All file movements should use `git mv` to preserve history. If a consolidation introduces broken references:

```bash
# Rollback specific archive
git mv docs/archive/old-adr/docs-adr/ docs/adr/
git mv docs/archive/planning/architecture-principles-concise.md architecture/ARCHITECTURE_PRINCIPLES.md

# Rollback entire phase
git revert <commit-hash>
```

### 13.2 Reference Update Rollback

If reference updates introduce broken links:

1. Maintain a `docs/CONSOLIDATION_REFERENCE_MAP.md` mapping old paths to new paths
2. Use grep to verify no broken links remain after each phase
3. Keep original files in place until all references are verified

### 13.3 Content Accuracy Rollback

If content updates to outdated documents introduce errors:

1. Do not delete or overwrite original content
2. Use `git diff` to review all changes before committing
3. Maintain a `docs/UPDATE_LOG.md` documenting all content corrections

### 13.4 Canonical Document Preservation

Never move or rename canonical documents without:
1. Updating ALL references first
2. Verifying no broken links remain
3. Getting explicit approval for changes to canonical ADR collections

---

## 14. Final PASS / FAIL

### 14.1 Audit Completeness

| Criterion | Status |
|-----------|--------|
| All documentation files inventoried | **PASS** (~215 files cataloged) |
| Duplicates identified | **PASS** (3 ADR collections, 6 duplicate principle/roadmap/dependency sets) |
| Conflicts identified | **PASS** (6 contradictions documented) |
| Obsolete documents identified | **PASS** (RAG, outdated business rules, generated reports) |
| Canonical documents mapped | **PASS** (single source of truth established per topic) |
| Safe archive candidates identified | **PASS** (~40 files with confidence levels) |
| Safe deletion candidates identified | **PASS** (1 exact duplicate, 1 empty file — both recommended for archive) |
| Documents requiring merge identified | **PASS** (`docs/refactoring/` collection, baseline documents) |
| Final structure recommended | **PASS** (single-source-of-truth hierarchy defined) |
| Execution order defined | **PASS** (9 phases with risk levels) |
| Risk analysis completed | **PASS** (high/medium/low risk per recommendation) |
| Rollback considerations documented | **PASS** (git-based, reference, content, canonical) |

### 14.2 Critical Warnings

1. **DO NOT archive `docs/architecture/future/`** — it is canonical reference material referenced by 15+ ADR files.
2. **DO NOT partially archive `docs/refactoring/`** — it is a tightly-coupled collection. Keep all 13 or archive all 13.
3. **DO NOT delete `docs/architecture/future/05_dependency_rules.md`** — even though it is an exact duplicate, it is referenced by 3 canonical ADRs.
4. **DO NOT archive `architecture/` files without updating ADR references first** — 14+ ADR files reference these documents.
5. **DO NOT archive `docs/adr/` without updating 6+ references first** — README, guardian script, 3 ADRs, AI governance.

### 14.3 Final Verdict

**PASS** — The documentation consolidation audit is complete. All required sections have been analyzed. The repository contains significant documentation sprawl with clear duplication, obsolescence, and conflict patterns. A safe consolidation plan exists, but it must be executed with extreme care due to extensive cross-references between documents.

**Key Success Factors:**
1. Reference tracing must be completed before any archival
2. Tightly-coupled collections (`docs/refactoring/`) must be treated as units
3. Canonical reference material (`docs/architecture/future/`) must remain in place
4. Content accuracy updates must be performed on outdated documents
5. All file movements must use `git mv` to preserve history

---

*End of Phase 3.1 Documentation Consolidation Audit*
