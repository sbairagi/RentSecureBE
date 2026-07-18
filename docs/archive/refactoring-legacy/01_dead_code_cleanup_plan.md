# Dead Code Cleanup Plan

## Executive Summary

This document catalogs confirmed dead code in the RentSecure backend.

**Total estimated dead LOC:** ~10,000 lines (12-15% of codebase)

## Removal Candidates

### Dead Apps
1. **dashboard/** — No URL routes, dummy model, HTML template views in API-only backend
2. **ai_assistant/** — No URL routes, duplicate of smartbot/, empty models
3. **referral_and_earn/** — No URL routes, no views, unused model

### Dead Views
1. **core/views.py** — 4 dead views (AboutUsAPIView, HealthCheckAPIView, PrivacyPolicyAPIView, TermsConditionsAPIView)
2. **notification/views.py** — Entire file dead (not included in urls.py)
3. **finance/views.py** — 3 dead views (CAProfileViewSet, TaxSubmissionToCAViewSet, DownloadTaxFilesView)
4. **properties/views/dashboard_views.py** — Dead views not included in urls.py

### Unused Models
1. **dashboard/models.py** — DashboardStat model
2. **ai_assistant/models.py** — Empty placeholder
3. **referral_and_earn/models.py** — Referral model
4. **properties/models/subscription_models.py** — Placeholder module

### Dead Services
1. **properties/services/rent_service.py** — All methods raise NotImplementedError
2. **notification/services/notifications.py** — Duplicate, no imports
3. **notification/services/services.py** — Buggy, no imports
4. **notification/services/schedule_reminders.py** — Duplicate, no imports
5. **notification/services/voice_note_service.py** — Duplicate, no imports
6. **notification/services/late_fees_notify_service.py** — Duplicate, no imports
7. **rentsecure_be/services/razorpay_service.py** — Disabled payment gateway
8. **rentsecure_be/services/cashfree_service.py** — Disabled payment gateway
9. **rentsecure_be/utils/cashfree_payout.py** — Disabled utility

### Unused Serializers
1. **core/serializers.py** — All serializers dead (no views use them)

### Dead Signals
1. **properties/signals/renter_signals.py** — No receivers connected

### Placeholder Modules
1. **properties/admin/subscription_admin.py** — Empty placeholder
2. **properties/admin/usage_limit_admin.py** — Empty placeholder

### Dead Management Commands
1. **management/commands/seed_subscription_plans.py** — Dev-only
2. **management/commands/retry_failed_payouts.py** — Disabled payment gateway
3. **management/commands/send_rent_reminders.py** — Disabled WhatsApp
4. **management/commands/monthly_whatsapp_and_email_summary_to_owner.py** — Disabled WhatsApp
5. **management/commands/send_tax_reminders.py** — Disabled WhatsApp

### Dead Cron Scripts
1. **properties/cron/flag_defaulters.py** — Broken (imports non-existent function)

### Obsolete CI/Tooling Scripts
1. **tools/ci_guard.py** — CI orchestrator (belongs in .github/workflows/)
2. **tools/migration_guard.py** — CI tooling
3. **tools/migration_rollback_validator.py** — CI/testing tool
4. **tools/report_generator.py** — CI tooling
5. **tools/security_guard.py** — CI tooling
6. **tools/ship.py** — CI orchestrator
7. **tools/autofix.py** — CI tooling
8. **scripts/arch_audit.py** — One-time analysis script
9. **scripts/harden_actions.py** — One-time hardening script

### Commented-Out Code
1. **notification/services/notifications.py** — Commented-out examples
2. **notification/services/communication.py** — Commented-out examples
3. **ai_assistant/views.py** — Commented-out React Native code

## Merge Candidates

1. **notification/services/** — 7 files with significant overlap → consolidate to 3 files
2. **smartbot/services/chatbot_service.py + gpt_services.py** — Merge into single chat service
3. **PDF generation** — Consolidate into documents/utils/pdf_generator.py

## Deprecation Candidates

1. **rentsecure_be/services/razorpay_service.py** — Disabled payment gateway (Stage 2)
2. **rentsecure_be/services/cashfree_service.py** — Disabled payment gateway (Stage 2)
3. **rentsecure_be/utils/cashfree_payout.py** — Disabled utility (Stage 2)
4. **notification/services/whatsapp_service.py** — Disabled channel (Stage 2)
5. **notification/services/sms_service.py** — Disabled channel (Stage 2)
6. **notification/services/voice_service.py** — Disabled channel (Stage 2)
7. **rentsecure_be/services/i18n_service.py** — Disabled translation (Stage 2)
8. **rentsecure_be/services/leegality_service.py** — Low usage, move to documents/

## Needs Manual Verification

1. **properties/views/property_views.py** — Function-based views
2. **properties/views/rent_record_views.py** — Function-based views
3. **documents/views.py** — PDF generation endpoints
4. **management/commands/send_monthly_rent_summary.py** — Scheduled?
5. **management/commands/daily_rent_reminder.py** — Scheduled?
6. **management/commands/downgrade_expired_users.py** — Scheduled?
7. **management/commands/archive_expired_users_data.py** — Scheduled?
8. **management/commands/auto_deactivate_renters.py** — Scheduled?
9. **management/commands/check_vacant_units.py** — Scheduled?
10. **properties/cron/vacate_reminder.py** — Scheduled?
11. **smartbot/cron/reminders.py** — Scheduled?
12. **properties/serializers/renter_serializers.py** — RenterRentRecordSerializer
13. **rentsecure_be/services/leegality_service.py** — Agreement signing via chatbot
14. **rentsecure_be/services/i18n_service.py** — Multilingual notifications
15. **properties/repositories/** — Unused methods
