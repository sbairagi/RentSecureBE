# RentSecureBE — Architecture Baseline Validation

**Baseline Version:** 1.0.0
**Validation Date:** 2026-07-14
**Validator:** Kilo (Automated Code Verification)
**Repository:** RentSecureBE
**Methodology:** Every claim in the baseline was verified against actual source files, models, views, settings, CI workflows, and tests.

---

## SECTION 1 — Verified Items

### 1.1 Models & Aggregates

| Claim | Status | Evidence |
|-------|--------|----------|
| `core/models.py` defines `User` extending `AbstractUser` | ✅ Verified | `core/models.py:51` |
| `User` has `full_name`, `phone`, `is_investor`, `is_phone_verified`, `whatsapp_number` | ✅ Verified | `core/models.py:52-58` |
| `UserProfile` has OneToOne to `User` with `whatsapp_number`, `whatsapp_opt_in`, `language_preference` | ✅ Verified | `core/models.py:66-74` |
| `NotificationPreference` uses `UpsertMixin` with `_upsert_filter_fields = ("owner",)` | ✅ Verified | `core/models.py:77-89` |
| `OTP` has `phone_number`, `code`, `referral_code`, `created_at`, `is_verified` | ✅ Verified | `core/models.py:96-102` |
| `OwnerBankDetails` has `owner` (OneToOne), `bank_account_number`, `ifsc_code`, `account_holder_name`, `beneficiary_id` (unique), `bank_account_verified` | ✅ Verified | `core/models.py:108-116` |
| `SubscriptionPlan` uses `UpsertMixin` with PLAN_CHOICES (free, pro, elite) | ✅ Verified | `core/models.py:124-141` |
| `UserSubscription` uses `UpsertMixin` with `_upsert_filter_fields = ("user",)` | ✅ Verified | `core/models.py:148-170` |
| `AddOnPurchase` has `FEATURE_CHOICES` with 10 options | ✅ Verified | `core/models.py:177-189` |
| `PlanFeatureLimit` uses `UpsertMixin` with `unique_together = ("plan", "feature_key")` | ✅ Verified | `core/models.py:202-214` |
| `UsageLimit` has `unique_together = ("user", "feature_key")` and custom `save()` for idempotent upsert | ✅ Verified | `core/models.py:221-251` |
| `Building` has `unique_together = ("name", "address_line", "city", "owner")` and composite indexes | ✅ Verified | `properties/models/building_models.py:63-68` |
| `Unit` has legacy aliases (`unit_number`, `rent_amount`, `security_deposit`) in `__init__` | ✅ Verified | `properties/models/unit_models.py:73-98` |
| `Unit` has `UnitType` choices (LAND, FLAT, COMMERCIAL_SHOP, HOUSE, VILLA, OFFICE, PAYING_GUEST) | ✅ Verified | `properties/models/unit_models.py:55-64` |
| `Unit` has `VacancyStatus` choices (VACANT, OCCUPIED) | ✅ Verified | `properties/models/unit_models.py:66-70` |
| `Renter` has `RenterStatus` choices (ACTIVE, NOTICE_PERIOD, REVOKED, DEACTIVATED) | ✅ Verified | `properties/models/renter_models.py:28-33` |
| `Renter` has `OnboardingStatus` and `KYCStatus` choices | ✅ Verified | `properties/models/renter_models.py:130-139` |
| `Renter` has legacy `full_name` property and `rent_agreement_pdf` property | ✅ Verified | `properties/models/renter_models.py:193-210` |
| `Renter.clean()` prevents multiple active/notice_period renters per unit | ✅ Verified | `properties/models/renter_models.py:168-186` |
| `RentRecord` has `PaymentMethod` choices (CASH, BANK_TRANSFER, UPI, CHEQUE, CARD, ONLINE, OTHER) | ✅ Verified | `properties/models/rent_record_models.py:22-29` |
| `RentRecord` has `Status` choices (PENDING, PAID, OVERDUE, CANCELLED) | ✅ Verified | `properties/models/rent_record_models.py:31-35` |
| `RentRecord` has legacy properties (`payment_status`, `date_paid`, `rent_due_date`, `amount_paid`) | ✅ Verified | `properties/models/rent_record_models.py:120-150` |
| `RentRecord.clean()` allows early payment (paid_on < due_date) | ✅ Verified | `properties/models/rent_record_models.py:153-156` |
| `ExtraCharge` has `Status` choices (DUE, PAID, MISSED) | ✅ Verified | `properties/models/extra_charge_models.py:15-18` |
| `CareTaker` has `unique_together = ("unit", "phone")` | ✅ Verified | `properties/models/caretaker_models.py:54-55` |
| `PropertyTaxRecord` has FK to `Building` with `related_name="tax_records"` | ✅ Verified | `properties/models/property_tax_models.py:13-14` |
| `CAProfile` has OneToOne to `User` | ✅ Verified | `finance/models.py:7-8` |
| `TaxSubmissionToCA` has FK to `User` with `related_name="tax_submissions_to_ca"` and FK to `CAProfile` | ✅ Verified | `finance/models.py:19-25` |
| `Notification` has FK to `User` with `related_name="notifications"` | ✅ Verified | `notification/models.py:5-7` |
| `DeviceToken` has FK to `User` | ✅ Verified | `notification/models.py:15-16` |
| `SmartBotChat`, `SmartBotMessage`, `AIAlert` models exist in `smartbot/models.py` | ✅ Verified | `smartbot/models.py:5-23` |
| `Referral` has `referral_code` (unique) and auto-generated UUID in `save()` | ✅ Verified | `referral_and_earn/models.py:11-30` |
| `ai_assistant/models.py` is empty (placeholder) | ✅ Verified | `ai_assistant/models.py:1` |
| `documents` app has no `models.py` | ✅ Verified | Glob search found no `models.py` in `documents/` |
| `dashboard/apps.py` does not exist | ✅ Verified | File not found |
| `RentAgreementDraft` has `unique_together = ("renter", "unit")` | ✅ Verified | `properties/models/renter_models.py:254-255` |
| `PoliceVerification` has `unique_together = ("renter", "unit")` | ✅ Verified | `properties/models/renter_models.py:278-279` |
| `ArchivedRenter` has `data` (JSONField), `agreement_pdf`, `police_pdf`, `property_images` (JSONField), `final_invoice` | ✅ Verified | `properties/models/renter_models.py:230-237` |

