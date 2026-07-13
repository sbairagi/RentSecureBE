# Architecture Principles

These principles govern every architecture phase of the RentSecureBE transformation.

## 1. Modular Monolith
The system remains a single deployable unit throughout the transformation. Service extraction is a future possibility, not an immediate goal.

## 2. Domain-First Design
Structure follows domain boundaries, not technical layers. Each bounded context owns its data, logic, and APIs.

## 3. Clear Bounded Contexts
Each Django app or package represents a bounded context with explicit entry points and no leakage outside its boundary.

## 4. Service Layer
All business logic lives in services, not views or serializers. Views coordinate, services execute.

## 5. Dependency Direction
Dependencies flow inward only. Outer layers depend on inner layers, never the reverse.

## 6. Thin Views
Views handle HTTP concerns (request/response, auth, permissions) and delegate to services. No business logic in views.

## 7. Fat Services
Services contain the full workflow for a use case. They are the only place business rules are implemented.

## 8. No Business Logic in Serializers
Serializers validate and transform data for transport. They do not enforce business rules.

## 9. No Cross-Layer Leakage
Models do not know about views. Services do not know about HTTP. Domains do not import from each other directly.

## 10. Backward Compatibility
External APIs never change during architecture phases. Internal refactoring is invisible to API consumers.

## 11. CI Always Green
Every commit must pass the full CI pipeline. Architecture phases never introduce failing tests or broken builds.

## 12. Incremental Change
No phase changes more than one bounded context. Small, reversible changes are preferred over large rewrites.

## 13. Contract-First
Interfaces between contexts are defined before implementation. Contract tests verify behavior across boundaries.

## 14. Documentation as Code
Architecture decisions, principles, and contracts are versioned alongside production code.

## 15. Explicit Over Implicit
Imports, dependencies, and data flows must be visible. No hidden coupling or magic imports.

## 16. Testability by Design
Every service is independently testable. No test requires a full Django stack unless testing integration.

## 17. Observability
Logs, metrics, and traces are added with every new component. Architecture changes do not reduce observability.

## 18. Security by Default
Authentication, authorization, and validation are applied at every boundary. Architecture changes do not bypass security.
