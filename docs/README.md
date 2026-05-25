# RentSecureBE Documentation

## Business rules (by domain)

Full index: **[business-rules/README.md](./business-rules/README.md)**

| Area | File |
|------|------|
| Overview | [00-overview.md](./business-rules/00-overview.md) |
| Access control | [01-ownership-and-access.md](./business-rules/01-ownership-and-access.md) |
| Subscriptions | [02-subscription-and-usage-limits.md](./business-rules/02-subscription-and-usage-limits.md) |
| Caching | [03-caching.md](./business-rules/03-caching.md) |
| Buildings → Renters → Rent | [04](./business-rules/04-buildings.md) – [08](./business-rules/08-rent-records.md) |
| Media & agreements | [09](./business-rules/09-unit-images-and-documents.md) – [11](./business-rules/11-payout-retry.md) |
| Reporting & APIs | [12](./business-rules/12-owner-reporting.md) – [14](./business-rules/14-known-behaviors-and-edge-cases.md) |
| Platform services | [15](./business-rules/15-authentication.md) – [22](./business-rules/22-signals-and-automation.md) |

## Deep dive

- [Business logic & subscription](./BUSINESS_LOGIC_AND_SUBSCRIPTION.md) — end-to-end flows, gaps, dev setup

## Gaps & bugs (code vs rules)

- [business-gaps/](./business-gaps/README.md) — audit of loopholes, security issues, and rules not enforced in code
- [bugs/](./bugs/README.md) — bugs filed **by Django app** (core, properties, finance, …)

## RAG / AI knowledge base

- [rag/](./rag/README.md) — self-contained chunks for RAG indexing (`manifest.json` + 23 topic files)

## Legacy

- `properties/business_rules.md` — original single-file version (superseded by `business-rules/`)