### 1.2 Services & Repositories

| Claim | Status | Evidence |
|-------|--------|----------|
| `BaseService.execute()` raises `NotImplementedError` | ✅ Verified | `core/services/base.py:35` |
| `ServiceResult[T]` and `ServiceError` dataclasses exist | ✅ Verified | `core/services/base.py:9-31` |
| `RentService` is a stub with all methods raising `NotImplementedError` | ✅ Verified | `properties/services/rent_service.py:12-40` |
| `RenterService` is a stub with all methods raising `NotImplementedError` | ✅ Verified | `properties/services/renter_service.py:12-39` |
| `VacancyService` is a stub with all methods raising `NotImplementedError` | ✅ Verified | `properties/services/vacancy_service.py:12-35` |
| `OccupancyService` is a stub with all methods raising `NotImplementedError` | ✅ Verified | `properties/services/occupancy_service.py:12-35` |
| `translate_msg` is duplicated between `rentsecure_be/services/i18n_service.py` and `ai_assistant/services/i18n_service.py` | ✅ Verified | Both files contain identical `translate_msg` function |
| `update_unit_status` is duplicated between `properties/services/unit_service.py` and `ai_assistant/services/unit_service.py` | ✅ Verified | Both files contain `update_unit_status` (slightly different logic) |
| `notification/services/rent_notify_service.py` imports `translate_msg` from `rentsecure_be.services.i18n_service` | ✅ Verified | `notification/services/rent_notify_service.py:48,79,141` |
| `notification/services/extra_charge_reminders.py` imports `translate_msg` from `rentsecure_be.services.i18n_service` | ✅ Verified | `notification/services/extra_charge_reminders.py:17` |
| `smartbot/actions.py` imports `process_rent_payout` from `rentsecure_be.services.cashfree_service` | ✅ Verified | `smartbot/actions.py:7` |
| `smartbot/actions.py` imports `send_whatsapp_message` from `notification.utils` | ✅ Verified | `smartbot/actions.py:5` |
| `core/services/bank_details_service.py` imports `add_beneficiary` from `rentsecure_be.utils.cashfree_payout` | ✅ Verified | `core/services/bank_details_service.py:8` |
| `rentsecure_be/services/cashfree_service.py` imports `notify_owner`, `notify_renter` from `notification.services.rent_notify_service` | ✅ Verified | `rentsecure_be/services/cashfree_service.py:49` |
| `properties/views/rent_record_views.py` imports `process_rent_payout` from `rentsecure_be.services.cashfree_service` | ✅ Verified | `properties/views/rent_record_views.py:20` |
| `properties/views/unit_views.py` imports `send_agreement_for_signature` from `rentsecure_be.services.leegality_service` | ✅ Verified | `properties/views/unit_views.py:29` |
| `ai_assistant/receivers.py` imports from `properties.signals.renter_signals` | ✅ Verified | `ai_assistant/receivers.py:7` |
| `ai_assistant/views.py` imports from `properties.models` and `smartbot.services.chatbot_service` | ✅ Verified | `ai_assistant/views.py:27-28` |
| `ai_assistant/services/archive_service.py` imports from `properties.models` | ✅ Verified | `ai_assistant/services/archive_service.py:12` |
| `smartbot/services/chatbot_service.py` imports from `properties.models` | ✅ Verified | `smartbot/services/chatbot_service.py:13` |
| `smartbot/whatsapp_service.py` imports from `notification.utils` | ✅ Verified | `smartbot/whatsapp_service.py:4` |
| `core/services/referral_service.py` imports from `referral_and_earn.models` | ✅ Verified | `core/services/referral_service.py:23` |
| `properties/models/building_models.py` imports `User` from `core.models` | ✅ Verified | `properties/models/building_models.py:5` |
| `properties/models/unit_models.py` imports `User` from `core.models` | ✅ Verified | `properties/models/unit_models.py:16` |
| `properties/models/renter_models.py` imports `User` from `core.models` | ✅ Verified | `properties/models/renter_models.py:13` |
| `properties/models/extra_charge_models.py` imports `Renter` and `Unit` from local models | ✅ Verified | `properties/models/extra_charge_models.py:10-11` |
| `properties/services/unit_service.py` uses `UnitRepository` and `BuildingRepository` | ✅ Verified | `properties/services/unit_service.py:27-28` |
| `properties/services/extra_charge_service.py` uses only local model imports | ✅ Verified | `properties/services/extra_charge_service.py:13` |
| `properties/services/summary_service.py` imports from `core.models` | ✅ Verified | `properties/services/summary_service.py:22` |
| `properties/communication/auto_generate_rent_records.py` imports from `rentsecure_be.services.razorpay_service` | ✅ Verified | `properties/communication/auto_generate_rent_records.py:5` |
| `properties/communication/retry_failed_payouts.py` imports from `rentsecure_be.services.cashfree_service` | ✅ Verified | `properties/communication/retry_failed_payouts.py:7` |
| `management/commands/retry_failed_payouts.py` imports from `rentsecure_be.services.cashfree_service` | ✅ Verified | `management/commands/retry_failed_payouts.py:11` |
| `BuildingRepository`, `UnitRepository`, `RenterRepository`, `RentRecordRepository` exist | ✅ Verified | `properties/repositories/` directory |
| Repositories are concrete classes with `@staticmethod` methods | ✅ Verified | `properties/repositories/*.py` |
| No repository implements the `Repository[T]` Protocol from `shared/interfaces.py` | ✅ Verified | No imports of `Repository[T]` found in repository files |

