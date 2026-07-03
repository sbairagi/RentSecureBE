# RAG-021 — Known Issues (for AI assistants)

**Metadata:** `id=RAG-021` | `tags=bugs,caveats,do-not-hallucinate`

**Purpose:** Prevent AI from stating broken features as working. Full detail in `docs/bugs/`.

## Do NOT claim these work without verification

1. **Razorpay webhook security** — Active handler may lack signature verification (CORE-001).
2. **Payment link → rent matching** — `reference_id` may be unset (CORE-002, RSBE-001).
3. **Auto Free subscription on signup** — Signals not wired (CORE-006).
4. **Post-payment voice/receipt** — Signals not wired (PROP-002).
5. **SmartBot HTTP API** — Not in root URLconf (BOT-004).
6. **Tax submission list API** — Broken queryset `tax_summary__user` (FIN-001).
7. **Monthly rent generation command** — Imports `rent.models` (CMD-001).
8. **Expired owner building list** — May crash on `get_free_plan_limit` (PROP-001).

## Security issues (high priority)

- Self-service upgrade to any subscription plan (CORE-004).
- Add-on `amount` inflates limits (CORE-004).
- Forged payment webhooks if unsigned handler is live (CORE-001).

## Data integrity gaps

- Multiple active renters per unit allowed (PROP-011).
- `is_active` vs `status` not validated (PROP-012).
- UsageLimit drift vs real counts (PROP-008).

## Wrong code patterns (suggest fixes using these)

| Wrong | Correct |
|-------|---------|
| `rent.renter.property.owner` | `rent.owner` |
| `owner.profile.whatsapp_number` | `owner.userprofile.whatsapp_number` or `owner.whatsapp_number` |
| `rent.status == "UNPAID"` | `rent.payment_status == "PENDING"` |
| `unit.unit_number` | `unit.unit` |

## Where to read more

| Corpus | Path |
|--------|------|
| All bugs by app | `docs/bugs/README.md` |
| Policy vs code gaps | `docs/business-gaps/BUSINESS_GAPS_AUDIT.md` |
| Intended rules | `docs/business-rules/README.md` |

## When user asks "is feature X implemented?"

1. Check RAG chunk for intended design.
2. Check `docs/bugs/` for that app.
3. Grep codebase for the view/signal/command.
4. State both **design** and **known breakage** if any.
