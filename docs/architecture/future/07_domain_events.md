# Domain Events

This document defines all domain events in the RentSecure platform, their publishers, subscribers, payloads, and purposes.

---

## Event Schema

All domain events inherit from the base `DomainEvent` class:

```python
class DomainEvent:
    event_id: UUID
    occurred_at: datetime
    aggregate_id: UUID
    aggregate_type: str
    event_type: str
    version: int = 1
    payload: dict
    metadata: dict
```

---

## Identity Events

### UserRegistered
| Field | Value |
|-------|-------|
| **Publisher** | `IdentityService.register()` |
| **Subscribers** | Notification (welcome email), Subscription (create free plan) |
| **Payload** | `user_id`, `email`, `name`, `role` |
| **Purpose** | Trigger onboarding workflow after user registration |

### UserVerified
| Field | Value |
|-------|-------|
| **Publisher** | `IdentityService.verify_otp()` |
| **Subscribers** | Notification (verification success), Subscription (activate trial) |
| **Payload** | `user_id`, `verified_at` |
| **Purpose** | Unlock platform features after email/phone verification |

### PasswordChanged
| Field | Value |
|-------|-------|
| **Publisher** | `IdentityService.change_password()` |
| **Subscribers** | Notification (security alert) |
| **Payload** | `user_id`, `changed_at` |
| **Purpose** | Security monitoring and user notification |

### UserSuspended
| Field | Value |
|-------|-------|
| **Publisher** | `IdentityService.suspend_user()` |
| **Subscribers** | Subscription (deactivate), Notification (account suspended) |
| **Payload** | `user_id`, `reason`, `suspended_at` |
| **Purpose** | Disable all platform access and notify user |

---

## Subscription Events

### SubscriptionActivated
| Field | Value |
|-------|-------|
| **Publisher** | `SubscriptionService.activate_subscription()` |
| **Subscribers** | Notification (welcome), Property (unlock features) |
| **Payload** | `user_id`, `plan_id`, `started_at`, `expires_at` |
| **Purpose** | Enable paid features after successful subscription |

### SubscriptionExpired
| Field | Value |
|-------|-------|
| **Publisher** | `SubscriptionService.check_expired()` (cron) |
| **Subscribers** | Notification (expiry warning), Property (restrict features) |
| **Payload** | `user_id`, `plan_id`, `expired_at` |
| **Purpose** | Gracefully degrade features after subscription ends |

### SubscriptionRenewed
| Field | Value |
|-------|-------|
| **Publisher** | `SubscriptionService.renew_subscription()` |
| **Subscribers** | Notification (receipt), Finance (record revenue) |
| **Payload** | `user_id`, `plan_id`, `renewed_at`, `amount` |
| **Purpose** | Record revenue and notify user of renewal |

### AddOnPurchased
| Field | Value |
|-------|-------|
| **Publisher** | `SubscriptionService.purchase_addon()` |
| **Subscribers** | Payment (create charge), Notification (receipt) |
| **Payload** | `user_id`, `addon_id`, `quantity`, `amount` |
| **Purpose** | Trigger payment and notify user |

### UsageLimitReached
| Field | Value |
|-------|-------|
| **Publisher** | `SubscriptionService.record_usage()` |
| **Subscribers** | Notification (limit warning) |
| **Payload** | `user_id`, `feature`, `current_usage`, `limit` |
| **Purpose** | Warn user before feature lockout |

---

## Property Events

### BuildingCreated
| Field | Value |
|-------|-------|
| **Publisher** | `PropertyService.create_building()` |
| **Subscribers** | Notification (welcome), Dashboard (update metrics) |
| **Payload** | `building_id`, `owner_id`, `name`, `unit_count` |
| **Purpose** | Track building creation and notify owner |

### UnitAdded
| Field | Value |
|-------|-------|
| **Publisher** | `PropertyService.add_unit()` |
| **Subscribers** | Dashboard (update metrics) |
| **Payload** | `unit_id`, `building_id`, `unit_number`, `rent_amount` |
| **Purpose** | Track unit inventory and trigger rent generation |

