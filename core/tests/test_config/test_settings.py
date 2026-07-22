from __future__ import annotations

import pytest

from core.config.constants import (
    ENVIRONMENT_DEVELOPMENT,
    ENVIRONMENT_PRODUCTION,
    ENVIRONMENT_STAGING,
)
from core.config.settings import get_bool, get_csv, get_int, get_str, require


class TestConfigSettings:
    def test_get_str_default(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("TEST_KEY", raising=False)
        assert get_str("TEST_KEY") == ""
        assert get_str("TEST_KEY", default="fallback") == "fallback"

    def test_get_str_from_env(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("TEST_KEY", "hello")
        assert get_str("TEST_KEY") == "hello"

    def test_get_bool_default(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("TEST_BOOL", raising=False)
        assert get_bool("TEST_BOOL") is False

    def test_get_bool_true(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("TEST_BOOL", "true")
        assert get_bool("TEST_BOOL") is True

    def test_get_bool_false(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("TEST_BOOL", "false")
        assert get_bool("TEST_BOOL") is False

    def test_get_int_default(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("TEST_INT", raising=False)
        assert get_int("TEST_INT") == 0

    def test_get_int_from_env(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("TEST_INT", "42")
        assert get_int("TEST_INT") == 42

    def test_get_csv_default(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("TEST_CSV", raising=False)
        assert get_csv("TEST_CSV") == []

    def test_get_csv_from_env(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("TEST_CSV", "a,b,c")
        assert get_csv("TEST_CSV") == ["a", "b", "c"]

    def test_require_raises_when_missing(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("REQUIRED_KEY", raising=False)
        with pytest.raises(Exception):  # noqa: B017
            require("REQUIRED_KEY")

    def test_require_returns_value_when_set(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("REQUIRED_KEY", "value123")
        assert require("REQUIRED_KEY") == "value123"


class TestConfigConstants:
    def test_environment_values(self):
        assert ENVIRONMENT_DEVELOPMENT == "development"
        assert ENVIRONMENT_STAGING == "staging"
        assert ENVIRONMENT_PRODUCTION == "production"
