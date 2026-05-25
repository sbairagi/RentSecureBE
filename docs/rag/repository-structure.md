# RAG-003 — Repository Structure

**Metadata:** `id=RAG-003` | `tags=folders,layout,navigation`

## Top-level layout

```
RentSecureBE/
├── rentsecure_be/          # Django project (settings, urls, payment services)
├── core/                   # Users, OTP, subscriptions, webhooks
├── properties/             # Main domain: buildings, units, renters, rent
│   ├── models/             # Split model modules
│   ├── views/              # DRF ViewSets per resource
│   ├── serializers/
│   ├── services/           # Business logic (onboarding, receipts, units)
│   ├── signals/            # post_save handlers (often not wired)
│   ├── feature_enforcer.py # Subscription limits
│   └── _legacy/            # Older monolithic code (avoid for new work)
├── notification/           # WhatsApp, email, push, reminder services
├── finance/                # CA profiles, tax ZIP export
├── documents/              # PDF API ViewSets
├── smartbot/               # GPT chat + intents (URLs not in root urls)
├── referral_and_earn/      # Referral model
├── ai_assistant/           # Archive/invoice AI helpers (not in INSTALLED_APPS)
├── dashboard/              # Agreement UI routes (not in INSTALLED_APPS)
├── management/commands/    # Cron-style commands (some broken)
├── docs/                   # business-rules, bugs, business-gaps, rag
├── tests/                  # Cross-app tests
└── manage.py
```

## Key files for common tasks

| Task | File(s) |
|------|---------|
| Add API route | app `urls.py`, `rentsecure_be/urls.py` |
| Change subscription limits | `core/models.py`, `properties/feature_enforcer.py` |
| Rent payment | `properties/views/rent_record_views.py`, `rentsecure_be/services/razorpay_service.py` |
| Payout | `rentsecure_be/services/cashfree_service.py`, `core/views.py` webhooks |
| Owner auth | `core/views.py` (`SendOTP`, `OwnerVerifyOTP`) |

## Main domain package

The **`properties`** app owns ~80% of business logic. Start any feature investigation in `properties/models/` and `properties/views/`.
