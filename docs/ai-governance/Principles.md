# AI Governance

## Principles

1. **Human-in-the-Loop**: All AI-generated code, diagrams, and documentation must be reviewed by a human before merging.
2. **Transparency**: AI-generated content must be clearly marked and traceable to its prompt version.
3. **Reproducibility**: Every AI-generated artifact must include the prompt version, model, and inputs used.
4. **Safety**: AI must never generate code that bypasses security controls or degrades system quality.
5. **Privacy**: AI must never process secrets, credentials, or PII in prompts or generated code.

## AI Rules

### Code Generation

- AI-generated code must pass all existing tests
- AI-generated code must follow the project's coding standards (ruff, mypy, pylint)
- AI-generated code must not introduce new dependencies without approval
- AI-generated code must include type annotations
- AI-generated code must not modify architecture contracts without approval

### Diagram Generation

- AI-generated diagrams must be validated by the UML validation workflow
- AI-generated diagrams must not include secrets or credentials
- AI-generated diagrams must use the project's standard formats (PlantUML, Mermaid, C4)
- AI-generated diagrams must be committed back to the repository

### Documentation Generation

- AI-generated documentation must be reviewed for accuracy
- AI-generated documentation must follow the project's markdown standards
- AI-generated documentation must include version and generation date

### Prompt Versioning

- All prompts must be versioned following semantic versioning
- All prompts must be stored in `docs/ai/prompts/`
- All prompts must include required metadata (version, author, date, purpose)
- Prompts must not be modified without updating the version

### Repository Modification

- AI must never delete existing files without explicit user instruction
- AI must never modify files outside the designated scope
- AI must always backup or create copies before destructive operations
- AI must follow the project's existing code style and patterns

## Hallucination Prevention

1. **Source-of-Truth Verification**: AI must verify claims against actual repository files
2. **No Invented Decisions**: ADRs must only be created for real, documented decisions
3. **No Fake Architecture**: Diagrams must reflect actual code structure, not assumed structure
4. **Prompt Validation**: Prompts must be reviewed for ambiguous instructions that could lead to hallucinations

## Review Process

1. AI generates content
2. Human reviews for accuracy and completeness
3. Human approves or requests changes
4. Approved content is committed to repository

## Escalation

If AI-generated content is uncertain or potentially harmful:
1. Do not commit the content
2. Flag for human review
3. Document the concern in the PR
