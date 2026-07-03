# Referral Program Rules

## Model

`referral_and_earn.models.Referral`

| Field | Rule |
|-------|------|
| `user` | One referral profile per user |
| `referred_by` | Who referred this user (nullable) |
| `referral_code` | Unique; auto-generated UUID prefix if empty on save |
| `bonus_earned` | Decimal; default 0 |

## Signup flow

1. Client sends optional `referral_code` with `POST /api/auth/send-otp/`.
2. Code stored on `OTP.referral_code`.
3. On `owner/verify-otp` or `renter/verify-otp`:
   - Lookup `Referral` by `referral_code`
   - If invalid → **400** `Invalid referral code`
   - Create/get `Referral` for new user; set `referred_by`
   - **Reward referrer:** `bonus_earned += 500` (fixed amount in code)

## Business rules

1. A user cannot apply a referral code if they already have `referred_by` set.
2. Referral code must exist before signup completes.
3. Bonus amount is hardcoded in `core/views.py` (not configurable per campaign).

## Related files

- `referral_and_earn/models.py`
- `core/views.py` (`SendOTP`, `OwnerVerifyOTP`, `RenterVerifyOTP`)
- `core/models.py` (`OTP.referral_code`)

## See also

- [Authentication](./15-authentication.md)
