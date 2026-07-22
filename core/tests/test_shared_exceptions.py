from __future__ import annotations

import pytest

from core.shared.exceptions import (
    AuthorizationException,
    BusinessRuleViolation,
    ConflictException,
    DomainException,
    EntityNotFound,
    ValidationException,
)


class TestSharedExceptions:
    def test_domain_exception_is_exception(self):
        assert issubclass(DomainException, Exception)

    def test_validation_exception_inherits_domain(self):
        assert issubclass(ValidationException, DomainException)

    def test_business_rule_violation_inherits_domain(self):
        assert issubclass(BusinessRuleViolation, DomainException)

    def test_entity_not_found_inherits_domain(self):
        assert issubclass(EntityNotFound, DomainException)

    def test_conflict_exception_inherits_domain(self):
        assert issubclass(ConflictException, DomainException)

    def test_authorization_exception_inherits_domain(self):
        assert issubclass(AuthorizationException, DomainException)

    def test_raise_with_message(self):
        with pytest.raises(ValidationException) as exc_info:
            raise ValidationException("invalid input")
        assert str(exc_info.value) == "invalid input"
        assert exc_info.value.message == "invalid input"

    def test_raise_with_details(self):
        exc = BusinessRuleViolation("rule broken", code="RULE_001")
        assert exc.message == "rule broken"
        assert exc.details == {"code": "RULE_001"}

    def test_entity_not_found_default(self):
        exc = EntityNotFound()
        assert str(exc) == ""
        assert exc.message == ""

    def test_conflict_exception_default(self):
        exc = ConflictException()
        assert str(exc) == ""
        assert exc.message == ""

    def test_authorization_exception_default(self):
        exc = AuthorizationException()
        assert str(exc) == ""
        assert exc.message == ""
