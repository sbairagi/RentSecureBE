# mypy: disable-error-code="import-not-found"

import sys
import types
from typing import Any

# WeasyPrint requires GTK/gobject system libraries (libgobject-2.0-0)
# that are not available on macOS. Inject a stub so test collection
# does not fail on environments without those C libraries.
# On Linux CI weasyprint imports normally and this block is skipped.
try:
    import weasyprint  # noqa: F401
except Exception:
    _weasyprint_stub = types.ModuleType("weasyprint")

    class _StubHTML:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            """Stub constructor for environments without weasyprint."""
            # Intentionally empty: stub for environments without weasyprint

        def write_pdf(self, *args: Any, **kwargs: Any) -> None:
            """Stub PDF writer for environments without weasyprint."""
            # Intentionally empty: stub for environments without weasyprint

    _weasyprint_stub.HTML = _StubHTML  # type: ignore[attr-defined]
    sys.modules["weasyprint"] = _weasyprint_stub

import os
from datetime import timedelta
from decimal import Decimal

import factory
import pytest
from faker import Faker

import django
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rentsecure_be.settings")
django.setup()

from django.conf import settings  # noqa: E402

settings.SECURE_SSL_REDIRECT = False
settings.SESSION_COOKIE_SECURE = False
settings.CSRF_COOKIE_SECURE = False

if len(settings.SECRET_KEY) < 32:
    settings.SECRET_KEY = (
        "test-secret-key-rentsecure-be-ci-pipeline-2026!"  # noqa: S105
    )

from core.models import (  # noqa: E402
    AddOnPurchase,
    NotificationPreference,
    OwnerBankDetails,
    PlanFeatureLimit,
    SubscriptionPlan,
    UsageLimit,
    UserSubscription,
)
from properties.models import (  # noqa: E402
    Building,
    Caretaker,
    ExtraCharge,
    PropertyTaxRecord,
    Renter,
    RentRecord,
    Unit,
)

fake = Faker()
User = get_user_model()


# ---------------------------------------------------------------------------
# Factory Boy Factories
# ---------------------------------------------------------------------------


class UserFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.LazyAttribute(lambda _: fake.user_name())
    email = factory.LazyAttribute(lambda _: fake.email())
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    full_name = factory.LazyAttribute(lambda _: fake.name())
    phone = factory.LazyAttribute(lambda _: f"+91{fake.random_number(digits=10)}")
    is_investor = False
    is_phone_verified = True
    whatsapp_number = factory.LazyAttribute(lambda obj: obj.phone)
    is_active = True
    is_staff = False
    is_superuser = False


class UserProfileFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = "core.UserProfile"

    user = factory.SubFactory(UserFactory)
    whatsapp_number = factory.LazyAttribute(lambda obj: obj.user.phone)
    whatsapp_opt_in = True
    language_preference = "en"


class SubscriptionPlanFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = SubscriptionPlan
        django_get_or_create = ("name",)

    name = factory.Iterator(["free", "pro", "elite"])
    monthly_price = factory.Iterator([Decimal("0"), Decimal("29.99"), Decimal("99.99")])
    yearly_price = factory.Iterator(
        [Decimal("0"), Decimal("299.99"), Decimal("999.99")]
    )
    features = "Full feature access"
    is_active = True


class UserSubscriptionFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = UserSubscription

    user = factory.SubFactory(UserFactory)
    plan = factory.SubFactory(SubscriptionPlanFactory)
    start_date = factory.LazyFunction(lambda: timezone.now().date())
    end_date = factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=30))
    is_active = True
    is_yearly = False
    tax_reminder_days_before = 7
    rent_reminder_days_before = 7


class PlanFeatureLimitFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = PlanFeatureLimit

    plan = factory.SubFactory(SubscriptionPlanFactory)
    feature_key = factory.Iterator(
        [
            "max_buildings",
            "max_units",
            "max_renters",
            "max_caretakers",
            "max_unit_images",
            "max_document_uploads",
            "tax_notifications",
            "whatsapp_alerts",
            "rent_agreement_drafting",
            "export_pdf_dossier",
        ]
    )
    value = factory.Iterator(["10", "50", "100", "unlimited", "yes", "no"])


class UsageLimitFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = UsageLimit

    user = factory.SubFactory(UserFactory)
    feature_key = factory.Iterator(
        ["max_buildings", "max_units", "max_renters", "max_caretakers"]
    )
    usage_count = 0
    updated_at = factory.LazyFunction(timezone.now)


class BuildingFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = Building

    owner = factory.SubFactory(UserFactory)
    name = factory.LazyAttribute(lambda _: f"{fake.street_address()} Building")
    address_line = factory.LazyAttribute(lambda _: fake.street_address())
    city = factory.LazyAttribute(lambda _: fake.city())
    state = factory.LazyAttribute(lambda _: fake.state_abbr())
    country = factory.LazyAttribute(lambda _: fake.country_code())
    postal_code = factory.LazyAttribute(lambda _: fake.postcode())
    is_archived = False


class UnitFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = Unit

    owner = factory.SubFactory(UserFactory)
    building = factory.SubFactory(BuildingFactory)
    building_name = factory.SelfAttribute("building.name")
    unit = factory.LazyAttribute(lambda _: str(fake.random_int(min=101, max=999)))
    address_line = factory.LazyAttribute(lambda _: fake.street_address())
    city = factory.LazyAttribute(lambda _: fake.city())
    state = factory.LazyAttribute(lambda _: fake.state_abbr())
    country = factory.LazyAttribute(lambda _: fake.country_code())
    postal_code = factory.LazyAttribute(lambda _: fake.postcode())
    unit_type = factory.Iterator([choice[0] for choice in Unit.UnitType.choices])
    status = factory.Iterator(["vacant", "occupied", "maintenance"])
    is_vacant = factory.LazyAttribute(lambda obj: obj.status == "vacant")
    rent_amount = factory.LazyAttribute(lambda _: Decimal(fake.random_int(5000, 50000)))
    is_archived = False


class RenterFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = Renter

    unit = factory.SubFactory(UnitFactory)
    name = factory.LazyAttribute(lambda _: fake.name())
    phone = factory.LazyAttribute(lambda _: f"+91{fake.random_number(digits=10)}")
    email = factory.LazyAttribute(lambda _: fake.email())
    start_date = factory.LazyFunction(
        lambda: timezone.now().date() - timedelta(days=30)
    )
    end_date = factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=335))
    rent_amount = factory.LazyAttribute(lambda _: Decimal(fake.random_int(5000, 50000)))
    is_active = True
    status = Renter.RenterStatus.ACTIVE
    is_flagged = False
    flagged_reason = ""
    missed_rents = 0


class RentRecordFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = RentRecord

    unit = factory.SubFactory(UnitFactory)
    renter = factory.SubFactory(RenterFactory, unit=factory.SelfAttribute("..unit"))
    amount = factory.LazyAttribute(lambda _: Decimal(fake.random_int(5000, 50000)))
    payment_method = factory.Iterator(
        [choice[0] for choice in RentRecord.PaymentMethod.choices]
    )
    status = factory.Iterator(["pending", "paid", "overdue", "cancelled"])
    paid_on = factory.LazyFunction(lambda: timezone.now().date() - timedelta(days=5))
    due_date = factory.Sequence(
        lambda n: timezone.now().date().replace(day=5) - timedelta(days=30 * n)
    )
    late_fee = Decimal("0")
    discount = Decimal("0")
    notes = ""
    transaction_id = factory.LazyAttribute(lambda _: str(fake.uuid4())[:32])
    payout_status = "PENDING"
    payout_reference = ""
    payment_link = ""
    razorpay_order_id = ""
    payout_retries = 0
    last_payout_retry = None
    payout_retry_count = 0
    adjustment_reason = ""


class RentRecordPaidFactory(RentRecordFactory):
    status = "paid"
    paid_on = factory.LazyFunction(lambda: timezone.now().date() - timedelta(days=5))


class CaretakerFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = Caretaker

    unit = factory.SubFactory(UnitFactory)
    owner = factory.SelfAttribute("unit.owner")  # noqa: S1192
    name = factory.LazyAttribute(lambda _: fake.name())
    phone = factory.LazyAttribute(lambda _: f"+91{fake.random_number(digits=10)}")
    email = factory.LazyAttribute(lambda _: fake.email())
    address = factory.LazyAttribute(lambda _: fake.address())
    joining_date = factory.LazyFunction(
        lambda: timezone.now().date() - timedelta(days=60)
    )
    leaving_date = factory.LazyFunction(
        lambda: timezone.now().date() + timedelta(days=180)
    )
    is_active = True
    notes = ""


class ExtraChargeFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = ExtraCharge

    unit = factory.SubFactory(UnitFactory)
    owner = factory.SelfAttribute("unit.owner")  # nosonar
    name = factory.Iterator(["Maintenance", "Water", "Parking", "Society Dues"])
    amount = factory.LazyAttribute(lambda _: Decimal(fake.random_int(100, 5000)))
    charge_type = factory.Iterator(["fixed", "variable"])
    is_recurring = False
    due_date = factory.LazyFunction(lambda: timezone.now().date().replace(day=10))
    is_paid = False


class PropertyTaxRecordFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = PropertyTaxRecord

    unit = factory.SubFactory(UnitFactory)
    owner = factory.SelfAttribute("unit.owner")  # nosonar
    financial_year = factory.LazyAttribute(
        lambda _: f"{timezone.now().year}-{str(timezone.now().year + 1)[2:]}"
    )
    amount = factory.LazyAttribute(lambda _: Decimal(fake.random_int(5000, 50000)))
    due_date = factory.LazyFunction(
        lambda: timezone.now().date().replace(month=3, day=31)
    )
    is_paid = False
    payment_reference = factory.LazyAttribute(lambda _: str(fake.uuid4())[:32])


class NotificationPreferenceFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = NotificationPreference

    owner = factory.SubFactory(UserFactory)
    rent_alerts_whatsapp = True
    rent_alerts_email = True
    monthly_summary_email = True
    monthly_summary_whatsapp = False
    payout_alerts_whatsapp = True
    payout_alerts_email = False


class OwnerBankDetailsFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = OwnerBankDetails

    owner = factory.SubFactory(UserFactory)
    bank_account_number = factory.LazyAttribute(lambda _: fake.bban())
    ifsc_code = factory.LazyAttribute(lambda _: fake.swift11()[:11])
    account_holder_name = factory.LazyAttribute(lambda obj: obj.owner.full_name)
    beneficiary_id = factory.LazyAttribute(lambda _: f"BENE-{str(fake.uuid4())}")
    bank_account_verified = False


class AddOnPurchaseFactory(factory.django.DjangoModelFactory):  # type: ignore[misc]
    class Meta:
        model = AddOnPurchase

    user = factory.SubFactory(UserFactory)
    name = factory.Iterator(
        [
            "max_buildings",
            "max_units",
            "max_renters",
            "whatsapp_alerts",
            "rent_agreement_drafting",
        ]
    )
    amount = factory.LazyAttribute(lambda _: Decimal(fake.random_int(99, 9999)))
    is_recurring = False
    purchase_date = factory.LazyFunction(timezone.now)


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)  # type: ignore[misc, unused-ignore]
def _rentsecure_test_defaults(db, monkeypatch):  # type: ignore[no-untyped-def]
    """Autouse fixture: clear caches and patch external services."""
    cache.clear()
    Group.objects.get_or_create(name="tenant")
    Group.objects.get_or_create(name="renter")

    class _FakeMessage:
        sid = "SM_TEST"

    class _FakeMessages:
        def create(self, *args: Any, **kwargs: Any) -> Any:
            return _FakeMessage()

    class _FakeTwilioClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.messages = _FakeMessages()

    monkeypatch.setattr("core.views.Client", _FakeTwilioClient)
    monkeypatch.setattr("core.services.otp_service.Client", _FakeTwilioClient)
    monkeypatch.setattr("notification.utils.Client", _FakeTwilioClient)
    monkeypatch.setattr(
        "notification.services.whatsapp_service.Client", _FakeTwilioClient
    )
    monkeypatch.setattr(
        "properties.views.rent_record_views.create_payment_link",
        lambda rent: f"https://payments.test/rent/{rent.id}",
    )
    monkeypatch.setattr(
        "notification.services.voice_note_service.send_thank_you_voice_note",
        lambda rent: None,
    )
    yield


@pytest.fixture  # type: ignore[misc, unused-ignore]
def user(db: Any) -> User:  # type: ignore[valid-type]
    return UserFactory()


@pytest.fixture  # type: ignore[misc, unused-ignore]
def owner(db: Any) -> User:  # type: ignore[valid-type]
    return UserFactory(username=fake.user_name(), full_name=fake.name())


@pytest.fixture  # type: ignore[misc, unused-ignore]
def plan_free(db: Any) -> SubscriptionPlan:
    return SubscriptionPlanFactory(name="free", monthly_price=Decimal("0"))


@pytest.fixture  # type: ignore[misc, unused-ignore]
def plan_pro(db: Any) -> SubscriptionPlan:
    return SubscriptionPlanFactory(name="pro", monthly_price=Decimal("29.99"))


@pytest.fixture  # type: ignore[misc, unused-ignore]
def subscription(owner: User, plan_pro: SubscriptionPlan) -> UserSubscription:  # type: ignore[valid-type]
    return UserSubscriptionFactory(user=owner, plan=plan_pro, is_active=True)


@pytest.fixture  # type: ignore[misc, unused-ignore]
def building(owner: User) -> Building:  # type: ignore[valid-type]
    return BuildingFactory(owner=owner)


@pytest.fixture  # type: ignore[misc, unused-ignore]
def unit(building: Building) -> Unit:
    return UnitFactory(owner=building.owner, building=building)


@pytest.fixture  # type: ignore[misc, unused-ignore]
def renter(unit: Unit) -> Renter:
    return RenterFactory(unit=unit, owner=unit.owner)


@pytest.fixture  # type: ignore[misc, unused-ignore]
def rent_record(unit: Unit, renter: Renter) -> RentRecord:
    return RentRecordFactory(unit=unit, renter=renter)


@pytest.fixture  # type: ignore[misc, unused-ignore]
def caretaker(unit: Unit) -> Caretaker:
    return CaretakerFactory(unit=unit, owner=unit.owner)


@pytest.fixture  # type: ignore[misc, unused-ignore]
def addon_purchase(user: User) -> AddOnPurchase:  # type: ignore[valid-type]
    return AddOnPurchaseFactory(user=user)
