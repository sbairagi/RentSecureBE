# Renter-Facing API Rules

## Authentication

Renters authenticate via:

- `POST /api/auth/send-otp/`
- `POST /api/auth/renter/verify-otp/`

JWT is returned; renter is added to Django group `renter` and may have `user.renter_profile` linked to `Renter`.

## Eligibility

- Renter-facing endpoints require linked `Renter` on the authenticated user.
- Intended for statuses **`active`** and **`notice_period`** only (inactive/revoked may be rejected).

## Endpoints

| Endpoint | Rule |
|----------|------|
| `GET /api/renter/rent-due/` | Latest **pending** rent for this renter |
| `GET /api/renter/rent-history/` | All rent records, newest due date first |
| `my_rent_records` (property views) | Records for renter profile; invoice URL when `PAID` |

## Payment

- Renter pays via **Razorpay payment link** on `RentRecord.payment_link` (created by owner when rent record is created).

## Rules

1. Renters **cannot** access owner CRUD (buildings, units, other tenants).
2. Renters see only their own `RentRecord` rows.
3. Receipt/invoice available when `payment_status == PAID` and `invoice_pdf` exists.

## Related files

- `properties/views/rent_record_views.py` (`get_latest_due_rent`, `rent_history`)
- `core/views.py` (`RenterVerifyOTP`)

## See also

- [Authentication](./15-authentication.md)
- [Rent records](./08-rent-records.md)
