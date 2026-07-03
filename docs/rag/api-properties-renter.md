# RAG-010 — API: Properties (Renter)

**Metadata:** `id=RAG-010` | `tags=renter,rent-due,history,api` | `app=properties`

## Authentication

Renter must complete `POST /api/auth/renter/verify-otp/` and have `Renter.user` linked to `request.user`.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/renter/rent-due/` | Latest pending rent + payment link |
| GET | `/api/renter/rent-history/` | All rent records for renter |

## Eligibility

Views filter renter with `status in ["active", "notice_period"]`.

## Response fields (rent-due)

Uses `RentRecord` properties: `amount`, `month`, `year`, `due_date`, `payment_link`.

**Known bug:** code may reference `renter.property.name` but `Unit` has no `name` field — see `docs/bugs/properties.md` PROP-010.

## Payment

Renter pays via `payment_link` on `RentRecord` (Razorpay). Status updated via webhook → see RAG-013.

## Owner vs renter

Renters cannot access `/api/buildings/`, `/api/units/`, or other owners' data.
