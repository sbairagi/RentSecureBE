# Module Boundaries

This document defines the bounded contexts and module boundaries for RentSecureBE.

## Current Modules

The current modular monolith consists of these Django apps:

| Module | Purpose | Bounded Context |
|--------|---------|-----------------|
| `core` | Authentication, subscriptions, bank details, OTP | Identity & Subscription |
| `properties` | Buildings, units, renters, rent records, caretakers | Property & Rent |
| `finance` | Tax management, CA profiles | Finance & Compliance |
| `notification` | Push, email, WhatsApp, voice notifications | Communication |
| `documents` | Document generation and management | Documents |
| `smartbot` | AI chatbot and smart features | AI Assistant |
| `ai_assistant` | AI-powered assistant services | AI Services |
| `referral_and_earn` | Referral program | Growth & Referrals |
| `dashboard` | Analytics and reporting | Analytics |
| `rentsecure_be` | Project configuration and services | Infrastructure |

## Bounded Context Definitions

### Identity Context
**Module**: `core` (authentication portion)

**Owns**:
- User authentication
- OTP verification
- Password management
- User groups and permissions

**Does NOT own**:
- Subscription plans
- Bank details
- Usage limits

**Future**: Extract to `identity/` bounded context

### Subscription Context
**Module**: `core` (subscription portion)

**Owns**:
- Subscription plans
- User subscriptions
- Add-on purchases
- Usage limits
- Feature availability

**Does NOT own**:
- Authentication
- Bank details
- Payment processing

**Future**: Extract to `subscription/` bounded context

### Property Context
**Module**: `properties`

**Owns**:
- Buildings
- Units
- Unit images
- Renters
- Rent records
- Caretakers
- Extra charges
- Property tax records

**Does NOT own**:
- Payment processing
- Notification dispatch
- Document generation

**Future**: Maintain as `properties/` bounded context

### Finance Context
**Module**: `finance`

**Owns**:
- Tax records
- CA profiles
- Tax notifications
- Financial reports

**Does NOT own**:
- Payment processing
- Rent records

**Future**: Maintain as `finance/` bounded context

### Notification Context
**Module**: `notification`

**Owns**:
- Notification preferences
- Push notifications
- Email notifications
- WhatsApp notifications
- Voice notes

**Does NOT own**:
- Business rules for when to notify
- Template content (owned by domain contexts)

**Future**: Maintain as `notification/` bounded context

### Document Context
**Module**: `documents`

**Owns**:
- PDF generation
- Document templates
- Document storage

**Does NOT own**:
- Business rules for document content
- User-specific document data

**Future**: Maintain as `documents/` bounded context

### AI Context
**Module**: `smartbot`, `ai_assistant`

**Owns**:
- Chatbot logic
- AI assistant features
- Prompt management
- AI governance

**Does NOT own**:
- Business domain data
- User authentication

**Future**: Consolidate into `ai/` bounded context

### Referral Context
**Module**: `referral_and_earn`

**Owns**:
- Referral codes
- Bonus tracking
- Referral rewards

**Does NOT own**:
- User authentication
- Payment processing

**Future**: Maintain as `referral/` bounded context

### Dashboard Context
**Module**: `dashboard`

**Owns**:
- Analytics aggregation
- Report generation
- Dashboard data

**Does NOT own**:
- Source data models
- Business rules

**Future**: Maintain as `dashboard/` bounded context

## Boundary Rules

1. **No Cross-Context Model Imports**: A model in one context must never directly import a model from another context
2. **Service Interfaces Only**: Cross-context communication happens through service interfaces defined in `shared/`
3. **Domain Events**: Use domain events for eventual consistency between contexts
4. **Explicit Contracts**: Each context exposes explicit contracts for other contexts to consume
5. **No Leaky Abstractions**: Internal implementation details of a context must not be exposed outside

## Migration Strategy

1. **Phase 0-5**: Establish shared foundation and document boundaries
2. **Phase 6-12**: Extract each bounded context into its own package structure
3. **Phase 13+**: Enforce boundaries with import-linter contracts and architecture tests

## Anti-Patterns to Avoid

1. **God Modules**: No module should own everything
2. **Circular Dependencies**: No circular imports between contexts
3. **Shared Models**: Models must not be shared across contexts
4. **Leaky Abstractions**: Internal details must not be exposed
5. **Cross-Context Queries**: No direct database queries across context boundaries