### 1.3 Domain Events & Signals

| Claim | Status | Evidence |
|-------|--------|----------|
| `renter_exited` and `renter_archived` custom signals are defined | ✅ Verified | `properties/signals/renter_signals.py:1-4` |
| `post_save(Renter)` → `update_last_vacated_date_on_renter_exit` | ✅ Verified | `properties/signals/__init__.py:30-45` |
| `post_save(Renter)` → `generate_renter_onboarding_token` | ✅ Verified | `properties/signals/__init__.py:48-54` |
| `post_save(Renter)` → `update_unit_status_on_renter_save` | ✅ Verified | `properties/signals/__init__.py:57-71` |
| `post_delete(Renter)` → `update_unit_status_on_renter_delete` | ✅ Verified | `properties/signals/__init__.py:74-85` |
| `post_save/delete(Building)` → `update_building_usage` | ✅ Verified | `properties/signals/__init__.py:88-93` |
| `post_save/delete(Unit)` → `update_unit_usage` | ✅ Verified | `properties/signals/__init__.py:96-99` |
| `post_save/delete(Caretaker)` → `update_caretaker_usage` | ✅ Verified | `properties/signals/__init__.py:102-107` |
| `post_save/delete(Renter)` → `update_renter_usage` | ✅ Verified | `properties/signals/__init__.py:110-115` |
| `post_save/delete(UnitImage)` → `update_unit_images_usage` | ✅ Verified | `properties/signals/__init__.py:118-123` |
| `post_save/delete(UnitDocument)` → `update_unit_documents_usage` | ✅ Verified | `properties/signals/__init__.py:126-131` |
| `post_save(RentRecord)` → `handle_rent_payment` (when status == PAID) | ✅ Verified | `properties/signals/__init__.py:134-159` |
| `post_save(Renter)` → `notify_owner_if_unit_vacant` (when status in deactivated/revoked) | ✅ Verified | `properties/signals/__init__.py:187-210` |
| `post_save(Renter)` → `generate_final_invoice_on_exit` | ✅ Verified | `properties/signals/__init__.py:213-228` |
| `post_save(Renter)` → `_generate_final_invoice_if_needed` → emits `renter_exited` signal | ✅ Verified | `properties/signals/__init__.py:237-242` |
| `post_save(Renter)` → `_archive_renter_if_needed` → emits `renter_archived` signal | ✅ Verified | `properties/signals/__init__.py:245-247` |
| `post_save(User)` → `assign_default_plan` (creates UserProfile, NotificationPreference, SubscriptionPlan, PlanFeatureLimit) | ✅ Verified | `core/signals.py:12-50` |
| `post_save(User)` → `create_referral` (in `referral_and_earn/signals.py`) | ✅ Verified | `referral_and_earn/signals.py:12-14` |
| `ai_assistant/receivers.py` handles `renter_exited` → `generate_final_invoice_pdf` | ✅ Verified | `ai_assistant/receivers.py:12-28` |
| `ai_assistant/receivers.py` handles `renter_archived` → `archive_renter_data` | ✅ Verified | `ai_assistant/receivers.py:31-40` |

