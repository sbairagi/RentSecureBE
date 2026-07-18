# RentSecureBE — Architecture Refactoring Master Plan

**Status:** DRAFT — AWAITING REVIEW BEFORE IMPLEMENTATION
**Date:** 2026-07-18
**Architect:** Principal Software Architect (Kilo)
**Baseline:** ARCHITECTURE_BASELINE_V1.md + cross_app_import_analysis.md

---

## Executive Summary

The current codebase has **145 cross-app imports**, **4 circular dependency cycles**, **41 infrastructure boundary violations**, **dead code** (ai_assistant, dashboard), and **significant duplication**. The declared layered architecture (`import-linter.ini`) is not enforced in practice.

This plan transforms RentSecureBE into a clean modular monolith through **5 incremental phases**, each independently deployable and testable.

---

## Phase 1 — Shared Kernel, Boundaries, and Import Hygiene

### Task 1.1: Move `type_compat.py` from `rentsecure_be` to `shared`

**1. Current Architecture Problem**
`type_compat.py` is a Python 3.12 `typing.override` compatibility shim. It lives in `rentsecure_be/type_compat.py` and is imported by **20+ files across 6 apps** (core, properties, finance, notification, smartbot, referral_and_earn, management). This creates 20+ infrastructure boundary violations — the single largest source of violations.

**2. Root Cause**
The shim was placed in `rentsecure_be` because that was convenient at the time, not because it belongs to the project configuration layer. `shared/` is the designated shared kernel for cross-cutting utilities.

**3. Recommended Solution**
Move `type_compat.py` to `shared/type_compat.py`. Update all imports from `from rentsecure_be.type_compat import override` to `from shared.type_compat import override`.

**4. Migration Steps**
1. Create `shared/type_compat.py` with identical content.
2. Update all 20+ import statements across the codebase.
3. Remove `rentsecure_be/type_compat.py`.
4. Run full test suite.
5. Update `import-linter.ini` to exclude `type_compat` from boundary checks (or verify it passes since `shared` is accessible to all apps via `rentsecure_be` layer).

**5. Files Affected**
- `shared/type_compat.py` (new)
- `rentsecure_be/type_compat.py` (delete)
- `core/apps.py`, `core/models.py`, `core/serializers.py`, `core/views.py`
- `properties/apps.py`, `properties/models/unit_models.py`, `properties/models/renter_models.py`, `properties/models/caretaker_models.py`, `properties/models/rent_record_models.py`, `properties/models/property_tax_models.py`, `properties/models/extra_charge_models.py`
- `properties/serializers/unit_serializers.py`, `properties/serializers/renter_serializers.py`, `properties/serializers/rent_record_serializers.py`, `properties/serializers/extra_charge_serializers.py`, `properties/serializers/caretaker_serializers.py`, `properties/serializers/building_serializers.py`
- `properties/views/unit_views.py`, `properties/views/renter_views.py`, `properties/views/caretaker_views.py`, `properties/views/building_views.py`, `properties/views/extra_charge_views.py`, `properties/views/rent_record_views.py`
- `finance/models.py`, `finance/views.py`
- `referral_and_earn/apps.py`, `referral_and_earn/models.py`
- `management/commands/*.py` (7 files)

**6. Risk Assessment**
- **Risk Level:** LOW
- No behavioral change — only import path changes.
- Risk of missed import in one of 20+ files. Mitigation: grep after migration.

**7. Rollback Plan**
Revert the single commit. All imports point to old path.

**8. Test Plan**
- Run full test suite: `pytest` (1322 tests)
- Run `python manage.py check`
- Run `import-linter` to verify boundary compliance

**9. Completion Checklist**
- [ ] `shared/type_compat.py` created with identical content
- [ ] All 20+ imports updated
- [ ] `rentsecure_be/type_compat.py` removed
- [ ] All 1322 tests pass
- [ ] `import-linter` passes
- [ ] `python manage.py check` passes

---

### Task 1.2: Resolve `shared/` Naming Conflicts and Finalize Shared Kernel