### RenterAssigned
| Field | Value |
|-------|-------|
| **Publisher** | `PropertyService.assign_renter()` |
| **Subscribers** | Notification (welcome to tenant), Rent (generate first rent record) |
| **Payload** | `unit_id`, `renter_id`, `assigned_at` |
| **Purpose** | Trigger onboarding and rent setup for new tenant |

### RenterVacated
| Field | Value |
|-------|-------|
| **Publisher** | `PropertyService.vacate_renter()` |
| **Subscribers** | Rent (finalize records), Notification (farewell), Finance (close tax records) |
| **Payload** | `unit_id`, `renter_id`, `vacated_at`, `final_dues` |
| **Purpose** | Finalize all tenant-related records |

---

## Rent Events

### RentGenerated
| Field | Value |
|-------|-------|
| **Publisher** | `RentService.generate_monthly_rent()` (cron) |
| **Subscribers** | Notification (rent due reminder to tenant), Payment (create payment request) |
| **Payload** | `rent_record_id`, `unit_id`, `tenant_id`, `amount`, `due_date` |
| **Purpose** | Notify tenant of new rent and create payment request |

### RentCalculated
| Field | Value |
|-------|-------|
| **Publisher** | `RentService.calculate_rent()` |
| **Subscribers** | Dashboard (update metrics) |
| **Payload** | `rent_record_id`, `base_amount`, `late_fee`, `total_amount` |
| **Purpose** | Track rent calculation for analytics |

### LateFeeApplied
| Field | Value |
|-------|-------|
| **Publisher** | `LateFeeService.apply_late_fee()` (cron) |
| **Subscribers** | Notification (late fee alert to tenant), Dashboard (update metrics) |
| **Payload** | `rent_record_id`, `late_fee_amount`, `total_due`, `days_late` |
| **Purpose** | Notify tenant of late fee and track revenue impact |

### AgreementSigned
| Field | Value |
|-------|-------|
| **Publisher** | `AgreementService.mark_signed()` |
| **Subscribers** | Notification (confirmation), Document (store signed copy) |
| **Payload** | `agreement_id`, `unit_id`, `signed_at`, `signature_url` |
| **Purpose** | Record agreement execution and notify parties |

---

## Payment Events

### PaymentSubmitted
| Field | Value |
|-------|-------|
| **Publisher** | `PaymentService.submit_payment()` |
| **Subscribers** | Notification (payment submitted for verification), Dashboard (update metrics) |
| **Payload** | `payment_id`, `tenant_id`, `rent_record_id`, `amount`, `utr`, `submitted_at` |
| **Purpose** | Notify owner of pending payment verification |

### PaymentVerified
| Field | Value |
|-------|-------|
| **Publisher** | `PaymentService.verify_payment()` |
| **Subscribers** | Notification (payment approved), Document (generate receipt), Finance (record revenue) |
| **Payload** | `payment_id`, `tenant_id`, `amount`, `verified_at`, `receipt_id` |
| **Purpose** | Trigger receipt generation and revenue recording |

### PaymentRejected
| Field | Value |
|-------|-------|
| **Publisher** | `PaymentService.reject_payment()` |
| **Subscribers** | Notification (payment rejected with reason) |
| **Payload** | `payment_id`, `tenant_id`, `reason`, `rejected_at` |
| **Purpose** | Notify tenant of rejection and reason |

### RefundProcessed
| Field | Value |
|-------|-------|
| **Publisher** | `RefundService.process_refund()` |
| **Subscribers** | Notification (refund initiated), Finance (record refund) |
| **Payload** | `payment_id`, `refund_amount`, `reason`, `processed_at` |
| **Purpose** | Track refund and notify parties |

---

## Notification Events

### NotificationSent
| Field | Value |
|-------|-------|
| **Publisher** | `NotificationService.send()` |
| **Subscribers** | Dashboard (track delivery rates) |
| **Payload** | `notification_id`, `user_id`, `channel`, `event_type`, `sent_at` |
| **Purpose** | Track notification delivery for analytics |

### NotificationFailed
| Field | Value |
|-------|-------|
| **Publisher** | `NotificationService.send()` (on failure) |
| **Subscribers** | Notification (retry logic) |
| **Payload** | `notification_id`, `user_id`, `channel`, `error`, `failed_at` |
| **Purpose** | Retry failed notifications via fallback channels |

