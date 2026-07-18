# Cross-App Import Analysis Report — RentSecureBE
## Scope
- **Apps analyzed:** `core`, `properties`, `finance`, `notification`, `documents`, `smartbot`, `referral_and_earn`, `ai_assistant`, `dashboard`, `rentsecure_be`
- **Excluded paths:** `tests/`, `migrations/`, `.venv/`, `.nox/`, `__pycache__/`, `docs/archive/`, `properties/_legacy/`, `properties/refactored_models_combined.py`, `properties/original_models.py`
- **Total cross-app imports found (non-test source files):** 145

---

## 1. Cross-App Imports by App Pair

### core → properties
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `core/views.py` | 62 | `from properties.models.rent_record_models import RentRecord` | model |
| `core/views.py` | 304 | `from properties.models.rent_record_models import RentRecord` | model |
| `core/views.py` | 349 | `from properties.models.rent_record_models import RentRecord` | model |
| `core/views.py` | 400 | `from properties.models.rent_record_models import RentRecord` | model |
| `core/views.py` | 438 | `from properties.models.rent_record_models import RentRecord` | model |
| `core/views.py` | 472 | `from properties.models.rent_record_models import RentRecord` | model |
| `core/services/owner_reporting_service.py` | 8 | `from properties.models.rent_record_models import RentRecord` | model |
| `core/services/bank_details_service.py` | 7 | `from properties.models.rent_record_models import RentRecord` | model |

### core → notification
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `core/views.py` | 35 | `from notification.services.rent_notify_service import send_payout_notification` | service |

### core → rentsecure_be
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `core/views.py` | 36 | `from rentsecure_be.services.cashfree_service import delete_beneficiary, process_rent_payout` | service |
| `core/views.py` | 40 | `from rentsecure_be.utils.export_utils import generate_owner_rent_report` | utility |
| `core/serializers.py` | 5 | `from rentsecure_be.type_compat import override` | utility |
| `core/models.py` | 10 | `from rentsecure_be.type_compat import override` | utility |
| `core/apps.py` | 5 | `from rentsecure_be.type_compat import override` | utility |
| `core/services/bank_details_service.py` | 8 | `from rentsecure_be.utils.cashfree_payout import add_beneficiary` | utility |

### core → referral_and_earn
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `core/services/referral_service.py` | 23 | `from referral_and_earn.models import Referral` | model |

### core → shared
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `core/views.py` | 41 | `from shared.exceptions import ValidationError` | utility |
| `core/services/referral_service.py` | 6 | `from shared.exceptions import ValidationError` | utility |
| `core/services/otp_service.py` | 12 | `from shared.exceptions import ValidationError` | utility |

---

### properties → core
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `properties/views/unit_views.py` | 28 | `from core.models import User` | model |
| `properties/views/rent_record_views.py` | 17 | `from core.models import User` | model |
| `properties/views/renter_views.py` | 15 | `from core.models import User` | model |
| `properties/services/unit_service.py` | 21 | `from core.models import User` | model |
| `properties/models/unit_models.py` | 16 | `from core.models import User` | model |
| `properties/models/renter_models.py` | 13 | `from core.models import User` | model |
| `properties/models/building_models.py` | 5 | `from core.models import User` | model |
| `properties/utils/utils.py` | 13 | `from core.models import AddOnPurchase, PlanFeatureLimit, UsageLimit, User, UserSubscription` | model |
| `properties/feature_enforcer.py` | 16 | `from core.models import AddOnPurchase, PlanFeatureLimit, SubscriptionPlan, UsageLimit, UserSubscription` | model |
| `properties/services/summary_service.py` | 22 | `from core.models import NotificationPreference, User` | model |

