# Renter Rules

## Model

`properties.models.Renter` — tenant on a unit.

## Status lifecycle

| Status | Meaning |
|--------|---------|
| `active` | Current tenant |
| `notice_period` | Leaving; still listed in owner APIs |
| `revoked` | Agreement ended by system/owner |
| `deactivated` | Tenant ended |

## Business rules

1. **Belongs to** one `Unit`; owner is `unit.owner`.
2. **Default list:** owner APIs return only `active` and `notice_period` renters.
3. **Uniqueness:** phone number unique per unit.
4. **Dates:** `end_date` ≥ `start_date`.
5. **Flags:** `is_active`, `is_agreement_revoked`, `revoked_by_owner`, `vacated_on` must stay consistent with `status`.
6. **KYC:** `kyc_status` — `not_started`, `in_progress`, `verified`, `rejected`.
7. **Onboarding:** `onboarding_status` — `pending`, `link_sent`, `completed`.
8. **Defaulters:** `missed_rents` ≥ 3 → `is_flagged`, `flagged_reason`, owner notification (intended via signals).
9. **Create limits:** `max_renters` — dual check: `check_feature_limit` + `FeatureEnforcer` in `RenterViewSet`.
10. **Destroy:** decrements usage; updates unit vacancy.

## Onboarding flow

1. Owner creates renter → optional `send_renter_onboarding_invite()` (WhatsApp link).
2. Renter completes KYC → `notify_owner_renter_completed_kyc()`.
3. Renter may link `User` via OTP (`renter_profile`).

## API

| Method | Path |
|--------|------|
| GET/POST | `/api/renters/` |

## Related files

- `properties/models/renter_models.py`
- `properties/views/renter_views.py`
- `properties/services/renter_onboarding_service.py`
- `properties/signals/__init__.py` (vacancy WhatsApp, archive on exit)

## See also

- [Renter-facing APIs](./13-renter-facing-apis.md)
- [Rent records](./08-rent-records.md)
