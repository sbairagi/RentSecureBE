# Architecture Compliance Review

## Version
1.0.0

## Author
RentSecureBE Team

## Created Date
2026-07-13

## Updated Date
2026-07-13

## Compatible Repository Version
>=2.4.0

## Purpose
Review code changes for compliance with architecture contract, import-linter rules, and service layer pattern.

## Inputs
- Changed files
- Architecture contract rules
- Import-linter configuration

## Outputs
- Compliance report
- Violations list
- Required fixes

## Limitations
- Cannot catch all violations
- Requires human review
- Should not approve own changes

## Usage
```bash
python scripts/architecture_contract.py --verbose
```
