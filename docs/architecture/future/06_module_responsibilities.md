# Module Responsibilities

This document defines what belongs in each bounded context app and what does not.

---

## apps/identity/

### Domain Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| User entity (credentials, status) | Subscription data |
| OTP token entity | Bank account details |
| Permission entity | Property data |
| Role entity | Payment records |
| Domain events: `UserRegistered`, `UserVerified`, `PasswordChanged` | Notification templates |

### Application Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| `AuthenticationService` | Payment processing |
| `RegistrationService` | Notification dispatch |
| `OTPService` | Document generation |
| `PermissionService` | Business logic from other contexts |

### Infrastructure Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| User Django model | Models from other apps |
| OTPToken Django model | Payment models |
| Permission/Group models | Finance models |
| Token-based auth adapters | Direct business logic |

### Interfaces Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Login/Register views | Payment views |
| Auth serializers | Finance serializers |
| Token permissions | Cross-context permissions |
| Auth URLs | URLs from other apps |

---

## apps/subscription/

### Domain Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| SubscriptionPlan entity | Payment processing |
| Subscription entity | User authentication |
| AddOn entity | Property data |
| FeatureFlag entity | Notification content |
| Domain events: `SubscriptionActivated`, `SubscriptionExpired`, `AddOnPurchased` | |

### Application Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| `SubscriptionService` | Auth workflows |
| `PlanService` | Payment workflows |
| `UsageService` | Property workflows |
| `FeatureFlagService` | Direct model queries from other apps |

### Infrastructure Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| SubscriptionPlan Django model | Payment models |
| Subscription Django model | User models |
| AddOn Django model | Rent models |
| UsageRecord Django model | |

### Interfaces Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Subscription views | Payment views |
| Plan serializers | Auth serializers |
| Feature permissions | Cross-context views |

---

## apps/property/

### Domain Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Building entity | Payment processing |
| Unit entity | Document generation logic |
| UnitImage entity | Notification dispatch |
| Renter entity | Tax compliance |
| RentRecord entity | Referral logic |
| Domain events: `BuildingCreated`, `UnitAdded`, `RenterAssigned`, `RentRecordGenerated` | |

### Application Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| `PropertyService` | Payment gateway calls |
| `UnitService` | PDF generation |
| `RenterService` | Tax calculations |
| `RentRecordService` | Direct notification sends |

### Infrastructure Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Building Django model | Payment models |
| Unit Django model | Finance models |
| UnitImage Django model | |
| Renter Django model | |
| RentRecord Django model | |
| `BuildingRepository` | |
| `UnitRepository` | |
| `RenterRepository` | |
| `RentRecordRepository` | |

### Interfaces Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Property views | Payment views |
| Property serializers | Finance serializers |
| Property filters | Cross-context filters |

---

## apps/rent/

### Domain Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| RentCycle entity | Payment gateway logic |
| LateFeePolicy entity | Document template definitions |
| AgreementDraft entity | Notification channel logic |
| Domain events: `RentCalculated`, `LateFeeApplied`, `AgreementCreated` | |

### Application Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| `RentCalculationService` | Direct payment processing |
| `LateFeeService` | PDF generation |
| `AgreementService` | Direct notification dispatch |

### Infrastructure Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| RentCycle Django model | Payment models |
| LateFeePolicy Django model | Document storage models |
| AgreementDraft Django model | |

### Interfaces Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Rent views | Payment views |
| Rent serializers | Finance serializers |

---

## apps/payment/

### Domain Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Payment entity | UPI ID storage (belongs to property/identity) |
| PaymentTransaction entity | Document template logic |
| Refund entity | Notification channel logic |
| Domain events: `PaymentSubmitted`, `PaymentVerified`, `PaymentRejected`, `RefundProcessed` | |

### Application Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| `PaymentService` | PDF generation |
| `RefundService` | Tax calculations |
| `WebhookService` (future) | Property management |

### Infrastructure Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Payment Django model | Property models |
| PaymentTransaction Django model | Finance models |
| `PaymentRepository` | |
| `ManualPaymentAdapter` (Year 1) | |
| `RazorpayAdapter` (Stage 2, disabled) | |
| `CashfreeAdapter` (Stage 2, disabled) | |

### Interfaces Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Payment views | Property views |
| Payment serializers | Finance serializers |
| Webhook handlers (future) | |

---

## apps/notification/

