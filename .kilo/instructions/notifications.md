# Notification Module Rules

Module-specific rules for the notification system.

## Year 1 Notification Strategy

### Core Principle
Use only free notification channels. Do NOT depend on paid channels unless explicitly enabled via feature flags.

### Enabled Channels (Year 1)

| Channel | Provider | Cost | Use Case |
|---------|----------|------|----------|
| Email | Django SMTP / AWS SES Free Tier | Free (first 62,000 emails/month) | Receipts, alerts, password reset |
| Push Notifications | Firebase Cloud Messaging (FCM) | Free | Real-time alerts, payment reminders |
| In-App Notifications | Database-backed (PostgreSQL) | Free | Activity feed, announcements |

### Disabled Channels (Behind Feature Flags)

| Channel | Status | Future Upgrade |
|---------|--------|---------------|
| WhatsApp Business API | `False` | Stage 2 |
| SMS (Twilio / MSG91 / etc.) | `False` | Stage 2 |
| Voice Calls | `False` | Stage 3 |
| Telegram Bot | `False` | Stage 3 |

### Architecture Requirements

- **Notification Service Interface:** `notifications.ports.NotificationChannel`
- **Adapters:**
  - `notifications.adapters.email.EmailAdapter` (enabled)
  - `notifications.adapters.fcm.FirebaseAdapter` (enabled)
  - `notifications.adapters.inapp.InAppAdapter` (enabled)
  - `notifications.adapters.whatsapp.WhatsAppAdapter` (disabled)
  - `notifications.adapters.sms.SMSAdapter` (disabled)
- **Feature Flags:**
  - `WHATSAPP_NOTIFICATIONS_ENABLED` = `False`
  - `SMS_NOTIFICATIONS_ENABLED` = `False`
- **UI Requirement:** Display "Coming Soon" badge on WhatsApp/SMS notification preferences

### Future Notification Integrations (Stage 2)

The codebase MUST contain:
- `notifications.adapters.whatsapp.WhatsAppAdapter` (disabled)
- `notifications.adapters.sms.SMSAdapter` (disabled)
- Template management for WhatsApp/SMS
- Fallback logic: WhatsApp → SMS → Email → Push

### Migration Strategy

1. Implement adapters with full provider abstraction
2. Test in sandbox environment
3. Enable for 10% of users (canary)
4. Monitor delivery rates and costs
5. Full rollout after 2 weeks of stable operation

### Expected Trigger Point for Stage 2

- User feedback indicates demand for WhatsApp/SMS
- Email open rates drop below 20%
- Users request instant delivery channels
