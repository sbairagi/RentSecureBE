# AI Rules

## Scope

These rules apply to all AI-assisted development activities in the RentSecureBE project.

## Code Generation Policy

1. **No New Dependencies Without Approval**: AI must not introduce new pip dependencies without explicit human approval.
2. **Follow Existing Patterns**: AI must study existing code before generating new code.
3. **Type Safety First**: All generated code must be fully type-annotated and pass `mypy --strict`.
4. **Tests Required**: All generated code must include tests.
5. **No Architecture Violations**: Generated code must not violate `import-linter` rules.

## Documentation Policy

1. **Mark Existing Docs**: AI-generated documentation must include a header indicating it was AI-generated.
2. **Version Everything**: All generated docs must include version and date.
3. **Link to Source**: Generated docs must reference the source files they describe.

## Prompt Review Checklist

- [ ] Prompt has a clear, unambiguous goal
- [ ] Prompt includes all necessary context
- [ ] Prompt specifies output format
- [ ] Prompt includes constraints and limitations
- [ ] Prompt has been tested with sample inputs
- [ ] Prompt does not request secrets or credentials
- [ ] Prompt does not request modification of protected files

## Security Review Policy

- AI must never generate code that bypasses authentication
- AI must never generate code that bypasses authorization
- AI must never generate code that exposes secrets
- AI must flag potential security issues in existing code

## Code Review Policy

- AI-assisted PRs must include a note indicating AI was used
- AI-generated code receives the same scrutiny as human-generated code
- All CI checks must pass before merge
- Architecture guard must not be bypassed

## Contribution Guide

See `docs/ai-governance/AI-Contribution-Guide.md` for the AI contribution workflow.
