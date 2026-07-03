# Authentication Rules

## Method

- **JWT** (`rest_framework_simplejwt`) for API access after OTP verification
- **OTP** via Twilio SMS (mocked in `DEBUG` — printed to console)

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/auth/send-otp/` | Send 6-digit OTP; 60s resend cooldown |
| `POST /api/auth/owner/verify-otp/` | Owner login/register |
| `POST /api/auth/renter/verify-otp/` | Renter login/register |
| `POST /api/api/token/refresh/` | Refresh access token |
| `POST /api/change-password/` | Change password (authenticated) |
| `POST /api/reset-password/` | Reset password |

## OTP rules

1. Phone number required for send.
2. OTP valid **5 minutes** from `created_at`.
3. Only **unverified** OTP rows accepted on verify.
4. On success: OTP marked verified; other OTPs for same phone deleted.
5. Optional **referral_code** on send — validated on verify (see [Referral](./19-referral-program.md)).

## User creation

- `User.objects.get_or_create(phone=phone, defaults={"username": phone})`
- `is_phone_verified = True`
- Owner → group `tenant` (verify intended role name)
- Renter → group `renter`

## JWT settings

- Access token: **5 minutes**
- Refresh token: **35 days**

## User model (`core.User`)

- Extends `AbstractUser`
- Fields: `full_name`, `phone`, `whatsapp_number`, `is_phone_verified`, `is_investor`
- Audit: `simple_history`

## Related profiles (intended on create via signals)

- `UserProfile` — WhatsApp, language (`en` / `hi`)
- `NotificationPreference` — rent/payout/summary toggles
- `UserSubscription` — default free plan (**signal not wired**)

## Related files

- `core/views.py` (`SendOTP`, `OwnerVerifyOTP`, `RenterVerifyOTP`)
- `core/models.py` (`User`, `OTP`)
- `rentsecure_be/settings.py` (`REST_FRAMEWORK`, `SIMPLE_JWT`)
