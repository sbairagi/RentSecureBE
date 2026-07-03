# Overview — Properties & Platform Scope

## Purpose

RentSecureBE is a rental property management backend. The `properties` app is the core domain; other apps add auth, subscriptions, payments, notifications, tax, documents, referrals, and AI.

## What `properties` manages

- Buildings
- Units
- Caretakers
- Renters
- Rent records (payments & payouts)
- Unit images and documents
- Rent agreement drafts
- Payout retry operations

## Core principles

1. **Owner isolation** — Every property entity belongs to one owner (`User`). APIs never cross owner boundaries.
2. **Plan limits** — Creates are gated by subscription feature keys (`FeatureEnforcer`).
3. **Cache coherence** — List querysets are cached per user; mutations invalidate cache keys.
4. **Rent integrity** — One `RentRecord` per renter per `rent_month`; renter must belong to the selected unit.
5. **External money flow** — Razorpay collects from renters; Cashfree pays owners.

## API base paths

| Prefix | App |
|--------|-----|
| `/api/` | `core`, `properties` |
| `/properties/` | `properties` (duplicate mount) |
| `/finance/` | `finance` |
| `/documents/document/` | `documents` |
| `/dashboard/` | `dashboard` |

## Related code

- `properties/business_rules.md` (legacy monolith; prefer this `docs/business-rules/` folder)
- `properties/models/`
- `properties/views/`
- `properties/feature_enforcer.py`
