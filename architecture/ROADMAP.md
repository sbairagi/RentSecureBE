# Architecture Roadmap

## Overview
This roadmap describes the 30+ phase transformation from the current modular monolith to a structured modular monolith with enforced bounded contexts. No implementation occurs during Phase 0 (this phase). Phases 1+ execute one at a time, each keeping CI green and production behavior unchanged.

---

## Phase 0 — Architecture Baseline
**Goal**: Establish permanent architecture workspace, ADRs, principles, coding standards, and roadmap.

**Scope**: Documentation only. No code changes.

**Deliverables**:
- `architecture/` directory structure
- ADR template and initial ADRs
- Architecture principles
- Coding standards
- This roadmap
- Architecture README

---

## Phase 1 — Shared Foundation
**Goal**: Establish shared kernel contracts and base classes used across all contexts.

**Scope**: Introduce shared base classes, utilities, and contracts without moving business logic.

**Deliverables**:
- `architecture/contracts/` with interface definitions
- Shared base service, serializer, and view classes
- Shared exception hierarchy
- Shared response envelope

---

## Phase 2 — Infrastructure
**Goal**: Extract infrastructure concerns (cache, queue, storage) into explicit adapters.

**Scope**: Refactor direct Redis, Celery, and S3 usage into adapter interfaces.

**Deliverables**:
- Cache adapter interface + Redis implementation
- Queue adapter interface + Celery implementation
- Storage adapter interface + S3 implementation
- Configuration-driven adapter selection

---

## Phase 3 — Identity
**Goal**: Define and enforce Identity bounded context boundaries.

**Scope**: Extract authentication, authorization, and user management into a clearly bounded context.

**Deliverables**:
- `core/` restructured with explicit domain boundaries
- Identity service interface
- Permission service interface
- Contract tests for identity boundaries

---

## Phase 4 — Subscription
**Goal**: Define and enforce Subscription bounded context boundaries.

**Scope**: Extract subscription and usage limit enforcement into a clearly bounded context.

**Deliverables**:
- Subscription service interface
- Limit enforcement contracts
- Feature flag integration points
- Contract tests for subscription boundaries

---

## Phase 5 — Property
**Goal**: Define and enforce Property bounded context boundaries.

**Scope**: Extract buildings, units, and unit images into a clearly bounded context.

**Deliverables**:
- Property service interface
- Unit service interface
- Image/document storage contracts
- Contract tests for property boundaries

---

## Phase 6 — Renter
**Goal**: Define and enforce Renter bounded context boundaries.

**Scope**: Extract renter profiles, status management, and onboarding into a clearly bounded context.

**Deliverables**:
- Renter service interface
- Status transition contracts
- Onboarding workflow contracts
- Contract tests for renter boundaries

---

## Phase 7 — Rent
**Goal**: Define and enforce Rent bounded context boundaries.

**Scope**: Extract rent records, calculations, and agreements into a clearly bounded context.

**Deliverables**:
- Rent record service interface
- Calculation contracts
- Agreement draft contracts
- Contract tests for rent boundaries

---

## Phase 8 — Payments
**Goal**: Define and enforce Payments bounded context boundaries.

**Scope**: Extract payment processing, webhooks, and payouts into a clearly bounded context.

**Deliverables**:
- Payment service interface
- Webhook handler contracts
- Payout service interface
- Idempotency contracts
- Contract tests for payment boundaries

---

## Phase 9 — Notification
**Goal**: Define and enforce Notification bounded context boundaries.

**Scope**: Extract notification dispatch, templates, and preferences into a clearly bounded context.

**Deliverables**:
- Notification service interface
- Channel adapter contracts (email, push, WhatsApp, voice)
- Preference management contracts
- Contract tests for notification boundaries

---

## Phase 10 — Documents
**Goal**: Define and enforce Documents bounded context boundaries.

**Scope**: Extract PDF generation, templates, and document storage into a clearly bounded context.

**Deliverables**:
- Document service interface
- PDF generation contracts
- Template management contracts
- Contract tests for document boundaries

---

## Phase 11 — AI
**Goal**: Define and enforce AI bounded context boundaries.

**Scope**: Extract SmartBot, AI assistant, and AI governance into a clearly bounded context.

**Deliverables**:
- AI service interface
- Prompt versioning contracts
- AI governance contracts
- Contract tests for AI boundaries

---

