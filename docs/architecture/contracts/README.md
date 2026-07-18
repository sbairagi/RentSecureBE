# Architecture Contracts

This directory contains architecture contracts that enforce module boundaries and interface agreements between bounded contexts.

## Purpose

Architecture contracts formalize the agreements between bounded contexts. They define:

- What interfaces a context exposes
- What interfaces a context depends on
- What data flows across context boundaries
- What invariants must be maintained

## Contract Types

### Context Boundary Contracts

Define the public API surface of each bounded context. Each context must have a boundary contract that specifies:

- Exposed service interfaces
- Exposed model interfaces
- Exposed event interfaces
- Prohibited imports (what the context must not depend on)

Location: `docs/architecture/contracts/{context}-boundary.md`

### Service Interface Contracts

Define the exact signatures, return types, and exceptions for each service interface in `shared/interfaces.py`. Every service interface must have a contract document specifying:

- Method signatures with types
- Expected return values
- Exception contracts
- Side effect contracts

Location: `docs/architecture/contracts/{service}-interface.md`

### Adapter Contracts

Define the interface compliance requirements for each adapter. Every adapter must implement a defined interface and pass contract tests.

Location: `docs/architecture/contracts/{adapter}-contract.md`

## Contract Testing Rules

1. Every bounded context must have a contract test file at `{context}/tests/test_contracts.py`
2. Contract tests verify that the context does not import from prohibited packages
3. Contract tests verify that service interfaces match their contract documents
4. Contract tests run on every PR via CI
5. Contract test failures block CI

## Contract Registry

| Context | Contract Test File |
|---------|-------------------|
| identity | `identity/tests/test_contracts.py` |
| subscription | `subscription/tests/test_contracts.py` |
| properties | `properties/tests/test_contracts.py` |
| payments | `payments/tests/test_contracts.py` |
| notification | `notification/tests/test_contracts.py` |
| documents | `documents/tests/test_contracts.py` |
| ai | `ai/tests/test_contracts.py` |
| dashboard | `dashboard/tests/test_contracts.py` |

## Enforcement

- Contract violations are detected by `scripts/architecture_contract.py`
- Contract tests are run on every PR
- `import-linter.ini` enforces import boundaries
- Architecture review is required before any contract is modified

## Creating a New Contract

1. Define the interface or boundary in the appropriate bounded context
2. Create the contract document in this directory
3. Create or update the contract test in the bounded context's `tests/` directory
4. Update `import-linter.ini` if new boundaries are introduced
5. Submit PR for review
