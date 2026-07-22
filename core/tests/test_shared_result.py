from __future__ import annotations

from core.shared.result import Result


class TestResult:
    def test_ok_creates_success(self):
        r = Result.ok(42)
        assert r.is_success is True
        assert r.value == 42
        assert r.error is None

    def test_fail_creates_failure(self):
        r = Result.fail("something went wrong")
        assert r.is_success is False
        assert r.value is None
        assert r.error == "something went wrong"

    def test_ok_with_string_value(self):
        r = Result.ok("hello")
        assert r.is_success is True
        assert r.value == "hello"

    def test_fail_with_empty_error(self):
        r = Result.fail("")
        assert r.is_success is False
        assert r.error == ""
