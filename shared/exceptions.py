from __future__ import annotations


class BaseDomainError(Exception):
    """Base class for all domain exceptions."""

    def __init__(self, message: str = "", **kwargs: object) -> None:
        super().__init__(message)
        self.message = message
        self.details = kwargs


class ValidationError(BaseDomainError):
    """Raised when validation fails."""


class BusinessRuleViolationError(BaseDomainError):
    """Raised when a business rule is violated."""


class ExternalServiceError(BaseDomainError):
    """Raised when an external service call fails."""


class ConfigurationError(BaseDomainError):
    """Raised when configuration is invalid or missing."""


__all__ = [
    "BaseDomainError",
    "ValidationError",
    "BusinessRuleViolationError",
    "ExternalServiceError",
    "ConfigurationError",
]
