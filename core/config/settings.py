from __future__ import annotations

from decouple import Csv, config  # type: ignore[import-untyped]

from core.events.inbox.constants import DEFAULT_BATCH_SIZE as DEFAULT_INBOX_BATCH_SIZE
from core.events.inbox.constants import DEFAULT_MAX_RETRY as DEFAULT_INBOX_MAX_RETRY
from core.events.inbox.constants import (
    DEFAULT_PROCESS_INTERVAL as DEFAULT_INBOX_PROCESS_INTERVAL,
)
from core.events.inbox.constants import (
    DEFAULT_RETENTION_DAYS as DEFAULT_INBOX_RETENTION_DAYS,
)
from core.events.outbox.constants import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_DISPATCH_INTERVAL,
    DEFAULT_MAX_RETRY,
    DEFAULT_RETENTION_DAYS,
)
from core.infrastructure.exceptions import ConfigurationError


def get_str(key: str, default: str = "") -> str:
    return config(key, default=default)


def get_bool(key: str, default: bool = False) -> bool:
    return config(key, default=default, cast=bool)


def get_int(key: str, default: int = 0) -> int:
    return config(key, default=default, cast=int)


def get_csv(key: str, default: str = "") -> list[str]:
    return config(key, default=default, cast=Csv())


def require(key: str) -> str:
    value = config(key, default="")
    if not value:
        raise ConfigurationError(f"Missing required configuration: {key}")
    return value


def get_outbox_batch_size() -> int:
    return get_int("OUTBOX_BATCH_SIZE", DEFAULT_BATCH_SIZE)


def get_outbox_max_retry() -> int:
    return get_int("OUTBOX_MAX_RETRY", DEFAULT_MAX_RETRY)


def get_outbox_retention_days() -> int:
    return get_int("OUTBOX_RETENTION_DAYS", DEFAULT_RETENTION_DAYS)


def get_outbox_dispatch_interval() -> int:
    return get_int("OUTBOX_DISPATCH_INTERVAL", DEFAULT_DISPATCH_INTERVAL)


def get_inbox_batch_size() -> int:
    return get_int("INBOX_BATCH_SIZE", DEFAULT_INBOX_BATCH_SIZE)


def get_inbox_max_retry() -> int:
    return get_int("INBOX_MAX_RETRY", DEFAULT_INBOX_MAX_RETRY)


def get_inbox_retention_days() -> int:
    return get_int("INBOX_RETENTION_DAYS", DEFAULT_INBOX_RETENTION_DAYS)


def get_inbox_process_interval() -> int:
    return get_int("INBOX_PROCESS_INTERVAL", DEFAULT_INBOX_PROCESS_INTERVAL)


__all__ = [
    "get_str",
    "get_bool",
    "get_int",
    "get_csv",
    "require",
    "get_outbox_batch_size",
    "get_outbox_max_retry",
    "get_outbox_retention_days",
    "get_outbox_dispatch_interval",
    "get_inbox_batch_size",
    "get_inbox_max_retry",
    "get_inbox_retention_days",
    "get_inbox_process_interval",
]
