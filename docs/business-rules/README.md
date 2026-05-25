# RentSecureBE — Business Rules Index

Each file documents rules for one domain: validation, access control, limits, APIs, and known gaps.

| # | Document | Module |
|---|----------|--------|
| 00 | [Overview](./00-overview.md) | Cross-cutting |
| 01 | [Ownership & access](./01-ownership-and-access.md) | All apps |
| 02 | [Subscription & usage limits](./02-subscription-and-usage-limits.md) | `core`, `properties` |
| 03 | [Caching](./03-caching.md) | `properties` |
| 04 | [Buildings](./04-buildings.md) | `properties` |
| 05 | [Units](./05-units.md) | `properties` |
| 06 | [Caretakers](./06-caretakers.md) | `properties` |
| 07 | [Renters](./07-renters.md) | `properties` |
| 08 | [Rent records](./08-rent-records.md) | `properties` |
| 09 | [Unit images & documents](./09-unit-images-and-documents.md) | `properties` |
| 10 | [Rent agreement drafts](./10-rent-agreement-drafts.md) | `properties` |
| 11 | [Payout retry](./11-payout-retry.md) | `properties`, `core` |
| 12 | [Owner reporting](./12-owner-reporting.md) | `properties` |
| 13 | [Renter-facing APIs](./13-renter-facing-apis.md) | `properties` |
| 14 | [Known behaviors & edge cases](./14-known-behaviors-and-edge-cases.md) | Cross-cutting |
| 15 | [Authentication](./15-authentication.md) | `core` |
| 16 | [Payments & webhooks](./16-payments-and-webhooks.md) | `core`, `rentsecure_be` |
| 17 | [Notifications](./17-notifications.md) | `notification` |
| 18 | [Finance & tax](./18-finance-and-tax.md) | `finance` |
| 19 | [Referral program](./19-referral-program.md) | `referral_and_earn` |
| 20 | [Documents & PDFs](./20-documents-and-pdfs.md) | `documents` |
| 21 | [SmartBot](./21-smartbot.md) | `smartbot` |
| 22 | [Signals & automation](./22-signals-and-automation.md) | `core`, `properties`, `management` |

**See also:**

- [Business logic & subscription (deep dive)](../BUSINESS_LOGIC_AND_SUBSCRIPTION.md)
- [Business gaps & bugs audit](../business-gaps/BUSINESS_GAPS_AUDIT.md) — code vs documented rules

**Source:** Derived from `properties/business_rules.md`, models, views, and `properties/TEST_DOCUMENTATION.md`.
