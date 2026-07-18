# RentSecure Backend — Target Architecture

**Project:** RentSecure Backend
**Phase:** Target Architecture Design
**Date:** 2026-07-17
**Status:** DESIGN DOCUMENT — Awaiting Implementation
**Constraint:** Design only. No production code was modified.

---

## 1. Executive Summary

### 1.1 Vision

RentSecure Backend will evolve into an **enterprise-grade modular monolith** with clearly bounded contexts, clean dependency boundaries, and a design that supports extraction into microservices when the business requires it. The architecture will support 10–20 years of growth, accommodate multiple teams, and maintain operational simplicity while enabling technical excellence.

### 1.2 Goals

| Goal | Description |
|------|-------------|
| **Maintainability** | Code is easy to understand, modify, and extend |
| **Testability** | All components are independently testable |
| **Scalability** | Architecture supports growth from 10 to 1M+ users |
| **Extensibility** | New features integrate without modifying existing code |
| **Operational Excellence** | Monitoring, logging, and debugging are straightforward |
| **Team Autonomy** | Bounded contexts can be owned by separate teams |
| **Future-Proofing** | Microservice extraction is possible without rewrites |

### 1.3 Architecture Principles

1. **Business Capability Over Technical Layer** — Organize by what the business does, not how the code is structured
2. **Dependency Inversion** — Depend on abstractions, not concretions
3. **Single Responsibility** — Each module has one, and only one, reason to change
4. **Open/Closed Principle** — Open for extension, closed for modification
5. **Interface Segregation** — Small, focused interfaces over large, general ones
6. **Explicit Dependencies** — All dependencies are declared and visible
7. **Zero Leaky Abstractions** — Implementation details do not cross boundaries
8. **Event-Driven where Appropriate** — Use events for cross-context communication
9. **Synchronous by Default** — Prefer simplicity; async only when necessary
10. **Backward Compatibility** — Never break existing contracts without deprecation

### 1.4 Design Philosophy

The architecture follows the **Modular Monolith** pattern with **Hexagonal/Ports-and-Adapters** at the module level. Each bounded context is a module with:
- A **domain layer** (entities, value objects, domain services, events)
- An **application layer** (use cases, application services)
- An **infrastructure layer** (repositories, external adapters)
- A **presentation layer** (views, serializers, API endpoints)

Modules communicate through **well-defined interfaces** (ports) and **explicit events**. No module may import implementation details from another module.

### 1.5 Non-goals

| Non-goal | Reason |
|----------|--------|
| Microservices in Year 1 | Operational complexity outweighs benefits at current scale |
| Event sourcing | Not required for current domain complexity |
| CQRS for all reads | Only for specific high-read scenarios (e.g., analytics) |
| Multi-database | Single database per bounded context is sufficient |
| Service mesh | Not needed in monolithic deployment |
| Distributed transactions | ACID within monolith; sagas only when extracting services |

---

## 2. System Architecture

### 2.1 Layered Architecture

The system uses a **strict layered architecture** within each bounded context:

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│   (Views, Serializers, API Endpoints)   │
├─────────────────────────────────────────┤
│      Application Layer                  │
│   (Use Cases, Application Services)     │
├─────────────────────────────────────────┤
│         Domain Layer                    │
│  (Entities, Value Objects, Domain        │
│   Services, Events, Policies)           │
├─────────────────────────────────────────┤
│    Infrastructure Layer                 │
│  (Repositories, Adapters, External      │
│   Integrations, Storage)                │
└─────────────────────────────────────────┘
```

**Dependency rule:** Outer layers depend on inner layers. Inner layers know nothing about outer layers.

### 2.2 Clean Architecture

The layered architecture follows **Clean Architecture** principles:
- **Entities**: Core business objects (Renter, RentRecord, Unit)
- **Use Cases**: Application-specific business rules (CreateRenter, ProcessPayment)
- **Interface Adapters**: Controllers, presenters, gateways
- **Frameworks & Drivers**: Web framework, database, external APIs

The domain layer has **zero dependencies** on Django, DRF, or any external framework.

### 2.3 Domain-Driven Design (DDD)

The architecture applies **DDD tactical patterns**:
- **Aggregates**: Renter + RentRecords, Unit + Renters, Building + Units
- **Entities**: Objects with identity (User, Renter, RentRecord)
- **Value Objects**: Immutable objects (Money, DateRange, Address)
- **Domain Events**: RenterCreated, RentPaid, AgreementSigned
- **Domain Services**: Business logic that doesn't belong to an entity
- **Repositories**: Data access abstraction
- **Factories**: Object creation logic
- **Policies**: Business rules and validation (FeatureEnforcer)

### 2.4 Hexagonal Architecture (Ports and Adapters)

Each bounded context uses **Hexagonal Architecture** at the module level:

```
                    ┌─────────────┐
                    │   Domain     │
                    │   (Ports)    │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Django   │    │  Twilio  │    │  Leegality│
    │ Adapter   │    │ Adapter  │    │  Adapter  │
    └──────────┘    └──────────┘    └──────────┘
