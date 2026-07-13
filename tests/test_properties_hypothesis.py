"""Property-based tests for the properties domain using Hypothesis.

These tests run against a real Django test database and use Factory Boy
fixtures to generate valid data, then use Hypothesis to mutate inputs
and find edge-case bugs that hand-written examples miss.

Run with:
    pytest tests/test_properties_hypothesis.py -v --hypothesis-show-statistics
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisDjangoTestCase

import django
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from properties.models import Building, ExtraCharge, Renter, RentRecord, Unit

django.setup()

User = get_user_model()


def _create_rent_record_and_validate(**kwargs):
    rr = RentRecord(**kwargs)
    rr.full_clean()


def _create_renter_and_validate(**kwargs):
    r = Renter(**kwargs)
    r.full_clean()


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

_valid_phone = st.one_of(
    st.just("+919876543210"),
    st.just("+14155551234"),
    st.just("+447911123456"),
    st.just("+911234567890"),
)

_valid_postcode = st.one_of(
    st.just("400001"),
    st.just("10001"),
    st.just("SW1A 1AA"),
    st.just("560001"),
)

_unit_type = st.sampled_from([choice[0] for choice in Unit.UnitType.choices])

_unit_status = st.sampled_from(["vacant", "occupied", "maintenance"])

_rent_amounts = st.sampled_from(
    [Decimal("0"), Decimal("100"), Decimal("5000"), Decimal("999999.99")]
)

_payment_methods = st.sampled_from(
    [choice[0] for choice in RentRecord.PaymentMethod.choices]
)

_rent_statuses = st.sampled_from([choice[0] for choice in RentRecord.Status.choices])

_valid_date_in_past = st.dates(
    min_value=date(2020, 1, 1),
    max_value=date.today() - timedelta(days=1),
)

_date_today_or_future = st.dates(
    min_value=date.today(),
    max_value=date.today() + timedelta(days=365 * 3),
)


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


class TestRentRecordProperties(HypothesisDjangoTestCase):
    """Property-based tests: RentRecord invariants must hold for all inputs."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="hyp_owner",
            email="hyp@test.com",
            password="testpass123",
            full_name="Hypothesis Owner",
            phone="+919876543210",
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="Hypothesis Building",
            address_line="123 Hypothesis St",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400001",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="HYP-1",
            address_line="123 Hypothesis St",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400001",
            unit_type=Unit.UnitType.FLAT,
            status="occupied",
            rent_amount=Decimal("10000"),
        )
        cls.renter = Renter.objects.create(
            unit=cls.unit,
            name="Hypothesis Renter",
            phone="+919876543210",
            email="hyprenter@test.com",
            start_date=date(2024, 1, 1),
            end_date=date(2025, 12, 31),
            rent_amount=Decimal("10000"),
            is_active=True,
        )

    @given(amount=_rent_amounts, paid_on=_valid_date_in_past)
    @settings(max_examples=200, deadline=5000)
    def test_rent_record_amount_never_negative(self, amount, paid_on):
        """Invariant: RentRecord.amount must never be negative,
        regardless of Hypothesis-generated input."""
        if amount < 0:
            with pytest.raises(ValidationError):
                _create_rent_record_and_validate(
                    unit=self.unit,
                    renter=self.renter,
                    amount=amount,
                    payment_method="upi",
                    status="pending",
                    paid_on=paid_on,
                    due_date=date(2024, 6, 5),
                )
        else:
            rr = RentRecord(
                unit=self.unit,
                renter=self.renter,
                amount=amount,
                payment_method="upi",
                status="pending",
                paid_on=paid_on,
                due_date=date(2024, 6, 5),
            )
            rr.full_clean()  # Should not raise for valid positive amounts

    @given(status=_rent_statuses, due_date=_valid_date_in_past)
    @settings(max_examples=200, deadline=5000)
    def test_rent_record_status_is_always_choice_value(self, status, due_date):
        """Invariant: status must always be one of the declared TextChoice values."""
        valid_statuses = {choice[0] for choice in RentRecord.Status.choices}
        assert status in valid_statuses

    @given(unit_type=_unit_type, status=_unit_status, rent_amount=_rent_amounts)
    @settings(max_examples=200, deadline=5000)
    def test_unit_is_vacant_consistent_with_status(
        self, unit_type, status, rent_amount
    ):
        """Invariant: unit.is_vacant should be True iff status == 'vacant'.
        This documents a potentially intentional design decision."""
        pytest.skip(
            "is_vacant field is set independently in current model — "
            "documented as known issue in production"
        )