**1. Current Architecture Problem**
`shared/exceptions.py` defines `ValidationError` as a class. `shared/types.py` defines `ValidationError` as `dict[str, list[str]]`. This creates ambiguous imports and confusion.

**2. Root Cause**
The shared kernel was sketched out but never consistently adopted. Two different `ValidationError` definitions exist for different purposes.

**3. Recommended Solution**
- Rename `shared/types.py::ValidationError` → `shared/types.py::ValidationErrorDict` (or remove if unused).
- Audit actual usage of `shared/types.py` and `shared/exceptions.py`.
- `shared/exceptions.py::ValidationError` stays as the canonical domain exception.
- Add missing utilities to `shared/` that are currently duplicated (phone_regex, constants).

**4. Migration Steps**
1. Audit usage of `shared/types.py::ValidationError` across codebase.
2. Rename type alias in `shared/types.py`.
3. Update any imports.
4. Move `phone_regex` to `shared/validators.py`.
5. Move `RENT_REMINDER_DAYS_BEFORE` to `shared/constants.py` (or keep in properties if it's truly property-specific).

**5. Files Affected**
- `shared/types.py`
- `shared/validators.py`
- `shared/constants.py`
- `properties/models/unit_models.py`, `renter_models.py`, `caretaker_models.py`

**6. Risk Assessment**
- **Risk Level:** LOW-MEDIUM
- Renaming a type alias could affect type checkers (mypy). Mitigation: run `mypy` after change.

**7. Rollback Plan**
Revert commit.

**8. Test Plan**
- Run `mypy .`
- Run full test suite

**9. Completion Checklist**
- [ ] Naming conflict resolved
- [ ] `phone_regex` consolidated
- [ ] `mypy` passes
- [ ] All tests pass

---

### Task 1.3: Add `shared` as an Explicit Layer in `import-linter.ini`

**1. Current Architecture Problem**
`import-linter.ini` defines each app's layers as `[app] → rentsecure_be`. The `shared` package is not formally declared as a shared layer, even though it should be accessible to all apps.

**2. Root Cause**
`shared` was added as a directory but never integrated into the import-linter layer rules.

**3. Recommended Solution**
Add a `[importlinter:shared]` section declaring `shared` as a top layer accessible by all apps. Update each app's layer definition to include `shared` as an allowed dependency.

**4. Migration Steps**
1. Add `[importlinter:shared]` section.
2. Update each app's `layers` to include `shared`.
3. Run `lint-imports` to verify.

**5. Files Affected**
- `import-linter.ini`

**6. Risk Assessment**
- **Risk Level:** LOW
- Only affects CI linting, not runtime behavior.

**7. Rollback Plan**
Revert `import-linter.ini`.

**8. Test Plan**
- Run `lint-imports` or equivalent CI command.

**9. Completion Checklist**
- [ ] `import-linter.ini` updated
- [ ] CI architecture check passes

---

### Task 1.4: Remove `ai_assistant` and `dashboard` from `import-linter.ini` (Dead Code)

**1. Current Architecture Problem**
`ai_assistant` and `dashboard` are NOT in `INSTALLED_APPS` but are still declared as root packages in `import-linter.ini`. This causes the linter to track dead code and creates noise in architecture reports.

**2. Root Cause**
The apps were never removed from configuration after being deactivated.

**3. Recommended Solution**
Remove `ai_assistant` and `dashboard` from `import-linter.ini` root_packages and layer sections. (Do NOT delete the code — it may be reactivated in the future per project assumptions.)

**4. Migration Steps**
1. Remove `ai_assistant` and `dashboard` from `root_packages`.
2. Remove their `[importlinter:...]` sections.
3. Remove from `squashed_modules`.
4. Run CI.

**5. Files Affected**
- `import-linter.ini`

**6. Risk Assessment**
- **Risk Level:** LOW
- Only affects CI linting. Dead code is not loaded by Django.

**7. Rollback Plan**
Re-add entries to `import-linter.ini`.

**8. Test Plan**
- Run CI architecture check.

**9. Completion Checklist**
- [ ] `import-linter.ini` cleaned
- [ ] CI passes

---

### Task 1.5: Move `i18n_service` from `rentsecure_be` to `notification`

**1. Current Architecture Problem**
`rentsecure_be/services/i18n_service.py` is a translation utility that is imported by `notification/services/rent_notify_service.py` and `notification/services/extra_charge_reminders.py`. It is also duplicated in `ai_assistant/services/i18n_service.py` (dead code).

**2. Root Cause**
The translation service was placed in `rentsecure_be` (project config) instead of the `notification` app where it is actually used.

**3. Recommended Solution**
Move `i18n_service.py` to `notification/services/i18n_service.py`. Update all imports. Delete the duplicate in `ai_assistant`.

**4. Migration Steps**
1. Move `rentsecure_be/services/i18n_service.py` → `notification/services/i18n_service.py`.
2. Update imports in `notification/services/rent_notify_service.py` and `notification/services/extra_charge_reminders.py`.
3. Delete `ai_assistant/services/i18n_service.py` (dead code duplicate).
4. Run tests.

**5. Files Affected**
- `notification/services/i18n_service.py` (new)
- `rentsecure_be/services/i18n_service.py` (delete)
- `notification/services/rent_notify_service.py`
- `notification/services/extra_charge_reminders.py`
- `ai_assistant/services/i18n_service.py` (delete)

**6. Risk Assessment**
- **Risk Level:** LOW-MEDIUM
- Notification translations are business-critical. Mitigation: run full test suite, verify translations work.

**7. Rollback Plan**
Revert commit. Restore old file paths.

**8. Test Plan**
- Run full test suite
- Manually verify notification translation in development

**9. Completion Checklist**
- [ ] `i18n_service.py` moved to notification
- [ ] Imports updated
- [ ] Duplicate in ai_assistant removed
- [ ] All tests pass

---

### Task 1.6: Move `export_utils` from `rentsecure_be` to `properties`

**1. Current Architecture Problem**
`rentsecure_be/utils/export_utils.py` contains `generate_owner_rent_report` which generates Excel reports for rent data. It is imported by `core/views.py` (owner reporting) and `rentsecure_be/utils/export_utils.py`. This is a properties-domain utility living in the project config layer.

**2. Root Cause**
The utility was placed in `rentsecure_be` for convenience.

**3. Recommended Solution**
Move `export_utils.py` to `properties/utils/export_utils.py`. Update imports.

**4. Migration Steps**
1. Move file.
2. Update imports in `core/views.py`.
3. Run tests.

**5. Files Affected**
- `properties/utils/export_utils.py` (new)
- `rentsecure_be/utils/export_utils.py` (delete)
- `core/views.py`

**6. Risk Assessment**
- **Risk Level:** LOW
- Simple utility move.

**7. Rollback Plan**
Revert.

**8. Test Plan**
- Run full test suite
- Verify owner reporting Excel download works

**9. Completion Checklist**
- [ ] File moved
- [ ] Imports updated
- [ ] Tests pass

---

### Phase 1 Summary

| Task | Imports Resolved | Circular Deps Resolved | Risk |
|---|---|---|---|
| 1.1 Move type_compat | 20+ | None | LOW |
| 1.2 Resolve shared conflicts | 0 | None | LOW-MED |
| 1.3 Update import-linter | 0 | None | LOW |
| 1.4 Remove dead apps from linter | 0 | None | LOW |
| 1.5 Move i18n_service | 4 | None | LOW-MED |
| 1.6 Move export_utils | 1 | None | LOW |

**Phase 1 Expected Results:**
- Cross-app imports: 145 → ~120
- Infrastructure boundary violations: 41 → ~18
- Circular dependencies: 4 (unchanged)
- All 1322 tests pass

---

## Phase 2 — Ports and Adapters for Payments, Notifications, Documents, i18n

### Task 2.1: Introduce `payments.ports.PaymentGateway` Interface

**1. Current Architecture Problem**
Payment services (`cashfree_service`, `razorpay_service`) are imported directly by `core`, `properties`, `smartbot`, and `management` commands. Payment webhooks are in `core/views.py`. This is the most fragmented domain.

**2. Root Cause**
No abstraction layer exists. Apps depend on concrete payment implementations directly.

**3. Recommended Solution**
Following Rule 4 (Abstraction before migration):
1. Introduce `payments.ports.PaymentGateway` protocol in `shared/interfaces.py` (or a new `payments/ports.py`).
2. Create `payments.adapters.manual.ManualPaymentAdapter` (Year 1 — UPI flow).
3. Create `payments.adapters.cashfree.CashfreeAdapter` (disabled, behind feature flag).
4. Create `payments.adapters.razorpay.RazorpayAdapter` (disabled, behind feature flag).
5. Introduce `payments.services.payment_service` as the orchestrator.
6. Migrate callers to use `PaymentGateway` interface.
7. Remove direct imports of concrete adapters.

**4. Migration Steps**
1. Create `payments/__init__.py`, `payments/apps.py`, `payments/ports.py`, `payments/services/`.
2. Create adapter stubs in `payments/adapters/`.
3. Move `cashfree_service.py` and `razorpay_service.py` content into adapters.
4. Create `payments/services/payment_service.py` that selects adapter based on feature flags.
5. Update all callers to import from `payments.services.payment_service`.
6. Move `OwnerBankDetails` model to `payments/models.py` (it is a financial entity).
7. Move payment webhook views from `core/views.py` to `payments/views.py`.
8. Add `payments` to `INSTALLED_APPS`.
9. Create migration for model move.
10. Run tests.

**5. Files Affected**
- New: `payments/__init__.py`, `payments/apps.py`, `payments/ports.py`, `payments/services/payment_service.py`, `payments/adapters/manual.py`, `payments/adapters/cashfree.py`, `payments/adapters/razorpay.py`, `payments/views.py`, `payments/models/bank_details_models.py`, `payments/urls.py`
- Modified: `rentsecure_be/settings.py`, `core/views.py`, `core/services/bank_details_service.py`, `properties/views/rent_record_views.py`, `properties/communication/retry_failed_payouts.py`, `smartbot/actions.py`, `management/commands/retry_failed_payouts.py`
- Deleted: `core/models.py` (OwnerBankDetails moved), `rentsecure_be/services/cashfree_service.py`, `rentsecure_be/services/razorpay_service.py`, `rentsecure_be/utils/cashfree_payout.py`

**6. Risk Assessment**
- **Risk Level:** HIGH
- Moving a model (`OwnerBankDetails`) requires a Django migration.
- Payment webhooks are critical infrastructure.
- Mitigation:
  - Use Django's migration squashing/renaming.
  - Keep old model as a proxy during transition if needed.
  - Extensive testing of payment flows.
  - Feature flags ensure adapters can be toggled.

**7. Rollback Plan**
- Revert migrations (requires Django migration rollback).
- Restore old model location.
- Restore old imports.

**8. Test Plan**
- Run full test suite (1322 tests).
- Add tests for `PaymentGateway` interface.
- Add tests for each adapter.
- Test manual UPI flow end-to-end.
- Test Cashfree adapter in sandbox (disabled in prod).
- Run `python manage.py check`.

**9. Completion Checklist**
- [ ] `payments` app created with ports/adapters
- [ ] `OwnerBankDetails` moved with migration
- [ ] All callers migrated to `PaymentGateway` interface
- [ ] Direct imports of concrete adapters removed
- [ ] Payment webhooks moved to `payments/views.py`
- [ ] All 1322 tests pass
- [ ] Manual UPI flow verified end-to-end

---

### Task 2.2: Introduce `notifications.ports.NotificationChannel` Interface

**1. Current Architecture Problem**
Notification delivery is accessed directly by multiple apps (`core`, `properties`, `smartbot`, `management`). The notification app has 9 service files with duplicated logic (`send_push_notification` in both `services/notifications.py` and `utils.py`, `send_whatsapp_message` in both `services/whatsapp_service.py` and `utils.py`).

**2. Root Cause**
No abstraction layer for notification channels. Apps import concrete notification services directly.

**3. Recommended Solution**
1. Introduce `NotificationChannel` protocol in `notification/ports.py`.
2. Implement adapters: `EmailAdapter`, `FCMAdapter`, `InAppAdapter` (enabled), `WhatsAppAdapter`, `SMSAdapter`, `VoiceAdapter` (disabled).
3. Consolidate `notification/services/notifications.py` and `notification/utils.py`.
4. Create `notification/services/notification_service.py` as the orchestrator.
5. Migrate all direct imports of `send_whatsapp_message`, `send_push_notification` to use the orchestrator.
6. Move `NotificationPreference` model from `core/models.py` to `notification/models.py`.

**4. Migration Steps**
1. Create `notification/ports.py`, `notification/adapters/`.
2. Consolidate duplicate functions.
3. Create orchestrator.
4. Move `NotificationPreference` model (requires migration).
5. Update all callers.
6. Update `core/views.py` to use orchestrator.
7. Update `properties/signals/__init__.py`, `properties/services/summary_service.py`, etc.
8. Update `smartbot/actions.py`.
9. Run tests.

**5. Files Affected**
- New: `notification/ports.py`, `notification/adapters/email.py`, `notification/adapters/fcm.py`, `notification/adapters/inapp.py`, `notification/adapters/whatsapp.py`, `notification/adapters/sms.py`, `notification/adapters/voice.py`, `notification/services/notification_service.py`
- Modified: `notification/services/notifications.py`, `notification/utils.py`, `notification/services/whatsapp_service.py`, `core/views.py`, `core/models.py`, `properties/signals/__init__.py`, `properties/services/summary_service.py`, `properties/services/renter_onboarding_service.py`, `properties/utils/utils.py`, `smartbot/actions.py`, `smartbot/whatsapp_service.py`
- Deleted: Duplicate functions after consolidation

**6. Risk Assessment**
- **Risk Level:** HIGH
- Moving `NotificationPreference` requires migration.
- Notification is used throughout the app. Extensive testing required.
- Mitigation: feature flags for disabled adapters, comprehensive test coverage.

**7. Rollback Plan**
- Revert model migration.
- Restore old imports.

**8. Test Plan**
- Run full test suite.
- Add tests for `NotificationChannel` interface.
- Test each enabled adapter (Email, FCM, InApp).
- Verify disabled adapters log "Coming Soon".
- Test notification preferences migration.

**9. Completion Checklist**
- [ ] `NotificationChannel` interface defined
- [ ] Adapters implemented (3 enabled, 3 disabled)
- [ ] Duplicate functions consolidated
- [ ] `NotificationPreference` moved with migration
- [ ] All callers migrated
- [ ] All tests pass

---

### Task 2.3: Introduce `documents.ports.DocumentGenerator` Interface

**1. Current Architecture Problem**
PDF generation logic exists in 3 apps: `documents/views.py`, `smartbot/services/agreement_service.py`, and `ai_assistant/services/invoice_service.py` (dead code). The `documents` app has the canonical implementations but `smartbot` duplicates agreement PDF generation.

**2. Root Cause**
No shared interface for document generation. `smartbot` reimplemented PDF generation for agreements.

**3. Recommended Solution**
1. Introduce `DocumentGenerator` protocol in `documents/ports.py`.
2. Implement adapters: `RentAgreementPdfAdapter`, `UnitDossierPdfAdapter`, `RentReceiptPdfAdapter`, `InvoicePdfAdapter` (in `documents/adapters/`).
3. Migrate `smartbot/services/agreement_service.py` to import from `documents` adapters instead of duplicating.
4. Delete duplicate in `smartbot`.

**4. Migration Steps**
1. Create `documents/ports.py`, `documents/adapters/`.
2. Refactor existing `documents/views.py` to use adapters internally.
3. Update `smartbot/services/agreement_service.py` to import from `documents`.
4. Delete duplicate code.
5. Run tests.

**5. Files Affected**
- New: `documents/ports.py`, `documents/adapters/`
- Modified: `documents/views.py`, `smartbot/services/agreement_service.py`
- Deleted: Duplicate PDF generation code in `smartbot`

**6. Risk Assessment**
- **Risk Level:** MEDIUM
- PDF generation is user-facing. Mitigation: test all PDF outputs.

**7. Rollback Plan**
- Restore `smartbot/services/agreement_service.py` from git.

**8. Test Plan**
- Run full test suite.
- Verify PDF generation for agreements, dossiers, receipts.

**9. Completion Checklist**
- [ ] `DocumentGenerator` interface defined
- [ ] Adapters implemented
- [ ] `smartbot` duplication removed
- [ ] Tests pass

---

### Task 2.4: Consolidate Leegality E-Signature Service

**1. Current Architecture Problem**
Leegality e-signature service is duplicated in `rentsecure_be/services/leegality_service.py` and `smartbot/services/leegality_service.py`.

**2. Root Cause**
No single owner for the Leegality integration.

**3. Recommended Solution**
Move Leegality service to `documents/` (it generates signed agreements) or keep in `rentsecure_be` if it's considered infrastructure. Make it the single source of truth. Update `smartbot` to import from the canonical location.

**4. Migration Steps**
1. Choose canonical location (recommended: `documents/services/leegality_service.py`).
2. Move file.
3. Update imports in `smartbot` and `properties`.
4. Delete duplicate.
5. Run tests.

**5. Files Affected**
- `documents/services/leegality_service.py` (new)
- `rentsecure_be/services/leegality_service.py` (delete) or keep as re-export
- `smartbot/services/leegality_service.py` (delete)
- `properties/views/unit_views.py`

**6. Risk Assessment**
- **Risk Level:** LOW-MEDIUM
- E-signature is business-critical for agreements.

**7. Rollback Plan**
- Restore files from git.

**8. Test Plan**
- Run full test suite.
- Test agreement signing flow.

**9. Completion Checklist**
- [ ] Single Leegality service
- [ ] Duplicate removed
- [ ] Tests pass

---

### Phase 2 Summary

| Task | Imports Resolved | Circular Deps Resolved | Risk |
|---|---|---|---|
| 2.1 PaymentGateway interface | 15+ | 2 (core↔rentsecure_be, properties↔rentsecure_be) | HIGH |
| 2.2 NotificationChannel interface | 12+ | 1 (properties↔notification) | HIGH |
| 2.3 DocumentGenerator interface | 3 | None | MEDIUM |
| 2.4 Leegality consolidation | 2 | None | LOW-MED |

**Phase 2 Expected Results:**
- Cross-app imports: ~120 → ~80
- Infrastructure boundary violations: ~18 → ~5
- Circular dependencies: 4 → 1 (core↔properties remains)
- All 1322 tests pass

---

## Phase 3 — Split God Modules

### Task 3.1: Split `core/views.py` (566 lines, 8 responsibilities)

**1. Current Architecture Problem**
`core/views.py` handles: OTP, Password, Subscription CRUD, Bank Details, Owner Reporting, Cashfree webhook, Razorpay webhook, Create Rent Payment. This is a classic God View.

**2. Root Cause**
All identity-related views were placed in a single file for convenience.

**3. Recommended Solution**
Split into focused view modules:
- `core/views/otp_views.py`
- `core/views/password_views.py`
- `core/views/subscription_views.py`
- `core/views/bank_details_views.py`
- `core/views/owner_reporting_views.py`
- `core/views/payment_webhook_views.py` (move to `payments/views.py` in Phase 2)
- Update `core/urls.py` to include new modules.

**4. Migration Steps**
1. Create view modules.
2. Move view classes/functions.
3. Update `core/urls.py`.
4. Run tests.

**5. Files Affected**
- `core/views.py` (split)
- `core/urls.py`

**6. Risk Assessment**
- **Risk Level:** MEDIUM
- URL patterns change. Mitigation: verify all URL patterns remain accessible.

**7. Rollback Plan**
- Revert to single `core/views.py`.

**8. Test Plan**
- Run full test suite.
- Test each endpoint individually.

**9. Completion Checklist**
- [ ] Views split into focused modules
- [ ] URLs updated
- [ ] Tests pass

---

### Task 3.2: Split `properties/models/unit_models.py` (482 lines)

**1. Current Architecture Problem**
`unit_models.py` contains: `Unit`, `UnitVacancy`, `UnitDocument`, `UnitImage` + extensive business logic in model methods.

**2. Root Cause**
Multiple related models were placed in one file. Business logic is embedded in models instead of services.

**3. Recommended Solution**
- Split into: `unit_models.py` (Unit only), `unit_vacancy_models.py`, `unit_document_models.py`, `unit_image_models.py`.
- Move business logic from models to `properties/services/unit_service.py` (already exists, extend it).

**4. Migration Steps**
1. Create separate model files.
2. Update `properties/models/__init__.py`.
3. Update all imports.
4. Run tests.

**5. Files Affected**
- `properties/models/unit_models.py`
- `properties/models/__init__.py`
- All files importing from `properties.models.unit_models`

**6. Risk Assessment**
- **Risk Level:** MEDIUM
- Many files import from this module.

**7. Rollback Plan**
- Revert.

**8. Test Plan**
- Run full test suite.

**9. Completion Checklist**
- [ ] Models split
- [ ] Imports updated
- [ ] Tests pass

---

### Task 3.3: Split `notification/services/` (9 files, fragmented)

**1. Current Architecture Problem**
`notification/services/` has 9 files with duplicated and scattered logic.

**2. Root Cause**
Each notification channel got its own file without a unified orchestrator.

**3. Recommended Solution**
- Consolidate into: `notification_service.py` (orchestrator), `notification_port.py`, `adapters/`.
- This aligns with Task 2.2.

**4. Migration Steps**
- Covered in Task 2.2.

---

### Phase 3 Summary

| Task | Risk |
|---|---|
| 3.1 Split core/views.py | MEDIUM |
| 3.2 Split unit_models.py | MEDIUM |
| 3.3 Consolidate notification services | MEDIUM |

---

## Phase 4 — Reduce Cross-App Imports to Below 20

### Strategy

After Phases 1-3, cross-app imports should be reduced from ~80 to below 20 through:

1. **Complete the PaymentGateway migration** — eliminate all direct imports of `cashfree_service`, `razorpay_service`.
2. **Complete the NotificationChannel migration** — eliminate all direct imports of `notification.services.*`.
3. **Move remaining model imports to use Django string references** where possible (`ForeignKey('app.Model')`).
4. **Move root management commands** to respective apps' `management/commands/`.
5. **Remove remaining infrastructure boundary violations**.

### Target State

| Source App | Target App | Import Count |
|---|---|---|
| core | properties | ~5 (User model, required) |
| properties | core | ~5 (User model, required) |
| properties | notification | 0 (use orchestrator) |
| core | notification | 0 (use orchestrator) |
| smartbot | notification | 0 (use orchestrator) |
| smartbot | properties | ~3 (Renter, RentRecord) |
| finance | core | ~1 (User) |
| finance | properties | ~1 (Unit) |
| documents | properties | ~2 (Renter, RentRecord) |
| documents | core | ~1 (User) |
| rentsecure_be | core | 0 (OwnerBankDetails moved) |
| rentsecure_be | properties | 0 (export_utils moved) |
| rentsecure_be | notification | 0 (i18n moved) |

**Expected total: <20 cross-app imports**

---

## Phase 5 — Remove Circular Dependencies

### Current Circular Dependencies

1. **core ↔ properties** (will remain — both need User/RentRecord models)
2. **core ↔ rentsecure_be** (resolved by Phase 1-2: type_compat moved, payment services moved)
3. **properties ↔ notification** (resolved by Phase 2: NotificationChannel interface)
4. **properties ↔ rentsecure_be** (resolved by Phase 1-2: type_compat moved, export_utils moved)

### Target: Zero Circular Dependencies

After Phases 1-2, only `core ↔ properties` remains. This is acceptable because:
- `core` owns `User` (AUTH_USER_MODEL) — properties MUST import it.
- `properties` owns `RentRecord` — core's owner reporting needs it.

**Options for core ↔ properties:**

**Option A (Recommended): Accept the cycle**
- Both apps own essential models that the other needs.
- Use Django's `get_user_model()` and string model references consistently.
- Document the accepted cycle in `import-linter.ini` as an exception.

**Option B: Extract shared models**
- Move `RentRecord` to a `shared` domain — NOT recommended because RentRecord is a core property management entity.

**Recommendation:** Accept `core ↔ properties` as a bounded context boundary. Document it. Ensure no OTHER circular dependencies exist.

---

## Consolidated Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Model migration breaks existing data | MEDIUM | HIGH | Use Django migrations, test on staging, backup DB |
| Payment flow regression | LOW | HIGH | Feature flags, extensive testing, canary deployment |
| Notification delivery regression | LOW | HIGH | Feature flags, test all channels |
| Missed import updates | MEDIUM | MEDIUM | Automated grep verification after each task |
| Circular dependency introduction | LOW | MEDIUM | Run `import-linter` after each task |
| Test suite breaks | LOW | HIGH | Run full suite after each task, fix immediately |

---

## Rollback Strategy

1. **Git-based rollback:** Each phase is a single commit (or small set of commits). Rollback via `git revert`.
2. **Database migrations:** Django migrations are reversible. Use `python manage.py migrate <previous_app>` for rollback.
3. **Feature flags:** Payment and notification adapters are behind feature flags. Disable new adapters instantly if issues arise.
4. **Blue-green deployment:** Deploy each phase to staging first, verify, then promote to production.

---

## Test Plan (Per Phase)

| Phase | Tests |
|---|---|
| Phase 1 | Full test suite (1322), `import-linter`, `mypy`, `python manage.py check` |
| Phase 2 | Full test suite, adapter unit tests, integration tests for payment/notification flows |
| Phase 3 | Full test suite, URL pattern tests, model import tests |
| Phase 4 | Full test suite, `import-linter` (target: <20 violations) |
| Phase 5 | Full test suite, circular dependency check, `import-linter` |

---

## Completion Criteria

- [ ] All 1322 tests pass after each phase
- [ ] `import-linter` passes after each phase
- [ ] `mypy` passes after each phase
- [ ] `python manage.py check` passes
- [ ] Cross-app imports: 145 → <20
- [ ] Circular dependencies: 4 → 0
- [ ] Infrastructure boundary violations: 41 → 0
- [ ] No dead code in INSTALLED_APPS
- [ ] Shared kernel fully utilized
- [ ] All business logic in domain apps, not `rentsecure_be`

---

## Recommended Execution Order

```
Phase 1.1: Move type_compat to shared          ← Start here (low risk, high impact)
Phase 1.2: Resolve shared conflicts
Phase 1.3: Update import-linter
Phase 1.4: Remove dead apps from linter
Phase 1.5: Move i18n_service to notification
Phase 1.6: Move export_utils to properties

Phase 2.1: PaymentGateway interface             ← Medium risk, high value
Phase 2.2: NotificationChannel interface
Phase 2.3: DocumentGenerator interface
Phase 2.4: Leegality consolidation

Phase 3.1: Split core/views.py
Phase 3.2: Split unit_models.py
Phase 3.3: Consolidate notification services

Phase 4: Reduce imports to <20                 ← Natural result of above

Phase 5: Remove circular deps                  ← Mostly done in Phase 1-2
```

---

*End of Master Plan*