```

**Ports** (interfaces) are defined in the domain layer. **Adapters** (implementations) are in the infrastructure layer.

### 2.5 Modular Monolith

The system is a **single deployable unit** with **internal modularity**:
- Each bounded context is a Django app
- Apps communicate through **explicit interfaces** and **domain events**
- No cross-app model imports
- Shared kernel for common types and utilities
- Clear module boundaries enforced by import-linter

**Future microservice extraction path:**
1. Extract bounded context to separate service
2. Replace in-process calls with HTTP/events
3. Deploy independently
4. No changes to business logic required

---

## 3. High-Level Module Map

### 3.1 Module Overview

| Module | Responsibility | Public APIs | Internal Components | Dependencies | Ownership |
|--------|---------------|-------------|---------------------|--------------|-----------|
| **Identity** | Users, authentication, authorization, OTP, passwords | Auth API, User API, OTP API | Users, Profiles, Roles, Permissions, OTP, Password Reset | Shared Kernel | Identity Team |
| **Subscriptions** | Plans, add-ons, usage limits, feature enforcement | Subscription API, Plan API, Usage API | Plans, Add-ons, Usage Limits, Feature Enforcer | Identity, Shared Kernel | Platform Team |
| **Property** | Buildings, units, renters, rent records, extra charges, property tax, caretakers, unit images/documents, rent agreement drafts | Property API, Unit API, Renter API, Rent Record API | Buildings, Units, Renters, RentRecords, ExtraCharges, PropertyTax, Caretakers, UnitImages, UnitDocuments, RentAgreementDrafts, Repositories, Policies | Identity, Notifications, Documents, Shared Kernel | Property Team |
| **Rent** | Rent lifecycle, payment tracking, payouts, reminders | Rent API (merged into Property) | RentRecord (entity), PaymentService, PayoutService, ReminderService | Property, Payments, Notifications, Documents | Property Team |
| **Payments** | Payment gateway adapters, payout processing, webhooks | Payment API (internal), Webhook API | ManualAdapter, RazorpayAdapter, CashfreeAdapter, PayoutService, WebhookHandlers | Property, Notifications, Shared Kernel | Finance Team |
| **Notifications** | Notification channels: email, push, WhatsApp, SMS, voice | Notification API, Channel API | Channels (Email, Push, WhatsApp, SMS, Voice), NotificationService, TemplateService | Identity, Shared Kernel, External Adapters | Platform Team |
| **Documents** | PDF generation, e-signature, document storage | Document API, PDF API, E-Signature API | PDFGenerator, AgreementService, ReceiptService, LeegalityAdapter, StorageAdapter | Property, Finance, Identity, Shared Kernel | Property Team |
| **Finance** | CA profiles, tax submissions, tax documents | Finance API, Tax API | CAProfile, TaxSubmission, TaxCalculator, TaxDocumentGenerator | Identity, Property, Documents, Shared Kernel | Finance Team |
| **AI** | Chatbot, GPT, intents, actions, chat history | AI API, Chat API | Chatbot, GPTClient, IntentExtractor, ActionDispatcher, ChatHistory | Property, Notifications, Documents, Payments, Shared Kernel | AI Team |
| **Dashboard** | Owner dashboard, analytics, reporting | Dashboard API, Analytics API | DashboardService, AnalyticsService, ReportGenerator | Property, Rent, Finance, Notifications | Analytics Team |
| **Referral** | Referral program, bonuses, rewards | Referral API | Referral, ReferralService, BonusService | Identity, Shared Kernel | Growth Team |
| **Shared Kernel** | Common utilities, types, exceptions, validators | None (internal) | Utils, Validators, Types, Constants, Exceptions, Events | None | All Teams |
| **Infrastructure** | Cross-cutting concerns: logging, metrics, caching, security | None (internal) | Logging, Metrics, Caching, Security, Health Checks | Shared Kernel, External Frameworks | Platform Team |

### 3.2 Module Details

#### 3.2.1 Identity Module

**Responsibility:** User authentication, authorization, profile management, OTP, password reset.

**Public APIs:**
- `POST /api/auth/send-otp`
- `POST /api/auth/verify-otp`
- `POST /api/auth/change-password`
- `POST /api/auth/reset-password`
- `GET /api/users/me`
- `PATCH /api/users/me`

**Internal Components:**
- `entities/`: User, UserProfile, NotificationPreference, OTP, OwnerBankDetails
- `services/`: AuthService, OTPService, PasswordService, TokenService
- `repositories/`: UserRepository, ProfileRepository
- `events/`: UserCreated, UserVerified, PasswordChanged

**Dependencies:** Shared Kernel

**Ownership:** Identity Team

#### 3.2.2 Subscriptions Module

**Responsibility:** Subscription plans, add-on purchases, usage limits, feature enforcement.

**Public APIs:**
- `GET /api/subscriptions/plans`
- `GET /api/subscriptions/usage-limits`
- `POST /api/subscriptions/add-ons`

**Internal Components:**
- `entities/`: SubscriptionPlan, PlanFeatureLimit, UserSubscription, AddOnPurchase, UsageLimit
- `services/`: SubscriptionService, UsageLimitService, FeatureEnforcer
- `repositories/`: SubscriptionRepository, UsageLimitRepository
- `events/`: SubscriptionCreated, SubscriptionExpired, UsageLimitExceeded

**Dependencies:** Identity, Shared Kernel

**Ownership:** Platform Team

#### 3.2.3 Property Module

**Responsibility:** Property management — buildings, units, renters, rent records, extra charges, property tax, caretakers, unit images/documents, rent agreement drafts.

**Public APIs:**
- `GET /api/properties/buildings`
- `POST /api/properties/buildings`
- `GET /api/properties/units`
- `POST /api/properties/units`
- `GET /api/properties/renters`
- `POST /api/properties/renters`
- `GET /api/properties/rent-records`
- `POST /api/properties/rent-records`
- `GET /api/properties/extra-charges`
- `POST /api/properties/extra-charges`

**Internal Components:**
- `entities/`: Building, Unit, Renter, RentRecord, ExtraCharge, PropertyTaxRecord, CareTaker, UnitImage, UnitDocument, RentAgreementDraft
- `services/`: BuildingService, UnitService, RenterService, RentRecordService, ExtraChargeService, ReceiptService, NotificationService
- `repositories/`: BuildingRepository, UnitRepository, RenterRepository, RentRecordRepository
- `policies/`: UnitPolicy, RenterPolicy, RentRecordPolicy
- `events/`: BuildingCreated, UnitCreated, RenterCreated, RentPaid, RentOverdue, ExtraChargeCreated

**Dependencies:** Identity, Notifications, Documents, Shared Kernel

**Ownership:** Property Team

#### 3.2.4 Rent Module (Merged into Property)

**Responsibility:** Rent lifecycle, payment tracking, payout processing, reminders.

**Note:** The `Rent` module is not a separate Django app. It is a **logical subdomain** within the `Property` module. Rent-related entities (RentRecord), services (PaymentService, PayoutService, ReminderService), and repositories (RentRecordRepository) live in the `properties/` app but are organized under `properties/domain/rent/` and `properties/application/rent/`.

**Rationale:** Rent is a core domain concept that is tightly coupled to Property. Splitting it into a separate app would create unnecessary cross-app dependencies without providing sufficient autonomy.

#### 3.2.5 Payments Module

**Responsibility:** Payment gateway adapters, payout processing, webhook handling.

**Public APIs:**
- Internal only — not exposed directly to frontend
- Webhook endpoints: `/api/payments/webhooks/razorpay`, `/api/payments/webhooks/cashfree`

**Internal Components:**
- `adapters/`: ManualAdapter, RazorpayAdapter, CashfreeAdapter
- `services/`: PaymentService, PayoutService, WebhookService
- `webhooks/`: RazorpayWebhook, CashfreeWebhook
- `events/`: PaymentInitiated, PaymentCompleted, PaymentFailed, PayoutInitiated, PayoutCompleted, PayoutFailed

**Dependencies:** Property, Notifications, Shared Kernel

**Ownership:** Finance Team

#### 3.2.6 Notifications Module

**Responsibility:** Notification channels (email, push, WhatsApp, SMS, voice) and channel orchestration.

**Public APIs:**
- `GET /api/notifications/`
- `POST /api/notifications/register-fcm`
- `POST /api/notifications/save-token`
- `POST /api/notifications/mark-read`

**Internal Components:**
- `channels/`: EmailChannel, PushChannel, WhatsAppChannel, SMSChannel, VoiceChannel
- `services/`: NotificationService, CommunicationService, TemplateService
- `events/`: NotificationSent, NotificationFailed

**Dependencies:** Identity, Shared Kernel, External Adapters (Twilio, FCM, AWS SES, OpenAI)

**Ownership:** Platform Team

#### 3.2.7 Documents Module

**Responsibility:** PDF generation, e-signature, document storage, document retrieval.

**Public APIs:**
- `GET /api/documents/rent-receipt/{id}`
- `GET /api/documents/rent-agreement/{id}`
- `GET /api/documents/unit-dossier/{id}`
- `POST /api/documents/send-for-signature`
- `POST /api/documents/webhooks/leegality`

**Internal Components:**
- `services/`: PDFGenerator, AgreementService, ReceiptService, LeegalityService, InvoiceService
- `adapters/`: LeegalityAdapter, StorageAdapter (S3)
- `templates/`: PDF templates (HTML)
- `events/`: DocumentGenerated, DocumentSent, DocumentSigned

**Dependencies:** Property, Finance, Identity, Shared Kernel

**Ownership:** Property Team

#### 3.2.8 Finance Module

**Responsibility:** CA profiles, tax submissions, tax document generation, tax calculations.

**Public APIs:**
- `GET /api/finance/ca-profiles`
- `POST /api/finance/ca-profiles`
- `GET /api/finance/tax-submissions`
- `POST /api/finance/tax-submissions`
- `GET /api/finance/tax-summary/download`

**Internal Components:**
- `entities/`: CAProfile, TaxSubmissionToCA, TaxCalculation
- `services/`: TaxService, TaxDocumentService, CAService
- `repositories/`: TaxRepository, CAProfileRepository
- `events/`: TaxSubmitted, TaxDocumentsGenerated

**Dependencies:** Identity, Property, Documents, Shared Kernel

**Ownership:** Finance Team

#### 3.2.9 AI Module

**Responsibility:** AI assistant, chatbot, GPT integration, intent extraction, actions, chat history.

**Public APIs:**
- `POST /api/assistant/chat`

**Internal Components:**
- `entities/`: SmartBotChat, SmartBotMessage, AIAlert
- `services/`: ChatbotService, GPTClient, IntentExtractor, ActionDispatcher
- `actions/`: SendRentReminder, RetryPayout, SendRentAgreement, SendAgreementForSignature
- `events/`: ChatMessageReceived, ActionExecuted, AlertCreated

**Dependencies:** Property, Notifications, Documents, Payments, Shared Kernel

**Ownership:** AI Team

#### 3.2.10 Dashboard Module

**Responsibility:** Owner dashboard, analytics, reporting, insights.

**Public APIs:**
- `GET /api/dashboard/owner/summary`
- `GET /api/dashboard/owner/rent-analytics`
- `GET /api/dashboard/owner/occupancy-analytics`
- `GET /api/dashboard/owner/monthly-summary`

**Internal Components:**
- `services/`: DashboardService, AnalyticsService, ReportGenerator
- `read-models/`: OwnerDashboardReadModel, RentAnalyticsReadModel
- `events/`: DashboardViewed, ReportGenerated

**Dependencies:** Property, Rent, Finance, Notifications, Shared Kernel

**Ownership:** Analytics Team

#### 3.2.11 Referral Module

**Responsibility:** Referral program, referral codes, bonus tracking.

**Public APIs:**
- `POST /api/referrals/process`
- `GET /api/referrals/my-referrals`

**Internal Components:**
- `entities/`: Referral, ReferralCode
- `services/`: ReferralService, BonusService
- `repositories/`: ReferralRepository
- `events/`: ReferralCreated, ReferralProcessed, BonusEarned

**Dependencies:** Identity, Shared Kernel

**Ownership:** Growth Team

#### 3.2.12 Shared Kernel

**Responsibility:** Common utilities, types, exceptions, validators, constants, enums, base classes.

**Internal Components:**
- `types/`: Common type aliases and protocols
- `exceptions/`: Base exceptions (ValidationError, NotFoundError, PermissionDeniedError)
- `validators/`: Reusable validators
- `constants/`: Application-wide constants
- `enums/`: Shared enumerations
- `utils/`: Utility functions
- `events/`: Base event classes and event bus

**Dependencies:** None

**Ownership:** Platform Team

#### 3.2.13 Infrastructure Module

**Responsibility:** Cross-cutting concerns: logging, metrics, caching, security, health checks, configuration.

**Internal Components:**
- `logging/`: Structured logging, log formatters
- `metrics/`: Prometheus metrics, custom metrics
- `caching/`: Cache strategies, cache decorators
- `security/`: Rate limiting, input sanitization, secret management
- `health/`: Health check endpoints
- `config/`: Configuration management

**Dependencies:** Shared Kernel, External Frameworks (Django, DRF, Celery, Redis)

**Ownership:** Platform Team

---

## 4. Dependency Rules

### 4.1 Allowed Dependency Matrix

| Source Module | Target Module | Allowed? | Rationale |
|---------------|---------------|----------|-----------|
| Identity | Shared Kernel | ✅ | Common utilities |
| Subscriptions | Identity | ✅ | Needs User model |
| Subscriptions | Shared Kernel | ✅ | Common utilities |
| Property | Identity | ✅ | Needs User for ownership |
| Property | Subscriptions | ✅ | Needs feature enforcement |
| Property | Notifications | ✅ | Needs notification channels |
| Property | Documents | ✅ | Needs PDF generation, e-signature |
| Property | Shared Kernel | ✅ | Common utilities |
| Rent | Property | ✅ | RentRecord is a Property entity |
| Payments | Property | ✅ | Needs RentRecord for payouts |
| Payments | Notifications | ✅ | Needs to send payment notifications |
| Payments | Shared Kernel | ✅ | Common utilities |
| Notifications | Identity | ✅ | Needs User for device tokens |
| Notifications | Shared Kernel | ✅ | Common utilities |
| Documents | Property | ✅ | Needs Renter, Unit, RentRecord |
| Documents | Finance | ✅ | Needs tax documents |
| Documents | Identity | ✅ | Needs User for ownership |
| Documents | Shared Kernel | ✅ | Common utilities |
| Finance | Identity | ✅ | Needs User for CA profiles |
| Finance | Property | ✅ | Needs Unit, Renter for tax data |
| Finance | Documents | ✅ | Needs PDF generation |
| Finance | Shared Kernel | ✅ | Common utilities |
| AI | Property | ✅ | Needs rent data, renter data |
| AI | Notifications | ✅ | Needs WhatsApp, push channels |
| AI | Documents | ✅ | Needs agreement PDFs, e-signature |
| AI | Payments | ✅ | Needs payout status |
| AI | Shared Kernel | ✅ | Common utilities |
| Dashboard | Property | ✅ | Needs property data |
| Dashboard | Rent | ✅ | Needs rent data |
| Dashboard | Finance | ✅ | Needs tax data |
| Dashboard | Notifications | ✅ | Needs to send summaries |
| Dashboard | Shared Kernel | ✅ | Common utilities |
| Referral | Identity | ✅ | Needs User model |
| Referral | Shared Kernel | ✅ | Common utilities |
| Infrastructure | Shared Kernel | ✅ | Needs base classes |
| Infrastructure | External Frameworks | ✅ | Django, DRF, Celery, Redis |
| All | Shared Kernel | ✅ | Common utilities are safe to depend on |

### 4.2 Forbidden Dependency Matrix

| Source Module | Target Module | Forbidden? | Rationale |
|---------------|---------------|------------|-----------|
| Identity | Property | ❌ | Identity must not know about property concepts |
| Identity | Finance | ❌ | Identity must not know about finance concepts |
| Identity | Notifications | ❌ | Identity must not know about notification channels |
| Identity | Documents | ❌ | Identity must not know about documents |
| Identity | AI | ❌ | Identity must not know about AI features |
| Identity | Dashboard | ❌ | Identity must not know about analytics |
| Identity | Referral | ❌ | Identity must not know about referral logic |
| Property | Finance | ❌ | Property must not know about tax/CA concepts |
| Property | AI | ❌ | Property must not know about AI features |
| Property | Dashboard | ❌ | Property must not know about analytics |
| Property | Referral | ❌ | Property must not know about referral logic |
| Finance | Property | ❌ | Finance must not know about property management |
| Finance | AI | ❌ | Finance must not know about AI features |
| Finance | Dashboard | ❌ | Finance must not know about analytics |
| Finance | Referral | ❌ | Finance must not know about referral logic |
| Notifications | Property | ❌ | Notifications must not know about property concepts |
| Notifications | Finance | ❌ | Notifications must not know about finance concepts |
| Notifications | AI | ❌ | Notifications must not know about AI features |
| Notifications | Dashboard | ❌ | Notifications must not know about analytics |
| Notifications | Referral | ❌ | Notifications must not know about referral logic |
| Documents | Finance | ❌ | Documents must not know about finance concepts (except tax docs) |
| Documents | AI | ❌ | Documents must not know about AI features |
| Documents | Dashboard | ❌ | Documents must not know about analytics |
| Documents | Referral | ❌ | Documents must not know about referral logic |
| AI | Finance | ❌ | AI must not know about finance concepts |
| AI | Dashboard | ❌ | AI must not know about analytics |
| AI | Referral | ❌ | AI must not know about referral logic |
| Dashboard | AI | ❌ | Dashboard must not know about AI features |
| Dashboard | Referral | ❌ | Dashboard must not know about referral logic |
| Referral | Property | ❌ | Referral must not know about property concepts |
| Referral | Finance | ❌ | Referral must not know about finance concepts |
| Referral | Notifications | ❌ | Referral must not know about notification channels |
| Referral | Documents | ❌ | Referral must not know about documents |
| Referral | AI | ❌ | Referral must not know about AI features |
| Referral | Dashboard | ❌ | Referral must not know about analytics |
| Any | Infrastructure | ❌ | Infrastructure is a cross-cutting concern, not a dependency |
| Domain | Presentation | ❌ | Domain must not know about views/serializers |
| Domain | Infrastructure | ❌ | Domain must not know about database/ORM |
| Application | Infrastructure | ❌ | Application must not know about database/ORM |

### 4.3 Dependency Enforcement

Dependencies are enforced through:

1. **import-linter**: Automated checks in CI
2. **Architecture Guardian**: Custom script that validates module boundaries
3. **Code Review**: Manual verification of dependency rules
4. **Mypy**: Type checking ensures interface contracts are respected
5. **Documentation**: ADRs document why dependencies exist

---

## 5. Layer Responsibilities

### 5.1 Views (Presentation Layer)

**Responsibility:**
- Handle HTTP requests and responses
- Authenticate and authorize requests
- Validate input (with serializers)
- Call application services
- Return appropriate HTTP responses

**Rules:**
- Views must NOT contain business logic
- Views must NOT directly access repositories or databases
- Views must NOT call other views
- Views must NOT know about domain entities
- Views delegate to application services

**Allowed to:**
- Import application services
- Import serializers
- Import permissions
- Call application service methods

**Forbidden to:**
- Import domain entities (except for type hints in `TYPE_CHECKING`)
- Import repositories
- Import other views
- Contain business logic

### 5.2 Application Services

**Responsibility:**
- Orchestrate use cases
- Coordinate domain objects
- Manage transactions
- Handle application-level concerns (logging, caching)

**Rules:**
- Application services must NOT contain business rules
- Application services must NOT know about HTTP or Django
- Application services must NOT directly access databases
- Application services delegate to domain services and repositories (via interfaces)

**Allowed to:**
- Import domain services
- Import repository interfaces (ports)
- Import domain events
- Import other application services in the same module

**Forbidden to:**
- Import views or serializers
- Import Django ORM models
- Import external frameworks
- Contain business logic (belongs in domain)

### 5.3 Domain Services

**Responsibility:**
- Implement business rules that don't belong to a single entity
- Coordinate multiple entities
- Enforce business invariants

**Rules:**
- Domain services must NOT know about databases
- Domain services must NOT know about HTTP or Django
- Domain services must NOT depend on infrastructure

**Allowed to:**
- Import domain entities
- Import value objects
- Import domain events
- Import other domain services

**Forbidden to:**
- Import repositories (use interfaces)
- Import application services
- Import views or serializers
- Import Django ORM models

### 5.4 Entities

**Responsibility:**
- Represent core business objects with identity
- Enforce business invariants
- Track state changes
- Emit domain events

**Rules:**
- Entities must NOT know about databases
- Entities must NOT know about HTTP or Django
- Entities must NOT depend on infrastructure
- Entities must be persistence-ignorant

**Allowed to:**
- Import value objects
- Import domain events
- Import other entities in the same aggregate

**Forbidden to:**
- Import repositories
- Import application services
- Import views or serializers
- Import Django ORM (except for `models.Model` base class)

### 5.5 Value Objects

**Responsibility:**
- Represent immutable values
- Enforce validation rules
- Provide type safety

**Rules:**
- Value objects must be immutable
- Value objects must NOT have identity
- Value objects must NOT know about databases

**Allowed to:**
- Import other value objects
- Import domain events (for event data)

**Forbidden to:**
- Import entities
- Import repositories
- Import application services
- Import Django ORM

### 5.6 Repositories

**Responsibility:**
- Abstract data access
- Provide collection-like interface for aggregates
- Hide ORM/query implementation details

**Rules:**
- Repositories are interfaces (ports) in the domain layer
- Repository implementations are in the infrastructure layer
- Repositories must NOT contain business logic
- Repositories must NOT emit domain events

**Allowed to:**
- Import domain entities (for type hints)
- Import value objects (for query parameters)

**Forbidden to:**
- Import application services
- Import views or serializers
- Contain business logic

### 5.7 Ports (Interfaces)

**Responsibility:**
- Define contracts for external integrations
- Enable dependency inversion
- Allow testing with mocks

**Rules:**
- Ports are defined in the domain or application layer
- Ports are implemented in the infrastructure layer
- Ports must be small and focused
- Ports must be versioned when changed

**Examples:**
- `PaymentGateway` port
- `NotificationChannel` port
- `StorageService` port
- `LLMClient` port

### 5.8 Adapters

**Responsibility:**
- Implement ports for specific external systems
- Handle translation between domain models and external APIs
- Manage connection lifecycle

**Rules:**
- Adapters must implement exactly one port
- Adapters must NOT contain business logic
- Adapters must NOT be imported by domain layer
- Adapters must handle external API errors gracefully

**Examples:**
- `RazorpayAdapter` implements `PaymentGateway`
- `TwilioWhatsAppAdapter` implements `NotificationChannel`
- `S3StorageAdapter` implements `StorageService`
- `OpenAILLMAdapter` implements `LLMClient`

### 5.9 Events

**Responsibility:**
- Communicate between bounded contexts
- Enable eventual consistency
- Decouple producers from consumers

**Rules:**
- Events must be immutable
- Events must contain all data needed by consumers
- Events must be versioned when schema changes
- Event handlers must be idempotent

**Event types:**
- **Domain Events**: Produced by domain layer (RenterCreated, RentPaid)
- **Integration Events**: Cross-context communication (UserCreated → SendWelcomeEmail)
- **System Events**: Infrastructure events (HealthCheckFailed)

### 5.10 Policies

**Responsibility:**
- Enforce business rules and constraints
- Validate state transitions
- Check permissions and limits

**Rules:**
- Policies must be pure functions (no side effects)
- Policies must return boolean or error details
- Policies must be testable without database

**Examples:**
- `UnitPolicy.can_access_unit(unit, user)`
- `RenterPolicy.can_create_renter(unit, user)`
- `RentRecordPolicy.can_mark_paid(rent_record, user)`

### 5.11 Validators

**Responsibility:**
- Validate input data
- Enforce format and type constraints
- Provide clear error messages

**Rules:**
- Validators must be pure functions
- Validators must NOT have side effects
- Validators must be reusable across contexts

**Examples:**
- `validate_non_empty_string(value)`
- `validate_positive_number(value)`
- `validate_phone_number(value)`

### 5.12 Serializers

**Responsibility:**
- Transform domain objects to/from JSON
- Validate input data
- Handle field-level serialization

**Rules:**
- Serializers must NOT contain business logic
- Serializers must NOT access repositories directly
- Serializers must delegate validation to domain layer

### 5.13 Signals

**Responsibility:**
- React to domain events within the same module
- Maintain invariants across aggregates
- Trigger side effects (notifications, logging)

**Rules:**
- Signals must NOT cross module boundaries
- Signals must be idempotent
- Signals must NOT contain business logic
- Signals must NOT trigger other signals

**Allowed signal patterns:**
- `post_save` → update related entities in the same module
- `post_delete` → clean up related data in the same module
- Domain event → trigger side effects within the same module

**Forbidden signal patterns:**
- Signal in one module calling code in another module
- Signal triggering another signal
- Signal containing business logic

### 5.14 Tasks (Background Jobs)

**Responsibility:**
- Execute long-running or scheduled operations
- Process asynchronous work
- Generate reports

**Rules:**
- Tasks must be idempotent
- Tasks must be retryable
- Tasks must NOT modify domain entities directly (use application services)
- Tasks must be logged and monitored

**Allowed tasks:**
- `send_monthly_rent_summary`
- `generate_monthly_rent_records`
- `process_rent_reminders`
- `generate_tax_documents`

### 5.15 Management Commands

**Responsibility:**
- Administrative operations
- Data seeding
- Maintenance tasks
- One-off scripts

**Rules:**
- Management commands must NOT be used for scheduled jobs (use tasks instead)
- Management commands must be idempotent where possible
- Management commands must have clear logging

---

## 6. Domain Events Strategy

### 6.1 Event Naming

Events follow the pattern: `{PastTenseVerb}{AggregateName}`

**Examples:**
- `RenterCreated`
- `RentRecordPaid`
- `RentRecordOverdue`
- `AgreementSigned`
- `PaymentCompleted`
- `PayoutFailed`
- `NotificationSent`
- `DocumentGenerated`

### 6.2 Publishing Rules

| Event Type | Producer | Consumer | Delivery |
|------------|----------|----------|----------|
| Domain Event | Domain entity/service | Same module | In-process |
| Integration Event | Application service | Other modules | In-process (current), message queue (future) |
| System Event | Infrastructure | Monitoring/alerting | In-process |

**Rules:**
- Domain events are published immediately after state change
- Integration events are published after transaction commits
- Events must be serializable (JSON)
- Events must contain correlation IDs

### 6.3 Consumers

Consumers are **explicit** and **registered** in the application layer:

```python
# Property module
class RenterEventHandlers:
    @handles(RenterCreated)
    def on_renter_created(self, event: RenterCreated) -> None:
        # Generate onboarding token
        # Send welcome notification
        # Create usage limits
        ...
