# Notifications Rules

## Channels

| Channel | Service |
|---------|---------|
| WhatsApp / SMS | Twilio (`notification.services.whatsapp_service`) |
| Email | Django SMTP (`settings.EMAIL_*`) |
| Push | FCM (`fcm_django`, `DeviceToken` model) |
| In-app | `notification.models.Notification` |
| Voice | gTTS MP3 (`notification/services/voice_service.py`) |

## Models

- **`Notification`** — `user`, `title`, `message`, `is_read`, `created_at`
- **`DeviceToken`** — FCM/Expo token per user

## Owner preferences (`core.NotificationPreference`)

| Field | Default |
|-------|---------|
| `rent_alerts_whatsapp` | true |
| `rent_alerts_email` | true |
| `monthly_summary_email` | true |
| `monthly_summary_whatsapp` | false |
| `payout_alerts_whatsapp` | true |
| `payout_alerts_email` | false |

Respect these flags when sending category-specific messages (implementation varies by service).

## Rent-related notifications

| Event | Behavior |
|-------|----------|
| Rent record created | WhatsApp payment link to renter |
| Rent PAID | Thank-you voice note, in-app notification, receipt email (if signals wired) |
| Payout success/failure | WhatsApp to owner/renter via `rent_notify_service` |
| Late fee | `late_fees_notify_service` to owner and renter |
| Extra charges | `send_extra_charge_reminders` management command |
| Vacant unit | WhatsApp to owner when last active renter leaves |

## Scheduled reminders

- Per-rent jobs via `properties/scheduler.py` (Celery beat)
- `UserSubscription.rent_reminder_days_before` (default 7)
- Commands: `daily_rent_reminder`, `send_rent_due_reminders` (some broken imports)

## Voice notes

`generate_voice_note(text, lang)` — returns temp MP3 path; failures return empty string.

## Related files

- `notification/services/`
- `notification/management/commands/`
- `properties/signals/__init__.py` (intended triggers)

## See also

- [Signals & automation](./22-signals-and-automation.md)
- [Rent records](./08-rent-records.md)
