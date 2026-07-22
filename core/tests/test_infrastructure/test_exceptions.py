from __future__ import annotations

import pytest

from core.infrastructure.exceptions import (
    ConfigurationError,
    ConnectionError,
    ExternalServiceError,
    InfrastructureError,
)


class TestInfrastructureExceptions:
    def test_base_exception_is_exception(self):
        assert issubclass(InfrastructureError, Exception)

    def test_derived_exceptions_inherit_base(self):
        assert issubclass(ConfigurationError, InfrastructureError)
        assert issubclass(ExternalServiceError, InfrastructureError)
        assert issubclass(ConnectionError, InfrastructureError)

    def test_raise_with_message(self):
        with pytest.raises(InfrastructureError) as exc_info:
            raise InfrastructureError("test failure")
        assert str(exc_info.value) == "test failure"
        assert exc_info.value.message == "test failure"

    def test_raise_with_details(self):
        exc = InfrastructureError("fail", code=500, service="db")
        assert exc.message == "fail"
        assert exc.details == {"code": 500, "service": "db"}

    def test_connection_error_default_message(self):
        exc = ConnectionError()
        assert str(exc) == ""
        assert exc.message == ""

    def test_configuration_error_default_message(self):
        exc = ConfigurationError()
        assert str(exc) == ""
        assert exc.message == ""

    def test_external_service_error_default_message(self):
        exc = ExternalServiceError()
        assert str(exc) == ""
        assert exc.message == ""