```

### 6.4 Event Flow

```
┌─────────────┐
│   Domain     │
│   Entity     │
│             │
│ 1. State    │
│    change   │
│             │
│ 2. Emit     │
│    event    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Event      │
│   Bus        │
│             │
│ 3. Route    │
│    event    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Handler    │
│             │
│ 4. Execute  │
│    side     │
│    effects  │
└─────────────┘
```

### 6.5 Idempotency

All event handlers must be **idempotent**:
- Events have unique IDs
- Handlers track processed event IDs
- Duplicate events are ignored
- Retries are safe

### 6.6 Transaction Boundaries

| Scenario | Boundary | Rationale |
|----------|----------|-----------|
| Single aggregate update | Database transaction | ACID guaranteed |
| Multiple aggregates in same module | Database transaction | Same database |
| Cross-module event | Event after commit | Eventual consistency |
| External API call | Compensating action | No distributed transactions |

**Rule:** No distributed transactions in Year 1. Use compensating actions for cross-module consistency.

---

## 7. Repository Strategy

### 7.1 Repository Interfaces (Ports)

Repositories are defined as **interfaces in the domain layer**:

```python
# properties/domain/renter/repositories/renter_repository.py
class RenterRepository(Protocol):
    def find_by_id(self, renter_id: int) -> Renter | None: ...
    def find_by_unit(self, unit_id: int) -> list[Renter]: ...
    def save(self, renter: Renter) -> Renter: ...
    def delete(self, renter: Renter) -> None: ...
