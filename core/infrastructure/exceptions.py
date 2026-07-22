from __future__ import annotations


class InfrastructureError(Exception):
    """Base exception for infrastructure layer failures."""

    def __init__(self, message: str = "", **kwargs: object) -> None:
        super().__init__(message)
        self.message = message
        self.details = kwargs


class ConnectionError(InfrastructureError):
    """Raised when a network or connection error occurs."""


class ExternalServiceError(InfrastructureError):
    """Raised when an external service call fails."""


class ConfigurationError(InfrastructureError):
    """Raised when configuration is invalid or missing."""


__all__ = [
    "InfrastructureError",
    "ConnectionError",
    "ExternalServiceError",
    "ConfigurationError",
]
