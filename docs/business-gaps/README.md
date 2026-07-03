# Business Gaps & Bugs

Audit of **documented business rules vs actual code behavior**. These are implementation gaps, loopholes, and bugs—not intended product behavior unless noted.

| Document | Description |
|----------|-------------|
| [BUSINESS_GAPS_AUDIT.md](./BUSINESS_GAPS_AUDIT.md) | Full audit (critical → low, doc accuracy, fix priority) |

## Related documentation

- [Business rules (by domain)](../business-rules/README.md) — intended behavior
- [Business logic deep dive](../BUSINESS_LOGIC_AND_SUBSCRIPTION.md) — flows and architecture
- [Properties test loopholes](../../properties/test_loopholes_critical.py) — automated loophole tests
- [Test issue registry](../../properties/TEST_DOCUMENTATION.md) — structured issue list

## Status legend

| Label | Meaning |
|-------|---------|
| **BUG** | Code error or crash |
| **GAP** | Rule documented or expected but not enforced |
| **SECURITY** | Abuse or fraud risk |
| **DOC** | Documentation says X; code does Y |

*Last reviewed against codebase: May 2026*
