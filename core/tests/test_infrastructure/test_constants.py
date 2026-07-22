from __future__ import annotations

from core.infrastructure.constants import (
    BATCH_SIZE,
    CACHE_TTL_LONG,
    CACHE_TTL_MEDIUM,
    CACHE_TTL_SHORT,
    DEFAULT_TIMEOUT_SECONDS,
    RETRY_ATTEMPTS,
)


class TestInfrastructureConstants:
    def test_default_timeout_seconds(self):
        assert DEFAULT_TIMEOUT_SECONDS == 30

    def test_cache_ttl_short(self):
        assert CACHE_TTL_SHORT == 300

    def test_cache_ttl_medium(self):
        assert CACHE_TTL_MEDIUM == 3600

    def test_cache_ttl_long(self):
        assert CACHE_TTL_LONG == 86400

    def test_retry_attempts(self):
        assert RETRY_ATTEMPTS == 3

    def test_batch_size(self):
        assert BATCH_SIZE == 100
