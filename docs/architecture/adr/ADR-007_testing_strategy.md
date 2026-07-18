# ADR-007: Testing Strategy

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

RentSecure needs a testing strategy that provides confidence for refactoring while maintaining fast feedback loops. The current test suite has some unit tests but lacks:
- Clear test categorization
- Contract tests between contexts
- Architecture tests
- Performance tests
- Consistent test patterns

---

## Decision

RentSecure uses a **four-tier testing strategy**:

1. **Unit Tests:** Test individual classes and functions in isolation
2. **Integration Tests:** Test interaction between components within a context
3. **Contract Tests:** Test public APIs between contexts
4. **Architecture Tests:** Test architecture rules (import boundaries, layer rules)

**Key principles:**
- Fast tests run first (unit → integration → contract → architecture)
- Tests are colocated with source code
- Shared test infrastructure in `tests/`
- Test factories for test data generation
- Coverage target: > 80%

---

## Alternatives Considered

### 1. Only Integration Tests

**Description:** Test only through the Django stack.

**Pros:**
- Tests real behavior
- No mocking needed

**Cons:**
- Slow execution
- Hard to isolate failures
- Difficult to test edge cases
- Low feedback frequency

**Decision:** Rejected. Too slow for TDD.

### 2. Only Unit Tests with Heavy Mocking

**Description:** Test everything in isolation with mocks.

**Pros:**
- Very fast
- Easy to isolate failures

**Cons:**
- Miss integration issues
- Mocks can hide real problems
- Over-mocking leads to fragile tests

**Decision:** Rejected. Needs integration tests.

### 3. Four-Tier Strategy (Selected)

**Description:** Unit + Integration + Contract + Architecture tests.

**Pros:**
- Fast feedback (unit tests)
- Confidence in integration (integration tests)
- Cross-context safety (contract tests)
- Architecture enforcement (architecture tests)
- Balanced speed and confidence

**Cons:**
- More test code to maintain
- Requires test infrastructure

**Decision:** Accepted. Best balance.

---

## Consequences

### Positive
- Fast feedback for developers
- Confidence in refactoring
- Cross-context contracts are tested
- Architecture rules are enforced by tests
- Test failures are easy to diagnose

### Negative
- More test code to maintain
- Requires test infrastructure investment
- CI time increases (mitigated by parallelization)

### Neutral
- Target coverage: > 80%
- Tests run in CI on every PR
- Architecture tests run in every build

---

## Test Organization

```
tests/
├── factories.py                 # Shared test factories
├── conftest.py                  # Shared fixtures
├── test_architecture_contract/  # Architecture tests
│   ├── test_dependencies.py
│   ├── test_layer_rules.py
│   └── test_validator.py
├── test_api_contracts/          # API contract tests
├── test_performance_benchmarks.py
└── load/
    └── locustfile.py

apps/<context>/tests/
├── unit/                        # Unit tests
│   ├── test_services/
│   ├── test_policies/
│   └── test_entities/
├── integration/                 # Integration tests
│   ├── test_repositories/
│   └── test_workflows/
└── contract/                    # Contract tests with other contexts
    └── test_identity_contract.py
```

---

## References

- [Testing Rules](../../../.kilo/instructions/testing.md)
- [Architecture Principles](../../../architecture/ARCHITECTURE_PRINCIPLES.md)
