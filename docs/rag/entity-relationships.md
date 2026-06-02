# RAG-007 — Entity Relationships & Ownership

**Metadata:** `id=RAG-007` | `tags=FK,ownership,ER diagram`

## Ownership rule (critical for AI)

Every query for an **owner** must scope by `User` who owns the resource:

- `Building.owner == request.user`
- `Unit.owner == request.user`
- Children: filter via `unit__owner=request.user` or `owner=request.user` on RentRecord

Renters access only records linked to `request.user.renter_profile`.

## Hierarchy

```
User (owner)
  └── Building [optional parent]
        └── Unit
              ├── Caretaker
              ├── Renter ──► User (renter login, optional)
              ├── UnitImage
              ├── UnitDocument
              └── RentRecord (also has owner FK denormalized)
```

## Money flow entities

```
RentRecord (PENDING)
    → Razorpay payment (renter pays)
    → RentRecord (PAID)
    → Cashfree payout → OwnerBankDetails.beneficiary_id
    → RentRecord.payout_status SUCCESS/FAILED
```

## Subscription entities (parallel tree)

```
User ── UserSubscription ── SubscriptionPlan
     └── UsageLimit (per feature_key)
     └── AddOnPurchase (adds to limits)
PlanFeatureLimit (plan + feature_key + value)
```

## FeatureEnforcer

Class: `properties/feature_enforcer.py`
Uses User + UsageLimit + PlanFeatureLimit + AddOnPurchase to allow/deny creates.

Grace period: 7 days after `UserSubscription.end_date` (`properties/constants.py`).
