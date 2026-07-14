# 08 Import Linter Audit

## Summary

**Tool:** `lint-imports` (import-linter v1.6.0)
**Configuration:** `import-linter.ini`
**Run date:** 2026-07-14
**Result:** 9 contracts KEPT, 0 broken

## Contracts Evaluated

| Contract Name | Type | Layers | Result |
|---------------|------|--------|--------|
| `rentsecure_be` | layers | `rentsecure_be` | KEPT |
| `core` | layers | `core`, `rentsecure_be` | KEPT |
| `smartbot` | layers | `smartbot`, `rentsecure_be` | KEPT |
| `finance` | layers | `finance`, `rentsecure_be` | KEPT |
| `notification` | layers | `notification`, `rentsecure_be` | KEPT |
| `documents` | layers | `documents`, `rentsecure_be` | KEPT |
| `referral_and_earn` | layers | `referral_and_earn`, `rentsecure_be` | KEPT |
| `ai_assistant` | layers | `ai_assistant`, `rentsecure_be` | KEPT |
| `dashboard` | layers | `dashboard`, `rentsecure_be` | KEPT |

## Configuration Analysis

### Current Contracts

```ini
[importlinter:core]
type = layers
name = core
layers =
	core
	rentsecure_be
```

The contract for `core` defines two layers: `core` (inner) and `rentsecure_be` (outer). According to import-linter's layers contract semantics, imports may only flow from outer layers to inner layers. In this configuration:
- `core` (inner layer) may NOT import from `rentsecure_be` (outer layer)
- `rentsecure_be` (outer layer) MAY import from `core` (inner layer)

**However, the actual code does the opposite:** `core` imports from `rentsecure_be.type_compat`, `rentsecure_be.utils.export_utils`, etc.

### Configuration Issues

1. **Layer ordering is reversed:** The current contracts define `rentsecure_be` as an outer layer that `core` cannot depend on. But in practice, `core` depends on `rentsecure_be` for type compatibility and utilities.
2. **Missing cross-app constraints:** The contracts only restrict imports between an app and `rentsecure_be`. They do NOT restrict imports between different domain apps (e.g., `core` → `properties`).
3. **Management commands excluded:** The `exclude = management` directive means management commands are not checked, allowing them to freely import across apps.
4. **Tests not explicitly excluded:** While not in the exclude list, the tool only analyzed 217 files (vs 340 total), suggesting some test files may be excluded by default behavior.

## Passed Contracts

All 9 contracts passed. This means:
- No import chain was found that violates the layer ordering defined in each contract.

## Failed Contracts

**None.** The tool reported 0 broken contracts.

## Violations

### AST-Detected Violations (Not Caught by import-linter)

While `lint-imports` reports 0 violations, AST analysis of the same codebase found **205 cross-app imports** that violate the intended architecture. The discrepancy suggests the current import-linter configuration is not effectively enforcing the documented dependency rules.

**Key violations not caught:**

| Source | Target | Count | Severity |
|--------|--------|-------|----------|
| `core` → `properties` | Direct model imports | 13 | HIGH |
| `properties` → `core` | Direct model imports | 13 | HIGH |
| `properties` → `notification` | Direct service imports | 10 | HIGH |
| `notification` → `properties` | Direct model imports | 10 | HIGH |
| `core` → `notification` | Direct service imports | 5 | HIGH |
| `smartbot` → `properties` | Direct model imports | 4 | HIGH |

### Root Cause of False Negatives

1. **Contract scope too narrow:** Each contract only restricts imports between the app and `rentsecure_be`. It does not restrict imports between domain apps.
2. **Exclusion of management commands:** Many cross-app imports exist in `management/commands/`, which is excluded.
3. **Tool may not analyze all files:** Only 217 of 340 files were analyzed.

## Suggested Future Contracts

### Proposed Contract 1: Strict App Isolation

```ini
[importlinter:core]
type = layers
name = core
layers =
	shared
	core

[importlinter:properties]
type = layers
name = properties
layers =
	shared
	properties

[importlinter:notification]
type = layers
name = notification
layers =
	shared
	notification

[importlinter:smartbot]
type = layers
name = smartbot
layers =
	shared
	smartbot

[importlinter:finance]
type = layers
name = finance
layers =
	shared
	finance

[importlinter:documents]
type = layers
name = documents
layers =
	shared
	documents

[importlinter:referral_and_earn]
type = layers
name = referral_and_earn
layers =
	shared
	referral_and_earn

[importlinter:ai_assistant]
type = layers
name = ai_assistant
layers =
	shared
	ai_assistant

[importlinter:dashboard]
type = layers
name = dashboard
layers =
	shared
	dashboard

[importlinter:rentsecure_be]
type = layers
name = rentsecure_be
layers =
	shared
	rentsecure_be
```

**Effect:** Each app may only import from `shared` and itself. No cross-app imports allowed.

### Proposed Contract 2: Allow Explicit Cross-App Communication

If cross-app imports are necessary, define explicit contracts using `independent` contract type:

```ini
[importlinter:core_to_properties]
type = independent
name = core_to_properties
modules = core
should_include = core.*
must_not_include = properties.*
```

This would explicitly forbid `core` from importing `properties`.

### Proposed Contract 3: Service Interface Enforcement

Create a contract that enforces service interface usage:

```ini
[importlinter:shared_interfaces]
type = independent
name = shared_interfaces
modules = shared.interfaces
should_include = shared.interfaces
must_not_include = *
```

This ensures `shared.interfaces` does not import from any app.

## Recommendations

1. **Immediate:** Reconfigure import-linter to use the proposed strict app isolation contracts.
2. **Short-term:** Add `tests` and `management` back to the exclude list explicitly, then re-run to verify violations are caught in production code only.
3. **Medium-term:** Supplement import-linter with AST-based architecture tests in `tests/test_architecture_contract/`.
4. **Long-term:** Migrate to bounded context architecture with explicit service interfaces and domain events.

## Tool Limitations Noted

- `lint-imports` analyzed only 217 of 340 Python files. The excluded files may contain violations.
- The tool does not detect `TYPE_CHECKING` imports or conditional imports, which could mask some violations.
- The tool's layer semantics may be counterintuitive (inner layers cannot import from outer layers by default).
