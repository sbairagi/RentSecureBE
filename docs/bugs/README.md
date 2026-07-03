# Project Bugs (by app)

Confirmed bugs and likely runtime failures from code review and `properties/test_loopholes_critical.py`.

| File | App / area |
|------|------------|
| [core.md](./core.md) | `core` — auth, subscriptions, webhooks |
| [properties.md](./properties.md) | `properties` — domain, views, signals, enforcer |
| [rentsecure_be.md](./rentsecure_be.md) | `rentsecure_be` — Razorpay/Cashfree services |
| [notification.md](./notification.md) | `notification` |
| [finance.md](./finance.md) | `finance` |
| [smartbot.md](./smartbot.md) | `smartbot` |
| [documents.md](./documents.md) | `documents` |
| [referral_and_earn.md](./referral_and_earn.md) | `referral_and_earn` |
| [ai_assistant.md](./ai_assistant.md) | `ai_assistant` |
| [management_commands.md](./management_commands.md) | `management/commands` |
| [project_config.md](./project_config.md) | Settings, deps, apps not wired |

**Related:** [business-gaps audit](../business-gaps/BUSINESS_GAPS_AUDIT.md) · [business-rules](../business-rules/README.md) · [RAG knowledge base](../rag/README.md)

### Severity

| Level | Meaning |
|-------|---------|
| **P0** | Security, money, or data corruption |
| **P1** | Crash / broken API for common flows |
| **P2** | Wrong behavior, missing validation |
| **P3** | Tech debt, dead code |