### properties → rentsecure_be
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `properties/views/unit_views.py` | 29 | `from rentsecure_be.services.leegality_service import send_agreement_for_signature` | service |
| `properties/views/unit_views.py` | 30 | `from rentsecure_be.type_compat import override` | utility |
| `properties/views/rent_record_views.py` | 20 | `from rentsecure_be.services.cashfree_service import process_rent_payout` | service |
| `properties/views/rent_record_views.py` | 21 | `from rentsecure_be.services.razorpay_service import create_payment_link` | service |
| `properties/views/rent_record_views.py` | 22 | `from rentsecure_be.type_compat import override` | utility |
| `properties/views/renter_views.py` | 16 | `from rentsecure_be.type_compat import override` | utility |
| `properties/views/caretaker_views.py` | 11 | `from rentsecure_be.type_compat import override` | utility |
| `properties/views/building_views.py` | 7 | `from rentsecure_be.type_compat import override` | utility |
| `properties/views/extra_charge_views.py` | 10 | `from rentsecure_be.type_compat import override` | utility |
| `properties/serializers/unit_serializers.py` | 5 | `from rentsecure_be.type_compat import override` | utility |
| `properties/serializers/renter_serializers.py` | 6 | `from rentsecure_be.type_compat import override` | utility |
| `properties/serializers/rent_record_serializers.py` | 5 | `from rentsecure_be.type_compat import override` | utility |
| `properties/serializers/extra_charge_serializers.py` | 5 | `from rentsecure_be.type_compat import override` | utility |
| `properties/serializers/caretaker_serializers.py` | 6 | `from rentsecure_be.type_compat import override` | utility |
| `properties/serializers/building_serializers.py` | 5 | `from rentsecure_be.type_compat import override` | utility |
| `properties/models/unit_models.py` | 17 | `from rentsecure_be.type_compat import override` | utility |
| `properties/models/renter_models.py` | 14 | `from rentsecure_be.type_compat import override` | utility |
| `properties/models/caretaker_models.py` | 7 | `from rentsecure_be.type_compat import override` | utility |
| `properties/models/rent_record_models.py` | 9 | `from rentsecure_be.type_compat import override` | utility |
| `properties/models/property_tax_models.py` | 7 | `from rentsecure_be.type_compat import override` | utility |
| `properties/models/extra_charge_models.py` | 8 | `from rentsecure_be.type_compat import override` | utility |
| `properties/communication/auto_generate_rent_records.py` | 5 | `from rentsecure_be.services.razorpay_service import create_payment_link` | service |
| `properties/communication/retry_failed_payouts.py` | 7 | `from rentsecure_be.services.cashfree_service import process_rent_payout` | service |
| `properties/apps.py` | 3 | `from rentsecure_be.type_compat import override` | utility |
| `properties/management/commands/send_monthly_rent_summary.py` | 7 | `from rentsecure_be.type_compat import override` | utility |
| `properties/management/commands/generate_monthly_extra_charges.py` | 6 | `from rentsecure_be.type_compat import override` | utility |

### properties → notification
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `properties/views/rent_record_views.py` | 18 | `from notification.services.rent_notify_service import send_payout_notification` | service |
| `properties/views/rent_record_views.py` | 19 | `from notification.utils import send_whatsapp_message` | utility |
| `properties/views/property_views.py` | 12 | `from notification.utils import send_whatsapp_message` | utility |
| `properties/services/summary_service.py` | 152 | `from notification.services.whatsapp_service import send_whatsapp_message` | service |
| `properties/services/renter_onboarding_service.py` | 12 | `from notification.services.whatsapp_service import send_whatsapp_message` | service |
| `properties/services/renter_onboarding_service.py` | 126 | `from notification.services.whatsapp_service import send_whatsapp_message` | service |
| `properties/utils/utils.py` | 20 | `from notification.services.late_fees_notify_service import notify_owner_about_late_fee, notify_renter_about_late_fee` | service |
| `properties/signals/__init__.py` | 9 | `from notification.models import Notification` | model |
| `properties/signals/__init__.py` | 139 | `from notification.services.voice_note_service import send_thank_you_voice_note` | service |
| `properties/signals/__init__.py` | 167 | `from notification.services.services import notify_owner_renter_flagged` | service |
| `properties/signals/__init__.py` | 196 | `from notification.services.whatsapp_service import send_whatsapp_message` | service |
| `properties/scheduler.py` | 24 | `from notification.services.voice_note_service import generate_voice_note` | service |
| `properties/cron/vacate_reminder.py` | 7 | `from notification.services.whatsapp_service import send_whatsapp_message` | service |

---

### finance → core
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `finance/views.py` | 22 | `from core.models import User` | model |

### finance → properties
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `finance/views.py` | 23 | `from properties.models import Unit` | model |
| `finance/utils.py` | 26 | `from properties.models import Unit` | model |

### finance → rentsecure_be
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `finance/views.py` | 24 | `from rentsecure_be.type_compat import override` | utility |
| `finance/models.py` | 4 | `from rentsecure_be.type_compat import override` | utility |

---

