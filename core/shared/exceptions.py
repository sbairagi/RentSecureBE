from __future__ import annotations


class DomainException(Exception):  # noqa: N818
    """Base class for all domain exceptions."""

    def __init__(self, message: str = "", **kwargs: object) -> None:
        super().__init__(message)
        self.message = message
        self.details = kwargs


class ValidationException(DomainException):  # noqa: N818
    """Raised when validation fails."""


class BusinessRuleViolation(DomainException):  # noqa: N818
    """Raised when a business rule is violated."""


class EntityNotFound(DomainException):  # noqa: N818
    """Raised when an entity does not exist."""


class ConflictException(DomainException):  # noqa: N818
    """Raised when a uniqueness or state conflict occurs."""


class AuthorizationException(DomainException):  # noqa: N818
    """Raised when an action is not authorized."""


__all__ = [
    "DomainException",
    "ValidationException",
    "BusinessRuleViolation",
    "EntityNotFound",
    "ConflictException",
    "AuthorizationException",
]
