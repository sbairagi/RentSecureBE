# RAG-012 — Subscription & Feature Limits

**Metadata:** `id=RAG-012` | `tags=FeatureEnforcer,subscription,limits` | `apps=core,properties`

## Plans

`SubscriptionPlan.name`: **free**, **pro**, **elite**

Limits defined in `PlanFeatureLimit` per (`plan`, `feature_key`).

## Feature keys (common)

| Key | Resource |
|-----|----------|
| `max_buildings` | Building |
| `max_units` | Unit |
| `max_renters` | Renter |
| `max_caretakers` | Caretaker |
| `max_unit_images` / `unit_images` | UnitImage (naming inconsistent in code) |
| `max_document_uploads` / `unit_documents` | UnitDocument |
| `rent_agreement_drafts` | RentAgreementDraft |
| `rent_records` | RentRecord |

## FeatureEnforcer (`properties/feature_enforcer.py`)

**Algorithm:**

1. No `UserSubscription` → limits from Free plan's `PlanFeatureLimit`
2. Active subscription → `plan_limit + sum(AddOnPurchase.amount for key)`
3. Expired ≤ 7 days → still paid limits
4. Expired > 7 days → free limits; list views may slice queryset
5. `can_create(key)` iff `usage_count < limit`
6. Create/delete → `increment`/`decrement` on `UsageLimit`

**Caveats for AI:**

- Missing `PlanFeatureLimit` row for paid plan → treated as **unlimited** (bug)
- `get_free_plan_limit` called in views but may not exist as public method (bug)
- Signals that sync usage counts are often **not registered**

## APIs

See RAG-008: `/api/subscription-plans/`, `/api/user-subscriptions/`, `/api/addon-purchases/`, `/api/usage-limits/`

## Human policy docs

`docs/business-rules/02-subscription-and-usage-limits.md`

## Bugs

`docs/bugs/core.md` (CORE-004), `docs/bugs/properties.md` (PROP-001, PROP-007–009)
