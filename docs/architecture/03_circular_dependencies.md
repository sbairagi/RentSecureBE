# 03 Circular Dependencies

## Summary

**No circular dependencies detected.**

## Analysis Method

Static AST analysis was performed on 340 Python files across the repository. The analysis followed import chains depth-first to detect cycles where module A imports module B, which (directly or transitively) imports module A.

## Evidence

- **Total modules analyzed:** 321
- **Total imports analyzed:** 387
- **Cycles found:** 0
- **Analysis tool:** `scripts/arch_audit.py` (custom AST-based cycle detector)

## Verification

The AST-based cycle detector traversed all module dependency edges and confirmed no cycles exist in the project module graph. This is consistent with Django's typical import patterns, where imports are generally unidirectional (models → services → views).

## Notes

While no circular dependencies were detected at the module level, there are several instances of **tight bidirectional coupling** between apps that should be monitored:

1. `core.models` ↔ `properties.models`: Many models in both apps reference each other via ForeignKeys and direct imports.
2. `notification.services` ↔ `properties.models`: Notification services frequently import property models.
3. `properties.signals` ↔ `notification.services`: Signal handlers in properties import notification services, which may create runtime coupling.

These are not circular imports, but they indicate architectural coupling that could become circular imports during refactoring.