### notification → properties
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `notification/services/schedule_reminders.py` | 15 | `from properties.models.rent_record_models import RentRecord` | model |
| `notification/services/schedule_reminders.py` | 22 | `from properties.models.property_tax_models import PropertyTaxRecord` | model |
| `notification/services/voice_note_service.py` | 47 | `from properties.models.renter_models import RentReminderLog` | model |
| `notification/services/extra_charge_reminders.py` | 16 | `from properties.models.extra_charge_models import ExtraCharge` | model |

### notification → rentsecure_be
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `notification/services/rent_notify_service.py` | 48 | `from rentsecure_be.services.i18n_service import translate_msg` | service |
| `notification/services/rent_notify_service.py` | 79 | `from rentsecure_be.services.i18n_service import translate_msg` | service |
| `notification/services/rent_notify_service.py` | 141 | `from rentsecure_be.services.i18n_service import translate_msg` | service |
| `notification/services/extra_charge_reminders.py` | 17 | `from rentsecure_be.services.i18n_service import translate_msg` | service |

---

### documents → core
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `documents/views.py` | 15 | `from core.models import User` | model |

### documents → properties
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `documents/views.py` | 16 | `from properties.models import Renter, RentRecord, Unit` | model |
| `documents/views.py` | 17 | `from properties.serializers import RentRecordSerializer` | serializer |
| `documents/utils.py` | 12 | `from properties.models import RentAgreementDraft` | model |

---

### smartbot → notification
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `smartbot/actions.py` | 5 | `from notification.utils import send_whatsapp_message` | utility |
| `smartbot/whatsapp_service.py` | 4 | `from notification.utils import send_whatsapp_message` | utility |
| `smartbot/cron/reminders.py` | 3 | `from notification.services.whatsapp_service import send_whatsapp_message` | service |

### smartbot → properties
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `smartbot/actions.py` | 6 | `from properties.models import Renter, RentRecord` | model |
| `smartbot/actions.py` | 74 | `from properties.models import RentAgreementDraft` | model |
| `smartbot/cron/reminders.py` | 4 | `from properties.models import RentAgreementDraft` | model |
| `smartbot/views.py` | 11 | `from properties.models import RentRecord` | model |
| `smartbot/services/services.py` | 11 | `from properties.models import Renter, RentRecord` | model |
| `smartbot/services/chatbot_service.py` | 13 | `from properties.models import RentAgreementDraft, RentRecord` | model |

### smartbot → rentsecure_be
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `smartbot/actions.py` | 7 | `from rentsecure_be.services.cashfree_service import process_rent_payout` | service |

---

### ai_assistant → core
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `ai_assistant/views.py` | 25 | `from core.models import UserProfile` | model |

### ai_assistant → notification
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `ai_assistant/views.py` | 26 | `from notification.services.whatsapp_service import send_whatsapp_message` | service |

### ai_assistant → properties
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `ai_assistant/views.py` | 27 | `from properties.models import PropertyTaxRecord, Renter, RentRecord` | model |
| `ai_assistant/receivers.py` | 7 | `from properties.signals.renter_signals import renter_archived, renter_exited` | utility |
| `ai_assistant/receivers.py` | 16 | `from properties.models import Renter, RentRecord` | model |
| `ai_assistant/receivers.py` | 33 | `from properties.models import Renter` | model |
| `ai_assistant/services/unit_service.py` | 5 | `from properties.models import Renter` | model |
| `ai_assistant/services/invoice_service.py` | 9 | `from properties.models import Renter, RentRecord` | model |
| `ai_assistant/services/archive_service.py` | 12 | `from properties.models import ArchivedRenter, RentRecord, UnitImage` | model |

### ai_assistant → smartbot
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `ai_assistant/views.py` | 28 | `from smartbot.services.chatbot_service import handle_chat_message` | service |

---

### dashboard → properties
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `dashboard/views.py` | 5 | `from properties.models import RentRecord` | model |

### dashboard → smartbot
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `dashboard/views.py` | 6 | `from smartbot.actions import send_agreement_for_signature` | utility |

---

### referral_and_earn → rentsecure_be
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `referral_and_earn/apps.py` | 3 | `from rentsecure_be.type_compat import override` | utility |
| `referral_and_earn/models.py` | 8 | `from rentsecure_be.type_compat import override` | utility |

---