---

## Document Events

### DocumentGenerated
| Field | Value |
|-------|-------|
| **Publisher** | `DocumentService.generate()` |
| **Subscribers** | Notification (document ready), Payment (attach receipt) |
| **Payload** | `document_id`, `template_id`, `owner_id`, `generated_at`, `url` |
| **Purpose** | Notify user of generated document availability |

### DocumentStored
| Field | Value |
|-------|-------|
| **Publisher** | `DocumentService.store()` |
| **Subscribers** | Dashboard (update document count) |
| **Payload** | `document_id`, `storage_path`, `stored_at` |
| **Purpose** | Track document storage for analytics |

---

## Finance Events

### TaxRecordCreated
| Field | Value |
|-------|-------|
| **Publisher** | `FinanceService.create_tax_record()` |
| **Subscribers** | Notification (tax record created) |
| **Payload** | `tax_record_id`, `owner_id`, `financial_year`, `amount` |
| **Purpose** | Notify owner and CA of new tax record |

### TaxFilingCompleted
| Field | Value |
|-------|-------|
| **Publisher** | `FinanceService.complete_filing()` |
| **Subscribers** | Notification (filing complete), Document (generate filing receipt) |
| **Payload** | `filing_id`, `owner_id`, `filing_date`, `acknowledgement_number` |
| **Purpose** | Notify owner of filing completion and generate receipt |

---

## Referral Events

### ReferralCodeGenerated
| Field | Value |
|-------|-------|
| **Publisher** | `ReferralService.generate_code()` |
| **Subscribers** | Notification (code ready to share) |
| **Payload** | `user_id`, `code`, `generated_at` |
| **Purpose** | Notify user of generated referral code |

### ReferralApplied
| Field | Value |
|-------|-------|
| **Publisher** | `ReferralService.apply_referral()` |
| **Subscribers** | Notification (referral bonus pending), Payment (create bonus credit) |
| **Payload** | `referrer_id`, `referee_id`, `code`, `applied_at` |
| **Purpose** | Track referral attribution and trigger bonus |

### BonusAwarded
| Field | Value |
|-------|-------|
| **Publisher** | `BonusService.award_bonus()` |
| **Subscribers** | Notification (bonus credited), Payment (record credit) |
| **Payload** | `user_id`, `bonus_id`, `amount`, `awarded_at` |
| **Purpose** | Notify user of bonus credit |

---

## Event Flow Examples

### Rent Payment Flow

```
RentGenerated ──▶ NotificationService.send(tenant, "Rent Due")
              ──▶ PaymentService.create_request(rent_id)

PaymentSubmitted ──▶ NotificationService.send(owner, "Payment Pending")

PaymentVerified ──▶ DocumentService.generate_receipt(payment_id)
                 ──▶ NotificationService.send(tenant, "Payment Approved")
                 ──▶ FinanceService.record_revenue(payment_id)
```

### Tenant Onboarding Flow

```
UserRegistered ──▶ SubscriptionService.create_free_plan(user_id)

UserVerified ──▶ SubscriptionService.activate_trial(user_id)
              ──▶ NotificationService.send(user, "Welcome")

RenterAssigned ──▶ RentService.generate_first_rent(unit_id)
                ──▶ NotificationService.send(tenant, "Rent Assigned")
                ──▶ AgreementService.create_draft(unit_id)
```

---

## Event Handling Rules

1. **Idempotent Handlers:** All event handlers must be idempotent (safe to process the same event twice).
2. **Async by Default:** Events are processed asynchronously via the event bus in Year 1 (in-process).
3. **No Business Logic in Handlers:** Handlers delegate to application services.
4. **Retry on Failure:** Failed events are retried with exponential backoff.
5. **Dead Letter Queue:** Events that fail after 3 retries go to a dead letter queue for manual inspection.
6. **Event Versioning:** Events include a version field for backward compatibility.
7. **No Circular Events:** Events must not trigger events that eventually trigger the original event.

---

*This catalog is the contract between bounded contexts. Adding a new event requires a new ADR.*
