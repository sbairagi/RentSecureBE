# RentSecure Backend — Target Architecture

**Document:** Target Architecture
**Version:** 1.0.0
**Date:** 2026-07-15
**Owner:** Principal Software Architect
**Status:** Ratified
**Scope:** Complete backend architecture after all planned refactoring
**Constraint:** This document is the permanent destination architecture. All refactoring efforts aim to reach this state. No implementation document supersedes this document.

---

## Table of Contents

1. [Overall Architecture](#1-overall-architecture)
2. [Bounded Contexts](#2-bounded-contexts)
3. [Folder Structure](#3-folder-structure)
4. [Layer Architecture](#4-layer-architecture)
5. [Dependency Diagram](#5-dependency-diagram)
6. [Request Lifecycle](#6-request-lifecycle)
7. [Cross Context Communication](#7-cross-context-communication)
8. [Shared Module](#8-shared-module)
9. [External Integrations](#9-external-integrations)
10. [Caching Architecture](#10-caching-architecture)
11. [Background Processing](#11-background-processing)
12. [Error Architecture](#12-error-architecture)
13. [Security Architecture](#13-security-architecture)
14. [Performance Architecture](#14-performance-architecture)
15. [Scalability Vision](#15-scalability-vision)
16. [Testing Architecture](#16-testing-architecture)
17. [Coding Standards](#17-coding-standards)
18. [Architecture Rules](#18-architecture-rules)
19. [Example Flows](#19-example-flows)
20. [Architecture Decision Summary](#20-architecture-decision-summary)

---

## 1. Overall Architecture

### 1.1 Architectural Style

RentSecure is a **Modular Monolith** built on Django and Django REST Framework (DRF). It is a single deployable unit—single process, single database, single code repository—but internally organized into strictly bounded contexts with explicit public interfaces, enforced dependency rules, and zero circular imports.

### 1.2 Why Modular Monolith

The team selected a modular monolith for the following reasons:

| Factor | Monolith | Microservices |
|--------|----------|---------------|
| Operational overhead | Low: one process, one DB, one deploy | High: service discovery, network, distributed tracing |
| Data consistency | Strong ACID across all contexts | Eventual consistency, sagas required |
| Development velocity | High: no network latency, single debug session | Lower: cross-service debugging, contract management |
| Cost | Low: no message broker, no service mesh | High: infrastructure, observability, networking |
| Team size fit | Optimal for < 20 engineers | Optimal for > 20 engineers with clear team boundaries |
| Extraction readiness | Boundaries designed for future extraction | Already extracted, expensive to consolidate |
| Monitoring | Simple: single logs, single metrics | Complex: distributed tracing, per-service dashboards |

**Decision:** Remain a modular monolith through Year 1 production. Extract only when business scale justifies it.

### 1.3 Future Microservice Readiness

The modular monolith is not a dead end. Every bounded context is designed with a clean public interface, explicit dependency direction, and no cross-context ORM writes. When the time comes to extract:

1. The bounded context's `api.py` or `services/` package becomes the service boundary.
2. The public interface is deployed as REST or gRPC.
3. Data ownership is transferred to the new service.
4. Callers are updated to use the network interface.
5. The old in-process code is deleted.

This extraction is possible because:
- No bounded context reaches into another's internals.
- No circular dependencies exist.
- All cross-context communication goes through explicit interfaces.
- Business logic is isolated in services, not scattered in views.

### 1.4 Internal Boundaries

Internal boundaries are enforced by three mechanisms:

1. **Directory structure:** Each bounded context lives in its own Django app directory.
2. **Import-linter:** CI fails if a bounded context imports a private module from another bounded context.
3. **Code review:** Reviewers enforce public interface rules and dependency direction.

These boundaries are not merely organizational. They are architectural contracts that govern every change to the codebase.

---

## 2. Bounded Contexts

A bounded context is a Django app that owns a single business capability. It has a well-defined responsibility, explicit dependencies, a public interface, and a single owner.

### 2.1 core — Identity and Access Management

**Purpose:** Owns all identity, authentication, authorization, and platform-level configuration.

**Responsibilities:**
- User registration, login, logout, password reset
- JWT token issuance and validation
- Role-based access control (RBAC)
- Platform-level feature flags
- Audit logging for authentication events
- Subscription tier enforcement

**What belongs inside:**
- `User`, `Role`, `Permission`, `Subscription`, `AuditLog` models
- Authentication views and serializers
- Permission classes
- JWT utilities
- Password hashing and validation

**What never belongs inside:**
- Property management logic
- Payment processing
- Notification delivery
- PDF generation
- AI features

**Owner:** Platform team

**Dependencies:** `shared` only.

**Public API:**
- `core.services.auth_service.AuthenticationService`
- `core.services.permission_service.PermissionService`
- `core.services.subscription_service.SubscriptionService`
- `core.api` (token endpoints, user endpoints)

**Internal structure:**
```
core/
  api/
    v1/
      auth.py
      users.py
      subscriptions.py
  models/
    user.py
    role.py
    permission.py
    subscription.py
    audit_log.py
  services/
    auth_service.py
    permission_service.py
    subscription_service.py
  serializers/
    user_serializer.py
    subscription_serializer.py
  permissions/
    is_authenticated.py
    has_role.py
    has_subscription.py
  validators/
    password_validator.py
  exceptions/
    authentication_error.py
    authorization_error.py
  constants/
    roles.py
    subscription_tiers.py
  interfaces/
    auth_provider.py
  dto/
    login_request.py
    login_response.py
  tests/
    unit/
    integration/
```

**Expected future growth:** Core remains relatively stable. Growth is in subscription tiers and new authentication methods (OAuth, SSO).

**Example request flow:**
1. Client POSTs credentials to `/api/v1/auth/login/`.
2. View calls `AuthenticationService.authenticate()`.
3. Service validates credentials, issues JWT.
4. Response returns tokens and user data.

---

### 2.2 accounts — Account and Billing Management

**Purpose:** Owns owner and tenant account management, billing details, and subscription administration.

**Responsibilities:**
- Owner profile management
- Tenant profile management
- Billing contact information
- Subscription management (upgrade, downgrade, cancel)
- Invoice generation triggers
- Payment method management (UPI ID, QR code upload, bank details)
- Account verification workflows

**What belongs inside:**
- `OwnerProfile`, `TenantProfile`, `BillingDetails`, `PaymentMethod` models
- Account settings views and serializers
- Profile update workflows
- Subscription change orchestration

**What never belongs inside:**
- Property CRUD
- Rent calculation
- Document generation
- Notification delivery

**Owner:** Accounts team

**Dependencies:** `core`, `properties`, `notification`, `finance`.

**Public API:**
- `accounts.services.owner_service.OwnerService`
- `accounts.services.tenant_service.TenantService`
- `accounts.services.billing_service.BillingService`
- `accounts.api`

**Internal structure:**
```
accounts/
  api/
    v1/
      owners.py
      tenants.py
      billing.py
  models/
    owner_profile.py
    tenant_profile.py
    billing_details.py
    payment_method.py
  services/
    owner_service.py
    tenant_service.py
    billing_service.py
  serializers/
    owner_serializer.py
    tenant_serializer.py
    billing_serializer.py
  permissions/
    is_owner.py
    is_tenant.py
  exceptions/
    account_error.py
  tests/
    unit/
    integration/
```

**Expected future growth:** Multi-tenant support, family accounts, corporate accounts.

---

### 2.3 properties — Property Management

**Purpose:** Owns the complete property lifecycle: buildings, units, leases, tenants, maintenance, and usage limits.

**Responsibilities:**
- Building and unit CRUD
- Lease agreement management
- Tenant onboarding and offboarding
- Maintenance request tracking
- Property usage limits and quotas
- Owner-tenant relationships
- Property-level notifications orchestration
- Rent record creation and status tracking (but not payment processing)

**What belongs inside:**
- `Building`, `Unit`, `Lease`, `MaintenanceRequest`, `UsageLimit` models
- Property and unit views
- Lease workflow services
- Tenant onboarding/offboarding services
- Maintenance request services
- Property notification orchestration (calls into `notification` bounded context)
- Rent record creation and status management

**What never belongs inside:**
- PDF generation (belongs in `documents`)
- Payment gateway integration (belongs in `payments`)
- Financial calculations and tax (belongs in `finance`)
- Channel implementations (belongs in `notification`)
- AI chatbot logic (belongs in `assistant`)

**Owner:** Properties team

**Dependencies:** `core`, `accounts`, `finance`, `notification`, `documents`, `assistant`.

**Public API:**
- `properties.services.building_service.BuildingService`
- `properties.services.unit_service.UnitService`
- `properties.services.lease_service.LeaseService`
- `properties.services.tenant_service.PropertyTenantService`
- `properties.services.maintenance_service.MaintenanceService`
- `properties.services.notification_service.PropertyNotificationService`
- `properties.api`

**Internal structure:**
```
properties/
  api/
    v1/
      buildings.py
      units.py
      leases.py
      tenants.py
      maintenance.py
      usage_limits.py
  models/
    building.py
    unit.py
    lease.py
    maintenance_request.py
    usage_limit.py
    rent_record.py
  services/
    building_service.py
    unit_service.py
    lease_service.py
    tenant_service.py
    maintenance_service.py
    notification_service.py
    usage_limit_service.py
  repositories/
    building_repository.py
    unit_repository.py
    lease_repository.py
  selectors/
    building_selectors.py
    unit_selectors.py
    lease_selectors.py
  validators/
    lease_validator.py
    unit_validator.py
  serializers/
    building_serializer.py
    unit_serializer.py
    lease_serializer.py
  permissions/
    is_property_owner.py
    is_tenant.py
  signals/
    lease_created.py
    tenant_onboarded.py
  exceptions/
    property_error.py
  constants/
    lease_statuses.py
    maintenance_statuses.py
  interfaces/
    notification_channel.py
  dto/
    create_building_request.py
    create_lease_request.py
  tests/
    unit/
    integration/
```

**Expected future growth:** Smart building integrations, IoT device management, advanced maintenance workflows.

**Example request flow:**
1. Owner creates a building via `/api/v1/buildings/`.
2. View validates permission, calls `BuildingService.create_building()`.
3. Service validates input, creates `Building` and `Unit` records via repository.
4. Service triggers `post_save` signal.
5. Signal enqueues notification to owner via `notification` bounded context.

---

### 2.4 finance — Tax, Compliance, and Financial Records

**Purpose:** Owns financial record keeping, tax calculations, compliance reporting, and rent record financial status.

**Responsibilities:**
- Rent record financial status tracking
- Late fee calculation and application
- Tax computation (TDS, GST where applicable)
- Financial compliance reporting
- Invoice generation requests (delegates PDF generation to `documents`)
- Reconciliation exports
- Financial dashboard data aggregation

**What belongs inside:**
- `RentRecord`, `LateFee`, `TaxRecord`, `Invoice`, `ReconciliationExport` models
- Financial calculation services
- Tax computation services
- Compliance report generators
- Financial data aggregators

**What never belongs inside:**
- Payment gateway integration (belongs in `payments`)
- PDF generation (belongs in `documents`)
- Property CRUD (belongs in `properties`)
- Notification delivery (belongs in `notification`)

**Owner:** Finance team

**Dependencies:** `core`, `properties`, `documents`, `analytics`.

**Public API:**
- `finance.services.rent_service.RentFinancialService`
- `finance.services.tax_service.TaxService`
- `finance.services.compliance_service.ComplianceService`
- `finance.api`

**Internal structure:**
```
finance/
  api/
    v1/
      rent_records.py
      taxes.py
      compliance.py
      invoices.py
  models/
    rent_record.py
    late_fee.py
    tax_record.py
    invoice.py
    reconciliation_export.py
  services/
    rent_service.py
    tax_service.py
    compliance_service.py
    invoice_service.py
  repositories/
    rent_repository.py
    tax_repository.py
  selectors/
    rent_selectors.py
    tax_selectors.py
  validators/
    tax_validator.py
  serializers/
    rent_serializer.py
    tax_serializer.py
  permissions/
    is_finance_admin.py
  signals/
    rent_paid.py
  exceptions/
    finance_error.py
  constants/
    tax_rates.py
    late_fee_rules.py
  interfaces/
    document_generator.py
    payment_gateway.py
  dto/
    calculate_tax_request.py
  tests/
    unit/
    integration/
```

**Expected future growth:** Advanced tax modules, multi-currency support, automated reconciliation.

---

### 2.5 documents — Document Generation and E-Signature

**Purpose:** Owns all document generation, template management, and e-signature workflows.

**Responsibilities:**
- PDF generation from HTML templates
- Agreement PDF creation
- Invoice PDF generation
- Rent receipt PDF generation
- E-signature workflow orchestration via Leegality
- Document download and archival
- Template management and versioning
- Document metadata tracking

**What belongs inside:**
- `Document`, `DocumentTemplate`, `SignatureRequest`, `SignatureField` models
- PDF generation utilities (unified WeasyPrint wrapper)
- Leegality API client
- Agreement service (PDF + send for signature)
- Invoice and receipt document services
- Template rendering engine

**What never belongs inside:**
- Property CRUD
- Payment processing
- Notification channel implementations
- AI logic

**Owner:** Documents team

**Dependencies:** `core`, `properties`, `finance`, `shared`.

**Public API:**
- `documents.services.pdf_generator.PDFGenerator`
- `documents.services.agreement_service.AgreementService`
- `documents.services.invoice_service.InvoiceDocumentService`
- `documents.services.leegality.LeegalityClient`
- `documents.services.template_service.TemplateService`
- `documents.api`

**Internal structure:**
```
documents/
  api/
    v1/
      documents.py
      templates.py
      signatures.py
  models/
    document.py
    document_template.py
    signature_request.py
    signature_field.py
  services/
    pdf_generator.py
    agreement_service.py
    invoice_service.py
    receipt_service.py
    leegality.py
    template_service.py
  repositories/
    document_repository.py
  selectors/
    document_selectors.py
  validators/
    template_validator.py
  serializers/
    document_serializer.py
    template_serializer.py
  permissions/
    can_access_document.py
  signals/
    document_generated.py
    signature_completed.py
  exceptions/
    document_error.py
    pdf_generation_error.py
  constants/
    document_types.py
    template_names.py
  interfaces/
    e_signature_provider.py
  dto/
    generate_pdf_request.py
    create_signature_request.py
  tests/
    unit/
    integration/
```

**Expected future growth:** Multi-language templates, document versioning, bulk document generation.

---

### 2.6 notification — Notification Channels

**Purpose:** Owns all notification channel implementations and channel-level orchestration.

**Responsibilities:**
- Email delivery via Django SMTP / AWS SES
- Push notification delivery via Firebase Cloud Messaging (FCM)
- In-app notification creation and retrieval
- WhatsApp Business API integration (disabled, Stage 2)
- SMS integration (disabled, Stage 2)
- Channel-level retry logic
- Template management per channel
- Delivery status tracking

**What belongs inside:**
- `Notification`, `NotificationChannel`, `NotificationTemplate`, `DeliveryAttempt` models
- Channel adapter implementations: `EmailAdapter`, `FCMAdapter`, `InAppAdapter`, `WhatsAppAdapter`, `SMSAdapter`
- Channel selection and fallback logic
- Template rendering per channel
- Delivery status tracking

**What never belongs inside:**
- Business notification orchestration (belongs in domain apps like `properties`, `finance`)
- Property CRUD
- Payment processing
- PDF generation

**Owner:** Notification team

**Dependencies:** `core`, `shared`. (Domain apps call into `notification`, not the reverse.)

**Public API:**
- `notification.services.communication.send_smart_alert(user, message, context)`
- `notification.services.communication.notify_owner_renter_flagged(property, message)`
- `notification.services.channels.EmailChannel`
- `notification.services.channels.FCMChannel`
- `notification.services.channels.InAppChannel`
- `notification.api.notifications` (in-app notification list)

**Internal structure:**
```
notification/
  api/
    v1/
      notifications.py
      preferences.py
  models/
    notification.py
    notification_channel.py
    notification_template.py
    delivery_attempt.py
    notification_preference.py
  services/
    communication.py
    channels/
      __init__.py
      base.py
      email.py
      fcm.py
      inapp.py
      whatsapp.py
      sms.py
    orchestrator.py
  serializers/
    notification_serializer.py
    preference_serializer.py
  permissions/
    is_notification_owner.py
  signals/
    notification_created.py
  exceptions/
    notification_error.py
  constants/
    channels.py
    template_types.py
  interfaces/
    notification_channel.py
  dto/
    send_notification_request.py
  tests/
    unit/
    integration/
```

**Expected future growth:** Rich notifications, notification scheduling, A/B testing for templates.

---

### 2.7 assistant — AI Assistant and Automation

**Purpose:** Owns all AI and automation features: chatbot, intent extraction, AI-generated responses, and smart automation.

**Responsibilities:**
- Chatbot API and conversation management
- Intent extraction from user messages
- AI-powered response generation via OpenAI
- Smart alert generation
- Document summarization
- Predictive analytics (e.g., late payment prediction)
- AI action execution (e.g., draft agreement generation)

**What belongs inside:**
- `ChatSession`, `ChatMessage`, `AIAction`, `AISuggestion` models
- Chatbot service
- GPT service (OpenAI wrapper)
- Intent extraction service
- Action execution service
- Smart alert generator

**What never belongs inside:**
- Leegality e-signature integration (belongs in `documents`)
- PDF generation (belongs in `documents`)
- WhatsApp/SMS channel implementations (belongs in `notification`)
- Archive/invoice/unit services that are not AI-related (belongs in `properties`/`documents`)

**Owner:** AI/Assistant team

**Dependencies:** `core`, `properties`, `documents`, `notification`, `shared`.

**Public API:**
- `assistant.services.chatbot_service.ChatbotService`
- `assistant.services.gpt_service.GPTService`
- `assistant.services.intent_service.IntentService`
- `assistant.services.action_service.ActionService`
- `assistant.api.chat` (chat endpoint)

**Internal structure:**
```
assistant/
  api/
    v1/
      chat.py
      actions.py
      suggestions.py
  models/
    chat_session.py
    chat_message.py
    ai_action.py
    ai_suggestion.py
  services/
    chatbot_service.py
    gpt_service.py
    intent_service.py
    action_service.py
    alert_generator.py
  repositories/
    chat_repository.py
  selectors/
    chat_selectors.py
  validators/
    intent_validator.py
  serializers/
    chat_serializer.py
    action_serializer.py
  permissions/
    can_use_assistant.py
  signals/
    ai_action_triggered.py
  exceptions/
    assistant_error.py
  constants/
    intents.py
    actions.py
  interfaces/
    llm_provider.py
    action_executor.py
  dto/
    chat_request.py
    execute_action_request.py
  tests/
    unit/
    integration/
```

**Expected future growth:** Voice assistant, image-based property analysis, advanced document Q&A.

---

### 2.8 analytics — Analytics and Reporting

**Purpose:** Owns all analytics computation, dashboard data aggregation, and business reporting.

**Responsibilities:**
- Dashboard summary computation
- Owner analytics (rent inflow, occupancy rates)
- Building analytics (maintenance trends, tenant turnover)
- Financial analytics (revenue, tax liability)
- Usage analytics (feature adoption, notification engagement)
- Report generation and export
- Analytics query optimization and caching

**What belongs inside:**
- `Dashboard`, `AnalyticsReport`, `MetricSnapshot` models
- Analytics computation services
- Aggregation pipelines
- Report generators
- Cache warming logic

**What never belongs inside:**
- Raw property CRUD
- PDF generation
- Notification delivery
- Payment processing

**Owner:** Analytics team

**Dependencies:** `core`, `properties`, `finance`, `notification`, `shared`.

**Public API:**
- `analytics.services.dashboard_service.DashboardService`
- `analytics.services.report_service.ReportService`
- `analytics.services.metric_service.MetricService`
- `analytics.api`

**Internal structure:**
```
analytics/
  api/
    v1/
      dashboards.py
      reports.py
      metrics.py
  models/
    dashboard.py
    analytics_report.py
    metric_snapshot.py
  services/
    dashboard_service.py
    report_service.py
    metric_service.py
    aggregation_service.py
  repositories/
    analytics_repository.py
  selectors/
    dashboard_selectors.py
  validators/
    report_validator.py
  serializers/
    dashboard_serializer.py
    report_serializer.py
  permissions/
    can_view_analytics.py
  signals/
    metrics_updated.py
  exceptions/
    analytics_error.py
  constants/
    metric_types.py
    report_types.py
  interfaces/
    data_source.py
  dto/
    dashboard_summary_request.py
  tests/
    unit/
    integration/
```

**Expected future growth:** Real-time analytics, predictive analytics, custom report builder, data export to BI tools.

---

### 2.9 integrations — External Integrations and Adapters

**Purpose:** Owns all third-party service integrations, adapter implementations, and integration-level orchestration.

**Responsibilities:**
- Payment gateway adapters (Razorpay, Cashfree)
- E-signature provider abstraction (Leegality)
- SMS provider abstraction (Twilio, MSG91)
- WhatsApp Business API client
- Email provider abstraction (SES, SMTP)
- Cloud storage abstraction (S3)
- AI provider abstraction (OpenAI)
- Webhook receivers and verifiers
- Integration health monitoring
- Retry and fallback logic

**What belongs inside:**
- Adapter implementations for all external services
- Webhook handlers
- Integration health checks
- Retry decorators and policies
- Fallback logic

**What never belongs inside:**
- Business workflows (belongs in domain bounded contexts)
- Domain models
- User-facing views
- Notification business logic (belongs in `notification`)

**Owner:** Integrations team

**Dependencies:** `core`, `shared`. (Other bounded contexts depend on `integrations`, not the reverse.)

**Public API:**
- `integrations.adapters.payment.razorpay.RazorpayAdapter`
- `integrations.adapters.payment.cashfree.CashfreeAdapter`
- `integrations.adapters.document.leegality.LeegalityAdapter`
- `integrations.adapters.notification.twilio.TwilioSMSAdapter`
- `integrations.adapters.storage.s3.S3Adapter`
- `integrations.services.webhook_service.WebhookService`

**Internal structure:**
```
integrations/
  adapters/
    __init__.py
    base.py
    payment/
      __init__.py
      razorpay.py
      cashfree.py
      manual.py
    document/
      __init__.py
      leegality.py
    notification/
      __init__.py
      twilio.py
      whatsapp_business.py
      ses.py
      fcm.py
    storage/
      __init__.py
      s3.py
      local.py
    ai/
      __init__.py
      openai.py
  services/
    webhook_service.py
    health_check_service.py
    retry_service.py
    fallback_service.py
  webhooks/
    razorpay_webhook.py
    cashfree_webhook.py
    leegality_webhook.py
  validators/
    webhook_validator.py
  exceptions/
    integration_error.py
    payment_gateway_error.py
    webhook_verification_error.py
  constants/
    gateway_statuses.py
  interfaces/
    payment_gateway.py
    e_signature_provider.py
    sms_provider.py
    storage_provider.py
    llm_provider.py
  tests/
    unit/
    integration/
```

**Expected future growth:** New payment gateways, new notification channels, new storage providers.

---

### 2.10 shared — Shared Utilities and Abstractions

**Purpose:** Owns cross-cutting concerns, base classes, utilities, and abstractions that are used by multiple bounded contexts. Contains NO business logic.

**Responsibilities:**
- Base exception classes
- Common types and type aliases
- Enums shared across bounded contexts
- Pure utility functions (date formatting, string manipulation, currency conversion)
- Abstract base classes and protocols
- Common validators (email, phone, GSTIN)
- Pagination utilities
- Response formatting utilities
- Constants shared across contexts

**What belongs inside:**
- `RentSecureException` and subclasses
- `Result[T]` type alias
- Common enums (`UserRole`, `PaymentStatus`, `DocumentStatus`)
- Pure functions: `format_currency()`, `parse_date()`, `generate_reference()`
- Protocols: `PaymentGateway`, `NotificationChannel`, `DocumentGenerator`
- Common Django validators
- Pagination helpers

**What never belongs inside:**
- Business workflows
- Domain models
- Views
- Services that contain business logic
- Any code that imports from a bounded context

**Owner:** Platform team (shared ownership, no single team owns all of it)

**Dependencies:** None. `shared` is a leaf module.

**Public API:**
- `shared.exceptions.RentSecureException` and subclasses
- `shared.types.Result`
- `shared.utils.formatting.format_currency`
- `shared.protocols.payment_gateway.PaymentGateway`
- `shared.protocols.notification_channel.NotificationChannel`

**Internal structure:**
```
shared/
  exceptions/
    __init__.py
    base.py
    validation.py
    payment.py
    document.py
    notification.py
    integration.py
  types/
    __init__.py
    result.py
    pagination.py
  enums/
    __init__.py
    user_roles.py
    payment_status.py
    document_status.py
    notification_channel.py
  utils/
    __init__.py
    formatting.py
    dates.py
    strings.py
    currency.py
    references.py
  protocols/
    __init__.py
    payment_gateway.py
    notification_channel.py
    document_generator.py
    e_signature_provider.py
    storage_provider.py
    llm_provider.py
  validators/
    __init__.py
    indian_phone.py
    gstin.py
    upi_id.py
  constants/
    __init__.py
    http_status.py
    default_pagination.py
  dto/
    __init__.py
    paginated_response.py
  tests/
    unit/
```

**Expected future growth:** Additional protocols as new integrations are added, additional validators for new business requirements.

---

### 2.11 Additional Proposed Bounded Contexts

#### 2.11.1 referral_and_earn — Referral and Rewards

**Purpose:** Owns the referral program, reward tracking, and earnings distribution.

**Rationale:** Currently in `referral_and_earn/`. It is a distinct business capability (growth and viral marketing) that does not naturally fit into any existing bounded context. It should remain separate until its complexity justifies merging or it becomes a candidate for extraction.

**Dependencies:** `core`, `accounts`, `notification`.

---

#### 2.11.2 payments — Payment Processing (Future)

**Purpose:** Owns payment workflow orchestration, payment record management, and payout processing.

**Rationale:** Currently payment code is in `rentsecure_be/services/` and `properties/`. The ADR specifies that payment gateways go behind adapters in `payments/`. This bounded context is not yet created but is part of the target architecture. It depends on `integrations` for gateway adapters and `finance` for payment record updates.

**Dependencies:** `core`, `accounts`, `properties`, `finance`, `integrations`.

**Note:** In Year 1, manual UPI payments are processed through `finance` and `properties`. The `payments` bounded context becomes active in Stage 2 when payment gateways are enabled.

---

## 3. Folder Structure

### 3.1 Top-Level Directory Layout

```
rentsecure_be/
  config/
    settings/
      __init__.py
      base.py
      development.py
      production.py
      test.py
    urls.py
    wsgi.py
    asgi.py
    celery.py
  manage.py
  requirements/
    base.txt
    development.txt
    production.txt
    test.txt
  scripts/
    migrate.sh
    backup.sh
    restore.sh
    deploy.sh
    healthcheck.sh
  docs/
    refactoring/
      00_architecture_principles.md
      01_target_architecture.md
      adr/
    api/
  tests/
    conftest.py
    factories/
      __init__.py
      user_factory.py
      property_factory.py
      finance_factory.py
    integration/
      __init__.py
      test_property_creation.py
      test_payment_flow.py
    architecture/
      __init__.py
      test_import_rules.py
      test_dependency_rules.py
      test_no_business_logic_in_views.py
  core/
  accounts/
  properties/
  finance/
  documents/
  notification/
  assistant/
  analytics/
  integrations/
  shared/
```

### 3.2 Bounded Context Internal Structure

Every bounded context follows the same internal structure. This consistency ensures that any developer can navigate any context without learning a new layout.

```
<bounded_context>/
  __init__.py
  apps.py
  api/
    __init__.py
    v1/
      __init__.py
      <resource>.py
  models/
    __init__.py
    <entity>.py
  services/
    __init__.py
    <service>.py
  repositories/
    __init__.py
    <repository>.py
  selectors/
    __init__.py
    <selector>.py
  validators/
    __init__.py
    <validator>.py
  serializers/
    __init__.py
    <serializer>.py
  permissions/
    __init__.py
    <permission>.py
  tasks/
    __init__.py
    <task>.py
  signals/
    __init__.py
    handlers.py
  exceptions/
    __init__.py
    <domain>_error.py
  constants/
    __init__.py
    <domain>_constants.py
  interfaces/
    __init__.py
    <protocol>.py
  dto/
    __init__.py
    <request>.py
    <response>.py
  tests/
    __init__.py
    unit/
      __init__.py
      test_<service>.py
    integration/
      __init__.py
      test_<workflow>.py
```

### 3.3 Folder Purpose Reference

| Folder | Purpose | Contains | Owner |
|--------|---------|----------|-------|
| `api/` | HTTP endpoint definitions | DRF ViewSets, APIViews, URL configurations | Backend developer |
| `models/` | Django ORM models | Model definitions, model methods, `Meta` classes | Backend developer |
| `services/` | Business logic | Service classes, workflow orchestration, pure business logic | Backend developer |
| `repositories/` | Data access abstraction | QuerySet wrappers, complex queries, `select_related`/`prefetch_related` | Backend developer |
| `selectors/` | Read model projections | Optimized read queries, aggregated data, read-optimized DTOs | Backend developer |
| `validators/` | Input validation | Django validators, custom validation logic, DRF validators | Backend developer |
| `serializers/` | Serialization | DRF serializers, validation, representation logic | Backend developer |
| `permissions/` | Authorization | DRF permission classes, custom permission logic | Backend developer |
| `tasks/` | Background jobs | Django management command wrappers, async task definitions | Backend developer |
| `signals/` | Event triggers | `post_save`, `pre_save` signal handlers (thin, event-only) | Backend developer |
| `exceptions/` | Domain exceptions | Exception classes, error codes | Backend developer |
| `constants/` | Domain constants | Enums, status choices, configuration constants | Backend developer |
| `interfaces/` | Abstract interfaces | Protocols, ABCs, interface definitions | Architect / Senior developer |
| `dto/` | Data transfer objects | Request/response DTOs, typed data containers | Backend developer |
| `tests/` | Test suite | Unit, integration, architecture tests | QA / Backend developer |

### 3.4 Special Directories

**`config/`** — Django settings and configuration:
- `config/settings/base.py` — Shared settings across all environments.
- `config/settings/development.py` — Development overrides.
- `config/settings/production.py` — Production overrides.
- `config/urls.py` — Root URL configuration.
- `config/celery.py` — Celery app definition (Stage 2).

**`tests/`** — Top-level test infrastructure:
- `tests/conftest.py` — Shared pytest fixtures.
- `tests/factories/` — Factory Boy factories for all models.
- `tests/integration/` — Cross-context integration tests.
- `tests/architecture/` — Architecture enforcement tests.
- `tests/performance/` — Performance and load tests.

**`scripts/`** — Operational scripts:
- Deployment scripts, database migration scripts, backup/restore scripts, health check scripts.

---

## 4. Layer Architecture

### 4.1 Views (HTTP Layer)

**Purpose:** Adapt HTTP requests to service calls and service responses to HTTP responses.

**Responsibilities:**
- Parse HTTP request (query params, body, headers).
- Authenticate the request.
- Authorize the request.
- Validate request data using serializers.
- Call the appropriate service method.
- Return an HTTP response.
- Handle exceptions and return appropriate status codes.

**What is allowed:**
- Import services.
- Import serializers for validation.
- Import permissions for authorization.
- Call service methods.
- Return DRF `Response` objects.

**What is forbidden:**
- Import models directly for queries.
- Import repositories.
- Import ORM for writes.
- Import other bounded contexts directly.
- Contain business logic.
- Contain validation logic beyond serializer validation.
- Contain data transformation logic.
- Call external APIs.

**Example:**
```python
# properties/api/v1/buildings.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from properties.services.building_service import BuildingService
from properties.serializers import BuildingSerializer
from properties.permissions import IsPropertyOwner

class BuildingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsPropertyOwner]
    serializer_class = BuildingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        building = BuildingService.create_building(
            owner=request.user,
            **serializer.validated_data,
        )
        return Response(
            BuildingSerializer(building).data,
            status=status.HTTP_201_CREATED,
        )
```

---

### 4.2 Services (Business Logic Layer)

**Purpose:** Implement all business rules, workflows, and orchestration logic.

**Responsibilities:**
- Implement business rules and invariants.
- Orchestrate multi-step workflows.
- Coordinate between repositories, external adapters, and other services.
- Enforce business constraints.
- Handle business-level transactions.
- Raise business exceptions for invalid states.

**What is allowed:**
- Import repositories.
- Import other services within the same bounded context.
- Import models.
- Import interfaces and protocols.
- Import exceptions.
- Call external adapters (through interfaces).
- Import utilities.

**What is forbidden:**
- Import views.
- Import HTTP request/response objects.
- Import Django settings directly.
- Contain SQL queries (use repositories).
- Call external APIs directly (use adapters).
- Import private modules from other bounded contexts.

**Example:**
```python
# properties/services/building_service.py
from properties.repositories.building_repository import BuildingRepository
from properties.exceptions import PropertyError
from shared.exceptions import ValidationError

class BuildingService:
    def __init__(self, repository: BuildingRepository):
        self.repository = repository

    def create_building(self, owner, name, address, **kwargs):
        if BuildingRepository.exists_for_owner(owner, name):
            raise ValidationError("Building name already exists for this owner.")
        return self.repository.create(
            owner=owner,
            name=name,
            address=address,
            **kwargs,
        )
```

---

### 4.3 Repositories (Data Access Layer)

**Purpose:** Encapsulate all database access logic.

**Responsibilities:**
- Execute CRUD operations.
- Construct complex querysets with `select_related` and `prefetch_related`.
- Apply business-level filters.
- Return model instances or querysets.
- Isolate ORM usage from the rest of the codebase.

**What is allowed:**
- Import models.
- Use Django ORM.
- Use raw SQL only when ORM is insufficient (rare, documented).
- Return querysets or model instances.

**What is forbidden:**
- Contain business logic.
- Call external APIs.
- Import services.
- Import views.
- Perform data transformation (return raw model instances; transformation happens in selectors or services).

**Example:**
```python
# properties/repositories/building_repository.py
from properties.models import Building

class BuildingRepository:
    @staticmethod
    def create(owner, name, address, **kwargs):
        return Building.objects.create(
            owner=owner,
            name=name,
            address=address,
            **kwargs,
        )

    @staticmethod
    def get_for_owner(owner_id):
        return Building.objects.filter(owner_id=owner_id)

    @staticmethod
    def exists_for_owner(owner, name):
        return Building.objects.filter(owner=owner, name=name).exists()
```

---

### 4.4 Selectors (Read Model Projections)

**Purpose:** Provide optimized, read-only queries that may join across models or compute aggregations.

**Responsibilities:**
- Execute optimized read queries.
- Apply pagination.
- Compute aggregations (sum, count, average).
- Return DTOs or dictionaries for read operations.
- Use `only()`, `defer()`, `select_related()`, `prefetch_related()` aggressively.

**What is allowed:**
- Import models.
- Use Django ORM.
- Use `.annotate()`, `.aggregate()`.
- Return DTOs, dictionaries, or model instances.

**What is forbidden:**
- Modify data.
- Call external APIs.
- Contain business logic beyond query optimization.
- Import services.

**Example:**
```python
# analytics/selectors/dashboard_selectors.py
from django.db.models import Count, Sum
from properties.models import Building, Unit
from analytics.dto import DashboardSummaryDTO

class DashboardSelectors:
    @staticmethod
    def get_owner_dashboard_summary(owner_id):
        buildings = Building.objects.filter(owner_id=owner_id)
        units = Unit.objects.filter(building__owner_id=owner_id)

        return DashboardSummaryDTO(
            total_buildings=buildings.count(),
            total_units=units.count(),
            occupied_units=units.filter(status="occupied").count(),
            vacant_units=units.filter(status="vacant").count(),
            occupancy_rate=...,
        )
```

---

### 4.5 ORM (Django Models)

**Purpose:** Define the data schema, field constraints, and model-level behavior.

**Responsibilities:**
- Define database schema via `models.Model` subclasses.
- Define field types, constraints, and validators.
- Implement `clean()` for model-level validation.
- Implement `save()` for pre-save logic (timestamps, status updates).
- Define `Meta` options (indexes, ordering, constraints).
- Define model methods that operate on a single instance.

**What is allowed:**
- Import `django.db.models`.
- Define fields, constraints, indexes.
- Implement `clean()`, `save()`, model methods.
- Use Django validators.

**What is forbidden:**
- Query across multiple models (use repositories or selectors).
- Call external APIs.
- Send notifications.
- Contain business workflows.
- Import services.
- Contain complex query logic.

**Example:**
```python
# properties/models/building.py
from django.db import models
from core.models import TimeStampedModel

class Building(TimeStampedModel):
    owner = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="buildings",
    )
    name = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner", "is_active"]),
            models.Index(fields=["city", "state"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"],
                name="unique_building_name_per_owner",
            ),
        ]

    def clean(self):
        if not self.name.strip():
            raise ValidationError("Building name cannot be empty.")

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=["is_active", "modified_at"])
```

---

### 4.6 Utilities

**Purpose:** Provide pure, stateless, reusable functions for common transformations.

**Responsibilities:**
- Date formatting and parsing.
- String manipulation.
- Currency formatting and conversion.
- Reference code generation.
- Phone number formatting.
- File path manipulation.
- Pure mathematical calculations.

**What is allowed:**
- Import standard library.
- Import other pure utilities.
- Return computed values.
- Raise `ValueError` for invalid input.

**What is forbidden:**
- Contain business logic.
- Import models.
- Import services.
- Contain side effects (no database, no HTTP, no filesystem writes).
- Import Django settings.
- Import other bounded contexts.

**Example:**
```python
# shared/utils/formatting.py

def format_currency(amount: Decimal, currency: str = "INR") -> str:
    symbols = {"INR": "₹", "USD": "$"}
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"

def generate_reference(prefix: str, identifier: int) -> str:
    return f"{prefix}-{identifier:08d}"
```

---

### 4.7 Tasks (Background Jobs)

**Purpose:** Execute work asynchronously outside the HTTP request lifecycle.

**Responsibilities:**
- Send batch notifications.
- Generate PDFs asynchronously.
- Process payment verifications.
- Run data aggregation jobs.
- Clean up expired data.
- Trigger scheduled reports.

**What is allowed:**
- Import services.
- Import repositories.
- Use Django management commands (Year 1).
- Use Celery tasks (Stage 2).
- Log progress and errors.

**What is forbidden:**
- Contain business logic directly (delegate to services).
- Access HTTP request context.
- Modify user-facing state without audit trail.

**Example:**
```python
# notification/tasks/send_batch_notifications.py
from django.core.management import call_command
from notification.services.communication import send_smart_alert

class SendBatchNotificationsTask:
    def __init__(self, notification_service):
        self.notification_service = notification_service

    def execute(self, user_ids, message, context):
        for user_id in user_ids:
            try:
                self.notification_service.send(user_id, message, context)
            except NotificationError as exc:
                logger.error(
                    "Batch notification failed",
                    extra={"user_id": user_id, "error": str(exc)},
                )
```

---

### 4.8 Signals

**Purpose:** React to model lifecycle events by triggering side effects, never by performing business operations.

**Responsibilities:**
- Enqueue background tasks.
- Send notifications (thin wrapper calls).
- Update caches.
- Emit domain events (future event bus).

**What is allowed:**
- Call `transaction.on_commit` to defer work.
- Enqueue tasks.
- Call thin notification wrappers.
- Update cache keys.

**What is forbidden:**
- Perform business operations directly.
- Call external APIs with business payloads.
- Modify unrelated models.
- Contain business validation.
- Import services for business logic.

**Example:**
```python
# properties/signals/handlers.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from properties.models import Lease
from notification.services.communication import send_smart_alert

@receiver(post_save, sender=Lease)
def lease_created_handler(sender, instance, created, **kwargs):
    if created:
        send_smart_alert(
            user_id=instance.tenant.user_id,
            message="Your lease has been created.",
            context={"lease_id": instance.id},
        )
```

---

### 4.9 Validators

**Purpose:** Encapsulate input validation logic separate from serializers and models.

**Responsibilities:**
- Validate individual fields or complex input structures.
- Raise `ValidationError` with meaningful messages.
- Be reusable across serializers, services, and forms.

**What is allowed:**
- Import Django validators.
- Raise `ValidationError`.
- Accept raw input values.

**What is forbidden:**
- Import models.
- Import services.
- Contain business logic.
- Access the database.

**Example:**
```python
# finance/validators/tax_validator.py
from django.core.exceptions import ValidationError

def validate_gstin(value):
    if not re.match(r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}$", value):
        raise ValidationError("Enter a valid GSTIN.")
```

---

### 4.10 Serializers

**Purpose:** Transform data between Python objects and JSON (or other formats).

**Responsibilities:**
- Serialize model instances to JSON.
- Deserialize JSON to validated Python data.
- Perform field-level validation.
- Handle nested relationships.
- Control representation (fields, read_only, write_only).

**What is allowed:**
- Import models.
- Import validators.
- Import other serializers.
- Define field-level validation.

**What is forbidden:**
- Contain business logic.
- Call external APIs.
- Import services.
- Perform database writes beyond saving the serialized object.

**Example:**
```python
# properties/serializers/building_serializer.py
from rest_framework import serializers
from properties.models import Building
from properties.validators import validate_building_name

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ["id", "name", "address", "city", "state", "pincode", "is_active"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        validate_building_name(value)
        return value
```

---

### 4.11 Permissions

**Purpose:** Enforce authorization rules at the view level.

**Responsibilities:**
- Determine if a user can access a resource.
- Return `True` (allowed) or `False` (denied).
- Raise `PermissionDenied` with meaningful messages.

**What is allowed:**
- Import the user object.
- Import models (for ownership checks).
- Import `core` for role/subscription checks.

**What is forbidden:**
- Contain business logic.
- Modify data.
- Import services.
- Import other bounded contexts beyond `core`.

**Example:**
```python
# properties/permissions/is_property_owner.py
from rest_framework import permissions
from core.models import User

class IsPropertyOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.owner_id == request.user.id
```

---

### 4.12 Adapters and Gateways

**Purpose:** Wrap external services behind a uniform interface.

**Responsibilities:**
- Implement a protocol or abstract base class.
- Translate internal requests to external API calls.
- Handle external API authentication.
- Translate external responses to internal types.
- Handle external API errors and map them to internal exceptions.
- Implement retry logic per adapter.

**What is allowed:**
- Import HTTP clients (`requests`, `httpx`).
- Import external SDKs.
- Implement protocol methods.
- Raise internal exceptions.

**What is forbidden:**
- Import bounded context business logic.
- Import views.
- Contain business workflows.
- Call other adapters.

**Example:**
```python
# integrations/adapters/payment/razorpay.py
from integrations.interfaces.payment_gateway import PaymentGateway
from integrations.exceptions import PaymentGatewayError

class RazorpayAdapter(PaymentGateway):
    def __init__(self, api_key: str, api_secret: str):
        self.client = razorpay.Client(auth=(api_key, api_secret))

    def create_order(self, amount: Decimal, currency: str, receipt: str) -> PaymentOrder:
        try:
            response = self.client.order.create({
                "amount": int(amount * 100),
                "currency": currency,
                "receipt": receipt,
            })
            return PaymentOrder(id=response["id"], amount=amount, currency=currency)
        except razorpay.errors.BadRequestError as exc:
            raise PaymentGatewayError("Invalid payment request") from exc
```

---

### 4.13 Protocols and Interfaces

**Purpose:** Define contracts that implementations must follow.

**Responsibilities:**
- Define method signatures and return types.
- Specify behavior contracts in docstrings.
- Enable dependency inversion.
- Enable testing with mocks.

**What is allowed:**
- Define method signatures using Python 3.8+ syntax or `typing.Protocol`.
- Import types.
- Contain docstrings.

**What is forbidden:**
- Contain implementations.
- Import adapters or gateways.
- Import models.
- Import services.

**Example:**
```python
# shared/protocols/payment_gateway.py
from typing import Protocol
from decimal import Decimal

class PaymentGateway(Protocol):
    def create_order(self, amount: Decimal, currency: str, receipt: str) -> PaymentOrder: ...
    def capture_payment(self, payment_id: str, amount: Decimal) -> PaymentCapture: ...
    def verify_webhook(self, request_body: bytes, signature: str) -> WebhookVerification: ...
```

---

### 4.14 DTOs (Data Transfer Objects)

**Purpose:** Provide typed containers for data moving between layers.

**Responsibilities:**
- Carry data between layers without exposing internal types.
- Provide type safety.
- Document expected data shapes.
- Be immutable or clearly mutable.

**What is allowed:**
- Use `dataclasses`, `pydantic.BaseModel`, or `TypedDict`.
- Contain type annotations.
- Contain validation (if using Pydantic).

**What is forbidden:**
- Contain business logic.
- Import models.
- Import services.

**Example:**
```python
# shared/dto/paginated_response.py
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

@dataclass
class PaginatedResponse(Generic[T]):
    results: list[T]
    count: int
    next: str | None
    previous: str | None
```

---

### 4.15 Factories

**Purpose:** Create test data and, in some cases, complex object graphs.

**Responsibilities:**
- Create model instances for tests.
- Provide sensible defaults.
- Allow overriding specific fields.
- Be deterministic.

**What is allowed:**
- Import models.
- Use Factory Boy.
- Be used only in tests.

**What is forbidden:**
- Be used in production code.
- Contain business logic.

---

## 5. Dependency Diagram

### 5.1 Layered Dependency Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        HTTP Request                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Views (HTTP Adapter)                                        │
│  - Parse request                                             │
│  - Authenticate / Authorize                                  │
│  - Validate via Serializer                                   │
│  - Call Service                                              │
│  - Return Response                                           │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Services (Business Logic)                                   │
│  - Business rules                                            │
│  - Workflow orchestration                                    │
│  - Validation                                                │
│  - Call Repositories / Adapters                              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Repositories / Selectors (Data Access)                      │
│  - Queryset construction                                     │
│  - CRUD operations                                           │
│  - Aggregations                                              │
│  - Read-optimized projections                                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  ORM (Django Models)                                         │
│  - Schema definition                                         │
│  - Field constraints                                         │
│  - Model-level validation                                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                       │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Bounded Context Dependency Graph

```
                    ┌───────────────────────────────────────┐
                    │                  core                  │
                    │  (Identity, Auth, RBAC, Subscriptions) │
                    └───────────────────┬───────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
            ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
            │    accounts    │   │  properties    │   │  integrations  │
            │               │   │               │   │               │
            │ - Owner mgmt  │   │ - Buildings   │   │ - Adapters    │
            │ - Billing     │   │ - Units       │   │ - Webhooks    │
            │ - Sub changes │   │ - Leases      │   │ - Health      │
            └───────┬───────┘   └───────┬───────┘   └───────┬───────┘
                    │                   │                   │
                    │                   │                   │
                    ▼                   ▼                   ▼
            ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
            │  notification  │   │   documents    │   │    finance     │
            │               │   │               │   │               │
            │ - Channels    │   │ - PDF gen     │   │ - Tax calc    │
            │ - Templates   │   │ - E-signature │   │ - Compliance  │
            │ - Delivery    │   │ - Templates   │   │ - Invoices    │
            └───────┬───────┘   └───────┬───────┘   └───────┬───────┘
                    │                   │                   │
                    │                   │                   │
                    ▼                   ▼                   ▼
            ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
            │   assistant    │   │   analytics    │   │               │
            │               │   │               │   │               │
            │ - Chatbot     │   │ - Dashboards  │   │               │
            │ - GPT         │   │ - Reports     │   │               │
            │ - Intents     │   │ - Metrics     │   │               │
            └───────────────┘   └───────────────┘   └───────────────┘

                    ┌───────────────────────────────────────┐
                    │                 shared                  │
                    │  (Exceptions, Types, Utils, Protocols)  │
                    └───────────────────────────────────────┘
```

**Legend:**
- Solid arrow: direct dependency through public interface.
- All bounded contexts depend on `shared`.
- `integrations` is depended upon by `properties`, `finance`, `documents`, `assistant`, `notification`.
- `notification` is depended upon by `properties`, `accounts`, `assistant`, `analytics`.
- `documents` is depended upon by `properties`, `finance`, `assistant`.

### 5.3 Internal Layer Dependency Diagram (per bounded context)

```
┌─────────────────────┐
│       Views         │
│   (api/v1/*.py)     │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│     Services        │
│  (services/*.py)    │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Repositories      │
│ (repositories/*.py) │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│       Models        │
│   (models/*.py)     │
└─────────────────────┘

Additional horizontal dependencies:
  Services → Interfaces (protocols)
  Services → Adapters (through interfaces)
  Services → Exceptions
  Services → Constants
  Services → DTOs
```

---

## 6. Request Lifecycle

### 6.1 Synchronous HTTP Request Lifecycle

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. HTTP Request Arrives                                             │
│    - Method: GET / POST / PUT / PATCH / DELETE                     │
│    - Path: /api/v1/buildings/                                      │
│    - Headers: Authorization, Content-Type, X-Request-ID           │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. Django URL Resolution                                           │
│    - config/urls.py routes to bounded context URLs                 │
│    - properties/urls.py routes to ViewSet                          │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. Authentication Middleware                                       │
│    - JWT token extracted from Authorization header                 │
│    - Token validated via core.services.AuthService                 │
│    - request.user set to authenticated user                        │
│    - If invalid: return 401 Unauthorized                           │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. Permission Check                                                │
│    - View permission_classes evaluated                              │
│    - IsPropertyOwner, HasRole, HasSubscription, etc.               │
│    - If denied: return 403 Forbidden                               │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. Request Validation                                             │
│    - Serializer instantiated with request.data                     │
│    - Field-level validation executed                               │
│    - Object-level validation executed                              │
│    - If invalid: return 400 Bad Request with errors                │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. Service Layer                                                   │
│    - View calls service method                                     │
│    - Service validates business rules                              │
│    - Service orchestrates workflow                                 │
│    - Service calls repositories                                    │
│    - Service may trigger signals                                   │
│    - Service raises business exceptions on failure                 │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 7. Repository Layer                                                │
│    - Service calls repository methods                              │
│    - Repository constructs optimized querysets                     │
│    - Repository executes ORM queries                               │
│    - Repository returns model instances or querysets               │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 8. Database                                                       │
│    - ORM translates queryset to SQL                                │
│    - PostgreSQL executes query                                     │
│    - Results returned to ORM                                       │
│    - Model instances created                                       │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 9. Response Construction                                           │
│    - Service returns result to view                                │
│    - View serializes result via Serializer                         │
│    - View returns Response with data and status code               │
│    - DRF renders JSON response                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Exception Propagation

```
Service raises RentSecureException
    │
    ▼
View catches RentSecureException
    │
    ▼
Maps to appropriate HTTP status code:
  ValidationError → 400
  PermissionError → 403
  NotFoundError → 404
  PaymentError → 402 / 422
  DocumentError → 500
  IntegrationError → 502 / 504
    │
    ▼
Returns error response with structured error body:
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Building name already exists.",
    "details": {"field": "name"},
    "request_id": "abc-123"
  }
}
```

### 6.3 Asynchronous Job Lifecycle

```
Trigger (HTTP request or scheduled task)
    │
    ▼
Enqueue job (Django management command or Celery task)
    │
    ▼
Worker picks up job
    │
    ▼
Job calls Service method
    │
    ▼
Service executes business logic
    │
    ▼
Result persisted or notification sent
    │
    ▼
Job logs outcome
    │
    ▼
If failure: Retry with exponential backoff (max 3 retries)
    │
    ▼
If max retries exceeded: Move to dead letter queue
    │
    ▼
Alert on-call team via monitoring
```

### 6.4 Signal Lifecycle

```
Model save triggered
    │
    ▼
pre_save signal
    │
    ▼
Model.save() executes
    │
    ▼
post_save signal
    │
    ▼
Signal handler executes
    │
    ├─► Enqueue background task (preferred)
    ├─► Call thin notification wrapper
    └─► Update cache key
```

---

## 7. Cross Context Communication

### 7.1 Allowed Communication

Cross-context communication is allowed only through **public interfaces**. A public interface is:
- A function or class explicitly exported in `services/__init__.py` or `api.py`.
- A protocol or abstract base class defined in `interfaces/`.
- A well-documented API endpoint.

**Allowed patterns:**

| Pattern | Example | When to Use |
|---------|---------|-------------|
| Direct service call | `from notification.services import send_smart_alert` | Synchronous, same process, low latency requirement |
| Interface-based injection | `PaymentService(payment_gateway=RazorpayAdapter())` | When substitution is needed (testing, multiple implementations) |
| DTO passing | `CreateBuildingRequest(name=..., address=...)` | When data must cross context boundary with explicit contract |
| Event enqueueing | `call_command("send_notification", user_id, message)` | When work can be deferred |

### 7.2 Forbidden Communication

| Pattern | Example | Why Forbidden |
|---------|---------|---------------|
| Import private module | `from notification.utils import render_template` | Tight coupling, private module may change |
| Direct model import | `from properties.models import Building` (unless in public interface) | Breaks data ownership |
| Direct ORM write | `RentRecord.objects.filter(...).update(...)` | Bypasses business logic |
| Circular import | `properties` imports `finance`, `finance` imports `properties` | Impossible to initialize |
| Cross-context signal | `properties` connects to `notification` model signals | Hidden coupling |
| Shared mutable state | Module-level cache, global variables | Impossible to reason about, not thread-safe |

### 7.3 Service Interfaces

Every cross-context dependency is expressed through a protocol or abstract base class.

**Example: Payment Gateway Interface**
```python
# shared/protocols/payment_gateway.py
class PaymentGateway(Protocol):
    def create_order(self, amount: Decimal, currency: str, receipt: str) -> PaymentOrder: ...
    def capture_payment(self, payment_id: str, amount: Decimal) -> PaymentCapture: ...
    def verify_webhook(self, body: bytes, signature: str) -> WebhookVerification: ...
```

**Implementations:**
```python
# integrations/adapters/payment/razorpay.py
class RazorpayAdapter:
    def create_order(self, amount, currency, receipt) -> PaymentOrder: ...

# integrations/adapters/payment/cashfree.py
class CashfreeAdapter:
    def create_order(self, amount, currency, receipt) -> PaymentOrder: ...

# integrations/adapters/payment/manual.py
class ManualPaymentAdapter:
    def create_order(self, amount, currency, receipt) -> PaymentOrder: ...
```

**Consumer:**
```python
# payments/services/payment_service.py
class PaymentService:
    def __init__(self, gateway: PaymentGateway):
        self.gateway = gateway

    def create_payment(self, rent_record):
        return self.gateway.create_order(
            amount=rent_record.amount,
            currency="INR",
            receipt=f"rent-{rent_record.id}",
        )
```

### 7.4 Events (Future)

In Stage 2, bounded contexts will communicate through an event bus. Events are immutable facts about something that happened.

**Example events:**
- `LeaseCreatedEvent`
- `PaymentSubmittedEvent`
- `DocumentGeneratedEvent`
- `NotificationSentEvent`

Event structure:
```python
@dataclass
class DomainEvent:
    event_id: str
    event_type: str
    aggregate_id: str
    occurred_at: datetime
    payload: dict
    metadata: dict
```

**Event bus contract:**
- Publishers emit events to the bus.
- Subscribers listen for events they care about.
- Events are persisted for replay.
- Events are ordered per aggregate.

**Year 1 alternative:** Django signals and management commands. No message broker required.

### 7.5 Synchronous vs Asynchronous

| Communication Type | Use Case | Mechanism |
|-------------------|----------|-----------|
| Synchronous (same process) | Property creation needs to generate document | Direct service call |
| Synchronous (cross-context) | `properties` needs tenant from `accounts` | Direct service call through public interface |
| Asynchronous (deferred) | Send notification after lease creation | Signal → enqueue task |
| Asynchronous (cross-service) | `finance` needs to know payment was made (Stage 2) | Event bus |
| Future async (cross-service) | `analytics` needs to update dashboard after rent payment | Event bus |

**Rule:** Default to synchronous for same-process, bounded-context communication. Default to asynchronous for cross-service communication (Stage 2) and for any work that can be deferred without blocking the user.

---

## 8. Shared Module

### 8.1 Purpose

The `shared` module is the only module that may contain code imported by multiple bounded contexts. It is a leaf in the dependency graph: no bounded context may depend on `shared`, but all bounded contexts may depend on `shared`.

### 8.2 What Belongs in Shared

| Category | Examples | Rationale |
|----------|----------|-----------|
| Exceptions | `RentSecureException`, `ValidationError`, `PaymentError` | Standardized error handling across all contexts |
| Types | `Result[T]`, `PaginatedResponse[T]` | Common type aliases used everywhere |
| Enums | `UserRole`, `PaymentStatus`, `DocumentStatus` | Shared enumerations that appear in multiple contexts |
| Utilities | `format_currency()`, `parse_date()`, `generate_reference()` | Pure functions with no business context |
| Protocols | `PaymentGateway`, `NotificationChannel`, `DocumentGenerator` | Abstraction contracts used across contexts |
| Validators | `validate_gstin()`, `validate_upi_id()`, `validate_indian_phone()` | Reusable validation logic |
| Constants | `HTTP_STATUS`, `DEFAULT_PAGINATION` | Configuration constants used everywhere |

### 8.3 What Never Belongs in Shared

| Category | Examples | Rationale |
|----------|----------|-----------|
| Business workflows | `process_rent_payment()` | Business logic belongs in domain contexts |
| Models | `Building`, `RentRecord` | Data ownership belongs in domain contexts |
| Services | `PaymentService`, `NotificationService` | Business logic belongs in domain contexts |
| Views | Any HTTP endpoint | Views belong in domain contexts |
| Adapters | `RazorpayAdapter` | Infrastructure belongs in `integrations` |
| Settings | Django settings | Configuration belongs in `config/` |

### 8.4 Shared Stability

`shared` must be extremely stable. Changes to `shared` affect every bounded context. Before modifying `shared`:

1. Identify all bounded contexts that import the modified module.
2. Ensure backward compatibility.
3. Add new functionality alongside old, deprecate old, remove after migration.
4. Run all tests across all bounded contexts.

### 8.5 Shared Internal Structure

```
shared/
  __init__.py
  exceptions/
    __init__.py          # Exports all exception classes
    base.py              # RentSecureException
    validation.py        # ValidationError
    payment.py           # PaymentError
    document.py          # DocumentError
    notification.py      # NotificationError
    integration.py       # IntegrationError
  types/
    __init__.py
    result.py            # Result[T] = Success[T] | Failure[T]
    pagination.py        # Page, PageSize, PaginatedResponse
  enums/
    __init__.py
    user_roles.py        # UserRole(OWNER, TENANT, ADMIN)
    payment_status.py    # PaymentStatus(PENDING, SUBMITTED, PAID, FAILED)
    document_status.py   # DocumentStatus(DRAFT, GENERATED, SIGNED, ARCHIVED)
    notification_channel.py  # NotificationChannel(EMAIL, PUSH, INAPP, WHATSAPP, SMS)
  utils/
    __init__.py
    formatting.py        # format_currency(), format_date()
    dates.py             # parse_date(), add_business_days()
    strings.py           # slugify(), truncate()
    currency.py          # convert_currency(), round_to_paise()
    references.py        # generate_reference()
  protocols/
    __init__.py
    payment_gateway.py   # PaymentGateway protocol
    notification_channel.py  # NotificationChannel protocol
    document_generator.py    # DocumentGenerator protocol
    e_signature_provider.py  # ESignatureProvider protocol
    storage_provider.py      # StorageProvider protocol
    llm_provider.py          # LLMProvider protocol
  validators/
    __init__.py
    indian_phone.py      # validate_indian_phone()
    gstin.py             # validate_gstin()
    upi_id.py            # validate_upi_id()
    pincode.py           # validate_pincode()
  constants/
    __init__.py
    http_status.py       # HTTP_200_OK, HTTP_400_BAD_REQUEST, etc.
    default_pagination.py # DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
  dto/
    __init__.py
    paginated_response.py  # PaginatedResponse[T]
    error_response.py      # ErrorResponse
```

---

## 9. External Integrations

### 9.1 Adapter Pattern Requirement

Every external integration must use the Adapter Pattern. The domain bounded context depends on an abstract interface defined in `shared/protocols/`. The concrete implementation lives in `integrations/adapters/`.

**Contract:**
```python
class AdapterName(Protocol):
    def operation(self, ...) -> ReturnType: ...
```

**Implementation:**
```python
class ConcreteAdapter:
    def operation(self, ...) -> ReturnType:
        # External API call
        # Error translation
        # Return internal type
```

### 9.2 Payment Gateways

| Adapter | Status | Location | Protocol |
|---------|--------|----------|----------|
| `ManualPaymentAdapter` | Year 1 (Active) | `integrations/adapters/payment/manual.py` | `PaymentGateway` |
| `RazorpayAdapter` | Stage 2 (Disabled) | `integrations/adapters/payment/razorpay.py` | `PaymentGateway` |
| `CashfreeAdapter` | Stage 2 (Disabled) | `integrations/adapters/payment/cashfree.py` | `PaymentGateway` |

**ManualPaymentAdapter behavior:**
- Accepts UTR, screenshot, and payment note from tenant.
- Creates a `PaymentSubmission` record.
- Returns a reference number.
- Does not call any external API.

**RazorpayAdapter behavior (Stage 2):**
- Creates Razorpay orders.
- Verifies Razorpay webhooks.
- Handles Razorpay-specific error codes.
- Maps Razorpay errors to `PaymentGatewayError`.

**CashfreeAdapter behavior (Stage 2):**
- Creates Cashfree orders.
- Verifies Cashfree webhooks.
- Handles Cashfree-specific error codes.
- Maps Cashfree errors to `PaymentGatewayError`.

### 9.3 E-Signature Provider

| Adapter | Status | Location | Protocol |
|---------|--------|----------|----------|
| `LeegalityAdapter` | Active | `integrations/adapters/document/leegality.py` | `ESignatureProvider` |

**Responsibilities:**
- Create envelope on Leegality.
- Upload PDF to Leegality.
- Add signers with roles.
- Trigger signing workflow.
- Poll for signature status.
- Download signed PDF.
- Handle webhook callbacks.

### 9.4 Notification Providers

| Adapter | Status | Location | Protocol |
|---------|--------|----------|----------|
| `EmailAdapter` | Active | `integrations/adapters/notification/ses.py` | `NotificationChannel` |
| `FCMAdapter` | Active | `integrations/adapters/notification/fcm.py` | `NotificationChannel` |
| `InAppAdapter` | Active | `integrations/adapters/notification/inapp.py` | `NotificationChannel` |
| `WhatsAppAdapter` | Disabled (Stage 2) | `integrations/adapters/notification/whatsapp_business.py` | `NotificationChannel` |
| `SMSAdapter` | Disabled (Stage 2) | `integrations/adapters/notification/twilio.py` | `NotificationChannel` |

**EmailAdapter responsibilities:**
- Accept email payload (to, subject, body, attachments).
- Send via Django SMTP or AWS SES.
- Handle bounces and complaints.
- Return delivery status.

**FCMAdapter responsibilities:**
- Accept push payload (device token, title, body, data).
- Send via Firebase Admin SDK.
- Handle invalid token errors.
- Return delivery status.

### 9.5 Storage Provider

| Adapter | Status | Location | Protocol |
|---------|--------|----------|----------|
| `S3Adapter` | Active | `integrations/adapters/storage/s3.py` | `StorageProvider` |
| `LocalStorageAdapter` | Fallback | `integrations/adapters/storage/local.py` | `StorageProvider` |

**Responsibilities:**
- Upload file to storage.
- Generate presigned download URL.
- Delete file.
- List files in a folder.

### 9.6 AI Provider

| Adapter | Status | Location | Protocol |
|---------|--------|----------|----------|
| `OpenAIAdapter` | Active | `integrations/adapters/ai/openai.py` | `LLMProvider` |

**Responsibilities:**
- Accept prompt and optional system message.
- Call OpenAI Chat Completions API.
- Handle rate limiting and retries.
- Return structured response.
- Stream responses for chat interface.

### 9.7 Webhook Handlers

All incoming webhooks are handled in `integrations/webhooks/`.

| Webhook | Handler | Verification |
|---------|---------|--------------|
| Razorpay | `razorpay_webhook.py` | Razorpay signature verification |
| Cashfree | `cashfree_webhook.py` | Cashfree signature verification |
| Leegality | `leegality_webhook.py` | Leegality signature verification |
| FCM | Handled by Firebase Admin SDK | N/A (FCM handles delivery) |

**Webhook contract:**
1. Verify signature using adapter-specific method.
2. Parse payload.
3. Map to internal event.
4. Call appropriate service method.
5. Return 200 OK immediately.
6. Enqueue any heavy processing as a background task.

### 9.8 Health Checks

All adapters implement a `health_check()` method that returns a health status. The `integrations.services.health_check_service` aggregates health checks and exposes a `/health/integrations` endpoint.

---

## 10. Caching Architecture

### 10.1 Cache Strategy

RentSecure uses Django's caching framework with **Local Memory Cache (LocMemCache)** in Year 1. Redis is evaluated for Stage 2 based on:
- Need for shared cache across multiple processes.
- Need for cache invalidation across processes.
- Need for cache warming from external sources.

### 10.2 Cache Layers

| Layer | Scope | TTL | Key Pattern | Used For |
|-------|-------|-----|-------------|----------|
| L1: Per-request cache | Single HTTP request | Request lifetime | N/A (in-memory variable) | Avoid repeated DB lookups in a single request |
| L2: View-level cache | Cross-request | 5 minutes | `view:{path}:{query_hash}` | Expensive analytics queries, public dashboards |
| L3: Data cache | Cross-request | 1 hour | `data:{model}:{id}:{field}` | Frequently accessed reference data (subscription tiers, notification templates) |
| L4: Computed cache | Cross-request | 15 minutes | `computed:{type}:{params_hash}` | Aggregated analytics, dashboard summaries |

### 10.3 Cache Invalidation

| Strategy | When to Use | Implementation |
|----------|-------------|----------------|
| Time-based (TTL) | Data that changes infrequently | Set TTL on all cached data |
| Event-based | Data that changes on specific events | Signal handler invalidates relevant cache keys |
| Version-based | Templates, computed data | Include version in cache key |

**Example event-based invalidation:**
```python
# properties/signals/handlers.py
@receiver(post_save, sender=Building)
def invalidate_building_cache(sender, instance, **kwargs):
    cache.delete(f"data:building:{instance.id}:details")
    cache.delete(f"view:buildings:owner:{instance.owner_id}")
```

### 10.4 Cache Keys

Cache keys must follow a strict naming convention:
- Prefix: `view:`, `data:`, `computed:`, `session:`
- Separator: `:`
- No spaces or special characters.
- Deterministic: same inputs always produce same key.

### 10.5 Distributed Locking

Distributed locking is required for:
- Payment processing (prevent double-charge).
- Webhook processing (prevent duplicate handling).
- Batch operations (prevent concurrent batch runs).

**Year 1 implementation:** File-based locking using `django.core.files.locks`.
**Stage 2 implementation:** Redis-based locking with `redis.lock`.

**Lock contract:**
```python
from django.core.files.locks import lock

with lock(f"payment-{rent_record.id}", timeout=30):
    # Critical section
    process_payment(rent_record)
```

---

## 11. Background Processing

### 11.1 Year 1 Strategy: Django Management Commands

Year 1 does not use Celery. Background jobs are implemented as Django management commands executed via:
- `python manage.py <command>` for ad-hoc execution.
- Systemd timers or crontab for scheduled execution.
- `call_command()` from within views or signals for immediate enqueueing.

**Why no Celery in Year 1:**
- Celery requires a message broker (Redis/RabbitMQ), adding operational complexity.
- For the expected transaction volume, management commands are sufficient.
- Celery is a Stage 2 upgrade when volume justifies it.

### 11.2 Job Structure

Every background job is a Django management command:

```python
# notification/management/commands/send_rent_reminders.py
from django.core.management.base import BaseCommand
from properties.services.rent_service import RentService
from notification.services.communication import send_smart_alert

class Command(BaseCommand):
    help = "Send rent reminders to tenants"

    def handle(self, *args, **options):
        rent_service = RentService()
        upcoming_rents = rent_service.get_upcoming_rents(days=3)
        for rent in upcoming_rents:
            send_smart_alert(
                user_id=rent.tenant.user_id,
                message="Your rent is due in 3 days.",
                context={"amount": rent.amount, "due_date": rent.due_date},
            )
        self.stdout.write(f"Sent {len(upcoming_rents)} reminders.")
```

### 11.3 Enqueueing from Code

```python
# properties/services/rent_service.py
from django.core.management import call_command

class RentService:
    def create_rent_record(self, ...):
        record = self.repository.create(...)
        call_command("send_rent_reminders", rent_id=record.id)
        return record
```

**Note:** `call_command` is synchronous. For true async behavior in Year 1, use `subprocess.Popen` or a systemd service. This is acceptable for non-critical tasks.

### 11.4 Retry Policy

| Job Type | Retries | Backoff | Dead Letter Action |
|----------|---------|---------|-------------------|
| Notification | 3 | Exponential (1s, 2s, 4s) | Log and alert |
| PDF generation | 2 | Exponential (2s, 4s) | Log and mark document as failed |
| Payment verification | 3 | Exponential (5s, 10s, 20s) | Mark as pending manual review |
| Analytics aggregation | 1 | None | Log and skip |
| Webhook processing | 3 | Exponential (1s, 2s, 4s) | Return 200 to external; process later |

### 11.5 Dead Letter Strategy

Jobs that exceed max retries are:
1. Logged with full context.
2. Marked as failed in the database (if applicable).
3. Alerted to on-call team via monitoring.
4. Placed in a dead letter table for manual review.

```python
# shared/exceptions/integration.py
class DeadLetterError(RentSecureException):
    """Raised when a job exceeds max retries."""
```

### 11.6 Idempotency

All background jobs must be idempotent:
- Use idempotency keys for payment-related jobs.
- Use `created_at` timestamps to avoid duplicate processing.
- Check current state before acting (e.g., check if notification already sent).

---

## 12. Error Architecture

### 12.1 Exception Hierarchy

All business exceptions inherit from `RentSecureException` defined in `shared/exceptions/base.py`.

```
RentSecureException (base)
├── ValidationError (400)
│   ├── FieldValidationError
│   └── BusinessRuleViolationError
├── AuthenticationError (401)
├── AuthorizationError (403)
├── NotFoundError (404)
│   ├── ResourceNotFoundError
│   └── EntityNotFoundError
├── ConflictError (409)
├── PaymentError (422)
│   ├── PaymentGatewayError
│   ├── InsufficientFundsError
│   └── PaymentVerificationError
├── DocumentError (422)
│   ├── PDFGenerationError
│   ├── ESignatureError
│   └── TemplateNotFoundError
├── NotificationError (422)
├── IntegrationError (502)
│   ├── WebhookVerificationError
│   ├── ExternalAPIError
│   └── RateLimitError
├── RateLimitExceededError (429)
└── InternalError (500)
    ├── UnexpectedStateError
    └── ConfigurationError
```

### 12.2 Logging Strategy

**Structured logging using Python `logging` module with `structlog` or manual JSON formatting.**

**Required log fields:**
- `timestamp`: ISO 8601 datetime.
- `level`: DEBUG, INFO, WARNING, ERROR, CRITICAL.
- `event`: Event name (e.g., `payment_processed`, `notification_sent`).
- `bounded_context`: Bounded context name.
- `user_id`: User ID (if applicable).
- `request_id`: Correlation ID (if applicable).
- `duration_ms`: Operation duration (if applicable).
- `error`: Error details (if applicable).

**Log levels:**
- `DEBUG`: Detailed diagnostic information (development only).
- `INFO`: Business events (payment processed, user logged in, document generated).
- `WARNING`: Recoverable errors, deprecation warnings, fallback activations.
- `ERROR`: Unhandled exceptions, failed operations, external API failures.
- `CRITICAL`: System-level failures, database connection lost, security breaches.

**Log destinations:**
- Development: Console (stdout).
- Production: Structured JSON to stdout, collected by log aggregation (ELK, Datadog, CloudWatch).

### 12.3 Correlation IDs

Every HTTP request receives a correlation ID (`X-Request-ID`) from the load balancer or generated by middleware. This ID is:
- Added to all log entries within the request.
- Propagated to external API calls.
- Returned in the response header.
- Used for tracing requests across logs.

```python
# config/middleware/correlation_id.py
class CorrelationIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.correlation_id = request_id
        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        return response
```

### 12.4 Monitoring

| Metric | Tool | Alert Threshold |
|--------|------|-----------------|
| HTTP error rate (5xx) | Prometheus / Datadog | > 1% over 5 minutes |
| HTTP latency (p95) | Prometheus / Datadog | > 2 seconds |
| Payment failure rate | Custom | > 5% over 15 minutes |
| Notification delivery failure rate | Custom | > 10% over 15 minutes |
| PDF generation failure rate | Custom | > 5% over 15 minutes |
| Database connection pool usage | Datadog | > 80% |
| Celery queue depth (Stage 2) | Flower / Datadog | > 1000 pending jobs |

### 12.5 Audit Logs

Audit logs capture security-relevant events:
- User login, logout, password change.
- Permission changes.
- Payment submissions and approvals.
- Document generation and signing.
- Data export requests.

Audit logs are:
- Written to a dedicated `AuditLog` model in `core`.
- Never modified or deleted (append-only).
- Exported to external storage for compliance.

---

## 13. Security Architecture

### 13.1 Authentication

**Mechanism:** JWT (JSON Web Tokens) with short-lived access tokens and long-lived refresh tokens.

**Flow:**
1. User POSTs credentials to `/api/v1/auth/login/`.
2. Server validates credentials.
3. Server returns `access_token` (15 minutes) and `refresh_token` (7 days).
4. Client includes `Authorization: Bearer <access_token>` in subsequent requests.
5. On expiry, client POSTs `refresh_token` to `/api/v1/auth/refresh/`.
6. Server returns new `access_token`.

**Token storage:**
- Access tokens: Client memory (localStorage with XSS protection, or memory).
- Refresh tokens: HTTP-only secure cookies (web) or secure storage (mobile).

**Token revocation:**
- Refresh tokens stored in database with expiry.
- Revocation endpoint invalidates refresh tokens.
- Access tokens are stateless; revocation is handled by short TTL.

### 13.2 Authorization

**Mechanism:** Role-Based Access Control (RBAC) with Django REST Framework permissions.

**Roles:**
- `OWNER`: Full access to owned resources.
- `TENANT`: Access to own lease, payments, and documents.
- `ADMIN`: Platform administration.
- `STAFF`: Property management staff.

**Enforcement:**
- DRF permission classes at the view level.
- Object-level permissions for resource ownership.
- Service-level authorization for sensitive operations.

### 13.3 Secrets Management

**Rule:** No secrets in code, no secrets in environment variables in production.

**Year 1 (development):** `.env` file (git-ignored).
**Year 1 (production):** Environment variables injected by deployment platform (Docker secrets, AWS Parameter Store, etc.).
**Stage 2:** Dedicated secrets manager (HashiCorp Vault, AWS Secrets Manager).

**Allowed in `.env`:**
- Database credentials.
- JWT secret key.
- Third-party API keys.
- AWS credentials.

**Forbidden in code:**
- Hardcoded API keys.
- Hardcoded passwords.
- Hardcoded tokens.

### 13.4 Permissions Model

```
User
  ├── Role (RBAC)
  │   ├── PlatformAdmin
  │   ├── Owner
  │   └── Tenant
  ├── SubscriptionTier (feature flags)
  │   ├── Free
  │   ├── Basic
  │   └── Premium
  └── ResourceOwnership
      ├── owns Building
      ├── leases Unit
      └── accesses Document
```

**Permission hierarchy:**
1. Is the user authenticated? → 401 if not.
2. Does the user have the required role? → 403 if not.
3. Does the user own the resource? → 403 if not.
4. Is the user's subscription tier sufficient? → 402/403 if not.

### 13.5 Rate Limiting

| Endpoint Type | Rate Limit | Window |
|---------------|------------|--------|
| Authentication | 5 attempts | 5 minutes |
| API (authenticated) | 100 requests | 1 minute |
| API (anonymous) | 20 requests | 1 minute |
| File upload | 10 uploads | 10 minutes |
| Webhook | Unlimited (IP whitelist) | N/A |

**Implementation:** Django REST Framework throttling classes.

### 13.6 OWASP Top 10 Mitigations

| Risk | Mitigation |
|------|------------|
| Broken Access Control | DRF permissions, object-level authorization, RBAC |
| Cryptographic Failures | TLS 1.3, JWT with strong secret, encrypted secrets storage |
| Injection | Django ORM (parameterized queries), input validation, serializer validation |
| Insecure Design | Architecture principles, bounded contexts, dependency rules |
| Security Misconfiguration | Hardened settings, disabled debug in production, security headers |
| Vulnerable Components | Dependabot, pre-commit hooks, regular audits |
| Authentication Failures | JWT with rotation, MFA (future), rate limiting on auth endpoints |
| Data Integrity Failures | Webhook signature verification, idempotency keys |
| Logging Failures | Structured logging, audit logs, no PII in logs |
| SSRF | Whitelist allowed domains for external calls, validate URLs |

### 13.7 Input Validation

**Rule:** All input must be validated at the earliest possible layer.

**Layers:**
1. **Serializer validation:** Field types, required fields, format validation.
2. **Model validation:** `clean()`, field constraints, model-level invariants.
3. **Service validation:** Business rules, cross-field validation, state transitions.
4. **Repository validation:** Existence checks, uniqueness constraints.

**No input may reach the database without passing all applicable validation layers.**

### 13.8 File Validation

| File Type | Allowed | Validation |
|-----------|---------|------------|
| PDF | Yes | Magic bytes check, size limit (10MB) |
| Image (QR, screenshot) | Yes | Magic bytes check, size limit (5MB), dimension limits |
| Document templates | Yes | HTML sanitization, no inline scripts |
| CSV (imports) | Yes | Row count limit, column validation, encoding check |

**Storage:** All files stored in S3 or local storage with restricted access. Never served directly from MEDIA_ROOT in production.

---

## 14. Performance Architecture

### 14.1 Pagination

**Default:** Page-based pagination with 20 items per page.
**Maximum:** 100 items per page.
**Cursor-based:** Used for real-time feeds and large datasets where offset pagination is inefficient.

```python
# shared/dto/pagination.py
@dataclass
class PaginatedResponse(Generic[T]):
    results: list[T]
    count: int
    next: str | None
    previous: str | None
```

### 14.2 Query Optimization

**Rule:** Every query that touches more than 100 rows must be reviewed for N+1 prevention.

**Techniques:**
- `select_related()` for foreign key joins (one-to-one, many-to-one).
- `prefetch_related()` for reverse foreign keys and many-to-many.
- `only()` and `defer()` to limit fetched columns.
- `annotate()` and `aggregate()` to push computation to the database.
- Database-level constraints and indexes.

**Example:**
```python
# Bad: N+1 query
units = Unit.objects.filter(building__owner=owner)
for unit in units:
    print(unit.tenant.name)  # Additional query per unit

# Good: select_related
units = Unit.objects.select_related("tenant").filter(building__owner=owner)
for unit in units:
    print(unit.tenant.name)  # No additional query
```

### 14.3 Indexes

**Required indexes for every model:**
- Foreign key fields (Django creates these automatically).
- Fields used in `filter()`, `exclude()`, `order_by()`.
- Compound indexes for common filter combinations.

**Example:**
```python
class Meta:
    indexes = [
        models.Index(fields=["owner", "is_active"]),
        models.Index(fields=["owner", "created_at"]),
    ]
```

**Index strategy:**
- Analyze slow query logs monthly.
- Add indexes for queries exceeding 100ms.
- Remove unused indexes.
- Monitor index bloat.

### 14.4 Bulk Operations

**Rule:** Operations affecting more than 100 rows must use bulk operations.

**Allowed:**
- `bulk_create()`
- `bulk_update()`
- `update()` on querysets
- Raw SQL for complex aggregations (isolated in repositories)

**Forbidden:**
- Looping over 100+ items and saving individually.
- Individual `save()` calls in bulk operations.

### 14.5 N+1 Prevention

**Enforcement:**
- Code review checklist: "Did you use `select_related` / `prefetch_related`?"
- Automated detection: Django Debug Toolbar in development, `nplusone` library.
- CI check: Integration tests assert query count.

```python
# Example: Assert no N+1 in test
with self.assertNumQueries(5):
    response = self.client.get("/api/v1/buildings/")
```

### 14.6 Caching

See [Section 10: Caching Architecture](#10-caching-architecture).

### 14.7 Streaming

Large file responses (PDFs, CSV exports) must use streaming HTTP responses to avoid loading entire files into memory.

```python
from django.http import StreamingHttpResponse

def download_pdf(request, document_id):
    pdf_stream = PDFGenerator.stream_pdf(document_id)
    response = StreamingHttpResponse(pdf_stream, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="document-{document_id}.pdf"'
    return response
```

---

## 15. Scalability Vision

### 15.1 Current Scale (Year 1)

- **Users:** ~10,000 (owners + tenants)
- **Transactions:** ~50,000/month (rent payments, document generations, notifications)
- **Database:** Single PostgreSQL instance (2 vCPU, 8GB RAM, 100GB storage)
- **Processes:** Single Django application (Gunicorn with 4 workers)
- **Cache:** Local memory cache per process

### 15.2 100K Users Scale

**Triggers for optimization:**
- Database connection pool exhaustion.
- Query latency exceeding 500ms.
- Cache hit rate below 80%.
- Worker CPU saturation.

**Actions:**
- Add read replica for analytics queries.
- Move cache to Redis (shared across workers).
- Add CDN for static files and generated PDFs.
- Optimize slow queries identified by query logs.
- Add database connection pooling (PgBouncer).

### 15.3 1M Users Scale

**Triggers for microservice extraction:**
- Monthly transaction volume exceeds 500,000 requests.
- Multiple teams require independent deployment cycles.
- Specific bounded contexts need different scaling characteristics.
- Operational requirements cannot be met by monolith.

**Extraction order:**
1. `notification` — Stateless, event-driven, clear interface. Easiest to extract.
2. `analytics` — Read-heavy, can use read replica or separate data store.
3. `documents` — Stateless, CPU-intensive (PDF generation), can scale horizontally.
4. `payments` — Requires strong consistency, but adapter pattern makes extraction possible.

**What stays in monolith:**
- `core` — Foundational, shared.
- `properties` — Central to business, requires strong consistency with `finance`.
- `finance` — Financial data requires ACID transactions.

### 15.4 When NOT to Split

Do NOT split a bounded context into a microservice when:
- The team is fewer than 20 engineers.
- Monthly transaction volume is below 500,000 requests.
- The bounded context requires strong consistency with other contexts.
- There is no proven scaling bottleneck.
- The team is not prepared for distributed systems complexity.

**Premature extraction is worse than staying in a monolith.** The cost of distributed systems is paid every day, not just on the day of extraction.

---

## 16. Testing Architecture

### 16.1 Test Location

```
tests/
  conftest.py                     # Shared fixtures
  factories/
    __init__.py
    user_factory.py
    building_factory.py
    rent_record_factory.py
    document_factory.py
  unit/                           # Unit tests live WITH the code
  integration/
    __init__.py
    test_property_creation.py
    test_payment_flow.py
    test_document_generation.py
  architecture/
    __init__.py
    test_import_rules.py          # No private imports across contexts
    test_dependency_rules.py      # No circular dependencies
    test_no_business_logic_in_views.py
    test_no_orm_in_views.py
    test_no_business_logic_in_signals.py
    test_shared_has_no_business_logic.py
  performance/
    __init__.py
    test_query_count.py
    test_n_plus_one.py
    test_api_latency.py
```

**Unit tests** live in `<bounded_context>/tests/unit/` alongside the code they test.
**Integration tests** and **architecture tests** live in the top-level `tests/` directory.

### 16.2 Test Types

| Test Type | Scope | Tool | Location |
|-----------|-------|------|----------|
| Unit | Single class/function | pytest, unittest | `<context>/tests/unit/` |
| Integration | Multiple classes, real DB | pytest, Django TestCase | `<context>/tests/integration/` and `tests/integration/` |
| Architecture | Cross-cutting rules | pytest, import-linter | `tests/architecture/` |
| Mutation | Test quality | mutmut | CI pipeline |
| Performance | Latency, query count | pytest, Locust | `tests/performance/` |
| Contract | Public interface stability | pytest | `tests/contract/` |

### 16.3 Coverage Goals

| Layer | Target |
|-------|--------|
| Services | 95% |
| Utilities | 90% |
| Models | 85% |
| Views | 80% |
| Integration tests | All critical workflows |

Coverage is a guide, not a goal. 100% coverage of critical business logic is better than 90% coverage of trivial code.

### 16.4 Test Factories

All test data is created using Factory Boy factories defined in `tests/factories/`.

```python
# tests/factories/building_factory.py
import factory
from properties.models import Building
from core.models import User

class BuildingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Building

    owner = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"Building {n}")
    address = factory.Faker("address")
    city = "Mumbai"
    state = "Maharashtra"
    pincode = "400001"
    is_active = True
```

### 16.5 Architecture Tests

Architecture tests enforce rules that linters cannot:

```python
# tests/architecture/test_import_rules.py
import pytest
from importlinter import check_imports

class TestImportRules:
    def test_no_private_imports_across_contexts(self):
        # Fail if any bounded context imports a private module from another
        result = check_imports()
        assert result.violations == []

    def test_no_circular_dependencies(self):
        # Fail if any circular dependency exists
        result = check_dependencies()
        assert result.cycles == []

    def test_views_do_not_contain_business_logic(self):
        # Static analysis: views must not call ORM directly
        violations = find_orm_calls_in_views()
        assert violations == []

    def test_signals_do_not_contain_business_logic(self):
        # Static analysis: signals must not call external APIs
        violations = find_external_calls_in_signals()
        assert violations == []
```

---

## 17. Coding Standards

### 17.1 Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Django apps | Lowercase, singular, descriptive | `properties`, `notification` |
| Models | PascalCase, singular | `Building`, `RentRecord` |
| Services | PascalCase, suffix `Service` | `BuildingService`, `PaymentService` |
| Repositories | PascalCase, suffix `Repository` | `BuildingRepository` |
| Selectors | PascalCase, suffix `Selectors` | `BuildingSelectors` |
| Validators | snake_case, suffix `_validator` or descriptive | `validate_gstin`, `lease_validator` |
| Serializers | PascalCase, suffix `Serializer` | `BuildingSerializer` |
| Permissions | PascalCase, suffix `Permission` or descriptive | `IsPropertyOwner` |
| Exceptions | PascalCase, suffix `Error` | `ValidationError`, `PaymentError` |
| Constants | UPPER_SNAKE_CASE | `MAX_UPLOAD_SIZE`, `DEFAULT_PAGE_SIZE` |
| Functions/methods | snake_case | `create_building()`, `send_notification()` |
| Variables | snake_case | `building_name`, `tenant_id` |
| Protocols | PascalCase, descriptive | `PaymentGateway`, `NotificationChannel` |
| DTOs | PascalCase, suffix `Request`/`Response`/`DTO` | `CreateBuildingRequest`, `PaginatedResponse` |
| Files | snake_case | `building_service.py`, `payment_gateway.py` |

### 17.2 Import Order

Imports must be ordered as follows, with a blank line between groups:

```python
# 1. Standard library
import os
import re
from datetime import date
from decimal import Decimal
from typing import Protocol

# 2. Third-party libraries
import requests
from django.db import models
from django.db.models import QuerySet
from rest_framework import serializers
from rest_framework.views import APIView

# 3. First-party: shared
from shared.exceptions import ValidationError, PaymentError
from shared.protocols.payment_gateway import PaymentGateway
from shared.utils.formatting import format_currency

# 4. First-party: current bounded context
from properties.models import Building
from properties.repositories import BuildingRepository
from properties.services.building_service import BuildingService
from properties.serializers import BuildingSerializer

# 5. Local imports (within same module)
from .exceptions import PropertyError
from .constants import BuildingStatus
```

### 17.3 Services

- Services must be classes with explicit dependencies injected via `__init__`.
- No module-level singletons for services.
- Service methods must be small (under 50 lines preferred).
- Service methods must do one thing.
- Services must raise business exceptions, not return error codes.

```python
class BuildingService:
    def __init__(self, repository: BuildingRepository):
        self.repository = repository

    def create_building(self, owner, name, **kwargs) -> Building:
        # Business validation
        # Repository call
        # Return result
        pass
```

### 17.4 Repositories

- Repositories must be classes or classes with static methods.
- Repositories must return model instances or querysets, not DTOs.
- Repositories must not contain business logic.
- Repositories must not call services.

### 17.5 DTOs

- DTOs must be used at public interface boundaries.
- DTOs must not contain business logic.
- DTOs must be type-annotated.
- Prefer `dataclasses` or Pydantic models.

### 17.6 Interfaces (Protocols)

- Protocols must be defined in `shared/protocols/` or the bounded context's `interfaces/`.
- Protocols must define only method signatures.
- Protocols must have descriptive docstrings.
- Protocols must not contain implementations.

### 17.7 Dependency Injection

- Dependencies are injected via constructor parameters.
- No global service locators.
- No module-level singletons for services.
- In tests, dependencies are injected via mocking or test doubles.

```python
# Production
service = BuildingService(repository=BuildingRepository())

# Test
mock_repo = Mock(spec=BuildingRepository)
service = BuildingService(repository=mock_repo)
```

---

## 18. Architecture Rules

These 130+ rules are enforceable by code review, linters, and architecture tests.

### Views (HTTP Layer)

1. Views must never contain business logic.
2. Views must never query the ORM directly.
3. Views must never modify data without calling a service.
4. Views must never import repositories.
5. Views must never import private modules from other bounded contexts.
6. Views must never call external APIs.
7. Views must never contain SQL queries.
8. Views must never access Django settings directly.
9. Views must never set module-level state.
10. Views must always return DRF Response objects.
11. Views must always handle business exceptions and return appropriate HTTP status codes.
12. Views must never swallow exceptions silently.
13. Views must never log sensitive data (passwords, tokens, PII).
14. Views must use serializers for all input validation.
15. Views must not perform data transformation beyond serialization.
16. Views must not contain pagination logic (delegate to pagination classes).
17. Views must not contain filtering logic (delegate to filtersets or selectors).
18. Views must not contain ordering logic (delegate to filtersets or selectors).
19. Views must not contain search logic (delegate to selectors).
20. Views must not instantiate services directly (use dependency injection or factory).
21. Views must not contain retry logic.
22. Views must not contain fallback logic.
23. Views must not contain caching logic (delegate to services or decorators).
24. Views must not contain authentication logic beyond permission classes.
25. Views must not contain authorization logic beyond permission classes.
26. Views must never return raw model instances (always use serializers).
27. Views must never expose internal error messages to clients.
28. Views must never return stack traces in production.
29. Views must never trust client input.
30. Views must always validate Content-Type for write operations.

### Services (Business Logic Layer)

31. Services must never import views.
32. Services must never import HTTP request/response objects.
33. Services must never import Django settings directly.
34. Services must never contain SQL queries.
35. Services must never call external APIs directly (must use adapters).
36. Services must never import private modules from other bounded contexts.
37. Services must never modify data without validation.
38. Services must never swallow exceptions silently.
39. Services must never log sensitive data.
40. Services must always raise business exceptions for invalid states.
41. Services must never return error codes (use exceptions).
42. Services must be classes with injected dependencies.
43. Services must not use module-level singletons.
44. Services must not contain view-specific logic.
45. Services must not contain serializer logic.
46. Services must not contain model definition logic.
47. Services must not contain signal registration logic.
48. Services must not contain URL routing logic.
49. Services must not contain template rendering logic (unless domain-specific).
50. Services must not contain caching logic (delegate to cache services).
51. Services must not contain retry logic (delegate to adapters).
52. Services must not contain authentication logic.
53. Services must not contain authorization logic.
54. Services must be testable without Django test client.
55. Services must be testable without database (unit tests).
56. Services must be testable with mocked dependencies.
57. Services must not depend on request context.
58. Services must not depend on user session.
59. Services must not depend on thread-local state.
60. Services must not contain time-dependent logic without injecting time source.

### Repositories (Data Access Layer)

61. Repositories must never contain business logic.
62. Repositories must never call external APIs.
63. Repositories must never import services.
64. Repositories must never import views.
65. Repositories must never import private modules from other bounded contexts.
66. Repositories must never modify data in selectors (read-only).
67. Repositories must never return serialized data (return model instances or querysets).
68. Repositories must never contain business validation.
69. Repositories must never contain authorization logic.
70. Repositories must never contain authentication logic.
71. Repositories must never contain caching logic (delegate to services).
72. Repositories must never contain retry logic.
73. Repositories must never contain logging of business events (log in services).
74. Repositories must use `select_related` and `prefetch_related` for foreign keys.
75. Repositories must not execute raw SQL unless ORM is insufficient.
76. Repositories must not use `raw()` for simple queries.
77. Repositories must not use `.extra()`.
78. Repositories must not use `.raw()` with string formatting (SQL injection risk).
79. Repositories must not contain pagination logic (return querysets; pagination happens in views or selectors).
80. Repositories must not contain filtering logic beyond model field filters.

### Selectors (Read Model Projections)

81. Selectors must never modify data.
82. Selectors must never call external APIs.
83. Selectors must never import services.
84. Selectors must never import views.
85. Selectors must never contain business logic.
86. Selectors must never contain authorization logic.
87. Selectors must return DTOs, dictionaries, or model instances.
88. Selectors must not return serialized JSON.
89. Selectors must use `only()` and `defer()` for large models.
90. Selectors must use `annotate()` and `aggregate()` for computed fields.
91. Selectors must not use `select_related` on nullable foreign keys without `Prefetch`.
92. Selectors must not contain pagination logic (use DRF pagination).
93. Selectors must not contain caching logic (delegate to services).
94. Selectors must be deterministic: same inputs always produce same outputs.

### Models (ORM)

95. Models must never contain business workflows.
96. Models must never call external APIs.
97. Models must never send notifications.
98. Models must never contain view logic.
99. Models must never contain serializer logic.
100. Models must never import services.
101. Models must never import views.
102. Models must never import private modules from other bounded contexts.
103. Models must not contain complex query logic (use repositories).
104. Models must not contain complex business logic (use services).
105. Models must define `Meta` indexes for all filtered fields.
106. Models must define `Meta` constraints for business invariants.
107. Models must implement `clean()` for model-level validation.
108. Models must not override `save()` for business logic (use signals or services).
109. Models must not contain string formatting for display (use serializers or utilities).
110. Models must not contain currency conversion logic.

### Signals

111. Signals must never perform business operations directly.
112. Signals must never call external APIs with business payloads.
113. Signals must never modify unrelated models.
114. Signals must never import services for business logic.
115. Signals must never contain business validation.
116. Signals must never contain complex orchestration.
117. Signals must only trigger side effects: enqueue tasks, send notifications, update caches.
118. Signals must use `transaction.on_commit` for deferred work.
119. Signals must not contain retry logic.
120. Signals must not contain fallback logic.
121. Signals must be thin wrappers over service calls.
122. Signals must not import private modules from other bounded contexts.
123. Signals must not import views.
124. Signals must not import repositories.
125. Signals must not contain data transformation.

### Utilities

126. Utilities must never contain business logic.
127. Utilities must never import models.
128. Utilities must never import services.
129. Utilities must never import views.
130. Utilities must never contain side effects (no DB, no HTTP, no filesystem writes).
131. Utilities must never import Django settings directly.
132. Utilities must never import private modules from other bounded contexts.
133. Utilities must be pure functions or classes.
134. Utilities must raise `ValueError` for invalid input.
135. Utilities must not contain hidden dependencies.
136. Utilities must not contain global state.
137. Utilities must not contain caching logic.
138. Utilities must not contain logging of business events.

### Cross-Cutting Rules

139. No circular imports between bounded contexts.
140. No cross-context ORM writes.
141. No direct infrastructure access from domain bounded contexts.
142. No bare `except:` clauses.
143. No silent failures (empty except blocks).
144. No hardcoded credentials.
145. No PII in logs.
146. No stack traces in production responses.
147. No debug mode in production.
148. No `print()` statements (use logging).
149. No commented-out code.
150. No `# TODO` without ticket reference.
151. No `# FIXME` without ticket reference and owner.
152. No `# HACK` without ticket reference and owner.
153. No magic numbers (use named constants).
154. No hardcoded URLs.
155. No hardcoded file paths.
156. No implicit dependencies.
157. No global mutable state.
158. No module-level service instantiation.
159. No singleton pattern for services.
160. No service locator pattern.
161. No God objects (classes doing too much).
162. No anemic domain models (models with no behavior).
163. No shotgun surgery (one change touches many files).
164. No copy-paste code.
165. No duplicate implementations.
166. No dead code (unused functions, classes, imports).
167. No unused imports.
168. No unused variables.
169. No wildcard imports (`from module import *`).
170. No mutable default arguments.
171. No bare `except Exception:` without specific exception handling.

---

## 19. Example Flows

### 19.1 Create Property (Owner Creates Building)

**Actors:** Owner (authenticated user)
**Bounded contexts involved:** `accounts`, `properties`, `notification`
**Duration:** ~200ms (synchronous)

```
1. Client → POST /api/v1/buildings/
   Headers: Authorization: Bearer <token>
   Body: { "name": "Sunrise Apartments", "address": "...", "city": "Mumbai", ... }

2. Django URL Router
   → properties.urls
   → BuildingViewSet.create()

3. Authentication Middleware
   → core.services.AuthService.validate_token()
   → request.user = Owner

4. Permission Check
   → IsPropertyOwner.has_permission()
   → True (user is authenticated owner)

5. Validation
   → BuildingSerializer.is_valid()
   → Field validation: name required, address required
   → Object validation: unique building name per owner

6. Service Call
   → BuildingService.create_building(
       owner=request.user,
       name="Sunrise Apartments",
       ...
     )

7. Service Logic
   → Check if building name exists for owner (repository)
   → Create Building record (repository)
   → BuildingRepository.create(...)
   → Building saved to PostgreSQL

8. Signal
   → post_save signal for Building
   → Enqueue notification task (call_command)

9. Response
   → BuildingSerializer(building).data
   → 201 Created
   → { "id": 1, "name": "Sunrise Apartments", ... }

10. Background
    → send_building_created_notification task
    → notification.services.send_smart_alert(owner, "Building created")
```

### 19.2 Create Tenant and Generate Agreement

**Actors:** Owner
**Bounded contexts involved:** `properties`, `accounts`, `documents`, `notification`
**Duration:** ~2s (synchronous + async PDF)

```
1. Owner → POST /api/v1/leases/
   Body: { "building_id": 1, "tenant_email": "tenant@example.com", "start_date": "...", ... }

2. properties.views.LeaseViewSet.create()
   → IsPropertyOwner permission
   → LeaseSerializer validation

3. properties.services.LeaseService.create_lease()
   → Create Tenant profile (accounts service)
   → Create Lease record
   → Set lease status to "draft"

4. Signal: lease_created
   → Enqueue generate_agreement_pdf task

5. Response
   → 201 Created
   → { "id": 1, "status": "draft", ... }

6. Background Task: generate_agreement_pdf
   → documents.services.AgreementService.generate_agreement(lease_id)
   → documents.services.PDFGenerator.render(template="agreement", context={...})
   → WeasyPrint generates PDF
   → Upload to S3
   → Create Document record

7. Background Task: send_agreement_for_signature
   → documents.services.LeegalityClient.create_envelope(document_id, signers=[tenant, owner])
   → Leegality sends signing links to tenant and owner

8. Signal: document_generated
   → notification.services.send_smart_alert(tenant, "Agreement ready for signing")
```

### 19.3 Pay Rent (Tenant Submits Payment)

**Actors:** Tenant
**Bounded contexts involved:** `accounts`, `properties`, `finance`, `notification`
**Duration:** ~500ms

```
1. Tenant → POST /api/v1/rent-records/{id}/submit_payment/
   Body: { "utr": "UTR123456789", "screenshot": <file>, "note": "Paid via GPay" }

2. properties.views.RentRecordViewSet.submit_payment()
   → IsTenant permission
   → Validate UTR format

3. properties.services.RentService.submit_payment()
   → Update rent record status to "submitted"
   → Save UTR, screenshot, note
   → Record submission timestamp

4. Signal: rent_payment_submitted
   → notification.services.send_smart_alert(
       user_id=owner.user_id,
       message="Tenant submitted rent payment. Please verify.",
       context={"rent_record_id": rent_record.id, "utr": rent_record.utr},
     )

5. Response
   → 200 OK
   → { "status": "submitted", "message": "Payment submitted for verification" }

6. Owner verifies payment (manual)
   → Owner sees notification
   → Owner checks UTR in bank app
   → Owner clicks Approve or Reject

7. Owner → POST /api/v1/rent-records/{id}/approve_payment/

8. finance.services.RentService.approve_payment()
   → Update rent record status to "paid"
   → Create finance record
   → Generate rent receipt PDF (documents service)
   → Send receipt to tenant (notification service)

9. Response
   → 200 OK
```

### 19.4 Send Notification

**Actors:** System
**Bounded contexts involved:** `notification`
**Duration:** ~100ms

```
1. Caller → notification.services.communication.send_smart_alert(user_id, message, context)

2. notification.services.NotificationOrchestrator.send()
   → Determine user notification preferences
   → Select channels (email, push, in-app)
   → For each channel:
     a. Get channel adapter
     b. Render template
     c. Send via adapter
     d. Record delivery attempt

3. Channel Adapters
   → EmailAdapter.send() → SMTP/SES
   → FCMAdapter.send() → Firebase
   → InAppAdapter.send() → Database

4. Response
   → NotificationResult(success=True, channels_sent=["email", "push", "inapp"])

5. Failure handling
   → If email fails: log warning, try next channel
   → If all channels fail: raise NotificationError
```

### 19.5 Generate PDF

**Actors:** System
**Bounded contexts involved:** `documents`
**Duration:** ~1-2s

```
1. Caller → documents.services.PDFGenerator.generate(template_name, context)

2. PDFGenerator
   → Load template from documents/templates/pdf/{template_name}.html
   → Render template with context (Jinja2 or Django templates)
   → Call WeasyPrint to convert HTML to PDF
   → Return PDF bytes or file path

3. Caller
   → Upload PDF to S3
   → Create Document record
   → Return download URL
```

### 19.6 AI Assistant Request

**Actors:** Tenant or Owner
**Bounded contexts involved:** `assistant`, `properties`, `documents`
**Duration:** ~2-5s (includes LLM latency)

```
1. User → POST /api/v1/assistant/chat/
   Body: { "message": "I need a rent agreement for my new tenant", "session_id": "..." }

2. assistant.views.ChatViewSet.create()
   → IsAuthenticated permission
   → ChatRequestSerializer validation

3. assistant.services.ChatbotService.process_message()
   → Load chat history
   → IntentService.extract_intent(message)
   → Intent: "generate_agreement"

4. ActionService.execute_action(intent="generate_agreement", context={...})
   → Call properties.services.LeaseService.create_lease_draft(...)
   → Call documents.services.AgreementService.generate_agreement(...)
   → Return result to user

5. Response
   → { "response": "I've generated a draft agreement. Please review and sign.", "actions": [...] }
```

---

## 20. Architecture Decision Summary

### 20.1 Why This Architecture Was Chosen

This architecture was chosen to balance competing pressures:

| Pressure | Decision | Rationale |
|----------|----------|-----------|
| Development velocity | Modular monolith | Single deployment, no network overhead, fast debugging |
| Long-term maintainability | Bounded contexts by business capability | Clear ownership, easy to reason about |
| Operational simplicity | Local memory cache, management commands | No Redis/Celery in Year 1, reduced infrastructure |
| Testability | Service layer, dependency injection, protocols | Easy to mock, easy to test in isolation |
| Future readiness | Clean public interfaces, adapter pattern | Extraction to microservices possible without rewriting |
| Consistency | 130+ enforceable architecture rules | Automated and manual enforcement prevents drift |
| Security | JWT, RBAC, input validation, secrets management | Defense in depth |
| Performance | Query optimization, caching, pagination | Handles expected scale with room to grow |

### 20.2 Tradeoffs

| Tradeoff | Accepted Risk | Mitigation |
|----------|--------------|------------|
| Monolith scaling limits | Cannot scale individual contexts independently | Profile before extracting; extract only proven bottlenecks |
| Shared database | ACID transactions across all contexts, but single point of failure | Read replicas, regular backups, point-in-time recovery |
| No message broker in Year 1 | Cannot do true async event-driven architecture | Use management commands and signals; upgrade to Celery in Stage 2 |
| Local memory cache | Not shared across processes, not persistent | Evaluate Redis when multi-process deployment is needed |
| Strong consistency | No eventual consistency patterns | Acceptable for Year 1; add event sourcing when needed |

### 20.3 Future Evolution

**Year 1:**
- Complete refactoring to bounded contexts.
- Consolidate duplicate services.
- Establish architecture tests and CI enforcement.
- Achieve 90%+ test coverage on business logic.

**Stage 2 (Post-Year 1):**
- Enable payment gateways (Razorpay/Cashfree).
- Add message broker (Redis/RabbitMQ) and Celery.
- Enable WhatsApp/SMS notifications.
- Add OpenSearch for full-text search.
- Extract `notification` to separate service if volume justifies.

**Stage 3 (Scale):**
- Extract `analytics` to separate service with dedicated data store.
- Extract `documents` for PDF generation scaling.
- Introduce event sourcing for audit and replay.
- Add multi-region deployment.

### 20.4 What Must Never Change

These architectural decisions are permanent and must not be reversed without a formal ADR and Principal Architect approval:

1. **Business capability organization.** Bounded contexts must remain organized by business capability, not technical layer.
2. **Views are thin.** Business logic must never return to views.
3. **Signals trigger events, not business logic.** This rule must be enforced forever.
4. **Public interfaces are contracts.** Breaking a public interface requires a formal deprecation process.
5. **No circular dependencies.** This must be maintained through all future changes.
6. **Single source of truth.** Duplicate implementations must never be reintroduced.
7. **Dependency direction.** Dependencies must always flow from business to infrastructure, never reverse.
8. **Zero breaking changes during migration.** Compatibility wrappers are mandatory.
9. **Shared has no business logic.** This must be enforced permanently.
10. **Testability is non-negotiable.** Code that cannot be tested easily must be refactored.

---

*Document ratified by the Principal Software Architect. This is the permanent target architecture for the RentSecure backend. All refactoring, development, and design decisions must align with this document.*