```

### 7.2 ORM Implementation (Adapters)

Repository implementations use Django ORM in the infrastructure layer:

```python
# properties/infrastructure/repositories/django_renter_repository.py
class DjangoRenterRepository:
    def find_by_id(self, renter_id: int) -> Renter | None:
        return Renter.objects.select_related("unit", "user").filter(pk=renter_id).first()

    def save(self, renter: Renter) -> Renter:
        renter.save()
        return renter
```

### 7.3 Query Services

Complex queries that don't map to a single repository use **query services**:

```python
# properties/domain/rent/queries/rent_analytics_query.py
class RentAnalyticsQuery:
    def get_rent_inflow_summary(self, owner_id: int) -> RentInflowSummary: ...
    def get_payment_trends(self, owner_id: int, months: int) -> list[PaymentTrend]: ...
```

### 7.4 Read Models

For read-heavy scenarios, use **read models** (denormalized projections):

```python
# dashboard/read-models/owner_dashboard_read_model.py
class OwnerDashboardReadModel:
    def get_summary(self, owner_id: int) -> OwnerDashboardSummary: ...
```

Read models are populated by domain events and updated asynchronously.

### 7.5 Specifications

For complex query criteria, use the **Specification pattern**:

```python
# properties/domain/rent/specifications/rent_specifications.py
class OverdueRentSpecification:
    def is_satisfied_by(self, rent_record: RentRecord) -> bool:
        return rent_record.status == RentRecord.Status.PENDING and rent_record.due_date < date.today()

