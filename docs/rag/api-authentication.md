# RAG-008 — API: Authentication & Account

**Metadata:** `id=RAG-008` | `tags=JWT,OTP,auth,api` | `app=core` | `path=core/urls.py,core/views.py`

## Base path

All routes below are under **`/api/`** (from `rentsecure_be/urls.py`).

## Public / auth endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/auth/send-otp/` | Send OTP; body: `phone`, optional `referral_code` |
| POST | `/api/auth/owner/verify-otp/` | Owner login; returns JWT |
| POST | `/api/auth/renter/verify-otp/` | Renter login; returns JWT |
| POST | `/api/api/token/refresh/` | Refresh JWT access token |
| POST | `/api/change-password/` | Authenticated password change |
| POST | `/api/reset-password/` | Password reset |

## JWT usage

Header: `Authorization: Bearer <access_token>`

Settings: access 5 minutes, refresh 35 days.

## Subscription APIs (authenticated)

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/subscription-plans/` | Public list (ReadOnly viewset) |
| GET/POST | `/api/user-subscriptions/` | User's subscription |
| GET/POST | `/api/addon-purchases/` | Add-on purchases |
| GET | `/api/usage-limits/` | Read-only usage counts |

## Bank & webhooks

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/api/owner/update-bank-details/` | JWT |
| POST | `/api/webhook/cashfree/payout/` | CSRF exempt, no JWT |
| POST | `/api/rent/payment-callback/` | Razorpay webhook, CSRF exempt |

## Owner vs renter groups (Django)

- Renter verify → group `renter`
- Owner verify → group **`tenant`** (likely misnamed; see bugs CORE-003)

## Code references

- `SendOTP`, `OwnerVerifyOTP`, `RenterVerifyOTP` → `core/views.py`
- Serializers → `core/serializers.py`
