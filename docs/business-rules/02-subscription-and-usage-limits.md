# Subscription & Usage Limits

## Models (`core`)

| Model | Role |
|-------|------|
| `SubscriptionPlan` | `free`, `pro`, `elite` + pricing |
| `PlanFeatureLimit` | Per plan: `feature_key` → `value` (`"3"`, `"unlimited"`, `"yes"`, `"no"`) |
| `UserSubscription` | One per owner: plan, `start_date`, `end_date`, `is_active` |
| `AddOnPurchase` | Extra capacity; **`amount` is summed** into the limit |
| `UsageLimit` | Per user + feature: `usage_count` |

## Feature keys

| Key | Resource |
|-----|----------|
| `max_buildings` | `Building` |
| `max_units` | `Unit` |
| `max_caretakers` | `Caretaker` |
| `max_renters` | `Renter` |
| `rent_records` | `RentRecord` |
| `max_unit_images` / `unit_images` | `UnitImage` (naming varies in code) |
| `max_document_uploads` / `unit_documents` | `UnitDocument` |
| `rent_agreement_drafts` | `RentAgreementDraft` |
| `whatsapp_alerts`, `tax_notifications`, etc. | Boolean-style plan features |

## `FeatureEnforcer` rules

1. **No subscription** → use Free plan limits from `PlanFeatureLimit` (0 if Free plan not seeded).
2. **Active subscription** → `plan_limit + sum(addon.amount)` for that key.
3. **Expired** → paid limits until **7 days** after `end_date` (`GRACE_PERIOD_DAYS`).
4. **Past grace** → Free plan limits; list APIs may **slice** queryset (e.g. first N buildings).
5. **Create** → `can_create(key)` then `increment(key)` on success.
6. **Delete** → `decrement(key)`.

## APIs

| Endpoint | Access |
|----------|--------|
| `GET /api/subscription-plans/` | Public |
| `GET/POST /api/user-subscriptions/` | Authenticated owner |
| `GET/POST /api/addon-purchases/` | Authenticated owner |
| `GET /api/usage-limits/` | Read-only, own rows |

## Duplicate enforcement

- `check_feature_limit()` in `properties/utils` — used in `RenterViewSet.create`.
- `enforce_limit()` — requires active subscription (stricter).
- Prefer consolidating on `FeatureEnforcer` only.

## Known gaps

- `core/signals.assign_default_plan` exists but **`core/apps.py` does not import signals** → new users may have no subscription.
- `seed_subscription_plans` and `downgrade_expired_users` commands are **commented out**.

## Related files

- `properties/feature_enforcer.py`
- `properties/constants.py` (`GRACE_PERIOD_DAYS`)
- `core/models.py`
- [Deep dive](../BUSINESS_LOGIC_AND_SUBSCRIPTION.md)