### rentsecure_be → core
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `rentsecure_be/services/cashfree_service.py` | 17 | `from core.models import OwnerBankDetails` | model |
| `rentsecure_be/services/cashfree_service.py` | 24 | `from core.models import OwnerBankDetails` | model |
| `rentsecure_be/services/cashfree_service.py` | 48 | `from core.models import OwnerBankDetails` | model |
| `rentsecure_be/services/cashfree_service.py` | 118 | `from core.models import OwnerBankDetails` | model |
| `rentsecure_be/services/cashfree_service.py` | 150 | `from core.models import OwnerBankDetails` | model |

### rentsecure_be → properties
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `rentsecure_be/services/cashfree_service.py` | 18 | `from properties.models.rent_record_models import RentRecord` | model |
| `rentsecure_be/utils/export_utils.py` | 8 | `from properties.models.rent_record_models import RentRecord` | model |

### rentsecure_be → notification
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `rentsecure_be/services/cashfree_service.py` | 49 | `from notification.services.rent_notify_service import notify_owner, notify_renter` | service |
| `rentsecure_be/services/cashfree_service.py` | 106 | `from notification.services.rent_notify_service import send_payout_notification` | service |
| `rentsecure_be/services/cashfree_service.py` | 151 | `from notification.services.rent_notify_service import notify_owner_post_payout, send_payout_notification` | service |

---

### management → core
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `management/commands/send_monthly_rent_summary.py` | 10 | `from core.models import User` | model |

### management → properties
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `management/commands/monthly_whatsapp_and_email_summary_to_owner.py` | 6 | `from properties.models import RentRecord` | model |
| `management/commands/apply_late_fees.py` | 16 | `from properties.models import RentRecord` | model |
| `management/commands/send_rent_reminders.py` | 7 | `from properties.models import Renter` | model |
| `management/commands/daily_rent_reminder.py` | 7 | `from properties.models import Renter` | model |
| `management/commands/auto_deactivate_renters.py` | 7 | `from properties.models import Renter` | model |
| `management/commands/generate_monthly_rent_records.py` | 6 | `from properties.models import Renter, RentRecord` | model |
| `management/commands/retry_failed_payouts.py` | 10 | `from properties.models import RentRecord` | model |
| `management/commands/check_vacant_units.py` | 9 | `from properties.models import Unit` | model |
| `management/commands/send_monthly_rent_summary.py` | 6 | `from properties.services.summary_service import send_monthly_rent_summary_email` | service |

### management → notification
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `management/commands/monthly_whatsapp_and_email_summary_to_owner.py` | 15 | `from notification.services.whatsapp_service import send_whatsapp_message` | service |
| `management/commands/apply_late_fees.py` | 15 | `from notification.services.whatsapp_service import send_whatsapp_message` | service |
| `management/commands/send_rent_reminders.py` | 6 | `from notification.services.whatsapp_service import send_whatsapp_message` | service |
| `management/commands/daily_rent_reminder.py` | 6 | `from notification.services.whatsapp_service import send_whatsapp_message` | service |
| `management/commands/check_vacant_units.py` | 8 | `from notification.services.whatsapp_service import send_whatsapp_message` | service |
| `management/commands/rent_reminder_service.py` | 4 | `from notification.services.whatsapp_service import send_whatsapp_message` | service |
| `management/commands/auto_deactivate_renters.py` | 6 | `from notification.utils import send_whatsapp_message` | utility |

### management → rentsecure_be
| Source File | Line | Import Statement | Type |
|---|---|---|---|
| `management/commands/apply_late_fees.py` | 17 | `from rentsecure_be.type_compat import override` | utility |
| `management/commands/send_rent_reminders.py` | 8 | `from rentsecure_be.type_compat import override` | utility |
| `management/commands/daily_rent_reminder.py` | 8 | `from rentsecure_be.type_compat import override` | utility |
| `management/commands/auto_deactivate_renters.py` | 8 | `from rentsecure_be.type_compat import override` | utility |
| `management/commands/retry_failed_payouts.py` | 11 | `from rentsecure_be.services.cashfree_service import process_rent_payout` | service |
| `management/commands/retry_failed_payouts.py` | 12 | `from rentsecure_be.type_compat import override` | utility |
| `management/commands/generate_monthly_rent_records.py` | 7 | `from rentsecure_be.type_compat import override` | utility |

---

## 2. Circular Dependencies

The following circular (bidirectional) dependency cycles were detected:

### 1. core ↔ properties
- **core → properties:** `core/views.py`, `core/services/owner_reporting_service.py`, `core/services/bank_details_service.py`
- **properties → core:** `properties/views/unit_views.py`, `properties/views/rent_record_views.py`, `properties/views/renter_views.py`, `properties/services/unit_service.py`, `properties/models/unit_models.py`, `properties/models/renter_models.py`, `properties/models/building_models.py`, `properties/utils/utils.py`, `properties/feature_enforcer.py`, `properties/services/summary_service.py`

