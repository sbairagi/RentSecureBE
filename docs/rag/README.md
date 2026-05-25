# RAG Knowledge Base — RentSecureBE

Structured documentation for **retrieval-augmented generation (RAG)**. Each file is a self-contained chunk: scope, facts, code paths, and links to related chunks.

## How to use (for AI / indexing)

1. **Embed per file** (recommended) or per H2 section for large files.
2. **Read `README.md` + `manifest.json`** for the full chunk list and keywords.
3. **Prefer this folder** for “what is RentSecureBE?”; use `../bugs/` for defect details and `../business-rules/` for intended policy.
4. Each chunk starts with a **Metadata** block (`id`, `tags`, `apps`, `paths`).

## Chunk index

| ID | File | Use when asking about… |
|----|------|-------------------------|
| RAG-001 | [project-summary.md](./project-summary.md) | Product purpose, users, value |
| RAG-002 | [tech-stack.md](./tech-stack.md) | Django, DRF, libraries, infra |
| RAG-003 | [repository-structure.md](./repository-structure.md) | Where code lives |
| RAG-004 | [django-apps-inventory.md](./django-apps-inventory.md) | Installed apps, URL mounts |
| RAG-005 | [data-model-core.md](./data-model-core.md) | User, subscription, OTP, bank |
| RAG-006 | [data-model-properties.md](./data-model-properties.md) | Building, Unit, Renter, RentRecord |
| RAG-007 | [entity-relationships.md](./entity-relationships.md) | FK graph, ownership |
| RAG-008 | [api-authentication.md](./api-authentication.md) | OTP, JWT, password endpoints |
| RAG-009 | [api-properties-owner.md](./api-properties-owner.md) | Owner CRUD & dashboard APIs |
| RAG-010 | [api-properties-renter.md](./api-properties-renter.md) | Renter-facing rent APIs |
| RAG-011 | [api-finance-documents.md](./api-finance-documents.md) | Tax, PDF, CA APIs |
| RAG-012 | [subscription-and-limits.md](./subscription-and-limits.md) | Plans, FeatureEnforcer, usage |
| RAG-013 | [payments-razorpay-cashfree.md](./payments-razorpay-cashfree.md) | Collect rent, payout, webhooks |
| RAG-014 | [notifications-and-reminders.md](./notifications-and-reminders.md) | WhatsApp, email, FCM, voice |
| RAG-015 | [external-integrations.md](./external-integrations.md) | Twilio, Leegality, OpenAI, S3 |
| RAG-016 | [signals-celery-commands.md](./signals-celery-commands.md) | Background jobs, automation |
| RAG-017 | [smartbot-and-ai-assistant.md](./smartbot-and-ai-assistant.md) | Chatbot, AI services |
| RAG-018 | [referral-program.md](./referral-program.md) | Referral codes, bonuses |
| RAG-019 | [glossary.md](./glossary.md) | Terms and enums |
| RAG-020 | [environment-configuration.md](./environment-configuration.md) | .env, settings keys |
| RAG-021 | [known-issues-for-ai.md](./known-issues-for-ai.md) | Critical bugs summary (do not hallucinate fixes) |
| RAG-022 | [business-rules-pointer.md](./business-rules-pointer.md) | Index to human business-rules docs |
| RAG-023 | [development-runbook.md](./development-runbook.md) | Run locally, test, migrate |

## Related human docs

- [business-rules/](../business-rules/README.md) — intended behavior by domain
- [business-gaps/](../business-gaps/BUSINESS_GAPS_AUDIT.md) — policy vs implementation gaps
- [bugs/](../bugs/README.md) — bugs by Django app
- [BUSINESS_LOGIC_AND_SUBSCRIPTION.md](../BUSINESS_LOGIC_AND_SUBSCRIPTION.md) — long-form deep dive

## Suggested system prompt snippet

```text
You are helping with RentSecureBE, a Django REST API for Indian rental property management.
Owners manage buildings/units/renters; renters pay rent via Razorpay; owners receive payouts via Cashfree.
Use docs/rag/*.md as source of truth for architecture. For bugs, cite docs/bugs/. For business policy, cite docs/business-rules/.
```