class PendingPayoutSpecification:
    def is_satisfied_by(self, rent_record: RentRecord) -> bool:
        return rent_record.payout_status == "PENDING"
```

---

## 8. External Integration Strategy

### 8.1 Integration Boundaries

All external integrations use **Ports and Adapters**:

```
Domain Layer
    │
    ▼
Port (Interface)
    │
    ▼
Adapter (Implementation)
    │
    ▼
External API
```

### 8.2 Payment Gateways

**Port:** `PaymentGateway`

**Adapters:**
- `ManualPaymentAdapter` — Manual UPI payment (Year 1)
- `RazorpayAdapter` — Razorpay integration (Stage 2)
- `CashfreeAdapter` — Cashfree integration (Stage 2)

**Interface:**
```python
class PaymentGateway(Protocol):
    def create_payment(self, rent_record: RentRecord) -> PaymentResult: ...
    def verify_payment(self, request: HttpRequest) -> PaymentVerification: ...
    def process_payout(self, payout: Payout) -> PayoutResult: ...
```

### 8.3 WhatsApp

**Port:** `NotificationChannel`

**Adapter:** `TwilioWhatsAppAdapter`

**Interface:**
```python
class NotificationChannel(Protocol):
    def send_text(self, to: str, message: str) -> SendResult: ...
    def send_audio(self, to: str, audio_url: str) -> SendResult: ...
    def send_template(self, to: str, template: str, variables: dict) -> SendResult: ...
```

### 8.4 SMS

**Port:** `NotificationChannel`

**Adapter:** `TwilioSMSAdapter`, `MSG91Adapter`

### 8.5 Push Notifications

**Port:** `NotificationChannel`

**Adapter:** `FCMAdapter` (Firebase Cloud Messaging), `ExpoAdapter`

### 8.6 Email

**Port:** `NotificationChannel`

**Adapter:** `SESAdapter` (AWS SES), `SMTPAdapter`

### 8.7 OpenAI

**Port:** `LLMClient`

**Adapter:** `OpenAIAdapter`

**Interface:**
```python
class LLMClient(Protocol):
    def chat_completion(self, messages: list[Message]) -> Completion: ...
    def embed(self, text: str) -> Embedding: ...
```

### 8.8 Leegality

**Port:** `ESignatureProvider`

**Adapter:** `LeegalityAdapter`

**Interface:**
```python
class ESignatureProvider(Protocol):
    def send_for_signature(self, document: Document, recipients: list[Recipient]) -> SignatureRequest: ...
    def check_status(self, signature_request_id: str) -> SignatureStatus: ...
    def handle_webhook(self, request: HttpRequest) -> WebhookResult: ...
```

### 8.9 Storage

**Port:** `StorageService`

**Adapters:**
- `LocalStorageAdapter` — Development
- `S3StorageAdapter` — Production

**Interface:**
```python
class StorageService(Protocol):
    def upload(self, path: str, content: bytes, content_type: str) -> StorageURL: ...
    def download(self, path: str) -> bytes: ...
    def delete(self, path: str) -> None: ...
    def get_url(self, path: str) -> str: ...
```

### 8.10 Translation

**Port:** `TranslationService`

**Adapter:** `GoogleTranslateAdapter`, `OpenAITranslationAdapter`

**Interface:**
```python
class TranslationService(Protocol):
    def translate(self, text: str, target_language: str) -> str: ...
    def detect_language(self, text: str) -> str: ...
```

### 8.11 Voice

**Port:** `TextToSpeechService`

**Adapter:** `OpenAITTSSAdapter`, `GoogleTTSAdapter`

**Interface:**
```python
class TextToSpeechService(Protocol):
    def synthesize(self, text: str, language: str) -> AudioFile: ...
