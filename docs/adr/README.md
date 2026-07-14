# Architecture Decision Records

## Index

This directory contains Architecture Decision Records (ADRs) for the RentSecureBE project.

## Status Legend

- **Proposed**: Under discussion
- **Accepted**: Approved and implemented
- **Rejected**: Not approved
- **Deprecated**: No longer relevant
- **Superseded**: Replaced by another ADR

## Decisions

| ID | Title | Status | Date |
|----|-------|--------|------|
| ADR-001 | Django as Primary Framework | Accepted | 2026-01-15 |
| ADR-002 | PostgreSQL as Primary Database | Accepted | 2026-01-15 |
| ADR-003 | Celery for Background Tasks | Accepted | 2026-01-15 |
| ADR-004 | DRF for API Layer | Accepted | 2026-01-15 |
| ADR-005 | Redis for Caching and Queues | Accepted | 2026-01-15 |
| ADR-006 | AWS EC2 for Deployment | Accepted | 2026-01-15 |
| ADR-007 | GitHub Actions for CI/CD | Accepted | 2026-01-15 |
| ADR-008 | Feature Flags for Optional Integrations | Accepted | 2026-07-13 |
| ADR-009 | Service Layer Pattern for Business Logic | Accepted | 2026-01-15 |
| ADR-010 | Import Linter for Architecture Enforcement | Accepted | 2026-01-15 |
| ADR-011 | SonarCloud for Code Quality | Accepted | 2026-01-15 |
| ADR-012 | PlantUML and Mermaid for Documentation | Accepted | 2026-07-13 |
| ADR-013 | UML Automation via GitHub Actions | Accepted | 2026-07-13 |
| ADR-014 | Architecture Contract for CI/CD | Accepted | 2026-06-26 |
| ADR-015 | SQLite for Development, PostgreSQL for Production | Accepted | 2026-01-15 |
| ADR-016 | Django Channels for WebSocket Support | Accepted | 2026-01-15 |
| ADR-017 | JWT Authentication via SimpleJWT | Accepted | 2026-01-15 |
| ADR-018 | Simple History for Audit Trail | Accepted | 2026-01-15 |
| ADR-019 | Feature Flags for Budget-Constrained Integrations | Accepted | 2026-07-13 |
| ADR-020 | AI Governance Framework | Accepted | 2026-07-13 |
| ADR-021 | Prompt Versioning System | Accepted | 2026-07-13 |
| ADR-022 | UML Validation in CI Pipeline | Accepted | 2026-07-13 |
| ADR-023 | Architecture Metrics Automation | Accepted | 2026-07-13 |
| ADR-024 | DDD Bounded Context Diagrams | Accepted | 2026-07-13 |
| ADR-025 | Repository Dependency Diagrams | Accepted | 2026-07-13 |
| ADR-026 | DRF Request Lifecycle Diagrams | Accepted | 2026-07-13 |
| ADR-027 | Celery Task Flow Diagrams | Accepted | 2026-07-13 |
| ADR-028 | Notification Flow Diagrams | Accepted | 2026-07-13 |
| ADR-029 | Payment Flow Diagrams | Accepted | 2026-07-13 |
| ADR-030 | AWS Deployment Diagrams | Accepted | 2026-07-13 |
| ADR-031 | Manual UPI Payments as Year 1 Payment Strategy | Accepted | 2026-07-14 |
| ADR-032 | Free Notification Channels Only in Year 1 | Accepted | 2026-07-14 |
| ADR-033 | Cron + Management Commands as Year 1 Background Job Strategy | Accepted | 2026-07-14 |
| ADR-034 | Django Local Memory Cache as Year 1 Cache Strategy | Accepted | 2026-07-14 |
| ADR-035 | PostgreSQL Full-Text Search as Year 1 Search Strategy | Accepted | 2026-07-14 |
| ADR-036 | S3 Only as Year 1 File Storage Strategy | Accepted | 2026-07-14 |

## Creating a New ADR

1. Create a new file: `ADR-XXX.md` (use next available number)
2. Use the template from `docs/ai-governance/AI-Decision-Record.md`
3. Fill in all sections
4. Submit PR for review
5. Update this index

## Guidelines

- One decision per ADR
- Include context, decision, and consequences
- Record alternatives considered
- Link related ADRs
- Update status as decision evolves
