# Known Behaviors & Edge Cases

## Data consistency

1. **`renter.unit` must match `unit`** on every rent record create/update — enforced in serializer and model `clean()`.
2. **`status` vs `is_active` vs `is_agreement_revoked`** — multiple flags; keep them aligned when changing tenant state.
3. **Rent API fields** — some code expects `due_date`, `month`, `year`; model exposes these as **properties** on `RentRecord`.

## Subscription edge cases

| Scenario | Behavior |
|----------|----------|
| No `UserSubscription` | `FeatureEnforcer` uses free limits (0 if not seeded) |
| Expired &lt; 7 days | Still uses paid plan limits |
| Expired &gt; 7 days | Free limits; lists may truncate |
| Usage not decremented on delete | Count can block creates (documented loophole in tests) |
| No subscription row | `enforce_limit()` raises error; `FeatureEnforcer` may still allow free tier |

## Payment / webhook edge cases

- **`razorpay_webhook` defined 3 times** in `core/views.py` — only the last handler runs (`payment_link.paid`).
- Payment link may not set `reference_id` to rent id — webhook lookup can fail.
- Payout code paths referencing `renter.property` will **fail** — use `renter.unit`.

## Signals not loaded

`core/apps.py` and `properties/apps.py` do not import signals in `ready()`:

- No auto Free plan on user create (despite `core/signals.py`)
- No post-payment receipt/voice note
- No usage sync on model save from signals

## Auth edge cases

- Owner OTP assigns group **`tenant`** (likely wrong name for owner role).

## Broken management commands

- `generate_monthly_rent_records` — imports `rent.models` (invalid)
- `daily_rent_reminder` — same
- `seed_subscription_plans`, `downgrade_expired_users` — fully commented

## Testing notes

See `properties/TEST_DOCUMENTATION.md` and `properties/test_loopholes_critical.py` for documented loopholes (overlapping renters, grace period, concurrency).

## Related

- [Signals & automation](./22-signals-and-automation.md)
- [Deep dive](../BUSINESS_LOGIC_AND_SUBSCRIPTION.md)