```

---

## 9. Feature Flag Strategy

### 9.1 Flag Categories

| Category | Purpose | Examples |
|----------|---------|----------|
| **Experimental** | Features in development, not ready for production | `ENABLE_OPENAI`, `ENABLE_LEEGALITY` |
| **Premium** | Features available only to paid plans | `ENABLE_ADVANCED_ANALYTICS`, `ENABLE_BULK_OPERATIONS` |
| **Disabled-by-default** | Features that are complete but not yet launched | `ENABLE_WHATSAPP`, `ENABLE_VOICE` |
| **Operational** | Infrastructure flags, not user-facing | `ENABLE_CACHE`, `ENABLE_RATE_LIMITING` |

### 9.2 Flag Management

- **Storage:** Environment variables + database table for dynamic flags
- **Evaluation:** Flags are evaluated at runtime, not import time
- **Default values:** Safe defaults (disabled) in code, overridden by environment
- **Documentation:** Every flag documented in `docs/feature-flags.md`

### 9.3 Flag Implementation

```python
# shared/domain/feature_flags.py
class FeatureFlags:
    def is_enabled(self, flag: str, user: User | None = None) -> bool:
        # Check database for user-specific flags
        # Fall back to environment variables
        ...
```

### 9.4 Guarded Imports

Services behind feature flags use **lazy imports**:

```python
# properties/services/rent_record_service.py
def process_payment(self, rent_record: RentRecord) -> PaymentResult:
    if not settings.ENABLE_RAZORPAY:
        return PaymentResult.error("Razorpay is not enabled")

    from payments.adapters.razorpay import RazorpayAdapter
    return RazorpayAdapter().create_payment(rent_record)
```

---

## 10. Background Processing Strategy

### 10.1 Processing Types

| Type | Use Case | Implementation |
|------|----------|----------------|
| **Management Command** | Admin tasks, data seeding, one-off scripts | `manage.py command` |
| **Scheduled Task** | Periodic jobs (daily, weekly, monthly) | Management command + cron/systemd |
| **Background Worker** | Async processing, long-running tasks | Celery (Stage 2) |
| **Immediate** | Synchronous, user-facing operations | Direct call |

### 10.2 Year 1 Strategy

Year 1 uses **management commands + cron/systemd** for background processing:
- No Celery required
- No message broker required
- Simple, reliable, observable

### 10.3 Task Categories

| Category | Examples | Scheduling |
|----------|----------|------------|
| **PDF Generation** | Generate monthly rent receipts | After rent payment (immediate via signal) |
| **Notifications** | Send rent reminders, monthly summaries | Daily cron, event-driven |
| **Payment Retries** | Retry failed payouts | Every 15 minutes cron |
| **Monthly Jobs** | Generate monthly rent records, send tax reminders | Monthly cron |
| **Reports** | Generate owner reports | On-demand (user request) |
| **AI Processing** | Process chat messages, generate insights | Immediate (user request) |

### 10.4 Task Design Rules

- Tasks must be **idempotent**
- Tasks must be **retryable**
- Tasks must have **clear logging**
- Tasks must be **monitored**
- Tasks must NOT modify domain entities directly (use application services)

---

## 11. Caching Strategy

### 11.1 Cache Ownership

| Cache | Owner | Scope |
|-------|-------|-------|
| **User Session** | Identity | Per-user, short-lived |
| **Property List** | Property | Per-user, medium-lived |
| **Unit List** | Property | Per-user, medium-lived |
| **Dashboard Data** | Dashboard | Per-user, short-lived |
| **PDF Templates** | Documents | Global, long-lived |
| **Feature Limits** | Subscriptions | Per-user, medium-lived |
| **Tax Calculations** | Finance | Per-user, long-lived |

### 11.2 Cache Invalidation

| Strategy | Use Case |
|----------|----------|
| **TTL** | Dashboard data, reports |
| **Event-driven** | Property lists (invalidate on create/update/delete) |
| **Manual** | Feature limits (invalidate on plan change) |
| **Versioned** | PDF templates (invalidate on template update) |

### 11.3 Cache Naming

Pattern: `{module}:{scope}:{identifier}`

**Examples:**
- `property:units:user_123`
- `dashboard:summary:user_123`
- `subscription:limits:user_123`

### 11.4 TTL Guidance

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| User session | 5 minutes | Security |
| Property list | 5 minutes | Moderate change frequency |
| Dashboard data | 5 minutes | Real-time requirements |
| Feature limits | 1 hour | Infrequent changes |
| PDF templates | 24 hours | Rarely change |
| Tax calculations | 1 hour | Computationally expensive |

### 11.5 Future Redis Migration

Year 1 uses **Django LocMemCache** (in-process). When scaling to multiple workers:

1. Replace `LocMemCache` with `RedisCache`
2. No code changes required (same cache API)
3. Enable cache serialization if needed
4. Monitor cache hit rates

---

## 12. Security Architecture

### 12.1 Authentication

- **Method:** JWT (SimpleJWT)
- **Access Token Lifetime:** 5 minutes
- **Refresh Token Lifetime:** 35 days
- **Storage:** HTTP-only, Secure, SameSite cookies (web) + Secure storage (mobile)
- **Rotation:** Refresh token rotation on each use

### 12.2 Authorization

- **Primary:** Role-Based Access Control (RBAC)
- **Roles:** `owner`, `renter`, `caretaker`, `admin`
- **Secondary:** Object-level permissions (users can only access their own data)
- **Implementation:** DRF permissions + custom permission classes

### 12.3 Permissions

| Resource | Owner | Renter | Caretaker | Admin |
|----------|-------|--------|-----------|-------|
| Buildings | CRUD own | Read own | Read assigned | CRUD all |
| Units | CRUD own | Read own | Read assigned | CRUD all |
| Renters | CRUD own | Read self | Read assigned | CRUD all |
| Rent Records | Read own | Read self | Read assigned | CRUD all |
| Finance | Full | None | None | Full |

### 12.4 Webhook Security

- **Signature Verification:** HMAC-SHA256 for all webhooks
- **Secret Rotation:** Secrets rotated quarterly
- **IP Allowlisting:** Where provider supports it
- **Replay Protection:** Timestamp validation (max 5 minutes)
- **Idempotency:** Idempotency keys for all webhook handlers

### 12.5 Secret Management

- **Development:** Environment variables + `.env` file
- **Production:** AWS Secrets Manager / HashiCorp Vault
- **Rotation:** Automatic rotation for API keys
- **Access:** Least privilege, audit logging

### 12.6 Audit Logging

All sensitive operations are logged:
- User authentication (login, logout, password change)
- Permission changes
- Data access (who accessed what, when)
- Financial operations (payments, payouts)
- Configuration changes

### 12.7 Rate Limiting

| Endpoint Type | Rate Limit | Window |
|---------------|------------|--------|
| Authentication | 5 requests | 1 minute |
| API (general) | 100 requests | 1 minute |
| Webhooks | Unlimited (with signature verification) | — |
| File uploads | 10 requests | 1 minute |

### 12.8 Input Validation

- **Serializers:** DRF serializers for API input
- **Validators:** Reusable validators in `shared/validators/`
- **Sanitization:** Input sanitized before processing
- **Type coercion:** Strict type checking with mypy

### 12.9 File Upload Security

- **Validation:** File type, size, content inspection
- **Storage:** Isolated storage (S3 with restricted access)
- **Scanning:** Virus scanning for uploaded files
- **Access:** Signed URLs with expiration

---

## 13. Observability

### 13.1 Logging

- **Format:** Structured JSON logs
- **Levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Correlation:** Request ID propagated through all logs
- **Sensitive Data:** Never log secrets, tokens, or PII
- **Retention:** 30 days in application, 1 year in S3/ELK

### 13.2 Metrics

- **Framework:** Prometheus + Grafana
- **Metrics:**
  - Request latency (p50, p95, p99)
  - Request count by endpoint
  - Error rate by endpoint
  - Database query count
  - Cache hit/miss rate
  - Background job queue depth
  - External API latency

### 13.3 Tracing

- **Framework:** OpenTelemetry
- **Propagation:** Trace ID in all logs and metrics
- **Sampling:** 100% in development, 10% in production
- **Export:** Jaeger (self-hosted) or AWS X-Ray

### 13.4 Health Checks

| Check | Endpoint | Purpose |
|-------|----------|---------|
| Liveness | `/health/live` | Process is running |
| Readiness | `/health/ready` | Dependencies are available |
| Startup | `/health/startup` | Application is initialized |

**Dependencies checked:**
- Database connectivity
- Cache connectivity
- External API availability (payment gateways, notification channels)

### 13.5 Error Reporting

- **Tool:** Sentry
- **Features:**
  - Real-time error alerting
  - Stack trace collection
  - Release tracking
  - User context
- **Alerting:** On-call for P1/P2 errors

### 13.6 Audit Events

All business-critical operations emit audit events:
- User authentication
- Permission changes
- Financial transactions
- Data modifications
- Configuration changes

Audit events are stored in a dedicated `audit_log` table and exported to SIEM.

---

## 14. Scalability Strategy

### 14.1 Growth Stages

#### Stage 1: 10 Users (Current)

- **Architecture:** Modular monolith, single server
- **Database:** SQLite (dev) / PostgreSQL (production)
- **Cache:** In-memory (LocMemCache)
- **Workers:** Synchronous request handling
- **Deployment:** Single EC2 instance

#### Stage 2: 100 Users

- **Architecture:** Modular monolith, single server
- **Database:** PostgreSQL with indexes
- **Cache:** Redis (optional)
- **Workers:** Synchronous + cron jobs
- **Deployment:** EC2 + RDS

#### Stage 3: 1,000 Users

- **Architecture:** Modular monolith, multiple workers
- **Database:** PostgreSQL with read replicas
- **Cache:** Redis for session and data caching
- **Workers:** Celery + Redis broker (optional)
- **Deployment:** ECS/EKS with auto-scaling

#### Stage 4: 10,000 Users

- **Architecture:** Modular monolith, optimized
- **Database:** PostgreSQL with connection pooling, read replicas
- **Cache:** Redis cluster
- **Workers:** Celery workers for background jobs
- **Storage:** S3 for files
- **CDN:** CloudFront for static assets
- **Deployment:** ECS/EKS with auto-scaling groups

#### Stage 5: 100,000 Users

- **Architecture:** Modular monolith + read model optimizations
- **Database:** PostgreSQL with sharding (if needed), read replicas
- **Cache:** Redis cluster with cache warming
- **Workers:** Dedicated Celery workers per queue
- **Storage:** S3 + CloudFront
- **CDN:** CloudFront with edge caching
- **Deployment:** ECS/EKS with separate services for high-load modules

#### Stage 6: 1,000,000 Users

- **Architecture:** Modular monolith with optional service extraction
- **Database:** PostgreSQL sharding + read replicas + materialized views
- **Cache:** Redis cluster with local caches
- **Workers:** Distributed Celery workers
- **Storage:** S3 + Glacier for archival
- **CDN:** CloudFront with edge functions
- **Deployment:** ECS/EKS with service extraction for high-scale modules

### 14.2 Extraction Criteria

A bounded context is extracted to a microservice when **any** of the following are true:
- Monthly transaction volume exceeds 500,000 requests
- The context needs independent scaling characteristics
- Multiple teams need independent deployment cycles
- The context has different availability requirements
- The context requires a different technology stack

### 14.3 Extraction Strategy

When extracting a bounded context:
1. Define service boundaries (API, events, data)
2. Implement anti-corruption layer
3. Migrate data to separate database
4. Route traffic to new service
5. Decommission old code

---

## 15. Coding Standards

### 15.1 Import Rules

```python
# Standard library imports
import os
import sys
from typing import Any

