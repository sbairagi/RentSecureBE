# RAG-005 — Data Model: `core` App

**Metadata:** `id=RAG-005` | `tags=User,subscription,OTP,models` | `app=core` | `path=core/models.py`

## User (`core.User`)

Extends `AbstractUser`.

| Field | Notes |
|-------|-------|
| `full_name` | Required display name |
| `phone` | Login identifier (OTP flow) |
| `whatsapp_number` | Notifications |
| `is_phone_verified` | Set on OTP success |
| `is_investor` | Optional flag |

Related: `userprofile` (UserProfile), `usersubscription`, `notification_preference`, `referral_profile`.

## UserProfile

- `whatsapp_number`, `whatsapp_opt_in`, `language_preference` (`en` / `hi`)

## NotificationPreference

Owner toggles for rent alerts, summaries, payout alerts (WhatsApp/email).

## OTP

- `phone_number`, `code` (6 digits), `referral_code`, `is_verified`
- Valid ~5 minutes in views; 60s resend throttle

## OwnerBankDetails

- `bank_account_number`, `ifsc_code`, `beneficiary_id` (Cashfree), `bank_account_verified`
- OneToOne with User (owner)

## SubscriptionPlan

- `name`: `free`, `pro`, `elite`
- `monthly_price`, `yearly_price`, `is_active`

## UserSubscription

- OneToOne `user` → `plan`
- `start_date`, `end_date`, `is_active`, `is_yearly`
- `rent_reminder_days_before`, `tax_reminder_days_before` (defaults 7)

## PlanFeatureLimit

- `plan` + `feature_key` + `value` (string: `"3"`, `"unlimited"`, `"yes"`, `"no"`)

## UsageLimit

- `user` + `feature_key` + `usage_count` (enforcement counter)

## AddOnPurchase

- `user`, `name` (feature key), `amount` (**summed into limit** — not price), `is_recurring`

## Intended signup side effects (`core/signals.py`)

On User create: UserProfile, NotificationPreference, Free UserSubscription — **only if signals imported in `core/apps.py` ready()** (often not wired).