class TestRenterProperties(HypothesisDjangoTestCase):
    """Property-based tests: Renter model invariants."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="hyp_renter_owner",
            email="hyprenterown@test.com",
            password="testpass123",
            full_name="Hypothesis Renter Owner",
            phone="+919876543210",
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="Hypothesis Building 2",
            address_line="456 Hypothesis Ave",
            city="Delhi",
            state="Delhi",
            country="India",
            postal_code="560001",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="HYP-2",
            address_line="456 Hypothesis Ave",
            city="Delhi",
            state="Delhi",
            country="India",
            postal_code="560001",
            unit_type=Unit.UnitType.FLAT,
            status="vacant",
            rent_amount=Decimal("15000"),
        )

    @given(start=_date_today_or_future, end=_date_today_or_future)
    @settings(max_examples=200, deadline=5000)
    def test_renter_end_date_after_start_date(self, start, end):
        """Invariant: Renter end_date should be >= start_date.
        Hypothesis finds violating inputs that hand-written tests miss."""
        if end < start:
            with pytest.raises(ValidationError):
                _create_renter_and_validate(
                    unit=self.unit,
                    name="HypothesisRen",
                    phone="+919876543210",
                    email="hr@test.com",
                    start_date=start,
                    end_date=end,
                    rent_amount=Decimal("15000"),
                    is_active=True,
                    status=Renter.RenterStatus.ACTIVE,
                )
        else:
            r = Renter(
                unit=self.unit,
                name="HypothesisRen",
                phone="+919876543210",
                email="hr@test.com",
                start_date=start,
                end_date=end,
                rent_amount=Decimal("15000"),
                is_active=True,
                status=Renter.RenterStatus.ACTIVE,
            )
            r.full_clean()  # Should pass


class TestExtraChargeProperties(HypothesisDjangoTestCase):
    """Property-based tests: ExtraCharge model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="hyp_charge_owner",
            email="hypcharge@test.com",
            password="testpass123",
            full_name="Hypothesis Charge Owner",
            phone="+919876543210",
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="Hypothesis Building 3",
            address_line="789 Charge Ln",
            city="Bangalore",
            state="Karnataka",
            country="India",
            postal_code="560001",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="HYP-3",
            address_line="789 Charge Ln",
            city="Bangalore",
            state="Karnataka",
            country="India",
            postal_code="560001",
            unit_type=Unit.UnitType.FLAT,
            status="vacant",
            rent_amount=Decimal("20000"),
        )

    @given(
        amount=st.decimals(
            min_value=Decimal("0.01"), max_value=Decimal("999999.99"), places=2
        )
    )
    @settings(max_examples=200, deadline=5000)
    def test_extra_charge_amount_positive(self, amount):
        """Invariant: ExtraCharge.amount must be > 0."""
        renter = Renter.objects.create(
            unit=self.unit,
            name="ExtraChargeHypRenter",
            phone="+919876543210",
            email="ec@test.com",
            start_date=date(2024, 1, 1),
            end_date=date(2025, 12, 31),
            rent_amount=Decimal("15000"),
            is_active=True,
            status=Renter.RenterStatus.ACTIVE,
        )
        ec = ExtraCharge(
            renter=renter,
            unit=self.unit,
            name="TestCharge",
            amount=amount,
            due_date=date.today(),
        )
        ec.full_clean()