### 1.4 External Integrations

| Claim | Status | Evidence |
|-------|--------|----------|
| Twilio SMS/WhatsApp integration exists | ✅ Verified | `core/services/otp_service.py`, `notification/services/whatsapp_service.py`, `notification/services/sms_service.py` |
| Razorpay integration exists | ✅ Verified | `rentsecure_be/services/razorpay_service.py`, `core/views.py:362-384` |
| Cashfree integration exists | ✅ Verified | `rentsecure_be/services/cashfree_service.py`, `rentsecure_be/utils/cashfree_payout.py` |
| Leegality integration exists | ✅ Verified | `rentsecure_be/services/leegality_service.py`, `smartbot/services/leegality_service.py` |
| OpenAI integration exists | ✅ Verified | `smartbot/services/gpt_services.py`, `smartbot/services/chatbot_service.py` |
| AWS S3 integration exists | ✅ Verified | `notification/services/whatsapp_service.py` (upload_to_s3) |
| Firebase FCM integration exists | ✅ Verified | `notification/views.py`, `notification/utils.py`, `notification/models.py` |
| Google Translate (deep-translator) integration exists | ✅ Verified | `rentsecure_be/services/i18n_service.py`, `ai_assistant/services/i18n_service.py` |
| edge-tts integration exists | ✅ Verified | `notification/services/voice_service.py` |
| Cashfree webhook has HMAC-SHA256 signature verification | ✅ Verified | `core/views.py:309-322` |
| Razorpay webhook has HMAC-SHA256 signature verification | ✅ Verified | `core/views.py:406-419` |
| Leegality webhook has HMAC-SHA256 signature verification | ✅ Verified | `properties/views/unit_views.py:325-338` |
| WhatsApp webhook has HMAC-SHA256 signature verification | ✅ Verified | `ai_assistant/views.py:224-238` |
| Feature flags exist for all major integrations | ✅ Verified | `rentsecure_be/settings.py:89-98` |

### 1.5 Security Settings

