# Security and Secret Handling

## Reliability Rules
- All payment flows must be idempotent.
- Webhooks must support retries.
- All async tasks must support retry policies.
- Use distributed locking for critical financial operations.
