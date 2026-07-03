# RAG-018 — Referral Program

**Metadata:** `id=RAG-018` | `tags=referral,bonus,signup` | `app=referral_and_earn`

## Model

`referral_and_earn.models.Referral`

| Field | Description |
|-------|-------------|
| `user` | OneToOne — referred user |
| `referred_by` | FK to referrer User |
| `referral_code` | Unique; auto-generated on save if empty |
| `bonus_earned` | Decimal; referrer reward total |

## Flow (in OTP signup)

1. Client sends `referral_code` with `POST /api/auth/send-otp/` → stored on `OTP`
2. On `owner/verify-otp` or `renter/verify-otp`:
   - Lookup `Referral` by code
   - Invalid code → 400 (may occur after user already saved — bug)
   - Link `referred_by`, add **₹500** to referrer `bonus_earned`

## No standalone REST API

Referral is only integrated in `core/views.py` OTP handlers.

## Bugs

`docs/bugs/referral_and_earn.md`, `docs/business-rules/19-referral-program.md`
