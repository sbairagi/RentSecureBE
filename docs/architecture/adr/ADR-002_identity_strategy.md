# ADR-002: Identity Strategy

**Status:** Accepted
**Date:** 2026-07-19
**Deciders:** Chief Software Architect, Staff Engineer, Platform Team Lead
**Supersedes:** ADR-003 (v1.0 — Service Layer, partial)

---

## Context

RentSecureBE's identity concerns are currently scattered across `core/models.py` (User, UserProfile, OTP), `core/views.py` (authentication, password, OTP views), and `core/services/` (AuthService, OTPService, PasswordService). The v1.0 architecture proposed moving the Django `AUTH_USER_MODEL` from `core.User` to a new `identity.User` model. However, Django does not support:

- Dual concrete `User` models coexisting
- Proxy-based `AUTH_USER_MODEL` transitions
- Changing `AUTH_USER_MODEL` after the database is created without a full data migration that breaks all ForeignKeys

Attempting the v1.0 `AUTH_USER_MODEL` migration would cause `RuntimeError`, migration conflicts, and data integrity failures. All 63 modules importing `core.models.User` directly would break when `AUTH_USER_MODEL` flips.

The identity strategy must preserve the existing `User` model while extracting identity *services* into their own bounded context.

---

## Decision

RentSecureBE uses a **Model Container + Service Extraction** identity strategy.

### Key Rules

1. **`core.User` remains `AUTH_USER_MODEL` permanently.** No migration of the Django user model.
2. **`core/` is the identity model container.** It contains only `User`, `UserProfile`, and `OTP` models after Phase 5.
3. **Identity services live in `identity/services/`.** `AuthService`, `OTPService`, and `PasswordService` are extracted from `core/services/` in Phase 1.
4. **Identity views live in `identity/views/`.** Views are extracted from `core/views/` in Phase 1–4 and removed from `core/` in Phase 5.
5. **`core/` is renamed to `identity/` in Phase 5.** The directory is renamed to reflect its role as the identity model container. All imports are updated.
6. **No `identity.User` model is created.** The `User` model stays in `identity/models.py` (renamed from `core/models.py`).
7. **All ForeignKeys use `settings.AUTH_USER_MODEL` string references.** Direct imports of `core.models.User` are forbidden in Phase 0.

### Target State (Post-Phase 5)

```
identity/
├── models.py          # User, UserProfile, OTP only
├── services/          # AuthService, OTPService, PasswordService
├── views/             # Auth, OTP, Password views
├── tests/
└── migrations/
```

### Extraction Sequence

| Phase | Action |
|-------|--------|
| Phase -1 | Break `core ↔ rentsecure_be` cycle by moving `type_compat.py` to `shared/` |
| Phase 0 | Split `core/views.py` into 4 focused modules; enforce `settings.AUTH_USER_MODEL` string references |
| Phase 1 | Extract `AuthService`, `OTPService`, `PasswordService` to `identity/services/`; update all cross-app imports |
| Phase 5 | Remove all views from `core/`; rename `core/` to `identity/` |

---

## Alternatives Considered

### 1. Move `User` Model to `identity/` (v1.0 Approach)

**Description:** Create `identity.User`, migrate all data, update `AUTH_USER_MODEL`, remove `core.User`.

**Pros:**
- Clean separation: identity app owns the User model
- Aligns with DDD principles (identity context owns identity aggregate)

**Cons:**
- Django does not support dual user models during transition
- `AUTH_USER_MODEL` is a project-wide singleton; cannot point to two models
- All 63 ForeignKeys to `User` must be updated simultaneously
- Proxy models do not solve the problem (shared table, separate migration histories)
- Data migration for `User` table is high-risk (affects authentication)
- Rollback requires restoring from backup

**Decision:** Rejected. Architecturally impossible in Django without breaking the project.

### 2. Keep Everything in `core/` Forever

**Description:** Do not extract identity services. Leave `core/` as a God app.

**Pros:**
- No migration effort
- Simple for small team

