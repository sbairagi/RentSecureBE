# Signals & Automation Rules

## Django signals (defined but often not wired)

### `core/signals.py`

On `User` **created**:

1. Create `UserProfile`
2. Create `NotificationPreference`
3. Create `UserSubscription` with plan `free`

**Status:** `core/apps.py` `ready()` does **not** import this module → **does not run** unless fixed.

### `properties/signals/__init__.py`

| Signal | Trigger | Action |
|--------|---------|--------|
| Building/Unit/Caretaker/Renter/Image/Doc save/delete | Usage sync | `update_usage_count()` |
| `RentRecord` save, PAID | Payment | Cancel reminder, voice note, notification, receipt email |
| `Renter` save, deactivated/revoked | Vacancy | WhatsApp owner if unit empty |
| `Renter` exit | Offboarding | Final invoice PDF, archive renter data |

**Status:** `properties/apps.py` does **not** import signals → receivers **inactive**.

## Management commands

| Command | Purpose | Status |
|---------|---------|--------|
| `generate_monthly_rent_records` | Create monthly `RentRecord` rows | Broken (`rent.models` import) |
| `apply_late_fees` | Apply late fees | Verify before use |
| `daily_rent_reminder` | Rent due reminders | Broken import |
| `send_rent_due_reminders` | Due reminders | Check implementation |
| `send_rent_reminders` | Reminders | Active pattern |
| `monthly_whatsapp_and_email_summary_to_owner` | Owner summary | Scheduled |
| `auto_deactivate_renters` | End expired agreements | Scheduled |
| `downgrade_expired_users` | Trim data after grace | **Commented out** |
| `archive_expired_users_data` | Archive old data | Check status |
| `seed_subscription_plans` | Seed plans | **Commented out** |
| `check_vacant_units` | Vacancy sync | Check status |
| `generate_monthly_extra_charges` | Extra charges | `properties/management/` |

## Celery / beat

- `django_celery_beat` in `INSTALLED_APPS`
- `properties/scheduler.py` — schedule/cancel per-rent reminder tasks

## Cron modules

- `properties/cron/vacate_reminder.py`
- `properties/cron/flag_defaulters.py` — imports defaulter function from signals directly

## Fix to enable signals

```python
# core/apps.py
def ready(self):
    import core.signals  # noqa: F401

# properties/apps.py
def ready(self):
    import properties.signals  # noqa: F401
```

## Related files

- `core/signals.py`
- `properties/signals/__init__.py`
- `management/commands/`
- `properties/scheduler.py`

## See also

- [Known behaviors](./14-known-behaviors-and-edge-cases.md)
- [Notifications](./17-notifications.md)