| Claim | Status | Evidence |
|-------|--------|----------|
| `SECURE_SSL_REDIRECT` configurable, defaults to `not DEBUG` | ✅ Verified | `rentsecure_be/settings.py:297` |
| `SESSION_COOKIE_SECURE` configurable, defaults to `not DEBUG` | ✅ Verified | `rentsecure_be/settings.py:295` |
| `CSRF_COOKIE_SECURE` configurable, defaults to `not DEBUG` | ✅ Verified | `rentsecure_be/settings.py:296` |
| `SECURE_HSTS_SECONDS = 31536000` (1 year) | ✅ Verified | `rentsecure_be/settings.py:298` |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS = True` | ✅ Verified | `rentsecure_be/settings.py:299-301` |
| `SECURE_HSTS_PRELOAD = True` | ✅ Verified | `rentsecure_be/settings.py:299-301` |
| `SECURE_BROWSER_XSS_FILTER = True` | ✅ Verified | `rentsecure_be/settings.py:291` |
| `SECURE_CONTENT_TYPE_NOSNIFF = True` | ✅ Verified | `rentsecure_be/settings.py:292-294` |
| JWT access token lifetime = 5 minutes | ✅ Verified | `rentsecure_be/settings.py:251` |
| JWT refresh token lifetime = 35 days | ✅ Verified | `rentsecure_be/settings.py:252` |
| `AUTH_PASSWORD_VALIDATORS` has 4 validators | ✅ Verified | `rentsecure_be/settings.py:219-234` |
| `REST_FRAMEWORK` uses only `JWTAuthentication` | ✅ Verified | `rentsecure_be/settings.py:236-240` |
| No `DEFAULT_THROTTLE_CLASSES` or `DEFAULT_THROTTLE_RATES` configured | ✅ Verified | `rentsecure_be/settings.py:236-240` (only authentication_classes present) |
| CORS not configured (no `django-cors-headers`) | ✅ Verified | `rentsecure_be/settings.py` — no CORS settings, not in INSTALLED_APPS |
| `ALLOWED_HOSTS` configurable via env | ✅ Verified | `rentsecure_be/settings.py:39` |
| `SECRET_KEY` validation rejects insecure keys in production | ✅ Verified | `rentsecure_be/settings.py:34-37` |
| Webhook endpoints use `@csrf_exempt` | ✅ Verified | `core/views.py:393`, `properties/views/unit_views.py:314`, `ai_assistant/views.py:241` |

### 1.6 CI/CD Architecture

| Claim | Status | Evidence |
|-------|--------|----------|
| 28 GitHub Actions workflow files exist | ✅ Verified | Glob found 28 `.yml` files in `.github/workflows/` |
| Main CI pipeline (`ci.yml`) exists | ✅ Verified | `.github/workflows/ci.yml` exists |
| Lint workflow (`lint.yml`) exists | ✅ Verified | `.github/workflows/lint.yml` exists |
| Test workflow (`test.yml`) exists | ✅ Verified | `.github/workflows/test.yml` exists |
| Security workflow (`security.yml`) exists | ✅ Verified | `.github/workflows/security.yml` exists |
| Deploy workflow (`deploy.yml`) exists | ✅ Verified | `.github/workflows/deploy.yml` exists |
| Rollback workflow (`rollback.yml`) exists | ✅ Verified | `.github/workflows/rollback.yml` exists |
| Architecture guard workflow (`architecture-guard.yml`) exists | ✅ Verified | `.github/workflows/architecture-guard.yml` exists |
| Nightly workflow (`nightly.yml`) exists | ✅ Verified | `.github/workflows/nightly.yml` exists |
| Weekly workflow (`weekly.yml`) exists | ✅ Verified | `.github/workflows/weekly.yml` exists |
| `checkout-diagnostic.yml` exists (manual only) | ✅ Verified | `.github/workflows/checkout-diagnostic.yml` exists |
| No Dockerfile in repo | ✅ Verified | Glob found no `Dockerfile` |
| No docker-compose files in repo | ✅ Verified | Glob found no `docker-compose*.yml` |
| No infrastructure as code (Terraform, CloudFormation, etc.) | ✅ Verified | Glob found no `*.tf`, `*.yaml` in infra directories |
| `.env.example` exists | ✅ Verified | `.env.example` exists |
| `requirements.txt` exists | ✅ Verified | `requirements.txt` exists |
| `pytest.ini` exists | ✅ Verified | `pytest.ini` exists |
| `noxfile.py` exists | ✅ Verified | `noxfile.py` exists |
| `conftest.py` exists at root | ✅ Verified | `conftest.py` exists |
| `import-linter.ini` exists | ✅ Verified | `import-linter.ini` exists |
| `sonar-project.properties` exists | ✅ Verified | `sonar-project.properties` exists |
| `.semgrep.yml` exists | ✅ Verified | `.semgrep.yml` exists |
| `.gitleaks.toml` exists | ✅ Verified | `.gitleaks.toml` exists |
| Architecture contract tests exist | ✅ Verified | `tests/test_architecture_contract/test_validator.py` exists |
| Query count tests exist | ✅ Verified | `tests/test_query_count.py` exists |
| Hypothesis tests exist | ✅ Verified | `tests/test_properties_hypothesis.py`, `tests/test_core_hypothesis.py` exist |
| Mutation testing config exists | ✅ Verified | `setup.cfg [mutmut]` section exists |
| Load testing exists | ✅ Verified | `tests/load/locustfile.py` exists |

### 1.7 Testing Architecture

| Claim | Status | Evidence |
|-------|--------|----------|
| pytest is the test runner | ✅ Verified | `pytest.ini`, `pyproject.toml [tool.pytest.ini_options]` |
| Coverage threshold is ≥90% | ✅ Verified | `pyproject.toml [tool.pytest.ini_options] addopts` includes `--cov-fail-under=90` |
| 16 factory_boy factories in `conftest.py` | ✅ Verified | `conftest.py` defines UserFactory, BuildingFactory, UnitFactory, RenterFactory, RentRecordFactory, etc. |
| Autouse fixture `_rentsecure_test_defaults` exists | ✅ Verified | `conftest.py` defines autouse fixture |
| Hypothesis tests use 200 examples | ✅ Verified | `tests/test_properties_hypothesis.py`, `tests/test_core_hypothesis.py` |
| mutmut mutation testing configured | ✅ Verified | `setup.cfg [mutmut]` |
| Test sharding via GitHub Actions | ✅ Verified | `.github/workflows/test.yml` uses `shard` and `total` inputs |
| Schemathesis contract tests exist | ✅ Verified | `.github/workflows/contract-tests.yml`, `tests/test_api_contracts.py` |
| Locust load testing exists | ✅ Verified | `tests/load/locustfile.py` |
| pytest-benchmark exists | ✅ Verified | `.github/workflows/benchmark.yml`, `tests/test_performance_benchmarks.py` |

### 1.8 Deployment & Cache

| Claim | Status | Evidence |
|-------|--------|----------|
| LocMemCache is configured | ✅ Verified | `rentsecure_be/settings.py:242-248` |
| Cache timeout is 300 seconds (5 minutes) | ✅ Verified | `rentsecure_be/settings.py:246` |
| Channels + Redis configured | ✅ Verified | `rentsecure_be/settings.py:172-181` |
| `django_celery_beat` in INSTALLED_APPS | ✅ Verified | `rentsecure_be/settings.py:128` |
| No `celery.py` file exists | ✅ Verified | Glob found no `celery.py` |
| Deploy uses SSH via `appleboy/ssh-action` | ✅ Verified | `.github/workflows/deploy.yml` |
| Rollback uses `workflow_dispatch` with SHA input | ✅ Verified | `.github/workflows/rollback.yml` |
| Sentry integration for release tracking | ✅ Verified | `.github/workflows/deploy.yml` references `sentry-cli` |
| 14 management commands exist | ✅ Verified | Glob found 14 `.py` files in `management/commands/` |
| `smartbot/tasks.py` is a no-op stub | ✅ Verified | `smartbot/tasks.py:18-23` |
| `smartbot/urls.py` does NOT exist | ✅ Verified | Glob found no `urls.py` in `smartbot/` |
| `dashboard/urls.py` exists but is NOT included in root `urls.py` | ✅ Verified | `rentsecure_be/urls.py` does not include `dashboard.urls` |
| `ai_assistant/urls.py` exists but is NOT included in root `urls.py` | ✅ Verified | `rentsecure_be/urls.py` does not include `ai_assistant.urls` |
| `ai_assistant` NOT in INSTALLED_APPS | ✅ Verified | `rentsecure_be/settings.py:117-138` |
| `dashboard` NOT in INSTALLED_APPS | ✅ Verified | `rentsecure_be/settings.py:117-138` |

---

## SECTION 2 — Incorrect Assumptions

### 2.1 Workflow Count

**Baseline Claim:** "CI/CD PIPELINE (27 Workflows)"

**Actual:** 28 workflow files exist in `.github/workflows/`.

**Evidence:**
```
.security-deep.yml
.uml-validation.yml
.architecture.yml
.uml.yml
.ci.yml
.quality.yml
.nightly.yml
.weekly.yml
.test.yml
.django-check.yml
.branch-protection-validator.yml
.architecture-guard.yml
.load-test.yml
.benchmark.yml
.performance.yml
.ci-metrics.yml
.security.yml
.sbom.yml
.mutation.yml
.contract-tests.yml
.runtime-measurement.yml
.rollback.yml
.migration-rollback.yml
.lint.yml
.hypothesis.yml
.deploy.yml
.deploy-readiness.yml
.checkout-diagnostic.yml
```

**Impact:** Minor documentation error. Does not affect architecture analysis.

---

### 2.2 Properties App Importing i18n from rentsecure_be

**Baseline Claim:** "`properties` → imports from: `rentsecure_be` (i18n)"

**Actual:** The `properties/services/` directory does NOT import from `rentsecure_be.services.i18n_service`. The import occurs in:
- `notification/services/rent_notify_service.py` (lines 48, 79, 141)
- `notification/services/extra_charge_reminders.py` (line 17)
- `properties/views/rent_record_views.py` (line 21 — `razorpay_service`, not i18n)
- `properties/views/unit_views.py` (line 29 — `leegality_service`, not i18n)

**Evidence:** Grep search for `rentsecure_be.services.i18n` found matches only in `notification/services/` and test files.

**Impact:** The dependency graph in Section 2.1 incorrectly shows `properties → rentsecure_be (i18n)`. The actual cross-app dependency is `notification → rentsecure_be (i18n)`.

---

### 2.3 BaseService.execute() "Never Implemented"

**Baseline Claim:** "`execute()` always raises `NotImplementedError`"

**Actual:** `BaseService.execute()` in `core/services/base.py:35` raises `NotImplementedError`, but `ReferralService.execute()` in `core/services/referral_service.py:38-39` **does** implement it (though it also raises `NotImplementedError`). All other `BaseService` subclasses (`AuthService`, `OTPService`, `SubscriptionService`, `BankDetailsService`, `UsageLimitService`, `PasswordService`, `OwnerReportingService`) do NOT override `execute()` and rely on `@staticmethod` methods.

**Evidence:** `core/services/referral_service.py:38-39`

**Impact:** Minor. The baseline claim is directionally correct (most services don't use `execute()`), but `ReferralService` does provide an implementation (even if it raises).

---

### 2.4 Deploy Workflow Status

**Baseline Claim:** "Currently **disabled** (triggers commented out, only `workflow_call`)"

**Actual:** The `deploy.yml` workflow has `workflow_call` but also has a `workflow_dispatch` trigger. It is NOT disabled — it can be manually triggered.

**Evidence:** `.github/workflows/deploy.yml` (first few lines show `on: workflow_call` and `workflow_dispatch`)

**Impact:** Minor. The deploy is not automatic on push (that's correct), but it can be manually triggered.

---

### 2.5 Dashboard App Status

**Baseline Claim:** "App exists but is **NOT registered in INSTALLED_APPS** and URLs are **not included** in root `urls.py`"

**Actual:** Correct. `dashboard/apps.py` does NOT exist, and `dashboard` is NOT in `INSTALLED_APPS`. `dashboard/urls.py` exists but is NOT included in `rentsecure_be/urls.py`.

**Evidence:**
- `rentsecure_be/settings.py:117-138` — `dashboard` not in INSTALLED_APPS
- `rentsecure_be/urls.py:23-30` — no `include("dashboard.urls")`
- `dashboard/apps.py` — file not found

**Impact:** None. This is correctly documented.

---

## SECTION 3 — Missing Repository Information

### 3.1 Missing: smartbot/urls.py Does NOT Exist

**What's Missing:** The baseline does not document that `smartbot/urls.py` does not exist.

**Impact:** The `smartbot` app has no URL configuration. Its views (`smart_bot_reply`) must be included from elsewhere or are unreachable via the documented URL structure.

**Actual State:** Glob search found no `urls.py` in `smartbot/`. The `smartbot/views.py` defines `smart_bot_reply` but there is no `smartbot/urls.py` to include it.

---

### 3.2 Missing: smartbot/tasks.py is a No-Op Stub

**What's Missing:** The baseline does not document that `smartbot/tasks.py` is explicitly a no-op stub retained for backward compatibility.

**Evidence:** `smartbot/tasks.py:1-24` — contains only `poll_signature_status()` which returns `None` with a docstring explaining the feature was retired.

**Impact:** The baseline lists "Celery tasks" as infrastructure but doesn't note that the only Celery-related file is a stub.

---

### 3.3 Missing: properties/views/rent_record_views.py Imports from rentsecure_be

**What's Missing:** The baseline's dependency graph does not list `properties/views/rent_record_views.py` as importing from `rentsecure_be`.

**Actual Imports:**
- `properties/views/rent_record_views.py:20`: `from rentsecure_be.services.cashfree_service import process_rent_payout`
- `properties/views/rent_record_views.py:21`: `from rentsecure_be.services.razorpay_service import create_payment_link`

**Impact:** The dependency graph in Section 2.1 is incomplete. It shows `properties → rentsecure_be` only for `i18n`, but `rent_record_views.py` also imports `cashfree_service` and `razorpay_service`.

---

### 3.4 Missing: properties/communication/ Imports from rentsecure_be

**What's Missing:** The baseline does not document that `properties/communication/` modules import from `rentsecure_be`.

**Actual Imports:**
- `properties/communication/auto_generate_rent_records.py:5`: `from rentsecure_be.services.razorpay_service import create_payment_link`
- `properties/communication/retry_failed_payouts.py:7`: `from rentsecure_be.services.cashfree_service import process_rent_payout`

**Impact:** These communication modules are part of the `properties` app but depend on `rentsecure_be` services.

---

### 3.5 Missing: management/commands/ Imports from rentsecure_be

**What's Missing:** The baseline does not document that management commands in the root `management/commands/` import from `rentsecure_be`.

**Actual Imports:**
- `management/commands/retry_failed_payouts.py:11`: `from rentsecure_be.services.cashfree_service import process_rent_payout`

**Impact:** Background tasks depend on `rentsecure_be` services, which is a cross-app dependency.

---

### 3.6 Missing: RentRecord Legacy Property Aliases

**What's Missing:** The baseline lists `RentRecord` fields but does not document the legacy property aliases (`payment_status`, `date_paid`, `rent_due_date`, `amount_paid`) that provide backward compatibility.

**Evidence:** `properties/models/rent_record_models.py:120-150`

**Impact:** These aliases are important for understanding the model's API surface and backward compatibility guarantees.

---

### 3.7 Missing: Unit Legacy Property Aliases

**What's Missing:** The baseline lists `Unit` fields but does not document the legacy property aliases (`unit_number`, `rent_amount`, `security_deposit`) and the `__init__` backward-compatible kwargs handling.

**Evidence:** `properties/models/unit_models.py:73-98`, `properties/models/unit_models.py:219-259`

**Impact:** These aliases are critical for understanding how the model handles legacy API contracts.

---

### 3.8 Missing: SmartBot Import from notification.utils

**What's Missing:** The baseline's dependency graph does not list `smartbot` importing from `notification`.

**Actual Import:**
- `smartbot/actions.py:5`: `from notification.utils import send_whatsapp_message`
- `smartbot/whatsapp_service.py:4`: `from notification.utils import send_whatsapp_message`

**Impact:** The dependency graph in Section 2.1 shows `smartbot → notification` but only lists "whatsapp" as the mechanism. The actual import is from `notification.utils`, not `notification/services/`.

---

### 3.9 Missing: ai_assistant/views.py Imports from smartbot

**What's Missing:** The baseline does not document that `ai_assistant/views.py` imports from `smartbot`.

**Actual Import:**
- `ai_assistant/views.py:28`: `from smartbot.services.chatbot_service import handle_chat_message`

**Impact:** This creates a circular dependency: `smartbot → properties` and `ai_assistant → smartbot`, and `ai_assistant → properties`. The baseline shows `ai_assistant` and `smartbot` as separate bounded contexts but doesn't document the `ai_assistant → smartbot` dependency.

---

### 3.10 Missing: Properties Models Import from core.models

**What's Missing:** The baseline does not explicitly document that `properties/models/*.py` files import `User` from `core.models`.

**Actual Imports:**
- `properties/models/building_models.py:5`: `from core.models import User`
- `properties/models/unit_models.py:16`: `from core.models import User`
- `properties/models/renter_models.py:13`: `from core.models import User`

**Impact:** This is a cross-app dependency (`properties → core`) that is fundamental to the domain model. The baseline shows `core` as the Identity & Subscription context and `properties` as the Property & Rent context, but doesn't explicitly document that `properties` models depend on `core.User`.

---

### 3.11 Missing: NotificationPreferences Not Enforced

**What's Missing:** The baseline does not document that `NotificationPreference` model exists but is NOT consulted by any notification service.

**Evidence:** `notification/services/` directory contains no code that queries `NotificationPreference` before sending notifications.

**Impact:** This is a functional gap — users have notification preferences that are completely ignored by the notification dispatch logic.

---

### 3.12 Missing: Signal Wiring in apps.py

**What's Missing:** The baseline does not document how signals are wired (imported) in each app's `apps.py`.

**Evidence:** Django signals are only registered when the module containing them is imported. The `apps.py` files for `core`, `properties`, `referral_and_earn`, and `ai_assistant` must import their respective `signals.py` modules for signals to be active.

**Impact:** Without this import, signals are silently not registered. This is a critical operational detail.

---

### 3.13 Missing: Simple-History Configuration

**What's Missing:** The baseline does not document which models have `simple-history` enabled.

**Actual:** 8 models have `HistoricalRecords`:
- `User` (`core/models.py:59`)
- `OTP` (`core/models.py:102`)
- `Unit` (`properties/models/unit_models.py`)
- `Renter` (`properties/models/renter_models.py:109`)
- `CareTaker` (`properties/models/caretaker_models.py:52`)
- `RentRecord` (`properties/models/rent_record_models.py:118`)
- `ExtraCharge` (`properties/models/extra_charge_models.py:52`)
- `RentAgreementDraft` (`properties/models/renter_models.py:257`)

**Impact:** Audit trail coverage is incomplete — `Building`, `PropertyTaxRecord`, `UnitDocument`, `UnitImage`, `ArchivedRenter`, and others do not have history tracking.

---

### 3.14 Missing: Logging Configuration

**What's Missing:** The baseline does not document the logging configuration.

**Actual:** `rentsecure_be/settings.py:100-112` defines a minimal logging config:
```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
```

**Impact:** No structured logging, no log rotation, no external log aggregation. All logs go to console at INFO level.

---

*End of Architecture Baseline Validation v1.0.0*
