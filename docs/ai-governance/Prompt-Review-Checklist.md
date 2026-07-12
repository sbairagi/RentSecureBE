# Prompt Review Checklist

Use this checklist before submitting any AI prompt for approval.

## Prompt Quality

- [ ] Prompt has a single, clear objective
- [ ] Prompt specifies the expected output format
- [ ] Prompt includes constraints and edge cases
- [ ] Prompt does not contain ambiguous instructions
- [ ] Prompt has been tested with at least one sample input

## Safety

- [ ] Prompt does not request secrets, credentials, or PII
- [ ] Prompt does not request modification of protected files without authorization
- [ ] Prompt does not request bypassing security controls
- [ ] Prompt does not request deleting existing code without explicit instruction

## Reproducibility

- [ ] Prompt includes version number
- [ ] Prompt specifies compatible repository versions
- [ ] Prompt documents required dependencies
- [ ] Prompt documents expected outputs

## Documentation

- [ ] Prompt includes purpose description
- [ ] Prompt documents input requirements
- [ ] Prompt documents output format
- [ ] Prompt documents known limitations
- [ ] Prompt includes usage examples

## Architecture Compliance

- [ ] Prompt respects `import-linter` rules
- [ ] Prompt does not request changes to CI/CD pipeline without approval
- [ ] Prompt follows existing code style guidelines
- [ ] Prompt does not introduce new dependencies without approval

## Review Sign-off

- [ ] Reviewed by: _________________
- [ ] Date: _________________
- [ ] Approved: [ ] Yes [ ] No [ ] Needs Revision
