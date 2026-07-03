# RAG-016 — Signals, Celery & Management Commands

**Metadata:** `id=RAG-016` | `tags=signals,celery,cron,management commands`

## Django signals

### `core/signals.py`

- `post_save` User → create UserProfile, NotificationPreference, Free UserSubscription

### `properties/signals/__init__.py`

- Usage sync on Building/Unit/Renter/Image/Document save/delete
- RentRecord PAID → cancel reminder, voice note, notification, receipt email
- Renter exit → vacancy WhatsApp, final invoice, archive

**Critical:** Both apps need `import ...signals` in `AppConfig.ready()`. Currently **often empty** → signals inactive.

## Celery / beat

- `django_celery_beat` installed
- `properties/scheduler.py` — schedule/cancel rent reminder tasks

## Management commands (`management/commands/`)

| Command | Purpose | Status |
|---------|---------|--------|
| `generate_monthly_rent_records` | Monthly RentRecord rows | **Broken** (`rent.models`) |
| `daily_rent_reminder` | Reminder cadence | **Broken** imports |
| `seed_subscription_plans` | Seed plans | Commented out |
| `downgrade_expired_users` | Trim after grace | Commented out |
| `send_rent_reminders` / `send_rent_due_reminders` | Reminders | Verify imports |
| `apply_late_fees` | Late fees | Verify |
| `monthly_whatsapp_and_email_summary_to_owner` | Owner summary | Verify |

Also: `properties/management/commands/generate_monthly_extra_charges.py`

## Properties cron modules

- `properties/cron/vacate_reminder.py`
- `properties/cron/flag_defaulters.py`

## For AI: safe assumption

Do not claim cron jobs work without verifying imports. Point to `docs/bugs/management_commands.md`.
