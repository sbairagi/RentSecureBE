# AI Security Review

## Scope

This policy applies to all AI-assisted code generation, infrastructure changes, and security configurations.

## Security Review Requirements

1. **All AI-generated security-related code must be reviewed** by the security team.
2. **AI must not generate code that bypasses security controls** under any circumstances.
3. **AI must flag potential security issues** in existing code when requested.

## Review Checklist

### Authentication
- [ ] Does the code properly authenticate users?
- [ ] Does it use JWT tokens securely?
- [ ] Are tokens stored and transmitted securely?

### Authorization
- [ ] Does the code enforce proper access controls?
- [ ] Does it check ownership before allowing operations?
- [ ] Does it prevent privilege escalation?

### Input Validation
- [ ] Does the code validate all inputs?
- [ ] Does it sanitize user inputs?
- [ ] Does it protect against SQL injection?
- [ ] Does it protect against XSS?

### Secrets Management
- [ ] Are secrets stored in environment variables?
- [ ] Are secrets never logged?
- [ ] Are secrets never exposed in error messages?
- [ ] Are secrets never committed to git?

### Data Protection
- [ ] Is sensitive data encrypted at rest?
- [ ] Is sensitive data encrypted in transit?
- [ ] Does the code follow data retention policies?

## Prohibited Patterns

AI must never generate:
- Hardcoded secrets or credentials
- Bypass of authentication checks
- Bypass of authorization checks
- Insecure direct object references
- SQL injection patterns
- XSS patterns
- Unsafe deserialization
- Command injection patterns

## Reporting

Security issues found by AI must be reported immediately to the security team and documented in a security ADR.