# Third-party imports
from django.db import models
from rest_framework import viewsets

# Application imports — order: shared → domain → infrastructure → presentation
from shared.exceptions import ValidationError
from properties.domain.renter.entities.renter import Renter
from properties.infrastructure.repositories.django_renter_repository import DjangoRenterRepository
from properties.serializers import RenterSerializer
```

**Rules:**
- Group imports: standard library, third-party, application
- Order within groups: alphabetical
- No wildcard imports (`from module import *`)
- No circular imports
- Use absolute imports, not relative imports

### 15.2 Folder Rules

```
properties/
├── __init__.py
├── apps.py
├── domain/                    # Domain layer (entities, services, events)
│   ├── renter/
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   └── renter.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── renter_service.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   └── renter_repository.py
│   │   ├── events/
│   │   │   ├── __init__.py
│   │   │   └── renter_events.py
│   │   └── policies/
│   │       ├── __init__.py
│   │       └── renter_policy.py
├── application/               # Application layer (use cases, services)
│   ├── __init__.py
│   ├── services/
│   │   └── renter_application_service.py
│   └── queries/
│       └── renter_queries.py
├── infrastructure/            # Infrastructure layer (repositories, adapters)
│   ├── __init__.py
│   ├── repositories/
│   │   └── django_renter_repository.py
│   └── adapters/
│       └── external_renter_adapter.py
├── presentation/              # Presentation layer (views, serializers)
│   ├── __init__.py
│   ├── views/
│   │   └── renter_views.py
│   ├── serializers/
│   │   └── renter_serializers.py
│   └── permissions/
│       └── renter_permissions.py
├── models/                    # Django ORM models (infrastructure concern)
│   └── renter_models.py
├── migrations/
├── signals.py
├── urls.py
└── tests/
    ├── __init__.py
    ├── domain/
    ├── application/
    ├── infrastructure/
    └── presentation/
