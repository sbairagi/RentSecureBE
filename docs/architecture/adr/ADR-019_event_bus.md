# ADR-019: Event Bus Implementation

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

RentSecure needs an event bus for domain events. The event bus must:
- Support in-process event handling in Year 1
- Be replaceable with a distributed bus in Stage 3
- Support event retry and dead letter queues
- Be testable

---

## Decision

RentSecure uses an **in-process event bus** in Year 1, with an interface that allows swapping to a distributed bus later.

**Key components:**
- `EventBus`: Publishes events to handlers
- `EventHandler`: Processes events
- `EventMiddleware`: Pre/post processing (logging, retry)
- `DeadLetterQueue`: Stores failed events

**Year 1:** In-process, synchronous event handling
**Stage 3:** Replace with Redis/Celery-based distributed bus

---

## Alternatives Considered

### 1. Direct Event Handler Calls

**Description:** Call event handlers directly without a bus.

**Pros:**
- Simple
- No infrastructure

**Cons:**
- Tightly coupled handlers
- Hard to add new handlers
- No retry logic
- No middleware support

**Decision:** Rejected. Doesn't scale.

### 2. Django Signals

**Description:** Use Django signals for event handling.

**Pros:**
- Django-native
- Built-in retry

**Cons:**
- Hard to trace
- No event versioning
- Hard to test
- No dead letter queue

**Decision:** Rejected. Insufficient for domain events.

### 3. Event Bus Interface (Selected)

**Description:** Abstract event bus with in-process implementation.

**Pros:**
- Decouples publishers from subscribers
- Supports middleware (retry, logging)
- Testable
- Swappable to distributed bus later

**Cons:**
- More code
- Requires interface maintenance

**Decision:** Accepted. Best for long-term flexibility.

---

## Event Bus Interface

```python
# platform/events/bus.py
class EventBus(ABC):
    @abstractmethod
    def publish(self, event: DomainEvent) -> None: ...

    @abstractmethod
    def subscribe(self, event_type: str, handler: EventHandler) -> None: ...

    @abstractmethod
    def unsubscribe(self, event_type: str, handler: EventHandler) -> None: ...

class InProcessEventBus(EventBus):
    def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers[event.event_type]:
            try:
                handler.handle(event)
            except Exception as e:
                self._dead_letter_queue.add(event, e)
```

---

## Consequences

### Positive
- Decouples publishers from subscribers
- Supports retry and dead letter queues
- Testable
- Swappable to distributed bus later

### Negative
- More code (interface + implementation)
- Requires discipline

### Neutral
- Year 1 uses in-process bus
- Stage 3 replaces with distributed bus

---

## References

- [Domain Events](../future/07_domain_events.md)
- [Bounded Contexts](../future/02_bounded_contexts.md)