### Domain Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Notification entity | Business rules for when to notify |
| NotificationPreference entity | Template content (provided by domains) |
| NotificationTemplate entity | Payment processing |
| Domain events: `NotificationSent`, `NotificationFailed` | |

### Application Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| `NotificationService` | Direct model manipulation from other apps |
| `PreferenceService` | Payment workflows |
| `TemplateService` | PDF generation |

### Infrastructure Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Notification Django model | Property models |
| NotificationPreference Django model | Finance models |
| `EmailAdapter` | |
| `FCMAdapter` | |
| `InAppAdapter` | |
| `WhatsAppAdapter` (disabled) | |
| `SMSAdapter` (disabled) | |

### Interfaces Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Notification views | Payment views |
| Preference serializers | Finance serializers |

---

## apps/document/

### Domain Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Document entity | Business rules for document content |
| DocumentTemplate entity | Payment processing |
| Domain events: `DocumentGenerated`, `DocumentStored` | |

### Application Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| `DocumentService` | Notification dispatch |
| `TemplateService` | Tax calculations |

### Infrastructure Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Document Django model | Payment models |
| DocumentTemplate Django model | |
| PDF generation adapter (WeasyPrint) | |
| S3 storage adapter | |

### Interfaces Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Document views | Payment views |
| Template serializers | |

---

## apps/finance/

### Domain Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| TaxRecord entity | Payment gateway logic |
| CAProfile entity | Notification content |
| TaxFiling entity | Document generation |
| ExpenseRecord entity | Property management |
| Domain events: `TaxRecordCreated`, `CAProfileUpdated` | |

### Application Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| `TaxService` | PDF generation |
| `CAService` | Direct notification sends |
| `ReportService` | Payment processing |

### Infrastructure Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| TaxRecord Django model | Payment models |
| CAProfile Django model | |
| `TaxRecordRepository` | |
| `CAProfileRepository` | |

### Interfaces Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Finance views | Payment views |
| Finance serializers | |

---

## apps/referral/

### Domain Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| ReferralCode entity | Payment processing logic |
| ReferralBonus entity | Notification content |
| Domain events: `ReferralCodeGenerated`, `ReferralApplied`, `BonusAwarded` | |

### Application Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| `ReferralService` | PDF generation |
| `BonusService` | Direct notification dispatch |

### Infrastructure Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| ReferralCode Django model | Payment models |
| ReferralBonus Django model | |

### Interfaces Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Referral views | Payment views |
| Referral serializers | |

---

## apps/ai/

### Domain Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| ChatSession entity | Business domain data (reads from other contexts) |
| ChatMessage entity | User authentication logic |
| AIPrompt entity | Payment processing |
| Domain events: `ChatMessageProcessed`, `DocumentAnalyzed`, `AnomalyDetected` | |

### Application Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| `ChatService` | Direct database writes to other apps |
| `DocumentAnalysisService` | Notification dispatch |
| `RentSuggestionService` | PDF generation |

### Infrastructure Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| ChatSession Django model | Payment models |
| ChatMessage Django model | |
| `ChatSessionRepository` | |
| LLM adapter (OpenAI/Anthropic) | |

### Interfaces Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Chat views | Payment views |
| Chat serializers | |

---

## apps/dashboard/

### Domain Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| DashboardMetric entity (computed) | Source data models |
| ReportJob entity | Business rules from other contexts |

### Application Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| `DashboardService` | Direct database queries to other apps |
| `AnalyticsService` | Business logic from other contexts |
| `ReportService` | |

### Infrastructure Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| DashboardMetric Django model (cached) | |
| ReportJob Django model | |

### Interfaces Layer
| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Dashboard views | Payment views |
| Dashboard serializers | |

---

## shared/

| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Base exception classes | Any app-specific logic |
| Domain event base class | Django models |
| Abstract interface definitions | Business services |
| Generic utilities (date, string, math) | Cross-app imports |
| Shared enumerations | |

---

## platform/

| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Cache adapters | Business logic |
| Storage adapters | Domain models |
| Search adapters | Application services |
| Queue adapters | Presentation layer |
| Event bus | |

---

## config/

| What Belongs | What Does NOT Belong |
|--------------|---------------------|
| Django settings | Business logic |
| URL configuration | Models |
| WSGI/ASGI | Services |

---

*This document is the reference for code reviews. Any PR that places code in the wrong module must be rejected.*
