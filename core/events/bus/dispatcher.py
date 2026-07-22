from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from core.events.bus.decorators import get_registry
from core.events.bus.exceptions import HandlerExecutionError, MiddlewareExecutionError
from core.events.bus.handlers import ExecutionReport, HandlerResult
from core.events.bus.interfaces import IEventHandler, IMiddleware
from core.events.bus.registry import EventHandlerRegistry
from shared.domain_events import BaseDomainEvent

logger = logging.getLogger(__name__)


class EventBus:
    """In-process event bus.

    Responsibilities:
    - Dispatch events to registered handlers
    - Run middleware pipeline
    - Collect execution metrics
    - Produce immutable ExecutionReport

    Does NOT:
    - Write Outbox
    - Read Inbox
    - Publish to Kafka/RabbitMQ/SQS/Celery
    """

    def __init__(
        self,
        registry: EventHandlerRegistry | None = None,
        middleware: list[IMiddleware] | None = None,
    ) -> None:
        self._registry = registry or get_registry()
        self._middleware: list[IMiddleware] = list(middleware or [])

    def subscribe(
        self, event_type: type, handler: IEventHandler | Callable[..., Any]
    ) -> None:
        self._registry.register(event_type, handler)

    def unsubscribe(
        self, event_type: type, handler: IEventHandler | Callable[..., Any]
    ) -> None:
        self._registry.unregister(event_type, handler)

    def get_handlers(
        self, event_type: type
    ) -> list[IEventHandler | Callable[..., Any]]:
        return self._registry.get_handlers(event_type)

    def clear(self) -> None:
        self._registry.clear()

    def discover(self) -> int:
        return self._registry.discover()

    def publish(self, event: BaseDomainEvent) -> ExecutionReport:
        event_type = type(event)
        event_id = getattr(event, "event_id", "")
        handlers = self._registry.get_handlers(event_type)
        successful: list[str] = []
        failed: list[HandlerResult] = []

        dispatch_start = time.perf_counter()

        for raw_handler in handlers:
            handler_name = self._resolve_name(raw_handler)
            context: dict[str, Any] = {}

            try:
                context = self._run_before_middleware(event, context)
            except MiddlewareExecutionError as exc:
                logger.warning(
                    "Middleware %s before_dispatch failed for %s: %s",
                    exc.middleware_name,
                    event_type.__name__,
                    exc,
                )
                failed.append(HandlerResult.failure_result(handler_name, 0.0, exc))
                continue

            handler_start = time.perf_counter()
            handler_failed = False
            try:
                if isinstance(raw_handler, IEventHandler):
                    raw_handler.execute(event)
                else:
                    raw_handler(event)
                duration = time.perf_counter() - handler_start
                successful.append(handler_name)
            except Exception as exc:
                duration = time.perf_counter() - handler_start
                handler_failed = True
                handler_exc = HandlerExecutionError(
                    str(exc),
                    event_type=event_type.__name__,
                    handler_name=handler_name,
                    original_exception=exc,
                )
                failed.append(
                    HandlerResult.failure_result(handler_name, duration, handler_exc)
                )
            finally:
                context["duration"] = duration
                context["handler_failed"] = handler_failed
                self._run_after_middleware(event, context, duration)

        total_duration = time.perf_counter() - dispatch_start

        return ExecutionReport(
            event_type=event_type.__name__,
            event_id=str(event_id),
            successful_handlers=tuple(successful),
            failed_handlers=tuple(failed),
            total_handlers=len(handlers),
            duration_seconds=total_duration,
        )

    def dispatch_payload(self, payload: dict[str, Any]) -> ExecutionReport:
        event_type_name = payload.get("event_type", payload.get("type", ""))
        successful: list[str] = []
        failed: list[HandlerResult] = []
        handlers: list[Any] = []

        for et, raw_handlers in self._registry.all_registered_types().items():
            if et.__name__ == event_type_name:
                handlers = raw_handlers
                break

        dispatch_start = time.perf_counter()
        handler_count = len(handlers)

        for raw_handler in handlers:
            handler_name = self._resolve_name(raw_handler)
            context: dict[str, Any] = {}
            try:
                context = self._run_before_middleware_payload(payload, context)
            except MiddlewareExecutionError as exc:
                logger.warning(
                    "Middleware %s before_dispatch failed for payload %s: %s",
                    exc.middleware_name,
                    event_type_name,
                    exc,
                )
                failed.append(HandlerResult.failure_result(handler_name, 0.0, exc))
                continue

            handler_start = time.perf_counter()
            handler_failed = False
            try:
                if isinstance(raw_handler, IEventHandler):
                    raw_handler.execute(payload)
                else:
                    raw_handler(payload)
                duration = time.perf_counter() - handler_start
                successful.append(handler_name)
            except Exception as exc:
                duration = time.perf_counter() - handler_start
                handler_failed = True
                handler_exc = HandlerExecutionError(
                    str(exc),
                    event_type=event_type_name,
                    handler_name=handler_name,
                    original_exception=exc,
                )
                failed.append(
                    HandlerResult.failure_result(handler_name, duration, handler_exc)
                )
            finally:
                context["duration"] = duration
                context["handler_failed"] = handler_failed
                self._run_after_middleware_payload(payload, context, duration)

        total_duration = time.perf_counter() - dispatch_start

        return ExecutionReport(
            event_type=event_type_name,
            event_id=str(payload.get("event_id", "")),
            successful_handlers=tuple(successful),
            failed_handlers=tuple(failed),
            total_handlers=handler_count,
            duration_seconds=total_duration,
        )

    def _run_before_middleware(
        self, event: BaseDomainEvent, context: dict[str, Any]
    ) -> dict[str, Any]:
        for middleware in self._middleware:
            try:
                context = middleware.before_dispatch(event, context)
            except Exception as exc:
                raise MiddlewareExecutionError(
                    str(exc),
                    middleware_name=type(middleware).__name__,
                    original_exception=exc,
                ) from exc
        return context

    def _run_after_middleware(
        self,
        event: BaseDomainEvent,
        context: dict[str, Any],
        duration: float,
    ) -> None:
        for middleware in reversed(self._middleware):
            try:
                middleware.after_dispatch(event, context, duration)
            except Exception as exc:
                logger.warning(
                    "Middleware %s after_dispatch failed: %s",
                    type(middleware).__name__,
                    exc,
                )

    def _run_before_middleware_payload(
        self, payload: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        for middleware in self._middleware:
            try:
                context = middleware.before_dispatch(payload, context)
            except Exception as exc:
                raise MiddlewareExecutionError(
                    str(exc),
                    middleware_name=type(middleware).__name__,
                    original_exception=exc,
                ) from exc
        return context

    def _run_after_middleware_payload(
        self,
        payload: dict[str, Any],
        context: dict[str, Any],
        duration: float,
    ) -> None:
        for middleware in reversed(self._middleware):
            try:
                middleware.after_dispatch(payload, context, duration)
            except Exception as exc:
                logger.warning(
                    "Middleware %s after_dispatch failed: %s",
                    type(middleware).__name__,
                    exc,
                )

    def _resolve_name(self, handler: Any) -> str:
        if hasattr(handler, "__name__"):
            return str(handler.__name__)
        if hasattr(handler, "execute"):
            return type(handler).__name__
        return repr(handler)


__all__ = ["EventBus"]
