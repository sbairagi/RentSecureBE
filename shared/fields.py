import os
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models

from shared.type_compat import override


def _get_fernet() -> Fernet:
    key = getattr(settings, "FIELD_ENCRYPTION_KEY", None) or os.environ.get(
        "FIELD_ENCRYPTION_KEY", ""
    )
    if not key:
        raise ImproperlyConfigured(
            "FIELD_ENCRYPTION_KEY is required for encrypted fields. "
            "Set it in settings or environment variables."
        )
    return Fernet(key)


class EncryptedCharField(models.CharField):
    description = "CharField encrypted at rest with Fernet"

    def from_db_value(self, value: Any, expression: Any, connection: Any) -> Any | None:
        if value is None:
            return value
        try:
            return _get_fernet().decrypt(value.encode()).decode()
        except InvalidToken:
            return value

    @override
    def get_prep_value(self, value: Any | None) -> Any | None:
        if value is None:
            return value
        if isinstance(value, str):
            try:
                _get_fernet().decrypt(value.encode())
                return value
            except InvalidToken:
                pass
        return _get_fernet().encrypt(value.encode()).decode()


class EncryptedTextField(models.TextField):
    description = "TextField encrypted at rest with Fernet"

    def from_db_value(self, value: Any, expression: Any, connection: Any) -> Any | None:
        if value is None:
            return value
        try:
            return _get_fernet().decrypt(value.encode()).decode()
        except InvalidToken:
            return value

    @override
    def get_prep_value(self, value: Any | None) -> Any | None:
        if value is None:
            return value
        if isinstance(value, str):
            try:
                _get_fernet().decrypt(value.encode())
                return value
            except InvalidToken:
                pass
        return _get_fernet().encrypt(value.encode()).decode()
