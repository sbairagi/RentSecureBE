# RAG-017 — SmartBot & AI Assistant

**Metadata:** `id=RAG-017` | `tags=smartbot,gpt,ai_assistant,chatbot`

## SmartBot (`smartbot` app)

**Installed:** Yes
**URLs in root:** **No** — API not mounted in `rentsecure_be/urls.py` (bug BOT-004)

**Entry view:** `smartbot/views.py` → `smart_bot_reply` (POST, authenticated)

**Flow:**

1. Load owner rent context (paid/unpaid this month)
2. `extract_intent(query)` from `smartbot/intents.py`
3. If intent → `smartbot/actions.py` (reminder, retry payout, agreement)
4. Else → `gpt_smart_reply` (`smartbot/services/gpt_services.py`)

**Intents (keyword):**

| Pattern | Action |
|---------|--------|
| reminder + rent | send_rent_reminder |
| retry + payout | retry_payout |
| send + agreement | send_rent_agreement |
| signature / esign | send_agreement_for_signature |

**Models:** `SmartBotChat`, `SmartBotMessage`, `AIAlert`

## AI Assistant (`ai_assistant` app)

**Installed:** No (not in INSTALLED_APPS)

**Used by:** `properties/signals` imports:

- `archive_service.archive_renter_data`
- `invoice_service.generate_final_invoice_pdf`

**Risk:** Import errors or partial installs if package structure changes.

## OpenAI

Requires `OPENAI_API_KEY` in environment.

## Related docs

- `docs/business-rules/21-smartbot.md`
- `docs/bugs/smartbot.md`, `docs/bugs/ai_assistant.md`
