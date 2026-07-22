from __future__ import annotations

from core.events.bus.decorators import (
    event_handler,
    get_registry,
    register_handler,
    unregister_handler,
)


class FakeEvent:
    pass


class UserCreated:
    pass


class PaymentReceived:
    pass


class TestEventHandlerDecorator:
    def setup_method(self) -> None:
        get_registry().clear()

    def test_decorator_registers_handler(self) -> None:
        @event_handler(UserCreated)
        def send_notification(event: FakeEvent) -> None:
            pass

        registry = get_registry()
        handlers = registry.get_handlers(UserCreated)
        assert len(handlers) == 1
        assert handlers[0].execute(FakeEvent()) is None

    def test_decorator_function_callable(self) -> None:
        @event_handler(UserCreated)
        def send_notification(event: FakeEvent) -> str:
            return "sent"

        assert send_notification(FakeEvent()) == "sent"

    def test_multiple_handlers_for_same_event(self) -> None:
        @event_handler(UserCreated)
        def handler_a(event: FakeEvent) -> None:
            pass

        @event_handler(UserCreated)
        def handler_b(event: FakeEvent) -> None:
            pass

        registry = get_registry()
        handlers = registry.get_handlers(UserCreated)
        names = [h._func.__name__ for h in handlers]
        assert "handler_a" in names
        assert "handler_b" in names

    def test_different_events_tracked_independently(self) -> None:
        @event_handler(UserCreated)
        def user_handler(event: FakeEvent) -> None:
            pass

        @event_handler(PaymentReceived)
        def payment_handler(event: FakeEvent) -> None:
            pass

        registry = get_registry()
        assert len(registry.get_handlers(UserCreated)) >= 1
        assert len(registry.get_handlers(PaymentReceived)) >= 1

    def test_decorated_function_has_metadata(self) -> None:
        @event_handler(UserCreated)
        def send_notification(event: FakeEvent) -> None:
            pass

        assert hasattr(send_notification, "_event_type")
        assert send_notification._event_type is UserCreated
        assert hasattr(send_notification, "_registered")
        assert send_notification._registered is True

    def test_handler_wrapper_conforms_to_protocol(self) -> None:
        @event_handler(UserCreated)
        def send_notification(event: FakeEvent) -> None:
            pass

        handler_wrapper = send_notification._handler
        from core.events.bus.interfaces import IEventHandler

        assert isinstance(handler_wrapper, IEventHandler)
        assert handler_wrapper.event_type is UserCreated
        assert handler_wrapper.execute(FakeEvent()) is None

    def test_register_handler_with_callable(self) -> None:
        def my_handler(event: FakeEvent) -> None:
            pass

        register_handler(UserCreated, my_handler)
        registry = get_registry()
        handlers = registry.get_handlers(UserCreated)
        assert len(handlers) >= 1
        unregister_handler(UserCreated, handlers[0])

    def test_unregister_handler_removes(self) -> None:
        @event_handler(UserCreated)
        def send_notification(event: FakeEvent) -> None:
            pass

        registry = get_registry()
        handlers_before = registry.get_handlers(UserCreated)
        unregister_handler(UserCreated, send_notification._handler)
        handlers_after = registry.get_handlers(UserCreated)
        assert len(handlers_after) < len(handlers_before)

    def test_event_handler_wrapper_repr(self) -> None:
        @event_handler(UserCreated)
        def send_notification(event: FakeEvent) -> None:
            pass

        handler = send_notification._handler
        r = repr(handler)
        assert "UserCreated" in r


__all__ = ["TestEventHandlerDecorator"]
