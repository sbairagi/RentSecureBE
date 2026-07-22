from __future__ import annotations

from decimal import Decimal

import pytest

from core.shared.value_objects.email import Email
from core.shared.value_objects.money import Money
from core.shared.value_objects.phone import Phone


class TestMoneyValueObject:
    def test_create_valid_money(self):
        m = Money(Decimal("100.50"), "USD")
        assert m.amount == Decimal("100.50")
        assert m.currency == "USD"

    def test_coerce_numeric_amount(self):
        m = Money(100, "USD")
        assert m.amount == Decimal("100")

    def test_invalid_currency_raises(self):
        with pytest.raises(ValueError, match="Invalid currency"):
            Money(Decimal("10"), "US")

    def test_add_same_currency(self):
        m1 = Money(Decimal("100"), "USD")
        m2 = Money(Decimal("50"), "USD")
        result = m1.add(m2)
        assert result.amount == Decimal("150")
        assert result.currency == "USD"

    def test_add_mismatched_currency_raises(self):
        m1 = Money(Decimal("100"), "USD")
        m2 = Money(Decimal("50"), "EUR")
        with pytest.raises(ValueError, match="Currency mismatch"):
            m1.add(m2)

    def test_subtract(self):
        m1 = Money(Decimal("100"), "USD")
        m2 = Money(Decimal("30"), "USD")
        result = m1.subtract(m2)
        assert result.amount == Decimal("70")

    def test_multiply(self):
        m = Money(Decimal("100"), "USD")
        result = m.multiply(2)
        assert result.amount == Decimal("200")

    def test_equality(self):
        m1 = Money(Decimal("100"), "USD")
        m2 = Money(Decimal("100"), "USD")
        assert m1 == m2

    def test_inequality(self):
        m1 = Money(Decimal("100"), "USD")
        m2 = Money(Decimal("200"), "USD")
        assert m1 != m2

    def test_comparison(self):
        m1 = Money(Decimal("100"), "USD")
        m2 = Money(Decimal("200"), "USD")
        assert m1 < m2
        assert m2 > m1
        assert m1 <= Money(Decimal("100"), "USD")
        assert m2 >= m1

    def test_hashable(self):
        m1 = Money(Decimal("100"), "USD")
        m2 = Money(Decimal("100"), "USD")
        assert hash(m1) == hash(m2)
        assert len({m1, m2}) == 1

    def test_string_representation(self):
        m = Money(Decimal("99.99"), "INR")
        assert str(m) == "99.99 INR"


class TestEmailValueObject:
    def test_valid_email(self):
        e = Email("user@example.com")
        assert str(e) == "user@example.com"

    def test_invalid_email_raises(self):
        with pytest.raises(ValueError, match="Invalid email address"):
            Email("not-an-email")

    def test_case_insensitive_equality(self):
        e1 = Email("User@Example.com")
        e2 = Email("user@example.com")
        assert e1 == e2

    def test_case_insensitive_hash(self):
        e1 = Email("User@Example.com")
        e2 = Email("user@example.com")
        assert len({e1, e2}) == 1


class TestPhoneValueObject:
    def test_valid_phone_with_plus(self):
        p = Phone("+911234567890")
        assert str(p) == "+911234567890"

    def test_normalizes_to_e164(self):
        p = Phone("911234567890")
        assert str(p) == "+911234567890"

    def test_invalid_phone_raises(self):
        with pytest.raises(ValueError, match="Invalid phone number"):
            Phone("123")

    def test_too_few_digits_raises(self):
        with pytest.raises(ValueError, match="Invalid phone number"):
            Phone("+123456")

    def test_equality(self):
        p1 = Phone("+911234567890")
        p2 = Phone("+911234567890")
        assert p1 == p2

    def test_hashable(self):
        p1 = Phone("+911234567890")
        p2 = Phone("+911234567890")
        assert len({p1, p2}) == 1