**Cons:**
- `core/` accumulates responsibilities (payment, subscription, reporting)
- Team autonomy is limited (Platform and Product teams both modify `core/`)
- Future extraction becomes harder as `core/` grows
- `core/` becomes a bottleneck for deployments

**Decision:** Rejected. Accumulates unmanageable technical debt.

### 3. Model Container + Service Extraction (Selected)

**Description:** Keep `User` model in `core/` (renamed to `identity/` in Phase 5). Extract services and views to `identity/` subdirectories in Phases 1–4.

**Pros:**
- Avoids impossible `AUTH_USER_MODEL` migration
- Services are testable and independently deployable
- Clear ownership: Platform Team owns `identity/`
- Gradual extraction with backward-compatible shims
- `core/` shrinks to models only, then is renamed

**Cons:**
- `core/` name is misleading during transition (contains only models, not services)
- Requires a rename operation in Phase 5
- Some legacy code references `core.` for identity concerns

**Decision:** Accepted. Best balance of safety and architectural cleanliness.

---

## Consequences

### Positive
- `AUTH_USER_MODEL` migration is avoided entirely (eliminates Critical risk)
- Identity services are testable in isolation
- Platform Team owns the complete identity flow
- `core/` shrinks to a model container, then is renamed
- ForeignKey updates use string references, making the model "movable" in theory
- Gradual extraction with deprecated shims ensures zero downtime

### Negative
- `core/` name is misleading during Phases 0–4 (it's not "core" anymore, it's "identity models")
- Requires a directory rename in Phase 5 (low risk but requires import updates)
- Some legacy code still references `core.services.auth_service` during transition

### Neutral
- `User` model location is stable (no data migration for the most critical table)
- Identity views are extracted last (Phase 5) because they depend on services being extracted first
- OTP logging is removed in Phase 0 (security fix)

---

## Migration Notes

### Phase 0: Preparation
- Split `core/views.py` into `auth_views.py`, `subscription_views.py`, `bank_views.py`, `reporting_views.py`
- Enforce `settings.AUTH_USER_MODEL` string references in all new ForeignKeys
- Remove `print()` OTP logging from `send_otp`

### Phase 1: Service Extraction
- Create `identity/services/` package
- Move `AuthService`, `OTPService`, `PasswordService` from `core/services/` to `identity/services/`
- Update `core/views/auth_views.py` and `core/views/password_views.py` to import from `identity/services/`
- Update all cross-app imports (5+ files across apps)
- Add `identity/tests/unit/` and `identity/tests/integration/`
- Deprecate `core/services/auth_service.py`, `otp_service.py`, `password_service.py` (shims or removed)

### Phase 5: Deprecate Core / Rename
- Remove all views from `core/views/`
- Remove all services from `core/services/`
- Rename `core/` directory to `identity/`
- Update all remaining `core.` imports to `identity.`
- Release as v2.0.0 (breaking change)

### Rollback
- Phase 1: Revert PR. `core/services/` files remain. `identity/services/` is removed.
- Phase 5: Restore `core/` from v1.x LTS branch. Redeploy previous version. Estimated 2–4 hours.

---

## Future Evolution

### Short-term (Phase 6)
- `identity/` may introduce event publishing for `UserCreated`, `UserDeleted` events
- OTP service may integrate with Firebase Auth or similar for phone authentication
- Password service may integrate with HaveIBeenPwned for breach detection

### Medium-term (Stage 2)
- If team grows, `identity/` can be extracted as a microservice with its own database
- OAuth2 / SSO integration for enterprise customers
- Multi-tenant identity with tenant isolation

### Long-term
- `identity/` remains a first-class bounded context
- No further splitting of identity concerns (User, Profile, OTP are cohesive)
- Encryption at rest for PII fields (email, phone) added as regulatory requirement

---

## References

- [Architecture v1.1 Release Candidate — Finding AD-01](../../../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Implementation Master Plan — Phase 1](../../../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Django AUTH_USER_MODEL Documentation](https://docs.djangoproject.com/en/stable/topics/auth/customizing/#substituting-a-custom-user-model)
