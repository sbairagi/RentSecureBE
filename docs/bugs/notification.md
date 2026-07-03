# Bugs — `notification` app

WhatsApp, email, push, voice notes.

---

## NOTIF-001 | P1 — Post-payment automation depends on unwired signals

**Files:** `notification/services/voice_note_service.py`, `properties/signals/__init__.py`

- `send_thank_you_voice_note` called from `handle_rent_payment` signal.
- Signals not registered in `properties/apps.py`.

**Impact:** Voice thank-you and related notifications never fire on PAID.

---

## NOTIF-002 | P2 — `voice_service.py` failures return empty string

**File:** `notification/services/voice_service.py`

```python
except Exception as e:
    print("Voice note generation failed:", e)
    return ""
```

**Impact:** Callers may treat empty path as success; uses `print` not logging.

---

## NOTIF-003 | P2 — Payout notifications use wrong profile path

**Files:** `rentsecure_be/services/cashfree_service.py`, `core/views.py` (cashfree webhook)

- References `owner.profile.whatsapp_number` instead of `userprofile` / `User.whatsapp_number`.

**Impact:** WhatsApp payout alerts fail silently.

---

## NOTIF-004 | P2 — Vacancy message never sent (signal bugs)

**File:** `properties/signals/__init__.py` → `send_whatsapp_message`

- Depends on PROP-004, PROP-005 (unit_number, profile).

---

## NOTIF-005 | P3 — `DeviceToken` / FCM not verified in audit

**Note:** Push paths exist in settings (`FCM_DJANGO_SETTINGS`) but integration should be tested separately; no registration API reviewed here.

---

## NOTIF-006 | P2 — Management commands may use broken imports

**Files:** `notification/management/commands/*`

- Depend on working `properties` models and renter data; verify each command imports (see [management_commands.md](./management_commands.md)).
