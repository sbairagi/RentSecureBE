from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from types import ModuleType
from typing import Any

import pytest

from django.conf import settings

from core.events.bus.registry import EventHandlerRegistry


class FakeEvent:
    pass


class AnotherEvent:
    pass


class FakeHandler:
    def __init__(self, name: str) -> None:
        self.name = name
        self.executed: list[str] = []

    def execute(self, event: Any) -> str:
        self.executed.append(type(event).__name__)
        return "ok"


class TestEventHandlerRegistry:
    def setup_method(self) -> None:
        self._registry = EventHandlerRegistry()

    def test_register_single_handler(self) -> None:
        handler = FakeHandler("h1")
        self._registry.register(FakeEvent, handler)
        handlers = self._registry.get_handlers(FakeEvent)
        assert handlers == [handler]

    def test_multiple_handlers_maintain_order(self) -> None:
        h1, h2, h3 = FakeHandler("h1"), FakeHandler("h2"), FakeHandler("h3")
        self._registry.register(FakeEvent, h1)
        self._registry.register(FakeEvent, h2)
        self._registry.register(FakeEvent, h3)
        handlers = self._registry.get_handlers(FakeEvent)
        assert handlers == [h1, h2, h3]

    def test_register_does_not_duplicate(self) -> None:
        handler = FakeHandler("h1")
        self._registry.register(FakeEvent, handler)
        self._registry.register(FakeEvent, handler)
        handlers = self._registry.get_handlers(FakeEvent)
        assert len(handlers) == 1

    def test_unregister_removes_handler(self) -> None:
        handler = FakeHandler("h1")
        self._registry.register(FakeEvent, handler)
        self._registry.unregister(FakeEvent, handler)
        assert self._registry.get_handlers(FakeEvent) == []

    def test_unregister_partial_keeps_others(self) -> None:
        h1, h2 = FakeHandler("h1"), FakeHandler("h2")
        self._registry.register(FakeEvent, h1)
        self._registry.register(FakeEvent, h2)
        self._registry.unregister(FakeEvent, h1)
        assert self._registry.get_handlers(FakeEvent) == [h2]

    def test_get_handlers_unknown_type_returns_empty(self) -> None:
        assert self._registry.get_handlers(FakeEvent) == []

    def test_clear_removes_all(self) -> None:
        self._registry.register(FakeEvent, FakeHandler("h1"))
        self._registry.register(AnotherEvent, FakeHandler("h2"))
        self._registry.clear()
        assert self._registry.get_handlers(FakeEvent) == []
        assert self._registry.get_handlers(AnotherEvent) == []

    def test_all_registered_types(self) -> None:
        self._registry.register(FakeEvent, FakeHandler("h1"))
        self._registry.register(AnotherEvent, FakeHandler("h2"))
        types = self._registry.all_registered_types()
        assert FakeEvent in types
        assert AnotherEvent in types

    def test_handlers_for_different_events_are_independent(self) -> None:
        handler = FakeHandler("h1")
        self._registry.register(FakeEvent, handler)
        self._registry.register(AnotherEvent, handler)
        assert len(self._registry.get_handlers(FakeEvent)) == 1
        assert len(self._registry.get_handlers(AnotherEvent)) == 1

    def test_concurrent_registration_is_safe(self) -> None:
        def register_many() -> None:
            for i in range(100):
                handler = FakeHandler(
                    f"concurrent_{i}_{threading.current_thread().name}"
                )
                self._registry.register(FakeEvent, handler)

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(register_many) for _ in range(8)]
            for f in futures:
                f.result()

        handlers = self._registry.get_handlers(FakeEvent)
        assert len(handlers) == 800

    def test_concurrent_dispatch_is_safe(self) -> None:
        handler = FakeHandler("shared")
        self._registry.register(FakeEvent, handler)

        def dispatch() -> None:
            self._registry.get_handlers(FakeEvent)

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(dispatch) for _ in range(100)]
            for f in futures:
                f.result()

        assert len(handler.executed) == 0

    def test_discover_returns_count(self) -> None:
        from unittest.mock import patch

        with patch("django.conf.settings.INSTALLED_APPS", []):
            count = self._registry.discover()
        assert isinstance(count, int)
        assert count == 0

    def test_discover_handles_import_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import core.events.bus.registry as rm

        fake_module = ModuleType("fakeapp.bus.handlers")

        def fake_handler(event: Any) -> None:
            pass

        fake_handler._event_type = FakeEvent
        fake_handler._registered = False
        fake_module.fake_handler = fake_handler

        original_imp = rm.importlib.import_module

        def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "fakeapp.bus.handlers":
                return fake_module
            return original_imp(name, *args, **kwargs)

        monkeypatch.setattr(rm.importlib, "import_module", mock_import)
        monkeypatch.setattr(settings, "INSTALLED_APPS", ["fakeapp"], raising=False)
        count = self._registry.discover()
        assert count == 1
        assert len(self._registry.get_handlers(FakeEvent)) == 1

    def test_reset_clears_registry(self) -> None:
        self._registry.register(FakeEvent, FakeHandler("h1"))
        self._registry.register(AnotherEvent, FakeHandler("h2"))
        self._registry.reset()
        assert self._registry.get_handlers(FakeEvent) == []
        assert self._registry.get_handlers(AnotherEvent) == []


__all__ = ["TestEventHandlerRegistry"]