### 2. core ↔ rentsecure_be
- **core → rentsecure_be:** `core/views.py`, `core/serializers.py`, `core/models.py`, `core/apps.py`, `core/services/bank_details_service.py`
- **rentsecure_be → core:** `rentsecure_be/services/cashfree_service.py`

### 3. properties ↔ notification
- **properties → notification:** `properties/views/rent_record_views.py`, `properties/views/property_views.py`, `properties/services/summary_service.py`, `properties/services/renter_onboarding_service.py`, `properties/utils/utils.py`, `properties/signals/__init__.py`, `properties/scheduler.py`, `properties/cron/vacate_reminder.py`
- **notification → properties:** `notification/services/schedule_reminders.py`, `notification/services/voice_note_service.py`, `notification/services/extra_charge_reminders.py`

### 4. properties ↔ rentsecure_be
- **properties → rentsecure_be:** 25+ files across views, serializers, models, services, management commands
- **rentsecure_be → properties:** `rentsecure_be/services/cashfree_service.py`, `rentsecure_be/utils/export_utils.py`

---

## 3. Infrastructure Boundary Violations (imports from `rentsecure_be` by other apps)

**`rentsecure_be`** is the project configuration / infrastructure layer. Other apps importing from it violate the modular monolith boundary.

### Total violations: 41 imports across 17 files

#### By source app:
- **properties:** 25 imports (views, serializers, models, services, communication, cron, management commands, apps.py)
- **core:** 6 imports (views, serializers, models, apps.py, services)
- **finance:** 2 imports (views, models)
- **notification:** 4 imports (services — i18n_service)
- **smartbot:** 1 import (actions — cashfree_service)
- **referral_and_earn:** 2 imports (apps.py, models — type_compat)
- **management:** 7 imports (commands — type_compat, cashfree_service)
- **ai_assistant:** 0 imports
- **dashboard:** 0 imports
- **documents:** 0 imports

#### Key violation patterns:
1. **`type_compat` shim used everywhere:** 20+ files import `from rentsecure_be.type_compat import override`. This is a Python 3.12 compatibility shim that should live in `shared/` or be vendored.
2. **Payment services accessed directly:** `rentsecure_be.services.cashfree_service` and `rentsecure_be.services.razorpay_service` are imported by `core`, `properties`, `smartbot`, and `management` commands.
3. **i18n service accessed directly:** `rentsecure_be.services.i18n_service` is imported by `notification` app.
4. **Export utilities accessed directly:** `rentsecure_be.utils.export_utils` is imported by `core`.

---

## 4. Summary Statistics

| Metric | Count |
|---|---|
| Total cross-app imports (non-test source files) | 145 |
| Source apps involved | 9 |
| Target apps involved | 10 (including `shared`) |
| Circular dependency cycles | 4 |
| Infrastructure boundary violations (`rentsecure_be`) | 41 |
| Model imports | 89 |
| Service imports | 34 |
| Utility imports | 18 |
| Serializer imports | 1 |
| View imports | 0 |

---

## 5. Recommendations

### Immediate Actions
1. **Move `type_compat.py` to `shared/`:** The `override` shim is imported by 20+ files across 6 apps. This is the single largest source of infrastructure boundary violations.
2. **Introduce a `payments` app or interface layer:** Payment services (`cashfree_service`, `razorpay_service`) are imported directly by multiple apps. Consider a port/adapter pattern with a `payments.ports.PaymentGateway` interface.
3. **Move `i18n_service` to `shared/`:** The translation service is imported by `notification` and could be a shared utility.
4. **Move `export_utils` to `properties` or `shared/`:** The Excel export utility for rent reports belongs with the properties domain or in shared.

### Circular Dependency Remediation
- **core ↔ properties:** Consider moving shared model references (e.g., `User`) to a `shared` domain or use Django's `get_user_model()` / string references more consistently.
- **core ↔ rentsecure_be:** Remove `type_compat` and payment service imports from `core` by introducing interfaces.
- **properties ↔ notification:** Use Django signals or a pub/sub pattern instead of direct service imports.
- **properties ↔ rentsecure_be:** Same as above — extract payment/export utilities to shared interfaces.

---

*Report generated by automated AST-based import analysis.*
