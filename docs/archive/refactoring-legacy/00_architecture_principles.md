# RentSecure Backend — Architecture Principles

**Document:** Architecture Principles
**Version:** 1.0.0
**Date:** 2026-07-15
**Owner:** Principal Software Architect
**Status:** Ratified
**Scope:** All backend bounded contexts, services, repositories, views, and utilities
**Constraint:** This document is the supreme authority for architectural decisions. When implementation preferences conflict with these principles, principles always win.

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Core Principles](#2-core-principles)
3. [Architectural Rules](#3-architectural-rules)
4. [Dependency Rules](#4-dependency-rules)
5. [Public Interface Rules](#5-public-interface-rules)
6. [Error Handling Principles](#6-error-handling-principles)
7. [Testing Principles](#7-testing-principles)
8. [Refactoring Principles](#8-refactoring-principles)
9. [Definition of Done](#9-definition-of-done)
10. [Future Architecture Vision](#10-future-architecture-vision)
11. [Appendix: Architecture Commandments](#11-appendix-architecture-commandments)

---

## 1. Purpose

### Why Architecture Principles Exist

Architecture principles exist to prevent the gradual accumulation of technical debt that destroys development velocity and operational stability. Without explicit principles, each developer makes localized decisions that seem correct in isolation but collectively produce an unmaintainable system. RentSecure is being built for a multi-year lifecycle, and the cost of correcting architectural mistakes grows exponentially with time.

These principles are not suggestions. They are binding rules that govern every change to the backend codebase. They exist to ensure that the system remains comprehensible, testable, and modifiable by any team member—not just its original authors.

### These Principles Override Implementation Preferences

A developer may prefer a specific library, pattern, or coding style. Those preferences are secondary. When a developer's preferred approach conflicts with these principles, the principles prevail. Personal coding style is irrelevant compared to the collective need for consistency across the codebase.

Consistency across a large team and a long-lived codebase is more important than any individual's sense of "clean" or "elegant" code. A consistently applied mediocre pattern is preferable to an inconsistently applied excellent pattern.

### Consistency Is More Important Than Personal Coding Style

When five developers each apply their own interpretation of what "good code" looks like, the result is five different ways of solving the same problem. This fragmentation increases cognitive load, slows onboarding, and makes defect isolation harder. These principles exist to ensure that any developer can open any bounded context and immediately understand the structure, conventions, and intent.

---

## 2. Core Principles

### 2.1 Business Capability Over Technical Layers

**Principle:** Organize code by what the business does, not by how the code is structured.

**Explanation:** The most common anti-pattern in Django projects is organizing apps by technical role: a `models.py` app, a `views.py` app, a `services.py` app. This forces a developer working on rental payments to navigate across `properties/`, `finance/`, `payments/`, and `notification/` to understand a single business transaction. It also makes it impossible to assign clear ownership: no single team can say "I own rental payments."

In RentSecure, each bounded context (Django app) represents a business capability: `core` handles identity and access, `properties` handles property management, `finance` handles tax and compliance, `documents` handles document generation, `assistant` handles AI features, and so on. All code related to a capability lives in one place.

**Rationale:** Business capabilities change slowly. Technical frameworks change rapidly. Organizing by business capability means that when the business reorganizes, the code structure changes naturally. Organizing by technical layers means that every business change requires touching every layer.

**Example:** A developer adding a "payment reminder" feature should only need to work within the `notification` bounded context and the `payments` bounded context. They should not need to modify `properties`, `finance`, or `core`.

**Consequences of Violation:** Cross-cutting concerns become scattered, ownership is unclear, change impact is difficult to assess, and onboarding new developers takes significantly longer.

---

### 2.2 Modular Monolith First

**Principle:** Build a single, well-structured deployable unit with clear internal boundaries. Do not introduce microservices until the business scale justifies it.

**Explanation:** A modular monolith is a single process and single database, but internally organized with strict boundaries between bounded contexts. Microservices introduce distributed systems complexity: service discovery, network latency, distributed transactions, eventual consistency, circuit breakers, and observability infrastructure. For a team of fewer than twenty engineers and a transaction volume below 500,000 requests per month, this complexity is a tax, not an investment.

RentSecure will remain a modular monolith through Year 1 production. Bounded contexts will be organized such that extraction to microservices is possible later—but only when data shows that extraction is necessary.

**Rationale:** Operational simplicity is a feature. A single deployment, single database, and straightforward monitoring allow the team to move fast and debug quickly. Clear internal boundaries preserve the option to extract later without incurring the cost of premature optimization.

**Example:** The `notification` bounded context lives in the same repository and process as `properties`, but it has a strict public interface. If transaction volume later justifies it, `notification` can be extracted into its own service by deploying its interface as a REST or gRPC endpoint.

**Consequences of Violation:** Premature microservices introduce network failure modes, distributed tracing requirements, cross-service data consistency problems, and an operational burden that consumes engineering time that should be spent on business features.

---

### 2.3 Single Source of Truth

**Principle:** Every piece of business logic, configuration, or data transformation has exactly one canonical implementation.

**Explanation:** When two locations contain the same logic, they will inevitably diverge. A bug fixed in one location will not be fixed in the other. A developer updating one location will not know to update the other. The result is inconsistent behavior that is extremely difficult to debug.

In RentSecure, duplicate implementations are treated as defects. If a PDF generation utility exists in `documents/utils/pdf_generator.py`, no other location may implement PDF generation. If a Leegality client exists in `documents/services/leegality.py`, no other location may implement Leegality API calls.

**Rationale:** Maintenance cost is proportional to the number of implementations. Two implementations require twice the testing, twice the bug fixing, and twice the review effort. A single implementation requires none of this.

**Example:** The codebase historically contained two WhatsApp notification implementations: one in `notification/utils.py` and another in `notification/services/whatsapp_service.py`. They used different return types and error handling. The fix was to consolidate into `notification/services/channels/whatsapp.py` and remove the duplicate.

**Consequences of Violation:** Behavioral drift, increased bug count, harder testing, and slower feature delivery. Developers waste time figuring out which implementation to use and whether they are equivalent.

---

### 2.4 Explicit Dependencies

**Principle:** Every import must be intentional, visible, and documented. Implicit dependencies created by shared modules or global state are forbidden.

**Explanation:** When bounded context A imports a module from bounded context B, that dependency must be explicit and justified. It must be visible in the import statement and documented in the bounded context's interface definition. Implicit dependencies—where A somehow reaches B's internals without a direct import—are architectural defects.

**Rationale:** Implicit dependencies make it impossible to understand the true coupling between bounded contexts. They break modularity because changes in B can silently break A without any visible connection. They also prevent extraction to microservices, because you cannot extract a service whose dependencies you cannot see.

**Example:** `properties` must not import `notification.utils` directly. It must import from `notification.services` or use the `NotificationChannel` interface. If `properties` needs to send a notification, the dependency is explicit: `from notification.services import notify_user`.

**Consequences of Violation:** Tight coupling, hidden breakage, impossible extraction to services, and cascading defects when internal modules change.

---

### 2.5 Loose Coupling

**Principle:** Bounded contexts must interact through well-defined interfaces, not by reaching into each other's internals.

**Explanation:** Loose coupling means that changing the internal implementation of one bounded context does not require changes to other bounded contexts. This is achieved by defining explicit interfaces (Python protocols, abstract base classes, or well-documented function signatures) and ensuring that all cross-context communication goes through those interfaces.

**Rationale:** Tightly coupled systems are fragile. A change in one module forces changes in every module that touches it. Loose coupling enables independent development, independent testing, and independent deployment.

**Example:** The `payments` bounded context defines a `PaymentGateway` protocol. `properties` depends on this protocol, not on any specific payment gateway implementation. When a new gateway is added, `properties` does not change.

**Consequences of Violation:** Change amplification—every change triggers a cascade of required changes across the system. The system becomes brittle and resistant to refactoring.

---

### 2.6 High Cohesion

**Principle:** Code that changes together should live together. Code that serves different purposes should live apart.

**Explanation:** High cohesion means that all code within a bounded context serves the same business purpose. `notification` contains channel implementations, message formatting, and delivery logic because they all serve the purpose of delivering notifications. It does not contain rent calculation logic because that serves a different purpose.

Low cohesion is visible when a single file or module contains unrelated functionality, when developers hesitate to modify a file because they are unsure what else depends on it, or when a single business change requires touching files scattered across multiple apps.

**Rationale:** High cohesion reduces cognitive load. A developer working on notifications knows that all relevant code is in the `notification` app. They do not need to search the entire codebase.

**Example:** `properties/services/notification_service.py` contains rent payout notification orchestration. It coordinates between the `properties` domain and the `notification` channels. It does not contain channel implementations—those belong in `notification/services/channels/`. This is high cohesion: orchestration lives with the domain that needs it, channel implementations live with the channel capability.

**Consequences of Violation:** Scattered logic, unclear ownership, difficult testing, and slow feature delivery.

---

### 2.7 Dependency Inversion

**Principle:** High-level modules must not depend on low-level modules. Both must depend on abstractions. Abstractions must not depend on details. Details must depend on abstractions.

**Explanation:** In RentSecure, the high-level module is the business workflow (e.g., "process rent payment"). The low-level modules are the implementation details (e.g., Razorpay API client, Cashfree API client, manual UPI verification). The business workflow must not import a specific gateway. Instead, it depends on a `PaymentGateway` abstraction. Each gateway implementation depends on that abstraction.

This is realized through Python protocols or abstract base classes. The `PaymentService` depends on `PaymentGateway`. The Razorpay adapter implements `PaymentGateway`.

**Rationale:** Dependency inversion enables substitution. When a new payment gateway is added, the business workflow does not change. It also enables testing: tests can inject a mock `PaymentGateway` without touching real payment APIs.

**Example:** `payments/services/payment_service.py` defines the `process_payment` workflow. It accepts any object that implements the `PaymentGateway` protocol. In production, this is `RazorpayAdapter` or `CashfreeAdapter`. In tests, it is a mock. The workflow code never changes when a new gateway is added.

**Consequences of Violation:** Tight coupling to infrastructure, impossible testing without real credentials, and high change cost when switching providers.

---

### 2.8 Composition Over Duplication

**Principle:** Build complex behavior by composing simple, reusable components rather than copying and modifying existing code.

**Explanation:** When a developer needs behavior similar to an existing module, they must extract the common logic into a shared component and compose the new behavior from that component. They must not copy the existing module and modify it.

**Rationale:** Duplication is the root of inconsistency. Every copied module is a future defect waiting to happen when the original is fixed but the copy is not. Composition creates a single source of truth and enables variation through configuration and parameterization rather than through copying.

**Example:** When PDF generation was needed in `properties`, `finance`, and `documents`, the solution was not to copy the WeasyPrint setup into each app. The solution was to create `documents/utils/pdf_generator.py` and import it from every app that needs PDF generation. Variation is achieved through template selection and context data, not through code duplication.

**Consequences of Violation:** Code bloat, behavioral drift, increased defect count, and slower refactoring because every change must be applied to multiple locations.

---

### 2.9 Backward Compatibility During Migration

**Principle:** Any migration must preserve existing behavior for existing callers until every caller has been migrated.

**Explanation:** When code is moved, renamed, or refactored, the old location must continue to work until all call sites have been updated. This is achieved through compatibility wrappers—thin modules at the old location that re-export the new implementation with a deprecation warning.

**Rationale:** Breaking changes force coordinated deployments where every consumer must update simultaneously. This is practically impossible in a fast-moving codebase with multiple teams. Compatibility wrappers allow migrations to happen gradually, one PR at a time, with zero production risk.

**Example:** When the `leegality_service.py` was moved from `rentsecure_be/services/` to `documents/services/leegality.py`, a compatibility wrapper was left at the old location:

```python
# rentsecure_be/services/leegality_service.py
import warnings
from documents.services.leegality import LeegalityClient

warnings.warn(
    "Import from documents.services.leegality instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["LeegalityClient"]
```

Existing callers continue to work. Each call site is migrated in a separate PR. The wrapper is removed only after `grep` confirms zero remaining imports.

**Consequences of Violation:** Coordinated deployment requirements, production outages, and developer resistance to future refactoring.

---

### 2.10 Small Incremental Refactoring

**Principle:** Refactoring must be done in small, reviewable, reversible steps. Large-scale rewrites are forbidden.

**Explanation:** Refactoring is the process of improving code structure without changing behavior. Large refactorings—moving entire apps, rewriting services, restructuring models—must be broken into small PRs, each of which can be reviewed, tested, and reverted independently.

**Rationale:** Large PRs are impossible to review thoroughly. They introduce defects that are difficult to isolate. They block other development while they are in review. Small PRs enable continuous refactoring without disrupting feature delivery.

**Example:** Merging `smartbot` and `ai_assistant` into `assistant` is not done in a single PR. It is done in a sequence:

1. Move non-AI services to their correct bounded contexts (`leegality_service.py` → `documents/`, `archive_service.py` → `properties/`).
2. Merge AI services into `assistant/`.
3. Update imports in `assistant/` itself.
4. Update imports in dependent apps one at a time, using compatibility wrappers.
5. Remove compatibility wrappers only after zero imports remain.

Each step is a separate PR with its own tests and review.

**Consequences of Violation:** Review fatigue, defect introduction, blocked development, and high rollback cost.

---

### 2.11 No Big Bang Migrations

**Principle:** Any change that touches more than three bounded contexts or more than twenty files must be broken into phases.

**Explanation:** A "Big Bang" migration is a single change that modifies many files, many apps, or many behaviors simultaneously. It is characterized by statements like "we will move everything at once" or "we will update all imports in one PR."

**Rationale:** Big Bang migrations are high-risk and low-reward. They produce massive PRs that are impossible to review. If they fail, they fail catastrophically—production may be broken and the fix may take days. Phased migrations allow each phase to be validated before the next begins.

**Example:** The migration to bounded contexts by business capability is not done in a single weekend. It is done over multiple sprints, one bounded context at a time, with compatibility wrappers ensuring zero breaking changes.

**Consequences of Violation:** Production outages, extended debugging sessions, developer burnout, and organizational resistance to future refactoring.

---

### 2.12 Clean Public Interfaces

**Principle:** Every bounded context must expose a clean, minimal, well-documented public interface. No internal module may be imported by another bounded context.

**Explanation:** A public interface is a small set of functions, classes, and protocols that a bounded context exposes to the outside world. It is the contract between bounded contexts. Everything else is internal and must not be imported.

In RentSecure, the public interface of a bounded context is typically `services.py`, `api.py`, or a `services/` package. A developer from another bounded context may import from `notification.services` but may not import from `notification.utils` or `notification.models`.

**Rationale:** Public interfaces enable independent evolution. The `notification` team can refactor `notification.utils` without warning other teams, as long as the public interface in `notification.services` remains stable. Without public interfaces, every internal change is a breaking change for every consumer.

**Example:** `notification/services/communication.py` exposes `send_smart_alert(user, message, context)`. This is the public interface. `notification/utils/template_renderer.py` is internal and must not be imported by `properties` or `finance`.

**Consequences of Violation:** Tight coupling, fragile internals, impossible refactoring, and cascading breakage.

---

### 2.13 Testability First

**Principle:** Code must be written to be testable. If code cannot be tested easily, it must be refactored until it can.

**Explanation:** Testability is not an afterthought. It is a primary design criterion. Code that is difficult to test indicates poor design: typically, tight coupling, hidden dependencies, or mixed responsibilities. The solution is not to write more complex tests—the solution is to refactor the code.

Testability requirements:
- Business logic must be in pure functions or classes that accept their dependencies as arguments.
- Side effects (database, HTTP, filesystem) must be injected, not hardcoded.
- No global state.
- No hidden dependencies through module-level imports.
- No business logic in views or signals.

**Rationale:** Untested code is broken code. But more importantly, untestable code is poorly designed code. Prioritizing testability during design produces better architecture.

**Example:** A view that directly calls `RazorpayService.create_payment()` is not testable without Razorpay credentials. A view that calls `PaymentService.process_payment(payment_gateway=RazorpayAdapter())` is testable by injecting a mock adapter.

**Consequences of Violation:** Low test coverage, fragile tests that break on implementation changes, and difficulty verifying correctness.

---

### 2.14 Production Stability Over Code Beauty

**Principle:** A working, stable system is preferable to a beautiful system that is risky to deploy.

**Explanation:** Developers often want to rewrite, refactor, or restructure code to make it "cleaner." This is valuable—but only when it does not jeopardize production stability. A refactoring that introduces a regression is worse than leaving "ugly" code in place.

**Rationale:** Production incidents cost money, damage user trust, and burn engineering time. The cost of a production outage dwarfs the cost of leaving imperfect code in place. Refactoring must be validated through tests, staged deployments, and rollback plans before it reaches production.

**Example:** A service with duplicated logic may be "ugly," but if it works and has test coverage, it is preferable to a rewritten service that introduces a subtle regression in payment processing. The duplication can be fixed in a subsequent PR with proper testing.

**Consequences of Violation:** Production incidents, user dissatisfaction, emergency rollbacks, and organizational distrust of refactoring efforts.

---

### 2.15 Prefer Deletion Over Addition

**Principle:** When faced with a choice between adding new code and deleting old code, prefer deletion.

**Explanation:** The codebase is an asset, but it is also a liability. Every line of code must be understood, maintained, tested, and reviewed. Dead code, unused features, and obsolete implementations increase the surface area for defects and slow down development.

Before adding a new module, ask: can an existing module be extended? Before adding a new bounded context, ask: can an existing context absorb this capability? Before adding a new utility, ask: is there already a utility that does this?

**Rationale:** Code deletion reduces maintenance burden, reduces defect surface, and simplifies onboarding. The best code is no code at all.

**Example:** When consolidating duplicate services, the canonical implementation is kept and the duplicate is deleted. The compatibility wrapper is temporary—it is deleted after all call sites are migrated.

**Consequences of Violation:** Code bloat, increased defect count, slower development, and higher cognitive load for new team members.

---

### 2.16 Simplicity Before Abstraction

**Principle:** Start with the simplest solution that works. Add abstraction only when concrete evidence shows it is needed.

**Explanation:** Abstraction is a tool, not a goal. Premature abstraction—creating interfaces, factories, and generic frameworks before there is a demonstrated need—produces complexity without value. The correct approach is to write concrete code first, observe where duplication or variation occurs, and then extract abstractions based on observed patterns.

**Rationale:** Premature abstractions are guesses about future requirements. Most guesses are wrong. When the abstraction does not match the actual need, it becomes a constraint that makes the code harder to modify, not easier.

**Example:** When PDF generation was first needed, the solution was a simple utility function, not a generic document generation framework. When PDF generation was needed in multiple contexts, the utility was extracted into a shared module. Only when multiple document types with different templates and flows emerged did a more structured `documents` app emerge.

**Consequences of Violation:** Over-engineered systems, unnecessary complexity, and resistance to change because abstractions must be preserved even when they no longer fit.

---

### 2.17 YAGNI (You Aren't Gonna Need It)

**Principle:** Do not implement functionality until it is actually required. Do not build for hypothetical future needs.

**Explanation:** YAGNI is the antidote to over-engineering. When a developer says "we might need this later," the answer is "then implement it later." Every line of code that is written "just in case" is code that must be maintained, tested, and reviewed without providing current value.

**Rationale:** Future requirements are unpredictable. The probability that a feature imagined today will be needed in exactly the form imagined is very low. Building for hypothetical futures produces code that is never used and must be maintained anyway.

**Example:** The codebase contains `smartbot/` and `ai_assistant/` apps that were built with the idea that AI features would grow in different directions. In practice, the boundaries blurred and the apps overlapped. The correct response was to merge them into `assistant/`, not to build elaborate frameworks to support hypothetical separation.

**Consequences of Violation:** Unused code, increased complexity, and wasted engineering time on features that are never used.

---

### 2.18 SOLID Principles

**Principle:** All five SOLID principles apply to RentSecure backend code.

**Explanation:**

- **Single Responsibility:** A class or module has one reason to change. `PaymentService` processes payments; it does not generate PDFs or send emails.
- **Open/Closed:** Software entities must be open for extension but closed for modification. New payment gateways are added by implementing `PaymentGateway`, not by modifying `PaymentService`.
- **Liskov Substitution:** Subtypes must be substitutable for their base types. A `RazorpayAdapter` must be usable wherever a `PaymentGateway` is expected.
- **Interface Segregation:** Clients must not be forced to depend on interfaces they do not use. A `NotificationChannel` interface must not require methods that email adapters do not need.
- **Dependency Inversion:** High-level modules must not depend on low-level modules. Both must depend on abstractions. `PaymentService` depends on `PaymentGateway`, not on `RazorpayAdapter`.

**Rationale:** SOLID principles are the foundation of maintainable object-oriented and component-based design. They reduce coupling, increase cohesion, and enable testing.

**Example:** The `NotificationChannel` protocol defines `send(user, message, context)`. Email, push, SMS, and WhatsApp adapters each implement this protocol. The `notify_user` function depends on the protocol, not on any specific adapter.

**Consequences of Violation:** Rigid code that is difficult to extend, difficult to test, and difficult to modify without breaking existing behavior.

---

### 2.19 KISS (Keep It Simple, Stupid)

**Principle:** The simplest solution that solves the problem is the best solution.

**Explanation:** KISS is the principle that most directly opposes over-engineering. A simple switch statement is preferable to a strategy pattern when there are only two options. A direct function call is preferable to a message bus when all code runs in the same process. A single file is preferable to a package when the module is small.

**Rationale:** Simple code is easier to understand, easier to test, easier to debug, and easier to modify. Complex code is the opposite of all these things.

**Example:** The `UPI_PAYMENT_ENABLED` feature flag is implemented as a simple boolean in settings. It does not require a dynamic plugin system, a configuration database, or a feature flag microservice. The manual UPI payment flow is a direct function call, not an event-driven saga.

**Consequences of Violation:** Unnecessary complexity, harder onboarding, more defects, and slower development velocity.

---

### 2.20 DRY (Don't Repeat Yourself)

**Principle:** Every piece of knowledge must have a single, unambiguous, authoritative representation within a system.

**Explanation:** DRY is the principle that duplication is a defect. When the same logic, configuration, or transformation appears in multiple places, it must be extracted into a single shared location. The RentSecure implementation of DRY is "Single Source of Truth" (Section 2.3), applied universally.

**Rationale:** Duplication multiplies the cost of change. A change that must be made in five places will be missed in at least one. The result is inconsistent behavior that is extremely difficult to debug.

**Example:** The WeasyPrint setup was duplicated in five locations. The fix was a single `pdf_generator.py` in `documents/utils/`. All PDF generation now goes through this single module.

**Consequences of Violation:** Code bloat, inconsistent behavior, higher defect count, and slower development.

---

## 3. Architectural Rules

These rules define the strict layering and responsibility boundaries within each bounded context. They are non-negotiable.

### 3.1 The Layering Contract

```
Views (HTTP Layer)
    ↓ calls
Services (Business Logic Layer)
    ↓ calls
Repositories / ORM (Data Access Layer)
```

**Views must never contain business logic.** Views are thin HTTP adapters. They parse the request, call the appropriate service, and return the response. They must not contain business rules, validation, or data transformation.

**Services own business rules.** All business logic—validation, workflow orchestration, decision making, and data transformation—lives in services. Services are the only layer that knows how to accomplish a business task.

**Models own validation.** Django models define field constraints, model-level validation (`clean()`), and business invariants. Services may call `full_clean()` and handle `ValidationError`, but they must not bypass model validation.

**Repositories / ORM own data access.** Services interact with the database through Django ORM querysets and model methods. They must not construct raw SQL unless absolutely necessary, and any raw SQL must be isolated in a repository method.

### 3.2 Signals Must Never Perform Business Operations

Django signals are event publishers, not business logic containers. Signals may trigger events—send a notification, enqueue a background task, update a cache—but they must not perform business operations directly.

**Rationale:** Signals are implicit and invisible. A signal handler that performs business logic creates a hidden dependency that is extremely difficult to trace. When a developer changes a model save, they do not expect business logic to execute in a signal handler they have never seen.

**Allowed in signals:**
- `post_save`: Send a notification, enqueue a task, update a cache.
- `pre_save`: Update a `modified_at` timestamp.

**Forbidden in signals:**
- Calling external APIs.
- Performing financial calculations.
- Modifying unrelated models.
- Sending emails with business content.
- Any logic that would be surprising to a developer reading the model save code.

**Example of violation:** `properties/signals/__init__.py` contains a `post_save` handler on `RentRecord` that directly calls the WhatsApp API to notify the tenant. This is forbidden. The correct approach is for the signal to call `notification.services.send_smart_alert`, which is a thin notification wrapper. The business logic of *when* to notify and *what* to say belongs in `properties/services/`, not in a signal.

### 3.3 Utilities Never Contain Business Workflows

Utility modules (`utils.py`, `helpers.py`) contain stateless, reusable functions that perform pure transformations: date formatting, string manipulation, file parsing, currency conversion. They must not contain business workflows, orchestration logic, or side effects.

**Rationale:** Utilities are shared and imported everywhere. If a utility contains business logic, that logic is implicitly available to every module that imports it, creating hidden coupling. Business logic in utilities is also impossible to test in isolation because it depends on the calling context.

**Example:** `properties/utils.py` contains `calculate_late_fee(rent_record)` — a pure function that calculates a late fee based on days overdue. This is acceptable. `properties/utils.py` must not contain `process_late_payment(rent_record)` — a function that calculates a late fee, creates a payment record, sends a notification, and updates the tenant balance. That is a business workflow and belongs in `properties/services/late_fee_service.py`.

### 3.4 Services Must Be Thin Wrappers Over Business Logic

Services should not be "god objects" that know everything. Each service should have a single, well-defined responsibility. A `PaymentService` processes payments. A `NotificationService` sends notifications. A `PDFGenerationService` generates PDFs.

**Rationale:** Fat services become dumping grounds for unrelated logic. They are difficult to test, difficult to reuse, and difficult to maintain.

---

## 4. Dependency Rules

### 4.1 Dependency Direction

Dependencies must flow in one direction only: from high-level business logic toward low-level infrastructure. They must never flow from infrastructure back to business logic.

```
Bounded Context (Business)
    ↓ depends on
Shared Abstractions
    ↓ depends on
Infrastructure (ORM, HTTP, external APIs)
```

**Allowed:**
- `properties` → `shared` (uses shared utilities)
- `finance` → `notification` (uses notification channels through interfaces)
- `assistant` → `documents` (uses document generation through interfaces)

**Not Allowed:**
- `notification` → `properties` (notification must not know about property internals)
- `assistant` → `properties` internals (assistant must use properties' public interface)
- `shared` → any bounded context (shared must be a leaf dependency)

### 4.2 No Circular Imports

Circular imports are forbidden. If `properties` imports from `finance` and `finance` imports from `properties`, the system is circularly dependent and cannot be initialized correctly.

**Rationale:** Circular imports indicate that two bounded contexts are too tightly coupled. The correct solution is to extract the shared logic into a third bounded context or into `shared`.

**Example:** `properties` needs the `RentRecord` model from `finance` to calculate late fees. `finance` needs the `Property` model from `properties` to validate rent amounts. The circular dependency is resolved by extracting the shared models into `shared` or by defining the calculation in `finance` that accepts `property_id` and `rent_amount` as arguments rather than importing the `Property` model directly.

### 4.3 No Cross-Domain ORM Writes

A bounded context must not write to another bounded context's tables directly. If `finance` needs to record that a payment was made, it must call `properties.services.record_payment()`, not execute `INSERT INTO properties_rentrecord`.

**Rationale:** Direct database writes bypass business logic, validation, and signals. They create invisible coupling and make it impossible to change the data model of one context without breaking another.

**Allowed:** `finance` calls `properties.services.update_rent_status(rent_id, status="paid")`.
**Forbidden:** `finance` executes `RentRecord.objects.filter(id=rent_id).update(status="paid")`.

### 4.4 No Direct Infrastructure Access from Domains

Domain bounded contexts must not import infrastructure libraries directly. If `properties` needs to send an email, it must call `notification.services.send_email()`, not import `django.core.mail.send_mail`.

**Rationale:** Direct infrastructure access creates tight coupling to specific implementations. If all domains import `send_mail` directly, switching to a different email provider requires changes in every domain. If all domains call `notification.services.send_email()`, the switch is made in one place.

---

## 5. Public Interface Rules

### 5.1 Every Bounded Context Exposes a Public Interface

Each bounded context must define and document its public interface. The public interface is the only part of the context that other contexts may import.

**Typical structure:**
```
properties/
  services/
    __init__.py          # Public interface: exports all service classes
    property_service.py
    unit_service.py
    rent_service.py
  api.py                 # Alternative public interface for simple cases
```

**Allowed imports from other bounded contexts:**
- `from properties.services import PropertyService`
- `from properties.api import get_property`

**Forbidden imports from other bounded contexts:**
- `from properties.models import Property` (unless `Property` is part of the public interface)
- `from properties.utils import format_address`
- `from properties.admin import PropertyAdmin`

### 5.2 Private Modules Cannot Be Imported

Any module that is not explicitly exported in `__init__.py` or documented in `api.py` is private. Other bounded contexts must not import private modules.

**Rationale:** Private modules are implementation details. They may change without notice. Importing them creates fragile dependencies that break when the implementation changes.

**Enforcement:** The `import-linter` tool enforces this rule. Any import from a private module will cause the CI pipeline to fail.

### 5.3 Interface Stability

Public interfaces must be stable. When a public interface needs to change, the change must be backward compatible: old callers must continue to work, and new callers may use the new interface.

**Rationale:** Breaking public interfaces forces coordinated changes across all consuming bounded contexts. This is the same problem as breaking changes in external APIs.

**Example:** `notification.services.notify_user` originally accepted `user_id` and `message`. It was extended to also accept `context` (a dictionary for template variables). The new parameter has a default value of `None`, so existing callers continue to work. New callers may pass `context`.

---

## 6. Error Handling Principles

### 6.1 Standardized Exceptions

All business exceptions must inherit from a common base class defined in `shared/exceptions.py`. Domain-specific exceptions inherit from this base.

```python
# shared/exceptions.py
class RentSecureException(Exception):
    """Base exception for all RentSecure business errors."""

class ValidationError(RentSecureException):
    """Raised when input fails business validation."""

class PaymentError(RentSecureException):
    """Raised when a payment operation fails."""

class DocumentError(RentSecureException):
    """Raised when document generation fails."""
```

**Rationale:** Standardized exceptions enable consistent error handling across bounded contexts. Views can catch `RentSecureException` and return appropriate HTTP responses. Logging can categorize errors by type. Monitoring can alert on specific exception classes.

### 6.2 No Silent Failures

Every error must be handled explicitly. Silent failures—catching an exception and doing nothing, or returning `None` on error without logging—are forbidden.

**Rationale:** Silent failures produce systems that appear to work but produce incorrect results. A payment that "succeeds" but does not record the transaction is worse than a payment that fails loudly.

**Example of violation:**
```python
try:
    result = payment_gateway.charge(amount)
except Exception:
    pass  # Silent failure
```

**Example of correct handling:**
```python
try:
    result = payment_gateway.charge(amount)
except PaymentGatewayError as exc:
    logger.error("Payment failed", exc_info=exc)
    raise PaymentError("Payment processing failed") from exc
```

### 6.3 No Bare Except

`except Exception:` or `except:` without specifying the exception type is forbidden. Every `except` clause must catch a specific exception type.

**Rationale:** Bare except clauses catch everything, including `KeyboardInterrupt`, `SystemExit`, and `MemoryError`. They mask unexpected errors and make debugging impossible.

### 6.4 Consistent Logging

All errors, warnings, and significant business events must be logged. Logging must use the standard Python `logging` module with structured context.

**Required log fields:**
- `event`: A string describing the event (e.g., "payment_processed", "notification_sent").
- `user_id`: The ID of the user involved (if applicable).
- `bounded_context`: The bounded context where the event occurred.
- `duration_ms`: The duration of the operation (if applicable).

**Rationale:** Consistent logging enables debugging, monitoring, and alerting. Without structured context, log aggregation tools cannot filter or correlate events.

### 6.5 Meaningful Error Messages

Error messages must be actionable. "An error occurred" is not an error message. "Payment of INR 5000.00 failed: insufficient balance in wallet W123" is an error message.

**Rationale:** Meaningful error messages reduce debugging time, improve user experience, and enable better monitoring. Operators can act on actionable messages. Users can correct actionable errors.

---

## 7. Testing Principles

### 7.1 Unit Tests

Every service, utility, and model method must have unit tests. Unit tests verify that a single unit of code produces the correct output for a given input, in isolation from external dependencies.

**Coverage target:** 90% of business logic.

**Requirements:**
- Tests must be fast (no database, no HTTP, no external APIs).
- Tests must use mocks or fakes for all external dependencies.
- Tests must be deterministic (no random data, no time-dependent logic without control).

### 7.2 Integration Tests

Integration tests verify that multiple units work together correctly. In RentSecure, integration tests verify that services correctly interact with the database, that views correctly serialize data, and that bounded contexts correctly interact through their public interfaces.

**Coverage target:** Critical workflows (payment processing, notification delivery, document generation).

**Requirements:**
- Tests must use a real database (test database).
- Tests must use real Django ORM.
- Tests must verify end-to-end workflows.

### 7.3 Architecture Tests

Architecture tests enforce architectural rules that cannot be enforced by linters alone. In RentSecure, architecture tests verify:
- No bounded context imports private modules from another bounded context.
- No circular dependencies between bounded contexts.
- Views do not contain business logic.
- Signals do not perform business operations.

**Tooling:** `pytest`, `import-linter`, custom pytest plugins.

### 7.4 Mutation Tests

Mutation tests verify that tests actually catch defects. A mutation testing tool (e.g., `mutmut`) introduces small changes (mutations) into the codebase and verifies that the test suite fails. If a mutation is not caught, the test suite has insufficient coverage.

**Coverage target:** 80% mutation score for critical services.

### 7.5 Contract Tests

Contract tests verify that public interfaces between bounded contexts remain stable. When `notification.services.notify_user` is called by `properties`, a contract test ensures that the function signature, return type, and behavior remain stable.

**Requirements:**
- Every public interface must have contract tests.
- Contract tests run in CI on every PR that modifies a public interface.

### 7.6 Coverage Goals

| Layer | Target |
|-------|--------|
| Business logic (services) | 95% |
| Utilities | 90% |
| Views | 80% |
| Models | 85% |
| Integration tests | Critical workflows covered |

Coverage is a guideline, not a target. 100% coverage of untested business logic is preferable to 90% coverage of tested business logic. The goal is to ensure that every significant behavior is tested, not to hit a number.

---

## 8. Refactoring Principles

### 8.1 Always Use Compatibility Wrappers

When moving or renaming code, always leave a compatibility wrapper at the old location. The wrapper re-exports the new implementation with a deprecation warning.

**Rationale:** Compatibility wrappers allow call sites to be migrated gradually, one PR at a time, with zero production risk.

### 8.2 Refactor in Small PRs

Each refactoring step must be a separate PR with its own tests, review, and merge. A PR that moves an entire app, merges two apps, and restructures services is too large to review safely.

**Rationale:** Small PRs are easier to review, easier to test, and easier to revert. They enable continuous refactoring without blocking feature development.

### 8.3 Zero Breaking Changes

No refactoring PR may introduce a breaking change to a public interface. If a public interface must change, the change must be backward compatible: old callers continue to work, and a deprecation warning guides them to the new interface.

**Rationale:** Breaking changes force coordinated deployments. Zero breaking changes enable independent, continuous deployment.

### 8.4 Delete Dead Code

When a compatibility wrapper is no longer imported by any call site, it must be deleted. When a feature is disabled and its code is no longer used, it must be deleted. Dead code is a defect.

**Rationale:** Dead code increases cognitive load, creates confusion, and may contain security vulnerabilities.

### 8.5 One Canonical Implementation

After consolidation, there must be exactly one implementation of every business capability. If two implementations exist, one is canonical and the other is a temporary compatibility wrapper that will be deleted.

**Rationale:** One implementation means one place to fix bugs, one place to add features, and one place to test.

---

## 9. Definition of Done

A change is not complete until all of the following criteria are met:

1. **Tests pass.** All unit tests, integration tests, and architecture tests pass locally and in CI.
2. **Architecture rules pass.** Import-linter and custom architecture tests pass. No new violations are introduced.
3. **Documentation updated.** Architecture Decision Records, API documentation, and inline docstrings are updated to reflect the change.
4. **Type checking passes.** `mypy` or equivalent passes with zero errors.
5. **Lint passes.** `ruff`, `flake8`, or equivalent passes with zero errors.
6. **No duplicated implementation exists.** The change does not introduce duplicate services, duplicate utilities, or duplicate models.
7. **Backward compatibility maintained.** No public interface is broken. Compatibility wrappers are used for any moved or renamed code.
8. **Error handling is correct.** No bare except, no silent failures, no unhandled exceptions in business logic.
9. **Logging is present.** Significant business events and errors are logged with structured context.
10. **Security review completed.** The change does not introduce new vulnerabilities, expose secrets, or bypass authentication or authorization.

A PR that does not meet all criteria must not be merged.

---

## 10. Future Architecture Vision

### 10.1 Intentional Modular Monolith

RentSecure is intentionally designed as a modular monolith. The bounded contexts are organized by business capability, not by technical layer. They communicate through clean public interfaces. They have no circular dependencies. They are organized such that extraction to microservices is possible—but only when the business justifies it.

**Extraction triggers:**
- Monthly transaction volume exceeds 500,000 requests.
- Multiple engineering teams require independent deployment cycles.
- A specific bounded context requires a different technology stack (e.g., a real-time analytics engine).
- Operational requirements (e.g., multi-region deployment) cannot be met by a monolith.

**When extraction occurs:**
1. The bounded context's public interface is extracted as a REST or gRPC API.
2. Data ownership is clearly defined: the extracted service owns its data.
3. Cross-context communication uses async events or synchronous API calls, depending on consistency requirements.
4. The extraction is done incrementally: first the API, then the data, then the dependent callers.

### 10.2 Extraction Points

The following bounded contexts are designed for easy extraction:
- `notification`: Stateless, event-driven, clear interface.
- `analytics`: Read-only, can be served from a read replica or separate data store.
- `documents`: Stateless, can be scaled horizontally.
- `payments`: Requires strong consistency, but the adapter pattern makes extraction straightforward.

The following bounded contexts are likely to remain in the monolith:
- `core`: Identity and access are foundational and shared.
- `properties`: Central to the business, requires strong consistency with `finance`.
- `finance`: Financial data requires ACID transactions.

---

## 11. Appendix: Architecture Commandments

These commandments are the distilled essence of the architecture principles. Every developer must internalize them.

1. **Business logic never belongs in Views.** Views are HTTP adapters. Services own business logic.
2. **No duplicate services.** Every capability has one canonical implementation.
3. **Every dependency must have a reason.** If you cannot explain why A depends on B, remove the dependency.
4. **Delete dead code.** Unused code is a defect.
5. **Prefer composition.** Build complex behavior from simple components.
6. **Every bounded context has one owner.** Ownership is by capability, not by file type.
7. **No circular imports.** If two modules depend on each other, extract the shared logic.
8. **Signals trigger events; services perform work.** Signals must not contain business logic.
9. **Utilities contain transformations, not workflows.** Utilities must not have side effects.
10. **Public interfaces are contracts.** Do not import private modules from other bounded contexts.
11. **No bare except and no silent failures.** Every error must be explicit and logged.
12. **Testability is a design requirement.** If you cannot test it easily, refactor it until you can.
13. **Backward compatibility is mandatory.** No breaking changes without a migration path.
14. **Refactor in small PRs.** Large changes are dangerous and impossible to review.
15. **Production stability beats code beauty.** A working system is better than a broken beautiful system.
16. **YAGNI.** Do not build for futures that may never arrive.
17. **KISS.** The simplest solution that works is the best solution.
18. **DRY.** One implementation, one location, one source of truth.
19. **SOLID.** Every class and module must follow the five SOLID principles.
20. **Consistency over cleverness.** Readable, consistent code is better than clever, concise code.

---

*Document ratified by the Principal Software Architect. All backend development must comply with these principles. Violations must be justified in an Architecture Decision Record and approved by the Principal Architect.*
