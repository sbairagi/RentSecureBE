# AI Code Review Policy

## Scope

This policy applies to all code generated or modified with AI assistance in the RentSecureBE project.

## Review Requirements

1. **All AI-generated code must be reviewed** by at least one human developer before merging.
2. **AI-assisted PRs must include a note** in the PR description indicating:
   - Which files were generated or modified by AI
   - Which prompts were used
   - Which model/version was used
3. **All existing CI checks must pass** — no exceptions.

## Review Focus Areas

### Correctness
- Does the code do what it claims to do?
- Are edge cases handled?
- Is error handling appropriate?

### Security
- Does the code introduce any security vulnerabilities?
- Does it bypass authentication or authorization?
- Does it expose any secrets or PII?

### Performance
- Does the code introduce N+1 queries?
- Does it use caching appropriately?
- Does it handle large datasets efficiently?

### Maintainability
- Is the code readable and well-structured?
- Does it follow the project's patterns?
- Is it properly typed?

### Architecture Compliance
- Does it respect `import-linter` rules?
- Does it place logic in the correct layer (views → services)?
- Does it follow the service layer pattern?

## Approval Matrix

| Change Type | Required Approver |
|-------------|-------------------|
| Bug fix | Any developer |
| Feature | Senior developer |
| Architecture change | Tech lead |
| Security-related | Security lead |
| CI/CD pipeline | Senior DevOps |
| Database migration | Tech lead |

## Rejection Criteria

Code should be rejected if:
- It fails any CI check
- It introduces security vulnerabilities
- It violates architecture contracts
- It is not properly tested
- It lacks documentation
- It introduces unapproved dependencies
