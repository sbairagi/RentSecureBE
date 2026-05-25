# SmartBot Rules

## Purpose

AI assistant for owners: natural-language queries and **action intents** (reminders, payouts, agreements).

## Models

- `SmartBotChat` — conversation session
- `SmartBotMessage` — query/response log
- `AIAlert` — AI-generated alerts

## API

`POST` to SmartBot endpoint (see `smartbot/urls.py`) with `{ "query": "..." }` — **authenticated owner**.

## Intent detection (`smartbot/intents.py`)

| User phrase pattern | Intent |
|---------------------|--------|
| "reminder" + "rent" | `send_rent_reminder` |
| "retry" + "payout" | `retry_payout` |
| "send" + "agreement" | `send_rent_agreement` |
| "signature" / "esign" | `send_agreement_for_signature` |

If intent matches → run action in `smartbot/actions.py`; else → GPT reply via `gpt_smart_reply`.

## Context

View loads owner’s rent context (current month paid/unpaid) to augment GPT responses.

## Business rules

1. Only **authenticated** users may call SmartBot.
2. Destructive/financial actions (payout retry, send agreement) must respect same rules as REST APIs (ownership, payment status).
3. OpenAI API key required (`OPENAI_API_KEY` in settings).

## Related files

- `smartbot/views.py`
- `smartbot/intents.py`
- `smartbot/actions.py`
- `smartbot/services/gpt_services.py`
- `smartbot/whatsapp_service.py`

## See also

- [Payout retry](./11-payout-retry.md)
- [Rent agreement drafts](./10-rent-agreement-drafts.md)
