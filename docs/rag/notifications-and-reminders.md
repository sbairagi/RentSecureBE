# RAG-014 — Notifications & Reminders

**Metadata:** `id=RAG-014` | `tags=whatsapp,email,fcm,voice,reminders` | `app=notification`

## Channels

| Channel | Implementation |
|---------|----------------|
| SMS OTP | Twilio (`core/views.py` send_otp) |
| WhatsApp | `notification/services/whatsapp_service.py` |
| Email | Django SMTP (`settings.EMAIL_*`) |
| Push | `fcm_django`, model `notification.DeviceToken` |
| In-app | `notification.models.Notification` |
| Voice MP3 | `notification/services/voice_service.py` (gTTS) |

## Owner preferences

`core.NotificationPreference` — toggles for rent alerts, summaries, payout alerts.

## Trigger examples (intended)

| Event | Action |
|-------|--------|
| Rent record created | WhatsApp payment link to renter |
| Rent PAID | Voice thank-you, in-app notification, email receipt (via signals) |
| Payout success/fail | WhatsApp via `rent_notify_service` |
| Renter leaves unit | Vacancy WhatsApp to owner (signal) |
| Extra charges | Management command reminders |

## Signals dependency

Most post-payment notifications are in `properties/signals/__init__.py` → **requires** `properties.apps.ready()` to import signals.

## Scheduled jobs

- `properties/scheduler.py` — per-rent reminder cancel/schedule
- `django_celery_beat` in INSTALLED_APPS
- Commands: `management/commands/daily_rent_reminder.py` (broken import), `send_rent_*` variants

## UserSubscription timing

`rent_reminder_days_before` (default 7) on subscription model.

## Bugs

`docs/bugs/notification.md`, signal bugs in `docs/bugs/properties.md`
