# RAG-019 — Glossary & Enums

**Metadata:** `id=RAG-019` | `tags=glossary,enums,definitions`

## Roles

| Term | Meaning |
|------|---------|
| **Owner** | Property landlord using the platform |
| **Renter** | Tenant; may have linked `User` for app login |
| **CA** | Chartered Accountant receiving tax exports |

## Renter.status

`active` | `notice_period` | `revoked` | `deactivated`

## RentRecord.payment_status

`PENDING` | `PAID` | `FAILED`

## RentRecord.payment_mode

`cash` | `cheque` | `online` | `other`

## Unit.status (VacancyStatus)

`vacant` | `occupied` (keep in sync with `is_vacant`)

## SubscriptionPlan.name

`free` | `pro` | `elite`

## Feature limit value strings

`"3"` (numeric cap) | `"unlimited"` | `"yes"` | `"no"`

## Common code names

| Term | Location |
|------|----------|
| **FeatureEnforcer** | `properties/feature_enforcer.py` |
| **UsageLimit** | `core.models.UsageLimit` |
| **rent_month** | First day of calendar month on RentRecord |
| **grace period** | 7 days after subscription `end_date` |

## Misleading names (AI caution)

| Name | Reality |
|------|---------|
| `renter.property` | Returns `Unit`, not Building |
| `AddOnPurchase.amount` | Added to **limit count**, not currency price |
| Owner Django group `tenant` | Assigned on owner OTP — likely wrong label |