```

### 15.3 Naming Conventions

| Artifact | Convention | Example |
|----------|-----------|---------|
| Django app | snake_case | `properties`, `notifications` |
| Python module | snake_case | `renter_service.py` |
| Python class | PascalCase | `RenterService` |
| Python function | snake_case | `create_renter` |
| Python variable | snake_case | `renter_count` |
| Django model | PascalCase | `Renter` |
| Database table | snake_case plural | `renters` |
| URL pattern | kebab-case | `rent-records` |
| Event | PascalCase past tense | `RenterCreated` |
| Repository interface | PascalCase + Repository | `RenterRepository` |
| Service interface | PascalCase + Service | `PaymentService` |
| Adapter | PascalCase + Adapter | `RazorpayAdapter` |
| Port | PascalCase + Port | `PaymentGatewayPort` |

### 15.4 Service Rules

1. **Application services orchestrate, domain services decide**
2. **No business logic in views**
3. **No database access in domain layer**
4. **No framework imports in domain layer**
5. **Services are stateless**
6. **Services return result objects, not raw data**

### 15.5 Testing Rules

1. **Unit tests for domain layer** — No dependencies, fast execution
2. **Integration tests for application layer** — Test use cases with real repositories
3. **API tests for presentation layer** — Test endpoints with test client
4. **Contract tests for external adapters** — Mock external APIs
5. **Test coverage target:** ≥90% for domain and application layers

### 15.6 Review Checklist

Before submitting a PR:
- [ ] No circular imports (`import-linter` passes)
- [ ] No forbidden dependencies (`import-linter` passes)
- [ ] All tests pass (`pytest`)
- [ ] No new mypy errors (`mypy --strict`)
- [ ] No new ruff errors (`ruff check`)
- [ ] Django system checks pass (`python manage.py check`)
- [ ] No new DeprecationWarnings
- [ ] Documentation updated
- [ ] Architecture ADRs updated if needed

---

## 16. Architecture Decision Records

The following ADRs have been recorded for this architecture:

| ADR | Title | Status |
|-----|-------|--------|
| ADR-001 | Modular Monolith vs Microservices | Accepted |
| ADR-002 | Bounded Contexts by Business Capability | Accepted |
| ADR-003 | Duplicate Service Consolidation | Accepted |
| ADR-004 | Compatibility Wrappers During Migration | Accepted |
| ADR-005 | Merge `smartbot` + `ai_assistant` into `assistant` | Accepted |
| ADR-006 | Notification Channel Centralization | Accepted |
| ADR-007 | PDF Generation as Shared Documents Capability | Accepted |
| ADR-008 | Leegality in Documents Bounded Context | Accepted |
| ADR-009 | Analytics as Independent Bounded Context | Accepted |
| ADR-010 | Payment Gateways Behind Adapters | Accepted |

**Location:** `docs/refactoring/08_architecture_decisions.md`

---

## 17. Migration Principles

### 17.1 Backward Compatibility

- Never break existing API contracts without deprecation
- Maintain compatibility wrappers during migration
- Support multiple versions during transition
- Version APIs when breaking changes are unavoidable

### 17.2 Incremental Migration

- One bounded context at a time
- One logical change per PR
- Small, reviewable changes
- No Big Bang migrations

### 17.3 Zero-Downtime Philosophy

- Deploy changes before routing traffic
- Use feature flags for gradual rollout
- Monitor metrics after deployment
- Instant rollback capability

### 17.4 Data Migration Approach

- No schema changes during migration
- Additive migrations only (new columns/tables)
- Backfill data asynchronously
- Validate data consistency after migration

### 17.5 Rollback Strategy

- Every phase is a single, revertible commit
- Rollback time < 15 minutes
- Tested rollback procedures
- Data rollback scripts for schema changes

---

## 18. Final Architecture Scorecard

### 18.1 Strengths

| Strength | Description |
|----------|-------------|
| **Clear Boundaries** | Bounded contexts are well-defined with explicit dependencies |
| **Testability** | Domain layer has no framework dependencies, easily testable |
| **Maintainability** | Single responsibility per module, easy to locate code |
| **Extensibility** | New features integrate without modifying existing code |
| **Operational Simplicity** | Single deployment unit, straightforward monitoring |
| **Future-Proofing** | Can extract microservices when needed without rewrites |
| **Team Autonomy** | Clear ownership enables independent teams |

### 18.2 Trade-offs

| Trade-off | Rationale |
|-----------|-----------|
| **Initial Migration Cost** | Significant refactoring effort, but pays off long-term |
| **Learning Curve** | Team must learn DDD and clean architecture patterns |
| **Indirection** | Compatibility wrappers add temporary complexity |
| **Cross-Module Communication** | Events and interfaces add overhead vs direct calls |

### 18.3 Known Constraints

| Constraint | Impact |
|------------|--------|
| **Single Database** | Cannot scale individual contexts independently |
| **Shared Tech Stack** | All contexts use Django/Python |
| **Team Size** | Small team may struggle with multiple contexts |
| **Legacy Code** | Existing code must be gradually refactored |

### 18.4 Future Extensibility

| Extension | Approach |
|-----------|----------|
| **New Bounded Context** | Create new Django app following established patterns |
| **Microservice Extraction** | Extract context with anti-corruption layer |
| **New Notification Channel** | Implement `NotificationChannel` port |
| **New Payment Gateway** | Implement `PaymentGateway` port |
| **New AI Feature** | Add to `assistant` module following established patterns |
| **New Analytics Report** | Add read model and API endpoint |

### 18.5 Overall Architecture Confidence

**HIGH** — The architecture is:
- **Proven**: Based on established patterns (DDD, Clean Architecture, Hexagonal)
- **Flexible**: Supports growth from 10 to 1M+ users
- **Maintainable**: Clear boundaries and responsibilities
- **Testable**: Domain layer is independently testable
- **Extensible**: New features integrate cleanly
- **Future-proof**: Microservice extraction is possible without rewrites

**Confidence Level:** 9/10

**Remaining Risks:**
- Migration effort is significant (requires discipline and time)
- Team must learn new patterns (requires training)
- Boundaries may evolve (requires ongoing governance)

---

## Appendix A: Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RentSecure Backend                           │
│                     Modular Monolith Architecture                   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Identity   │  │Subscriptions│  │   Property  │  │   Finance   │
│             │  │             │  │             │  │             │
│ • Users     │  │ • Plans     │  │ • Buildings │  │ • CA        │
│ • Auth      │  │ • Add-ons   │  │ • Units     │  │ • Tax       │
│ • OTP       │  │ • Limits    │  │ • Renters   │  │ • Reports   │
│ • Profiles  │  │ • Features  │  │ • Rent      │  │             │
└──────┬──────┘  └─────────────┘  └──────┬──────┘  └─────────────┘
       │                                 │
       │         ┌─────────────┐         │
       │         │  Payments   │◄────────┘
       │         │             │
       │         │ • Razorpay  │
       │         │ • Cashfree  │
       │         │ • UPI       │
       │         └──────┬──────┘
       │                │
┌──────▼──────┐  ┌──────▼──────┐  ┌─────────────┐  ┌─────────────┐
│Documents   │  │AI Assistant │  │  Dashboard  │  │   Referral  │
│             │  │             │  │             │  │             │
│ • PDFs      │  │ • Chatbot   │  │ • Owner     │  │ • Codes     │
│ • E-Sig     │  │ • GPT       │  │   Dashboard │  │ • Bonuses   │
│ • Storage   │  │ • Actions   │  │ • Analytics │  │ • Rewards   │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     Notifications (Channels)                        │
│  • Email • Push • WhatsApp • SMS • Voice                            │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        Shared Kernel                                │
│  • Utils • Validators • Types • Constants • Exceptions • Events    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     Infrastructure                                  │
│  • Logging • Metrics • Caching • Security • Health Checks          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Appendix B: Context Map

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Identity   │────▶│ Subscriptions│────▶│    Referral  │
│              │◀────│              │◀────│              │
└──────────────┘     └──────────────┘     └──────────────┘
        │                    │                    │
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Property   │────▶│   Payments   │────▶│  Documents   │
│              │◀────│              │◀────│              │
└──────────────┘     └──────────────┘     └──────────────┘
        │                    │                    │
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Finance    │     │ Notifications│     │     AI       │
│              │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
        │                    │                    │
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────────────────────────────────────────────────┐
│                     Dashboard                             │
│  (Reads from Property, Rent, Finance, Notifications)     │
└──────────────────────────────────────────────────────────┘
```

**Relationship types:**
- `───▶` : Uses (depends on)
- `◀──` : Publishes events to
- `───` : Shared kernel (no direct dependency)

---

## Appendix C: Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Framework** | Django 5.2 | Mature, secure, excellent ORM |
| **API** | Django REST Framework | Standard for Django APIs |
| **Auth** | SimpleJWT | JWT authentication, refresh tokens |
| **Database** | PostgreSQL | ACID, JSON support, full-text search |
| **Cache** | Redis (future) | High-performance caching |
| **Storage** | AWS S3 | Scalable file storage |
| **Queue** | Celery + Redis (Stage 2) | Background job processing |
| **Search** | PostgreSQL trigram | Full-text search (Year 1) |
| **Monitoring** | Prometheus + Grafana | Metrics and dashboards |
| **Logging** | ELK / CloudWatch | Centralized logging |
| **Tracing** | OpenTelemetry | Distributed tracing |
| **Error Tracking** | Sentry | Real-time error alerting |
| **CI/CD** | GitHub Actions | Integrated with GitHub |
| **Code Quality** | Ruff, Mypy, Pylint | Static analysis |
| **Testing** | Pytest | Testing framework |

---

*Document generated by Kilo Target Architecture Design. This is a design document only. No production code was modified.*