## Phase 12 — Dashboard
**Goal**: Define and enforce Dashboard bounded context boundaries.

**Scope**: Extract analytics, reporting, and dashboards into a clearly bounded context.

**Deliverables**:
- Dashboard service interface
- Analytics aggregation contracts
- Report generation contracts
- Contract tests for dashboard boundaries

---

## Phase 13 — Architecture Enforcement
**Goal**: Automate architecture validation and enforce contracts in CI.

**Scope**: Strengthen import-linter rules, add architecture test suites, and enforce contract compliance.

**Deliverables**:
- Enhanced import-linter configuration
- Architecture test suite
- Automated contract validation
- Architecture review checklist

---

## Phases 14+ — Future Extensions
Future phases may include:
- Referral program extraction
- Caretaker module extraction
- External integrations boundary enforcement
- Domain event bus implementation
- Event sourcing for audit trails (if required)
- Service extraction preparation (packaging, deployment configuration)
- Observability enhancements
- Performance optimization
- Security hardening

---

## Infrastructure Evolution Stages

The following stages describe the production infrastructure evolution while keeping business logic unchanged.

### Stage 1 — Year 1 Bootstrap (Current)
**Goal:** Minimum viable production infrastructure within ₹2,000–3,000 INR/month budget.

**Infrastructure:**
- Single EC2 instance (t3.micro, Free Tier eligible)
- RDS PostgreSQL (db.t3.micro, Free Tier eligible)
- S3 for file storage
- CloudWatch Basic
- GitHub Actions CI/CD
- No Redis, No Celery, No CloudFront, No OpenSearch

**Services:**
- Manual UPI payments (free)
- Email + FCM Push + In-App notifications (free)
- Django management commands + cron for background jobs
- Django Local Memory Cache

---

### Stage 2 — Scale & Optimize
**Trigger:** CPU > 70% OR 500+ payments/month OR manual verification > 10 hrs/week.

**Infrastructure:**
- Auto Scaling Group (2x EC2 t3.small)
- Application Load Balancer
- RDS PostgreSQL (db.t3.small Multi-AZ)
- ElastiCache Redis (cache.t3.micro)
- S3 + CloudFront CDN
- Celery + Redis for background jobs
- Payment gateway integration (Razorpay/Cashfree)
- WhatsApp/SMS notifications enabled

---

### Stage 3 — High Availability
**Trigger:** 10,000+ users OR latency > 500ms OR search complexity requires advanced features.

**Infrastructure:**
- 2x EC2 t3.large
- RDS read replicas (db.t3.large)
- ElastiCache Redis cluster
- OpenSearch for advanced search
- Enhanced CloudWatch + X-Ray
- OpenTelemetry

---

### Stage 4 — Enterprise Scale
**Trigger:** 100,000+ users OR global expansion.

**Infrastructure:**
- Container orchestration (EKS/ECS)
- Microservice extraction from modular monolith
- Multi-region deployment
- OpenSearch cluster
- Full observability stack
- Global CDN

---

### Infrastructure Decision Matrix

| Component | Year 1 | Stage 2 | Stage 3 | Stage 4 |
|-----------|--------|---------|---------|---------|
| Payment | Manual UPI | Razorpay/Cashfree | Smart routing | Global orchestration |
| Notifications | Email + FCM | WhatsApp + SMS | Voice + Telegram | AI-powered |
| Background Jobs | Cron + management commands | Celery + Redis | Priority queues | Event-driven |
| Cache | Django Local Memory | Redis | Redis Cluster | Multi-tier |
| Search | PostgreSQL full-text | PostgreSQL optimized | OpenSearch | OpenSearch Cluster |
| File Storage | S3 only | S3 + CloudFront | Multi-region S3 | Global CDN |
| Observability | CloudWatch Basic | CloudWatch + X-Ray | OpenTelemetry | Full observability |
| Deployment | Single EC2 | ASG + ALB + Redis | Read replicas | Container orchestration |

---

## Execution Rules
1. One phase at a time
2. Each phase requires its own ADR
3. Each phase passes all CI checks before proceeding
4. Rollback plan must exist for each phase
5. No phase changes external APIs
6. No phase changes business logic behavior
7. Documentation updates are part of each phase
8. Infrastructure changes must preserve Clean Architecture and DDD patterns
9. Feature flags control all premium integrations
10. Domain interfaces remain stable across all stages
