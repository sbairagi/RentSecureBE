# Bounded Contexts

This document defines every business domain in RentSecure, their responsibilities, ownership, dependencies, and APIs.

---

## Context Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RentSecure Platform                         │
│                                                                     │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐                  │
│  │ Identity  │    │Subscription│   │  Property │                  │
│  │           │───▶│            │───▶│           │                  │
│  └───────────┘    └───────────┘    └─────┬─────┘                  │
│       ▲                  ▲                │                        │
│       │                  │                ▼                        │
│  ┌────┴────┐       ┌────┴────┐     ┌──────┴──────┐               │
│  │ Referral│       │ Finance │     │     Rent    │                │
│  │         │       │         │     │             │                │
│  └─────────┘       └─────────┘     └──────┬──────┘               │
│                                            │                       │
│  ┌───────────┐    ┌───────────┐           │                       │
│  │Notification│◀──│ Documents │◀──────────┘                       │
│  │            │    │           │                                   │
│  └───────────┘    └───────────┘                                   │
│       ▲                                                           │
│       │                                                           │
│  ┌────┴──────────┐                                               │
│  │  AI Assistant │                                               │
│  │               │                                               │
│  └───────────────┘                                               │
│                                                                   │
│  ┌──────────────┐                                                │
│  │   Dashboard  │ (read-only, cross-cutting)                      │
│  └──────────────┘                                                │
└───────────────────────────────────────────────────────────────────┘
```

---

## 1. Identity Context

**Module:** `apps/identity/`
**Ownership:** Platform Team
**Maturity:** Stable

### Responsibilities
- User registration and authentication
- OTP generation and verification
- Password management (reset, change)
- Role-based access control (RBAC)
- Permission enforcement
- User profile management

### Owned Data
- `User` account (credentials, status, roles)
- `OTPToken` (verification codes)
- `Permission` and `Group` definitions
- `UserProfile` (personal information)

### Does NOT Own
- Subscription plans or billing
- Bank account details
- Property data
- Payment records

### Public APIs
| Interface | Description |
|-----------|-------------|
| `IdentityService.authenticate(email, password)` | Returns user or raises `InvalidCredentials` |
| `IdentityService.verify_otp(user_id, code)` | Marks user as verified |
| `IdentityService.has_permission(user, permission)` | Permission check |
| `IdentityService.get_user(user_id)` | User profile |

### Internal APIs
- `UserRepository`
- `PermissionRepository`
- `OTPService`

### Dependencies
- **Depends on:** Shared (types, exceptions)
- **Depended on by:** All other contexts (everyone needs identity)

---

## 2. Subscription Context

**Module:** `apps/subscription/`
**Ownership:** Platform Team
**Maturity:** Stable

### Responsibilities
- Subscription plan management
- User subscription lifecycle
- Add-on purchase and activation
- Usage limit enforcement
- Feature flag evaluation
- Billing cycle management

### Owned Data
- `SubscriptionPlan`
- `Subscription`
- `AddOn`
- `UsageRecord`
- `FeatureFlag`

### Does NOT Own
- Payment processing (delegates to Payment context)
- User authentication
- Property-specific features

### Public APIs
| Interface | Description |
|-----------|-------------|
| `SubscriptionService.get_active_subscription(user_id)` | Current plan |
| `SubscriptionService.can_access_feature(user_id, feature)` | Feature gate |
| `SubscriptionService.record_usage(user_id, feature, amount)` | Meter usage |
| `SubscriptionService.upgrade_plan(user_id, plan_id)` | Plan change |

### Internal APIs
- `SubscriptionRepository`
- `PlanRepository`
- `UsageRepository`

### Dependencies
- **Depends on:** Identity (user exists), Shared
- **Depended on by:** All feature-bearing contexts

---

## 3. Property Context

**Module:** `apps/property/`
**Ownership:** Product Team
**Maturity:** Active Development

### Responsibilities
- Building and unit management
- Renter profile management
- Rent record creation and tracking
- Caretaker assignment and management
- Extra charge management
- Property image and document storage
- Occupancy tracking

### Owned Data
- `Building`
- `Unit`
- `UnitImage`
- `Renter`
- `RentRecord`
- `Caretaker`
- `ExtraCharge`
- `PropertyTaxRecord`

### Does NOT Own
- Payment processing
- Document PDF generation (delegates to Documents)
- Notification dispatch
- Tax compliance (delegates to Finance)

### Public APIs
| Interface | Description |
|-----------|-------------|
| `PropertyService.create_building(owner_id, data)` | New building |
| `PropertyService.add_unit(building_id, data)` | New unit |
| `PropertyService.assign_renter(unit_id, renter_id)` | Renter assignment |
| `PropertyService.generate_rent_records(month)` | Monthly rent generation |
| `PropertyService.get_rent_dashboard(owner_id)` | Owner analytics |

### Internal APIs
- `BuildingRepository`
- `UnitRepository`
- `RenterRepository`
- `RentRecordRepository`
- `CaretakerRepository`

### Dependencies
- **Depends on:** Identity, Subscription, Documents, Notification
- **Depended on by:** Rent, Finance, Dashboard

---

## 4. Rent Context

**Module:** `apps/rent/`
**Ownership:** Product Team
**Maturity:** Active Development

### Responsibilities
- Rent amount calculation
- Rent record lifecycle management
- Late fee calculation
- Payment request initiation
- Agreement draft creation
- Rent receipt tracking

### Owned Data
- `RentCycle`
- `LateFeePolicy`
- `PaymentRequest`
- `AgreementDraft`

### Does NOT Own
- Payment gateway processing (delegates to Payment)
- Receipt PDF generation (delegates to Documents)
- Notification dispatch (delegates to Notification)
- Rent record source data (reads from Property)

### Public APIs
| Interface | Description |
|-----------|-------------|
| `RentService.calculate_rent(unit_id, month)` | Rent amount |
| `RentService.apply_late_fee(rent_id)` | Late fee calculation |
| `RentService.initiate_payment(rent_id, method)` | Create payment request |
| `RentService.generate_agreement(unit_id, template)` | Draft agreement |

### Internal APIs
- `RentCycleRepository`
- `LateFeePolicyRepository`
- `AgreementDraftRepository`

### Dependencies
- **Depends on:** Property (unit data), Payment, Documents, Notification, Finance
- **Depended on by:** Dashboard

---

## 5. Payment Context

**Module:** `apps/payment/`
**Ownership:** Platform Team
**Maturity:** Stable (Manual UPI), Stage 2 (Gateway)

### Responsibilities
- Payment initiation and tracking
- Payment verification (manual and automated)
- Refund processing
- Payout management (future)
- Idempotency enforcement
- Payment webhook handling (future)

### Owned Data
- `Payment`
- `PaymentTransaction`
- `Refund`
- `Payout` (future)

### Does NOT Own
- Payment method storage (UPI ID is in Property/Identity)
- Receipt generation (delegates to Documents)
- Notification dispatch

### Public APIs
| Interface | Description |
|-----------|-------------|
| `PaymentService.submit_payment(tenant_id, rent_id, utr)` | Submit manual payment |
| `PaymentService.verify_payment(payment_id, owner_id)` | Owner approval |
| `PaymentService.get_payment_history(user_id)` | Payment history |
| `PaymentService.process_refund(payment_id, reason)` | Refund initiation |

### Internal APIs
- `PaymentRepository`
- `TransactionRepository`

### Dependencies
- **Depends on:** Identity, Rent, Documents, Notification
- **Depended on by:** Finance, Dashboard

### Adapters
- `ManualPaymentAdapter` (Year 1, active)
- `RazorpayAdapter` (Stage 2, disabled)
- `CashfreeAdapter` (Stage 2, disabled)

---

## 6. Notification Context

**Module:** `apps/notification/`
**Ownership:** Platform Team
**Maturity:** Stable

### Responsibilities
- Notification preference management
- Multi-channel notification dispatch
- Template rendering per channel
- Delivery tracking
- Notification history

### Owned Data
- `Notification`
- `NotificationPreference`
- `NotificationTemplate`
- `NotificationChannel`

### Does NOT Own
- Business rules for when to notify (decided by domain contexts)
- Template content (provided by domain contexts)

### Public APIs
| Interface | Description |
|-----------|-------------|
| `NotificationService.send(user_id, event, context)` | Send notification |
| `NotificationService.get_preferences(user_id)` | User preferences |
| `NotificationService.update_preferences(user_id, prefs)` | Update preferences |
| `NotificationService.get_history(user_id)` | Notification history |

### Internal APIs
- `NotificationRepository`
- `PreferenceRepository`
- `TemplateRepository`

### Dependencies
- **Depends on:** Identity, Shared
- **Depended on by:** All contexts

### Adapters
- `EmailAdapter` (active)
- `FCMAdapter` (active)
- `InAppAdapter` (active)
- `WhatsAppAdapter` (disabled, Stage 2)
- `SMSAdapter` (disabled, Stage 2)

---

## 7. Document Context

**Module:** `apps/document/`
**Ownership:** Platform Team
**Maturity:** Stable

### Responsibilities
- PDF generation from templates
- Document storage and retrieval
- Template management
- Digital signature integration (future)
- Document metadata tracking

### Owned Data
- `Document`
- `DocumentTemplate`
- `DocumentStorage`

### Does NOT Own
- Business rules for document content (provided by domain contexts)
- Template design (provided by domain contexts)

### Public APIs
| Interface | Description |
|-----------|-------------|
| `DocumentService.generate(template_id, context)` | Generate PDF |
| `DocumentService.store(document, owner_id)` | Store document |
| `DocumentService.get(user_id, document_id)` | Retrieve document |
| `DocumentService.get_templates(context)` | Available templates |

### Internal APIs
- `DocumentRepository`
- `TemplateRepository`

### Dependencies
- **Depends on:** Identity, Shared
- **Depended on by:** Rent, Payment, Property, Finance

---

## 8. Finance Context

**Module:** `apps/finance/`
**Ownership:** Finance Team
**Maturity:** Stable

### Responsibilities
- Tax record management
- CA profile management
- Tax filing status tracking
- Financial report generation
- GST compliance (future)
- Expense tracking

### Owned Data
- `TaxRecord`
- `CAProfile`
- `TaxFiling`
- `ExpenseRecord`
- `FinancialReport`

### Does NOT Own
- Payment processing (delegates to Payment)
- Rent record data (reads from Property/Rent)

### Public APIs
| Interface | Description |
|-----------|-------------|
| `FinanceService.create_tax_record(owner_id, data)` | New tax record |
| `FinanceService.assign_ca(owner_id, ca_id)` | CA assignment |
| `FinanceService.generate_report(owner_id, period)` | Financial report |
| `FinanceService.get_compliance_status(owner_id)` | Compliance check |

### Internal APIs
- `TaxRecordRepository`
- `CAProfileRepository`
- `ReportRepository`

### Dependencies
- **Depends on:** Identity, Property, Payment, Document
- **Depended on by:** Dashboard

---

## 9. Referral Context

**Module:** `apps/referral/`
**Ownership:** Growth Team
**Maturity:** Stable

### Responsibilities
- Referral code generation and validation
- Bonus tracking
- Reward distribution
- Referral analytics

### Owned Data
- `ReferralCode`
- `ReferralBonus`
- `ReferralReward`

### Does NOT Own
- Payment processing (delegates to Payment)
- User data (reads from Identity)

### Public APIs
| Interface | Description |
|-----------|-------------|
| `ReferralService.generate_code(user_id)` | Create referral code |
| `ReferralService.validate_code(code)` | Validate code |
| `ReferralService.apply_referral(referrer_id, referee_id)` | Apply referral |
| `ReferralService.get_bonuses(user_id)` | Bonus history |

### Internal APIs
- `ReferralCodeRepository`
- `ReferralBonusRepository`

### Dependencies
- **Depends on:** Identity, Payment (for reward distribution)
- **Depended on by:** Dashboard

---

## 10. AI Assistant Context

**Module:** `apps/ai/`
**Ownership:** Platform Team
**Maturity:** Experimental

### Responsibilities
- Chatbot intent processing
- AI-powered document analysis
- Smart rent suggestions
- Anomaly detection
- Prompt management
- AI governance and safety

### Owned Data
- `ChatSession`
- `ChatMessage`
- `AIPrompt`
- `AIAnalysisResult`

### Does NOT Own
- Business domain data (reads from other contexts)
- User authentication

### Public APIs
| Interface | Description |
|-----------|-------------|
| `AIService.chat(user_id, message, session_id)` | Process chat message |
| `AIService.analyze_document(document_id)` | AI document analysis |
| `AIService.suggest_rent(unit_id, comparables)` | Rent suggestion |
| `AIService.detect_anomaly(payment_id)` | Fraud detection |

### Internal APIs
- `ChatSessionRepository`
- `PromptRepository`

### Dependencies
- **Depends on:** Identity, Property, Rent, Payment, Document (read-only)
- **Depended on by:** Dashboard

---

## 11. Dashboard Context

**Module:** `apps/dashboard/`
**Ownership:** Platform Team
**Maturity:** Stable

### Responsibilities
- Analytics aggregation
- Report generation
- Dashboard data composition
- Metric calculation
- Data export

### Owned Data
- `DashboardMetric` (cached/computed)
- `ReportJob`

### Does NOT Own
- Source data models (reads from all other contexts)
- Business rules

### Public APIs
| Interface | Description |
|-----------|-------------|
| `DashboardService.get_owner_metrics(owner_id)` | Owner dashboard data |
| `DashboardService.get_tenant_metrics(tenant_id)` | Tenant dashboard data |
| `DashboardService.generate_report(user_id, type)` | Generate report |
| `DashboardService.get_platform_metrics()` | Admin analytics |

### Internal APIs
- `MetricRepository`
- `ReportRepository`

### Dependencies
- **Depends on:** All contexts (read-only, via services)
- **Depended on by:** None (leaf context)

---

## Context Interaction Summary

| Source Context | Target Context | Communication Method |
|----------------|----------------|---------------------|
| Identity | All | Direct (User exists check) |
| Subscription | All | Feature flag check |
| Property | Rent | Domain Event: `RentGenerated` |
| Property | Dashboard | Read via service |
| Rent | Payment | Direct service call |
| Rent | Notification | Domain Event: `RentDue` |
| Rent | Documents | Direct service call |
| Payment | Notification | Domain Event: `PaymentSubmitted` |
| Payment | Finance | Domain Event: `PaymentRecorded` |
| Payment | Documents | Direct service call |
| Notification | All | Read via service |
| Documents | All | Direct service call |
| Finance | Dashboard | Read via service |
| Referral | Payment | Direct service call |
| AI | All | Read via service |
| All | Dashboard | Read via service |

---

*Each bounded context is independently deployable when service extraction occurs. Internal structure changes do not affect other contexts as long as public APIs remain stable.*
